# isaac/queue/command_queue.py

"""
Command Queue - SQLite-based command persistence for offline resilience.

Provides atomic queue operations with retry tracking and automatic cleanup.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CommandQueue:
    """Local command queue with SQLite persistence."""

    def __init__(self, db_path: Path):
        """
        Initialize queue manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"Command queue initialized at {db_path}")

    def _init_db(self):
        """Create queue table and indexes if not exists."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS command_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                queued_at TEXT NOT NULL,
                command_type TEXT NOT NULL,
                command_text TEXT NOT NULL,
                target_device TEXT,
                retry_count INTEGER DEFAULT 0,
                last_retry_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                error_message TEXT,
                metadata TEXT
            )
        """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON command_queue(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_queued_at ON command_queue(queued_at)")
        conn.commit()
        conn.close()

    def enqueue(
        self,
        command: str,
        command_type: str,
        target_device: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> int:
        """
        Add command to queue.

        Args:
            command: Full command string
            command_type: 'meta' | 'shell' | 'device_route'
            target_device: Device alias for routing (None = local)
            metadata: Additional context (tier, validation, etc.)

        Returns:
            Queue ID for tracking
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute(
            """
            INSERT INTO command_queue
            (queued_at, command_type, command_text, target_device, metadata)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                datetime.utcnow().isoformat(),
                command_type,
                command,
                target_device,
                json.dumps(metadata or {}),
            ),
        )
        queue_id = cursor.lastrowid
        if queue_id is None:
            raise RuntimeError("Failed to get queue ID after insert")
        conn.commit()
        conn.close()

        logger.info(f"Queued command #{queue_id}: {command_type} - {command[:50]}...")
        return queue_id

    def dequeue_pending(self, limit: int = 10) -> List[Dict]:
        """
        Get pending commands in FIFO order.

        Args:
            limit: Maximum commands to retrieve

        Returns:
            List of command dicts with all fields
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT * FROM command_queue
            WHERE status='pending'
            ORDER BY queued_at ASC
            LIMIT ?
        """,
            (limit,),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def mark_syncing(self, queue_id: int):
        """Mark command as currently being synced."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            UPDATE command_queue
            SET status='syncing', last_retry_at=?
            WHERE id=?
        """,
            (datetime.utcnow().isoformat(), queue_id),
        )
        conn.commit()
        conn.close()

    def mark_done(self, queue_id: int):
        """Mark command as successfully synced."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            UPDATE command_queue
            SET status='done'
            WHERE id=?
        """,
            (queue_id,),
        )
        conn.commit()
        conn.close()
        logger.info(f"Command #{queue_id} synced successfully")

    def mark_failed(self, queue_id: int, error: str):
        """
        Mark command as failed, increment retry count.

        Args:
            queue_id: Command to mark
            error: Error message for logging
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            UPDATE command_queue
            SET status='failed',
                retry_count=retry_count+1,
                error_message=?,
                last_retry_at=?
            WHERE id=?
        """,
            (error, datetime.utcnow().isoformat(), queue_id),
        )
        conn.commit()
        conn.close()
        logger.warning(f"Command #{queue_id} failed: {error}")

    def reset_stale_syncing(self, timeout_minutes: int = 5):
        """
        Reset 'syncing' commands stuck for > timeout back to 'pending'.
        Prevents deadlock if sync worker crashes mid-sync.

        Args:
            timeout_minutes: How long before considering stuck
        """
        cutoff = (datetime.utcnow() - timedelta(minutes=timeout_minutes)).isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute(
            """
            UPDATE command_queue
            SET status='pending'
            WHERE status='syncing'
              AND last_retry_at < ?
        """,
            (cutoff,),
        )
        updated = cursor.rowcount
        conn.commit()
        conn.close()

        if updated > 0:
            logger.warning(f"Reset {updated} stale 'syncing' commands to 'pending'")

    def get_queue_status(self) -> Dict:
        """
        Get queue statistics.

        Returns:
            {pending: int, failed: int, done: int, last_sync: str}
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute(
            """
            SELECT status, COUNT(*) as count
            FROM command_queue
            GROUP BY status
        """
        )
        stats = {row[0]: row[1] for row in cursor.fetchall()}

        # Get last successful sync timestamp
        cursor = conn.execute(
            """
            SELECT MAX(queued_at) FROM command_queue WHERE status='done'
        """
        )
        last_sync = cursor.fetchone()[0]
        conn.close()

        return {
            "pending": stats.get("pending", 0),
            "failed": stats.get("failed", 0),
            "done": stats.get("done", 0),
            "last_sync": last_sync,
        }

    def clear_old_entries(self, days: int = 7):
        """
        Delete successfully synced commands older than N days.

        Args:
            days: Retention period for 'done' commands
        """
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute(
            """
            DELETE FROM command_queue
            WHERE status='done'
              AND queued_at < ?
        """,
            (cutoff,),
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old queue entries")
