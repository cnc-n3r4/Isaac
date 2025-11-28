"""
Memory Manager for Persistent AI Memory System
Orchestrates memory storage, retrieval, and management with performance optimizations.
"""

import time
import uuid
import weakref
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sqlite3
import threading
import json

from isaac.core.performance_manager import performance_timer, memory_profile, memory_optimizer
from .database import ConversationContext, MemoryDatabase, MemoryEntry


class OptimizedMemoryManager:
    """Enhanced memory management system with performance optimizations"""

    def __init__(self, db_path: Optional[Path] = None, cache_size_mb: int = 50):
        if db_path is None:
            # Default to user's Isaac directory
            from pathlib import Path

            isaac_dir = Path.home() / ".isaac"
            isaac_dir.mkdir(exist_ok=True)
            db_path = isaac_dir / "memory.db"

        self.db = MemoryDatabase(db_path)
        self.current_session_id = str(uuid.uuid4())
        self.active_context: Optional[ConversationContext] = None
        
        # Performance optimizations
        self.cache_size_mb = cache_size_mb
        self._memory_cache = {}  # In-memory cache for frequent reads
        self._cache_stats = {'hits': 0, 'misses': 0}
        self._write_buffer = []  # Buffer writes for better performance
        self._buffer_lock = threading.Lock()
        self._last_flush = time.time()
   
        # Memory optimization
        self._weak_refs = set()
        
        # Auto-flush timer
        self._setup_auto_flush()
    
    def _setup_auto_flush(self):
        """Setup automatic buffer flushing"""
        def auto_flush():
            while True:
                time.sleep(30)  # Flush every 30 seconds
                if time.time() - self._last_flush > 30:
                    self.flush_writes()
        
        thread = threading.Thread(target=auto_flush, daemon=True)
        thread.start()

    @performance_timer
    def start_new_session(self) -> str:
        """Start a new memory session"""
        self.current_session_id = str(uuid.uuid4())
        self._clear_session_cache()
        return self.current_session_id

    def set_session(self, session_id: str):
        """Set the current session ID"""
        self.current_session_id = session_id
        self._clear_session_cache()

    def _clear_session_cache(self):
        """Clear session-specific cache"""
        session_keys = [k for k in self._memory_cache.keys() if k.startswith(f"{self.current_session_id}:")]
        for key in session_keys:
            del self._memory_cache[key]

    # Context Window Management with Caching
    @performance_timer
    def create_context(
        self, title: str = "", metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """Create a new conversation context with caching"""
        context = ConversationContext(
            session_id=self.current_session_id,
            context_id=str(uuid.uuid4()),
            title=title or f"Context {int(time.time())}",
            metadata=metadata or {},
        )
        self.active_context = context
  
        # Cache the context
        cache_key = f"{self.current_session_id}:context:{context.context_id}"
        self._memory_cache[cache_key] = context
        
        return context

    @performance_timer
    def load_context(self, context_id: str) -> Optional[ConversationContext]:
        """Load a conversation context with caching"""
        cache_key = f"{self.current_session_id}:context:{context_id}"
        
        # Check cache first
        if cache_key in self._memory_cache:
            self._cache_stats['hits'] += 1
            context = self._memory_cache[cache_key]
            self.active_context = context
            return context
        
        # Load from database
        self._cache_stats['misses'] += 1
        context = self.db.get_context(context_id)
        if context:
            self.active_context = context
            # Cache for future access
            self._memory_cache[cache_key] = context
            self._cleanup_cache_if_needed()
        return context

    @memory_profile
    def save_context(self, context: Optional[ConversationContext] = None) -> Optional[int]:
        """Save a conversation context with buffering"""
        ctx = context or self.active_context
        if ctx:
            # Add to write buffer instead of immediate save
            with self._buffer_lock:
                self._write_buffer.append(('context', ctx))
                # Auto-flush if buffer is large
                if len(self._write_buffer) > 100:
                    self._flush_buffer()
           
   return 1  # Return placeholder ID
        return None

    def add_to_context(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the active context with optimized saving"""
        if self.active_context:
            self.active_context.add_message(role, content, metadata)
            # Periodic auto-save (not every message for performance)
            if len(self.active_context.messages) % 5 == 0:
                self.save_context()

    @performance_timer
    def get_context_history(self, limit: int = 10) -> List[ConversationContext]:
        """Get recent conversation contexts with caching"""
        cache_key = f"{self.current_session_id}:history:{limit}"
        
        if cache_key in self._memory_cache:
            self._cache_stats['hits'] += 1
            return self._memory_cache[cache_key]
 
        self._cache_stats['misses'] += 1
        contexts = self.db.get_contexts(session_id=self.current_session_id, limit=limit)
        
        # Cache the result
        self._memory_cache[cache_key] = contexts
        self._cleanup_cache_if_needed()
        
        return contexts

    # Memory Storage with Performance Optimizations
    @performance_timer
    def store_memory(
        self,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 1.0,
        tags: Optional[List[str]] = None,
    ) -> Optional[int]:
        """Store a memory entry with buffering"""
        entry = MemoryEntry(
            session_id=self.current_session_id,
            timestamp=time.time(),
            memory_type=memory_type,
            content=content,
            metadata=metadata or {},
            importance=importance,
            tags=tags or [],
        )
        
        # Add to write buffer
        with self._buffer_lock:
            self._write_buffer.append(('memory', entry))
         
            # Auto-flush if buffer is large
            if len(self._write_buffer) > 50:
                self._flush_buffer()
        
        return 1  # Return placeholder ID

    @performance_timer 
    def store_conversation_memory(
        self, user_input: str, ai_response: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """Store conversation memory with optimized format"""
        return self.store_memory(
        memory_type="conversation",
        content={
            "user_input": user_input,
            "ai_response": ai_response,
            "turn_id": str(uuid.uuid4())
        },
          metadata=metadata,
          importance=0.8,  # Conversations are moderately important
          tags=["conversation", "turn"]
        )

    @performance_timer
    def search_memories(
      self,
        query: str,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
     limit: int = 10,
        min_importance: float = 0.0
    ) -> List[MemoryEntry]:
        """Search memories with caching for common queries"""
        # Create cache key
        cache_key = f"search:{hash(query)}:{memory_type}:{str(tags)}:{limit}:{min_importance}"
        
        if cache_key in self._memory_cache:
            self._cache_stats['hits'] += 1
            return self._memory_cache[cache_key]
        
        self._cache_stats['misses'] += 1
        results = self.db.search_memories(
            session_id=self.current_session_id,
            query=query,
   memory_type=memory_type,
    tags=tags,
          limit=limit,
        min_importance=min_importance
        )
        
      # Cache search results (they're relatively stable)
        self._memory_cache[cache_key] = results
      self._cleanup_cache_if_needed()
        
   return results

    def flush_writes(self):
        """Manually flush write buffer to database"""
        with self._buffer_lock:
         if self._write_buffer:
             self._flush_buffer()

    def _flush_buffer(self):
        """Internal method to flush write buffer"""
        if not self._write_buffer:
            return
            
        try:
         # Batch write to database
            for item_type, item_data in self._write_buffer:
       if item_type == 'context':
 self.db.store_context(item_data)
    elif item_type == 'memory':
            self.db.store_memory(item_data)
      
   self._write_buffer.clear()
            self._last_flush = time.time()
            
        except Exception as e:
            # Log error but don't crash
          print(f"Memory flush error: {e}")

    def _cleanup_cache_if_needed(self):
  """Clean up cache if it's getting too large"""
        import sys
        
        # Rough estimate of cache size
        cache_size_bytes = sum(sys.getsizeof(v) for v in self._memory_cache.values())
        max_size_bytes = self.cache_size_mb * 1024 * 1024
      
        if cache_size_bytes > max_size_bytes:
           # Remove oldest 25% of cache entries
            cache_items = list(self._memory_cache.items())
            remove_count = len(cache_items) // 4
      
         for key, _ in cache_items[:remove_count]:
             del self._memory_cache[key]
      
    # Also run memory optimization
      memory_optimizer.optimize_memory()

    def get_performance_stats(self) -> Dict[str, Any]:
    """Get memory manager performance statistics"""
    return {
            'cache_size': len(self._memory_cache),
  'cache_hits': self._cache_stats['hits'],
            'cache_misses': self._cache_stats['misses'], 
            'cache_hit_rate': self._cache_stats['hits'] / max(1, self._cache_stats['hits'] + self._cache_stats['misses']),
       'write_buffer_size': len(self._write_buffer),
            'last_flush': self._last_flush,
  'session_id': self.current_session_id
      }

    def optimize_memory(self):
        """Run memory optimization"""
        # Clear old cache entries
   current_time = time.time()
        old_keys = [
 key for key, value in self._memory_cache.items()
            if hasattr(value, 'timestamp') and current_time - getattr(value, 'timestamp', 0) > 3600
        ]
        
   for key in old_keys:
       del self._memory_cache[key]
    
        # Flush any pending writes
        self.flush_writes()
        
      # Run global memory optimization
    return memory_optimizer.optimize_memory()

    def close(self):
        """Clean shutdown of memory manager"""
        self.flush_writes()
        if hasattr(self.db, 'close'):
    self.db.close()


# For backward compatibility
MemoryManager = OptimizedMemoryManager
