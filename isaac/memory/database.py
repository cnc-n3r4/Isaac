"""
Persistent AI Memory System for Isaac
Manages conversation contexts, memory storage, and retrieval across sessions.
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class MemoryEntry:
    """A single memory entry"""
    id: Optional[int] = None
    session_id: str = ""
    timestamp: float = 0.0
    memory_type: str = ""  # 'conversation', 'context', 'fact', 'command'
    content: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    importance: float = 1.0  # 0.0 to 1.0
    tags: Optional[List[str]] = None
    checksum: str = ""

    def __post_init__(self):
        if self.content is None:
            self.content = {}
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []
        if not self.checksum and self.content:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate checksum for deduplication"""
        content_str = json.dumps(self.content, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects if any
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ConversationContext:
    """A conversation context window"""
    id: Optional[int] = None
    session_id: str = ""
    context_id: str = ""
    title: str = ""
    messages: Optional[List[Dict[str, Any]]] = None
    created_at: float = 0.0
    updated_at: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.metadata is None:
            self.metadata = {}
        if not self.created_at:
            self.created_at = time.time()
        if not self.updated_at:
            self.updated_at = time.time()

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the context"""
        if self.messages is None:
            self.messages = []
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        self.updated_at = time.time()

    def get_recent_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages from the context"""
        if self.messages is None:
            return []
        return self.messages[-limit:] if limit > 0 else self.messages

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Create from dictionary"""
        return cls(**data)


class MemoryDatabase:
    """SQLite database for persistent memory storage"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    importance REAL DEFAULT 1.0,
                    tags TEXT NOT NULL,
                    checksum TEXT UNIQUE,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS contexts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    context_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    messages TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    metadata TEXT NOT NULL
                )
            ''')

            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memories_checksum ON memories(checksum)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_contexts_session ON contexts(session_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_contexts_context_id ON contexts(context_id)')

    def store_memory(self, entry: MemoryEntry) -> Optional[int]:
        """Store a memory entry"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT OR REPLACE INTO memories
                (session_id, timestamp, memory_type, content, metadata, importance, tags, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.session_id,
                entry.timestamp,
                entry.memory_type,
                json.dumps(entry.content),
                json.dumps(entry.metadata),
                entry.importance,
                json.dumps(entry.tags),
                entry.checksum
            ))
            return cursor.lastrowid

    def get_memories(self, session_id: Optional[str] = None, memory_type: Optional[str] = None,
                    limit: int = 100, offset: int = 0) -> List[MemoryEntry]:
        """Retrieve memories with optional filtering"""
        query = "SELECT * FROM memories WHERE 1=1"
        params = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            memories = []
            for row in cursor:
                entry = MemoryEntry(
                    id=row['id'],
                    session_id=row['session_id'],
                    timestamp=row['timestamp'],
                    memory_type=row['memory_type'],
                    content=json.loads(row['content']),
                    metadata=json.loads(row['metadata']),
                    importance=row['importance'],
                    tags=json.loads(row['tags']),
                    checksum=row['checksum']
                )
                memories.append(entry)

            return memories

    def search_memories(self, query: str, session_id: Optional[str] = None, limit: int = 50) -> List[MemoryEntry]:
        """Search memories by content"""
        search_query = """
            SELECT * FROM memories WHERE 1=1
        """
        params = []

        if session_id:
            search_query += " AND session_id = ?"
            params.append(session_id)

        # Simple text search in content and metadata
        search_query += """
            AND (content LIKE ? OR metadata LIKE ?)
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        """
        search_pattern = f"%{query}%"
        params.extend([search_pattern, search_pattern, limit])

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(search_query, params)

            memories = []
            for row in cursor:
                entry = MemoryEntry(
                    id=row['id'],
                    session_id=row['session_id'],
                    timestamp=row['timestamp'],
                    memory_type=row['memory_type'],
                    content=json.loads(row['content']),
                    metadata=json.loads(row['metadata']),
                    importance=row['importance'],
                    tags=json.loads(row['tags']),
                    checksum=row['checksum']
                )
                memories.append(entry)

            return memories

    def store_context(self, context: ConversationContext) -> Optional[int]:
        """Store a conversation context"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT OR REPLACE INTO contexts
                (session_id, context_id, title, messages, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                context.session_id,
                context.context_id,
                context.title,
                json.dumps(context.messages),
                context.created_at,
                context.updated_at,
                json.dumps(context.metadata)
            ))
            return cursor.lastrowid

    def get_context(self, context_id: str) -> Optional[ConversationContext]:
        """Retrieve a conversation context"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM contexts WHERE context_id = ?",
                (context_id,)
            )

            row = cursor.fetchone()
            if row:
                return ConversationContext(
                    id=row['id'],
                    session_id=row['session_id'],
                    context_id=row['context_id'],
                    title=row['title'],
                    messages=json.loads(row['messages']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    metadata=json.loads(row['metadata'])
                )
            return None

    def get_contexts(self, session_id: Optional[str] = None, limit: int = 20) -> List[ConversationContext]:
        """Get recent conversation contexts"""
        query = "SELECT * FROM contexts WHERE 1=1"
        params = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            contexts = []
            for row in cursor:
                context = ConversationContext(
                    id=row['id'],
                    session_id=row['session_id'],
                    context_id=row['context_id'],
                    title=row['title'],
                    messages=json.loads(row['messages']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    metadata=json.loads(row['metadata'])
                )
                contexts.append(context)

            return contexts

    def prune_old_memories(self, days_old: int = 30, min_importance: float = 0.3) -> int:
        """Prune old and low-importance memories"""
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                DELETE FROM memories
                WHERE timestamp < ? AND importance < ?
            ''', (cutoff_time, min_importance))

            return cursor.rowcount

    def get_stats(self) -> Dict[str, Any]:
        """Get memory database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Memory stats
            memory_cursor = conn.execute('''
                SELECT
                    COUNT(*) as total_memories,
                    COUNT(DISTINCT session_id) as sessions,
                    AVG(importance) as avg_importance,
                    MIN(timestamp) as oldest_memory,
                    MAX(timestamp) as newest_memory
                FROM memories
            ''')
            memory_row = memory_cursor.fetchone()
            memory_stats = dict(zip([desc[0] for desc in memory_cursor.description], memory_row)) if memory_row else {}

            # Context stats
            context_cursor = conn.execute('''
                SELECT
                    COUNT(*) as total_contexts,
                    COUNT(DISTINCT session_id) as context_sessions,
                    AVG(LENGTH(messages)) as avg_context_size
                FROM contexts
            ''')
            context_row = context_cursor.fetchone()
            context_stats = dict(zip([desc[0] for desc in context_cursor.description], context_row)) if context_row else {}

            return {
                "memories": memory_stats,
                "contexts": context_stats,
                "database_size_mb": self.db_path.stat().st_size / (1024 * 1024)
            }