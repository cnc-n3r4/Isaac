# isaac/core/message_queue.py

"""
Message Queue System - Notification management for autonomous AI assistant

Handles queuing and management of system and code-related notifications
with persistent storage and priority-based retrieval.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages in the queue."""

    SYSTEM = "system"  # ! - System operations, updates, monitoring
    CODE = "code"  # ¢ - Code operations, linting, testing, debugging


class MessagePriority(Enum):
    """Message priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageQueue:
    """
    Persistent message queue for AI assistant notifications.

    Stores messages by type (system/code) with priority and metadata.
    Provides queue management and retrieval operations.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize message queue.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            db_path = Path.home() / ".isaac" / "message_queue.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"Message queue initialized at {db_path}")

    def _init_db(self):
        """Create message queue table and indexes."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                message_type TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'normal',
                title TEXT NOT NULL,
                content TEXT,
                metadata TEXT,
                acknowledged_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending'
            )
        """
        )

        # Create indexes for efficient queries
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_messages_type_status
            ON messages(message_type, status)
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_messages_created
            ON messages(created_at)
        """
        )

        conn.commit()
        conn.close()

    def add_message(
        self,
        message_type: MessageType,
        title: str,
        content: str = "",
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Add a new message to the queue.

        Args:
            message_type: Type of message (system or code)
            title: Brief title/summary
            content: Detailed message content
            priority: Message priority level
            metadata: Additional structured data

        Returns:
            Message ID
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (created_at, message_type, priority, title, content, metadata, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """,
                (
                    datetime.now().isoformat(),
                    message_type.value,
                    priority.value,
                    title,
                    content,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            message_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added {message_type.value} message: {title}")
            return message_id
        finally:
            conn.close()

    def get_pending_counts(self) -> Dict[str, int]:
        """
        Get count of pending messages by type.

        Returns:
            Dict with 'system' and 'code' counts
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT message_type, COUNT(*)
                FROM messages
                WHERE status = 'pending'
                GROUP BY message_type
            """
            )

            counts = {"system": 0, "code": 0}
            for msg_type, count in cursor.fetchall():
                counts[msg_type] = count

            return counts
        finally:
            conn.close()

    def get_messages(
        self, message_type: Optional[MessageType] = None, status: str = "pending", limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve messages from the queue.

        Args:
            message_type: Filter by message type (None for all)
            status: Message status ('pending', 'acknowledged', 'all')
            limit: Maximum number of messages to return

        Returns:
            List of message dictionaries
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()

            query = """
                SELECT id, created_at, message_type, priority, title, content, metadata, acknowledged_at, status
                FROM messages
            """
            conditions = []
            params = []

            if message_type:
                conditions.append("message_type = ?")
                params.append(message_type.value)

            if status != "all":
                conditions.append("status = ?")
                params.append(status)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            messages = []
            for row in cursor.fetchall():
                msg = {
                    "id": row[0],
                    "created_at": row[1],
                    "message_type": row[2],
                    "priority": row[3],
                    "title": row[4],
                    "content": row[5],
                    "metadata": json.loads(row[6]) if row[6] else None,
                    "acknowledged_at": row[7],
                    "status": row[8],
                }
                messages.append(msg)

            return messages
        finally:
            conn.close()

    def acknowledge_message(self, message_id: int) -> bool:
        """
        Mark a message as acknowledged.

        Args:
            message_id: ID of message to acknowledge

        Returns:
            True if message was acknowledged, False if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE messages
                SET status = 'acknowledged', acknowledged_at = ?
                WHERE id = ? AND status = 'pending'
            """,
                (datetime.now().isoformat(), message_id),
            )

            success = cursor.rowcount > 0
            conn.commit()

            if success:
                logger.info(f"Acknowledged message {message_id}")

            return success
        finally:
            conn.close()

    def acknowledge_all(self, message_type: Optional[MessageType] = None) -> int:
        """
        Acknowledge all pending messages of a type.

        Args:
            message_type: Type of messages to acknowledge (None for all)

        Returns:
            Number of messages acknowledged
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()

            if message_type:
                cursor.execute(
                    """
                    UPDATE messages
                    SET status = 'acknowledged', acknowledged_at = ?
                    WHERE status = 'pending' AND message_type = ?
                """,
                    (datetime.now().isoformat(), message_type.value),
                )
            else:
                cursor.execute(
                    """
                    UPDATE messages
                    SET status = 'acknowledged', acknowledged_at = ?
                    WHERE status = 'pending'
                """,
                    (datetime.now().isoformat(),),
                )

            count = cursor.rowcount
            conn.commit()

            logger.info(f"Acknowledged {count} messages")
            return count
        finally:
            conn.close()

    def cleanup_old_messages(self, days: int = 30) -> int:
        """
        Remove old acknowledged messages.

        Args:
            days: Remove messages older than this many days

        Returns:
            Number of messages removed
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM messages
                WHERE status = 'acknowledged' AND acknowledged_at < ?
            """,
                (cutoff_date.isoformat(),),
            )

            count = cursor.rowcount
            conn.commit()

            if count > 0:
                logger.info(f"Cleaned up {count} old messages")

            return count
        finally:
            conn.close()

    def get_message_by_id(self, message_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single message by its ID.

        Args:
            message_id: ID of message to retrieve

        Returns:
            Message dict or None if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, created_at, message_type, priority, title, content,
                       metadata, acknowledged_at, status
                FROM messages
                WHERE id = ?
            """,
                (message_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            # Parse metadata if present
            metadata = json.loads(row[6]) if row[6] else {}

            return {
                "id": row[0],
                "created_at": row[1],
                "message_type": row[2],
                "priority": row[3],
                "title": row[4],
                "content": row[5],
                "metadata": metadata,
                "acknowledged_at": row[7],
                "status": row[8],
            }
        finally:
            conn.close()

    def delete_message(self, message_id: int) -> bool:
        """
        Delete a specific message by ID.

        Args:
            message_id: ID of message to delete

        Returns:
            True if message was deleted, False if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
            success = cursor.rowcount > 0
            conn.commit()

            if success:
                logger.info(f"Deleted message {message_id}")

            return success
        finally:
            conn.close()

    def clear_messages(
        self, message_type: Optional[MessageType] = None, status: Optional[str] = None
    ) -> int:
        """
        Clear (delete) multiple messages by type and/or status.

        Args:
            message_type: Type of messages to clear (None for all types)
            status: Status of messages to clear (None for all statuses)

        Returns:
            Number of messages deleted
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()

            # Build query based on filters
            query = "DELETE FROM messages WHERE 1=1"
            params = []

            if message_type:
                query += " AND message_type = ?"
                params.append(message_type.value)

            if status:
                query += " AND status = ?"
                params.append(status)

            cursor.execute(query, params)
            count = cursor.rowcount
            conn.commit()

            if count > 0:
                logger.info(f"Cleared {count} messages")

            return count
        finally:
            conn.close()

    def get_prompt_indicator(self) -> str:
        """
        Generate prompt indicator string showing total pending message count.

        Returns:
            String like '[7$]>' for 7 messages or '$>' if no messages
        """
        counts = self.get_pending_counts()
        total_count = counts["system"] + counts["code"]

        if total_count == 0:
            return "$>"

        return f"[{total_count}$]>"
