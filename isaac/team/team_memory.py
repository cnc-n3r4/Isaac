"""Team memory for shared AI memory across team members."""

import json
import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


class TeamMemory:
    """Shared AI memory for teams."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize team memory.

        Args:
            base_dir: Base directory for team memory (default: ~/.isaac/team_memory/)
        """
        self.base_dir = Path(base_dir or os.path.expanduser("~/.isaac/team_memory"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / "team_memory.db"
        self._init_db()

    def _init_db(self):
        """Initialize the database."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS team_memories (
                    memory_id TEXT PRIMARY KEY,
                    team_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    tags TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS team_conversations (
                    conversation_id TEXT PRIMARY KEY,
                    team_id TEXT NOT NULL,
                    title TEXT,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_message_at TEXT,
                    message_count INTEGER DEFAULT 0,
                    participants TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS team_messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES team_conversations(conversation_id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_team_memories_team
                ON team_memories(team_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_team_conversations_team
                ON team_conversations(team_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_team_messages_conversation
                ON team_messages(conversation_id)
            """)
            conn.commit()

    def add_memory(self, team_id: str, user_id: str, memory_type: str,
                  content: str, metadata: Optional[Dict] = None,
                  tags: Optional[List[str]] = None) -> str:
        """Add a memory to team memory.

        Args:
            team_id: Team ID
            user_id: User ID adding the memory
            memory_type: Type of memory (context, fact, decision, etc.)
            content: Memory content
            metadata: Optional metadata
            tags: Optional tags

        Returns:
            Memory ID
        """
        import uuid
        memory_id = str(uuid.uuid4())

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT INTO team_memories (memory_id, team_id, user_id, memory_type, content, metadata, created_at, tags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (memory_id, team_id, user_id, memory_type, content,
                 json.dumps(metadata) if metadata else None,
                 datetime.now().isoformat(),
                 json.dumps(tags) if tags else None)
            )
            conn.commit()

        return memory_id

    def get_memories(self, team_id: str, memory_type: Optional[str] = None,
                    user_id: Optional[str] = None, tags: Optional[List[str]] = None,
                    limit: int = 100) -> List[Dict]:
        """Get memories for a team.

        Args:
            team_id: Team ID
            memory_type: Optional memory type filter
            user_id: Optional user ID filter
            tags: Optional tags filter
            limit: Maximum number of memories to return

        Returns:
            List of memory dictionaries
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM team_memories WHERE team_id = ?"
            params = [team_id]

            if memory_type:
                query += " AND memory_type = ?"
                params.append(memory_type)

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

            memories = []
            for row in rows:
                memory = {
                    'memory_id': row['memory_id'],
                    'team_id': row['team_id'],
                    'user_id': row['user_id'],
                    'memory_type': row['memory_type'],
                    'content': row['content'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'created_at': row['created_at'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                }

                # Filter by tags if specified
                if tags:
                    memory_tags = set(memory['tags'])
                    if not memory_tags.intersection(tags):
                        continue

                memories.append(memory)

            return memories

    def search_memories(self, team_id: str, query: str, limit: int = 50) -> List[Dict]:
        """Search team memories.

        Args:
            team_id: Team ID
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching memories
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row

            rows = conn.execute(
                """SELECT * FROM team_memories
                   WHERE team_id = ? AND content LIKE ?
                   ORDER BY created_at DESC LIMIT ?""",
                (team_id, f'%{query}%', limit)
            ).fetchall()

            memories = []
            for row in rows:
                memories.append({
                    'memory_id': row['memory_id'],
                    'team_id': row['team_id'],
                    'user_id': row['user_id'],
                    'memory_type': row['memory_type'],
                    'content': row['content'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'created_at': row['created_at'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                })

            return memories

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory.

        Args:
            memory_id: Memory ID

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("DELETE FROM team_memories WHERE memory_id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0

    def create_conversation(self, team_id: str, created_by: str,
                          title: Optional[str] = None) -> str:
        """Create a team conversation.

        Args:
            team_id: Team ID
            created_by: User ID creating the conversation
            title: Optional conversation title

        Returns:
            Conversation ID
        """
        import uuid
        conversation_id = str(uuid.uuid4())

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT INTO team_conversations (conversation_id, team_id, title, created_by, created_at, participants)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (conversation_id, team_id, title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                 created_by, datetime.now().isoformat(), json.dumps([created_by]))
            )
            conn.commit()

        return conversation_id

    def add_message(self, conversation_id: str, user_id: str, role: str,
                   content: str, metadata: Optional[Dict] = None) -> str:
        """Add a message to a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID sending the message
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata

        Returns:
            Message ID
        """
        import uuid
        message_id = str(uuid.uuid4())

        with sqlite3.connect(str(self.db_path)) as conn:
            # Add message
            conn.execute(
                """INSERT INTO team_messages (message_id, conversation_id, user_id, role, content, created_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (message_id, conversation_id, user_id, role, content,
                 datetime.now().isoformat(), json.dumps(metadata) if metadata else None)
            )

            # Update conversation
            conn.execute(
                """UPDATE team_conversations
                   SET last_message_at = ?, message_count = message_count + 1
                   WHERE conversation_id = ?""",
                (datetime.now().isoformat(), conversation_id)
            )

            # Add user to participants if not already there
            row = conn.execute(
                "SELECT participants FROM team_conversations WHERE conversation_id = ?",
                (conversation_id,)
            ).fetchone()

            if row:
                participants = json.loads(row[0]) if row[0] else []
                if user_id not in participants:
                    participants.append(user_id)
                    conn.execute(
                        "UPDATE team_conversations SET participants = ? WHERE conversation_id = ?",
                        (json.dumps(participants), conversation_id)
                    )

            conn.commit()

        return message_id

    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get a conversation with its messages.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation dictionary or None if not found
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row

            # Get conversation
            conv_row = conn.execute(
                "SELECT * FROM team_conversations WHERE conversation_id = ?",
                (conversation_id,)
            ).fetchone()

            if not conv_row:
                return None

            # Get messages
            message_rows = conn.execute(
                """SELECT * FROM team_messages WHERE conversation_id = ?
                   ORDER BY created_at ASC""",
                (conversation_id,)
            ).fetchall()

            messages = []
            for row in message_rows:
                messages.append({
                    'message_id': row['message_id'],
                    'user_id': row['user_id'],
                    'role': row['role'],
                    'content': row['content'],
                    'created_at': row['created_at'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                })

            conversation = {
                'conversation_id': conv_row['conversation_id'],
                'team_id': conv_row['team_id'],
                'title': conv_row['title'],
                'created_by': conv_row['created_by'],
                'created_at': conv_row['created_at'],
                'last_message_at': conv_row['last_message_at'],
                'message_count': conv_row['message_count'],
                'participants': json.loads(conv_row['participants']) if conv_row['participants'] else [],
                'messages': messages,
            }

            return conversation

    def list_conversations(self, team_id: str, limit: int = 50) -> List[Dict]:
        """List conversations for a team.

        Args:
            team_id: Team ID
            limit: Maximum number of conversations

        Returns:
            List of conversation summaries
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row

            rows = conn.execute(
                """SELECT * FROM team_conversations WHERE team_id = ?
                   ORDER BY last_message_at DESC LIMIT ?""",
                (team_id, limit)
            ).fetchall()

            conversations = []
            for row in rows:
                conversations.append({
                    'conversation_id': row['conversation_id'],
                    'team_id': row['team_id'],
                    'title': row['title'],
                    'created_by': row['created_by'],
                    'created_at': row['created_at'],
                    'last_message_at': row['last_message_at'],
                    'message_count': row['message_count'],
                    'participants': json.loads(row['participants']) if row['participants'] else [],
                })

            return conversations

    def export_memories(self, team_id: str, export_path: str) -> bool:
        """Export team memories to a file.

        Args:
            team_id: Team ID
            export_path: Path to export to

        Returns:
            True if exported, False on error
        """
        try:
            memories = self.get_memories(team_id, limit=10000)
            conversations = self.list_conversations(team_id, limit=1000)

            export_data = {
                'team_id': team_id,
                'exported_at': datetime.now().isoformat(),
                'memories': memories,
                'conversation_count': len(conversations),
                'conversation_ids': [c['conversation_id'] for c in conversations],
            }

            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)

            return True
        except Exception:
            return False

    def import_memories(self, team_id: str, import_path: str, imported_by: str) -> int:
        """Import memories from a file.

        Args:
            team_id: Team ID
            import_path: Path to import from
            imported_by: User ID importing the memories

        Returns:
            Number of memories imported
        """
        try:
            with open(import_path) as f:
                import_data = json.load(f)

            count = 0
            for memory in import_data.get('memories', []):
                self.add_memory(
                    team_id=team_id,
                    user_id=imported_by,
                    memory_type=memory.get('memory_type', 'imported'),
                    content=memory.get('content', ''),
                    metadata={
                        **memory.get('metadata', {}),
                        'imported_from': import_data.get('team_id'),
                        'imported_at': datetime.now().isoformat(),
                        'original_user': memory.get('user_id'),
                    },
                    tags=memory.get('tags', [])
                )
                count += 1

            return count
        except Exception:
            return 0
