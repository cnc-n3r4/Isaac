"""
Sync Queue - Queue operations for later synchronization
"""

import asyncio
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json
import uuid


class SyncQueue:
    """
    Manages queue of operations to sync when back online
    """

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            storage_path = Path.home() / '.isaac' / 'offline'

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.db_path = self.storage_path / 'sync_queue.db'
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_queue (
                id TEXT PRIMARY KEY,
                operation_type TEXT NOT NULL,
                data TEXT NOT NULL,
                priority INTEGER DEFAULT 5,
                created_at TEXT NOT NULL,
                retry_count INTEGER DEFAULT 0,
                last_retry TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')

        conn.commit()
        conn.close()

    async def add(
        self,
        operation_type: str,
        data: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """
        Add operation to queue

        Args:
            operation_type: Type of operation
            data: Operation data
            priority: Priority (1-10)

        Returns:
            Operation ID
        """
        operation_id = str(uuid.uuid4())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO sync_queue (id, operation_type, data, priority, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            operation_id,
            operation_type,
            json.dumps(data),
            priority,
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()

        return operation_id

    async def get_next(self) -> Optional[Dict[str, Any]]:
        """Get next operation from queue (highest priority first)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, operation_type, data, priority, created_at, retry_count
            FROM sync_queue
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        ''')

        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        return {
            'id': result[0],
            'operation_type': result[1],
            'data': json.loads(result[2]),
            'priority': result[3],
            'created_at': result[4],
            'retry_count': result[5]
        }

    async def mark_completed(self, operation_id: str):
        """Mark operation as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE sync_queue
            SET status = 'completed'
            WHERE id = ?
        ''', (operation_id,))

        conn.commit()
        conn.close()

    async def mark_failed(self, operation_id: str):
        """Mark operation as failed and increment retry count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE sync_queue
            SET retry_count = retry_count + 1,
                last_retry = ?,
                status = CASE
                    WHEN retry_count >= 3 THEN 'failed'
                    ELSE 'pending'
                END
            WHERE id = ?
        ''', (datetime.utcnow().isoformat(), operation_id))

        conn.commit()
        conn.close()

    async def process_all(self) -> Dict[str, Any]:
        """
        Process all pending operations in queue

        Returns:
            Statistics about processed operations
        """
        processed = 0
        failed = 0

        while True:
            operation = await self.get_next()

            if not operation:
                break

            try:
                # TODO: Actually execute the operation
                # For now, just mark as completed
                await self.mark_completed(operation['id'])
                processed += 1

            except Exception as e:
                print(f"Error processing operation {operation['id']}: {e}")
                await self.mark_failed(operation['id'])
                failed += 1

        return {
            'processed': processed,
            'failed': failed
        }

    def get_queue_size(self) -> int:
        """Get number of pending operations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM sync_queue WHERE status = "pending"')
        count = cursor.fetchone()[0]

        conn.close()

        return count

    def get_all_pending(self) -> List[Dict[str, Any]]:
        """Get all pending operations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, operation_type, data, priority, created_at, retry_count
            FROM sync_queue
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
        ''')

        results = cursor.fetchall()
        conn.close()

        return [
            {
                'id': row[0],
                'operation_type': row[1],
                'data': json.loads(row[2]),
                'priority': row[3],
                'created_at': row[4],
                'retry_count': row[5]
            }
            for row in results
        ]

    def clear_completed(self):
        """Remove completed operations from queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM sync_queue WHERE status = "completed"')

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM sync_queue
            GROUP BY status
        ''')

        results = cursor.fetchall()
        conn.close()

        stats = {row[0]: row[1] for row in results}

        return {
            'pending': stats.get('pending', 0),
            'completed': stats.get('completed', 0),
            'failed': stats.get('failed', 0),
            'total': sum(stats.values())
        }
