"""
State Manager - Manages workspace state persistence and restoration
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class StateManager:
    """
    Manages storage and retrieval of workspace states
    """

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = Path.home() / ".isaac" / "bubbles"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.db_path = self.storage_path / "bubbles.db"
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for bubble metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bubbles (
                id TEXT PRIMARY KEY,
                name TEXT,
                workspace_path TEXT,
                created_at TEXT,
                created_on_platform TEXT,
                file_path TEXT,
                size INTEGER,
                metadata TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bubble_tags (
                bubble_id TEXT,
                tag TEXT,
                FOREIGN KEY (bubble_id) REFERENCES bubbles(id)
            )
        """
        )

        conn.commit()
        conn.close()

    def save_bubble(self, bubble_state: Dict[str, Any], name: Optional[str] = None) -> str:
        """Save bubble state and register in database"""
        bubble_id = bubble_state["metadata"]["bubble_id"]

        if name is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            name = f"bubble_{timestamp}"

        # Save bubble file
        file_path = self.storage_path / f"{bubble_id}.json"

        with open(file_path, "w") as f:
            json.dump(bubble_state, f, indent=2)

        # Register in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO bubbles
            (id, name, workspace_path, created_at, created_on_platform, file_path, size, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                bubble_id,
                name,
                bubble_state["workspace"]["path"],
                bubble_state["created_at"],
                bubble_state["created_on"]["system"],
                str(file_path),
                file_path.stat().st_size,
                json.dumps(bubble_state["metadata"]),
            ),
        )

        conn.commit()
        conn.close()

        return bubble_id

    def load_bubble(self, bubble_id: str) -> Optional[Dict[str, Any]]:
        """Load bubble state from storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT file_path FROM bubbles WHERE id = ?", (bubble_id,))
        result = cursor.fetchone()

        conn.close()

        if not result:
            return None

        file_path = Path(result[0])

        if not file_path.exists():
            return None

        with open(file_path, "r") as f:
            return json.load(f)

    def list_bubbles(self, workspace_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all saved bubbles, optionally filtered by workspace"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if workspace_path:
            cursor.execute(
                """
                SELECT id, name, workspace_path, created_at, created_on_platform, size
                FROM bubbles
                WHERE workspace_path = ?
                ORDER BY created_at DESC
            """,
                (workspace_path,),
            )
        else:
            cursor.execute(
                """
                SELECT id, name, workspace_path, created_at, created_on_platform, size
                FROM bubbles
                ORDER BY created_at DESC
            """
            )

        results = cursor.fetchall()
        conn.close()

        bubbles = []
        for row in results:
            bubbles.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "workspace_path": row[2],
                    "created_at": row[3],
                    "platform": row[4],
                    "size": row[5],
                }
            )

        return bubbles

    def delete_bubble(self, bubble_id: str) -> bool:
        """Delete a bubble from storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get file path
        cursor.execute("SELECT file_path FROM bubbles WHERE id = ?", (bubble_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return False

        file_path = Path(result[0])

        # Delete from database
        cursor.execute("DELETE FROM bubbles WHERE id = ?", (bubble_id,))
        cursor.execute("DELETE FROM bubble_tags WHERE bubble_id = ?", (bubble_id,))

        conn.commit()
        conn.close()

        # Delete file
        if file_path.exists():
            file_path.unlink()

        return True

    def add_tag(self, bubble_id: str, tag: str):
        """Add a tag to a bubble"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO bubble_tags (bubble_id, tag)
            VALUES (?, ?)
        """,
            (bubble_id, tag),
        )

        conn.commit()
        conn.close()

    def get_tags(self, bubble_id: str) -> List[str]:
        """Get all tags for a bubble"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT tag FROM bubble_tags WHERE bubble_id = ?", (bubble_id,))
        results = cursor.fetchall()

        conn.close()

        return [row[0] for row in results]

    def search_bubbles(self, query: str) -> List[Dict[str, Any]]:
        """Search bubbles by name or tag"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT b.id, b.name, b.workspace_path, b.created_at, b.created_on_platform, b.size
            FROM bubbles b
            LEFT JOIN bubble_tags t ON b.id = t.bubble_id
            WHERE b.name LIKE ? OR t.tag LIKE ?
            ORDER BY b.created_at DESC
        """,
            (f"%{query}%", f"%{query}%"),
        )

        results = cursor.fetchall()
        conn.close()

        bubbles = []
        for row in results:
            bubbles.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "workspace_path": row[2],
                    "created_at": row[3],
                    "platform": row[4],
                    "size": row[5],
                }
            )

        return bubbles

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), SUM(size) FROM bubbles")
        count, total_size = cursor.fetchone()

        conn.close()

        return {
            "total_bubbles": count or 0,
            "total_size": total_size or 0,
            "storage_path": str(self.storage_path),
        }
