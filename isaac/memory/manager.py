"""
Memory Manager for Persistent AI Memory System
Orchestrates memory storage, retrieval, and management.
"""

import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from .database import MemoryDatabase, MemoryEntry, ConversationContext


class MemoryManager:
    """Main memory management system"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            # Default to user's Isaac directory
            from pathlib import Path
            isaac_dir = Path.home() / '.isaac'
            isaac_dir.mkdir(exist_ok=True)
            db_path = isaac_dir / 'memory.db'

        self.db = MemoryDatabase(db_path)
        self.current_session_id = str(uuid.uuid4())
        self.active_context: Optional[ConversationContext] = None

    def start_new_session(self) -> str:
        """Start a new memory session"""
        self.current_session_id = str(uuid.uuid4())
        return self.current_session_id

    def set_session(self, session_id: str):
        """Set the current session ID"""
        self.current_session_id = session_id

    # Context Window Management
    def create_context(self, title: str = "", metadata: Optional[Dict[str, Any]] = None) -> ConversationContext:
        """Create a new conversation context"""
        context = ConversationContext(
            session_id=self.current_session_id,
            context_id=str(uuid.uuid4()),
            title=title or f"Context {int(time.time())}",
            metadata=metadata or {}
        )
        self.active_context = context
        return context

    def load_context(self, context_id: str) -> Optional[ConversationContext]:
        """Load a conversation context"""
        context = self.db.get_context(context_id)
        if context:
            self.active_context = context
        return context

    def save_context(self, context: Optional[ConversationContext] = None) -> Optional[int]:
        """Save a conversation context"""
        ctx = context or self.active_context
        if ctx:
            return self.db.store_context(ctx)
        return None

    def add_to_context(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the active context"""
        if self.active_context:
            self.active_context.add_message(role, content, metadata)
            # Auto-save context periodically
            self.save_context()

    def get_context_history(self, limit: int = 10) -> List[ConversationContext]:
        """Get recent conversation contexts"""
        return self.db.get_contexts(session_id=self.current_session_id, limit=limit)

    # Memory Storage
    def store_memory(self, memory_type: str, content: Dict[str, Any],
                    metadata: Optional[Dict[str, Any]] = None,
                    importance: float = 1.0, tags: Optional[List[str]] = None) -> Optional[int]:
        """Store a memory entry"""
        entry = MemoryEntry(
            session_id=self.current_session_id,
            timestamp=time.time(),
            memory_type=memory_type,
            content=content,
            metadata=metadata or {},
            importance=importance,
            tags=tags or []
        )
        return self.db.store_memory(entry)

    def store_conversation_memory(self, user_input: str, ai_response: str,
                                 metadata: Optional[Dict[str, Any]] = None):
        """Store a conversation exchange"""
        content = {
            "user_input": user_input,
            "ai_response": ai_response,
            "context_id": self.active_context.context_id if self.active_context else None
        }
        self.store_memory("conversation", content, metadata, importance=0.8)

    def store_command_memory(self, command: str, result: str, success: bool = True,
                           metadata: Optional[Dict[str, Any]] = None):
        """Store a command execution"""
        content = {
            "command": command,
            "result": result,
            "success": success
        }
        importance = 0.9 if success else 0.7
        self.store_memory("command", content, metadata, importance=importance)

    def store_fact_memory(self, fact: str, source: str = "user",
                         metadata: Optional[Dict[str, Any]] = None):
        """Store a factual memory"""
        content = {
            "fact": fact,
            "source": source
        }
        self.store_memory("fact", content, metadata, importance=0.95, tags=["fact"])

    # Memory Retrieval
    def get_memories(self, memory_type: Optional[str] = None, limit: int = 50) -> List[MemoryEntry]:
        """Get memories for current session"""
        return self.db.get_memories(
            session_id=self.current_session_id,
            memory_type=memory_type,
            limit=limit
        )

    def search_memories(self, query: str, limit: int = 20) -> List[MemoryEntry]:
        """Search memories by content"""
        return self.db.search_memories(query, self.current_session_id, limit)

    def get_recent_conversations(self, limit: int = 10) -> List[MemoryEntry]:
        """Get recent conversation memories"""
        return self.get_memories("conversation", limit)

    def get_command_history(self, limit: int = 20) -> List[MemoryEntry]:
        """Get command execution history"""
        return self.get_memories("command", limit)

    def get_facts(self, limit: int = 50) -> List[MemoryEntry]:
        """Get stored facts"""
        return self.get_memories("fact", limit)

    # Context-Aware Memory
    def get_relevant_context(self, current_input: str, limit: int = 5) -> List[MemoryEntry]:
        """Get contextually relevant memories for current input"""
        # Search for similar conversations
        relevant = self.search_memories(current_input, limit=limit)

        # Also get recent context if available
        if self.active_context and self.active_context.messages and len(self.active_context.messages) > 0:
            recent_messages = self.active_context.get_recent_messages(10)
            # Add recent context as pseudo-memories
            for msg in recent_messages[-3:]:  # Last 3 messages
                pseudo_memory = MemoryEntry(
                    session_id=self.current_session_id,
                    timestamp=msg["timestamp"],
                    memory_type="recent_context",
                    content={"message": msg},
                    importance=0.6
                )
                relevant.append(pseudo_memory)

        return relevant[:limit]

    # Memory Maintenance
    def prune_old_memories(self, days_old: int = 30, min_importance: float = 0.3) -> int:
        """Prune old and low-importance memories"""
        return self.db.prune_old_memories(days_old, min_importance)

    def cleanup_session_memories(self, session_id: str, keep_recent: int = 100):
        """Clean up old memories for a specific session"""
        # This would be more complex - for now just prune old ones
        return self.prune_old_memories()

    # Memory Export/Import
    def export_memories(self, file_path: Path, session_id: Optional[str] = None) -> bool:
        """Export memories to JSON file"""
        try:
            memories = self.db.get_memories(session_id=session_id or self.current_session_id, limit=10000)
            contexts = self.db.get_contexts(session_id=session_id or self.current_session_id, limit=1000)

            export_data = {
                "exported_at": time.time(),
                "session_id": session_id or self.current_session_id,
                "memories": [m.to_dict() for m in memories],
                "contexts": [c.to_dict() for c in contexts]
            }

            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False

    def import_memories(self, file_path: Path, merge_session: bool = False) -> Tuple[int, int]:
        """Import memories from JSON file"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            memories_imported = 0
            contexts_imported = 0

            # Import memories
            for mem_data in data.get("memories", []):
                try:
                    memory = MemoryEntry.from_dict(mem_data)
                    if merge_session:
                        memory.session_id = self.current_session_id
                    self.db.store_memory(memory)
                    memories_imported += 1
                except Exception:
                    continue

            # Import contexts
            for ctx_data in data.get("contexts", []):
                try:
                    context = ConversationContext.from_dict(ctx_data)
                    if merge_session:
                        context.session_id = self.current_session_id
                        context.context_id = str(uuid.uuid4())  # New ID
                    self.db.store_context(context)
                    contexts_imported += 1
                except Exception:
                    continue

            return memories_imported, contexts_imported
        except Exception:
            return 0, 0

    # Statistics and Monitoring
    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        stats = self.db.get_stats()
        stats["current_session"] = self.current_session_id
        stats["active_context"] = self.active_context.context_id if self.active_context else None
        return stats

    def get_session_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary for a session"""
        sid = session_id or self.current_session_id
        memories = self.db.get_memories(session_id=sid, limit=1000)
        contexts = self.db.get_contexts(session_id=sid, limit=100)

        memory_types = {}
        for mem in memories:
            memory_types[mem.memory_type] = memory_types.get(mem.memory_type, 0) + 1

        return {
            "session_id": sid,
            "total_memories": len(memories),
            "memory_types": memory_types,
            "total_contexts": len(contexts),
            "oldest_memory": min((m.timestamp for m in memories), default=0),
            "newest_memory": max((m.timestamp for m in memories), default=0)
        }