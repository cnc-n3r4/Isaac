"""
Query Cache - Cache AI query responses to reduce costs and improve performance
Provides both in-memory and persistent disk caching
"""

import hashlib
import json
import os
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional


class QueryCache:
    """
    Two-tier cache for AI query responses

    Features:
    - Fast in-memory LRU cache (hot queries)
    - Persistent disk cache (warm queries)
    - Automatic cache key generation from query + model
    - Cache statistics and hit rate tracking
    - Cost savings estimation
    """

    def __init__(self, cache_dir: Optional[str] = None, max_memory_entries: int = 1000):
        """
        Initialize query cache

        Args:
            cache_dir: Directory for persistent cache (defaults to ~/.isaac/query_cache)
            max_memory_entries: Maximum number of entries in memory cache
        """
        if cache_dir is None:
            cache_dir = str(Path.home() / ".isaac" / "query_cache")

        self.cache_dir = cache_dir
        self.max_memory_entries = max_memory_entries

        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)

        # In-memory LRU cache (hot queries)
        self._memory_cache: OrderedDict = OrderedDict()

        # Statistics tracking
        self._stats = {
            "memory_hits": 0,
            "disk_hits": 0,
            "misses": 0,
            "total_queries": 0,
            "cost_saved": 0.0,  # Estimated cost savings from cache hits
        }

        # Load stats if they exist
        self._load_stats()

    def _generate_key(self, query: str, model: str, **kwargs) -> str:
        """
        Generate cache key from query parameters

        Args:
            query: Query text
            model: Model name
            **kwargs: Additional parameters to include in cache key

        Returns:
            SHA256 hash as cache key
        """
        # Normalize query (strip whitespace, lowercase)
        normalized_query = query.strip().lower()

        # Include model and any additional parameters
        cache_input = {
            "query": normalized_query,
            "model": model,
            **kwargs
        }

        # Create deterministic string representation
        cache_str = json.dumps(cache_input, sort_keys=True)

        # Generate SHA256 hash
        return hashlib.sha256(cache_str.encode('utf-8')).hexdigest()

    def get(self, query: str, model: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get cached response for query

        Args:
            query: Query text
            model: Model name
            **kwargs: Additional parameters

        Returns:
            Cached response dict or None if not found
        """
        self._stats["total_queries"] += 1
        key = self._generate_key(query, model, **kwargs)

        # Check memory cache first (fastest)
        if key in self._memory_cache:
            self._stats["memory_hits"] += 1
            # Move to end (LRU)
            self._memory_cache.move_to_end(key)
            cached_data = self._memory_cache[key]
            return cached_data["response"]

        # Check disk cache (slower but persistent)
        cache_file = self._get_cache_file_path(key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)

                self._stats["disk_hits"] += 1

                # Promote to memory cache
                self._add_to_memory_cache(key, cached_data)

                return cached_data["response"]
            except Exception as e:
                print(f"Warning: Failed to load from disk cache: {e}")

        # Cache miss
        self._stats["misses"] += 1
        return None

    def set(self, query: str, model: str, response: Any, cost: float = 0.0, **kwargs):
        """
        Store response in cache

        Args:
            query: Query text
            model: Model name
            response: Response to cache
            cost: Cost of this query (for savings calculation)
            **kwargs: Additional parameters
        """
        key = self._generate_key(query, model, **kwargs)

        cached_data = {
            "query": query,
            "model": model,
            "response": response,
            "cost": cost,
            "timestamp": time.time(),
            "kwargs": kwargs
        }

        # Store in memory cache
        self._add_to_memory_cache(key, cached_data)

        # Store on disk for persistence
        cache_file = self._get_cache_file_path(key)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to write to disk cache: {e}")

    def _add_to_memory_cache(self, key: str, data: Dict):
        """Add entry to memory cache with LRU eviction"""
        # Add to cache
        self._memory_cache[key] = data

        # Evict oldest if over limit
        if len(self._memory_cache) > self.max_memory_entries:
            # Remove oldest (first item)
            self._memory_cache.popitem(last=False)

    def _get_cache_file_path(self, key: str) -> str:
        """Get file path for cache key"""
        # Use first 2 chars for subdirectory to avoid too many files in one dir
        subdir = os.path.join(self.cache_dir, key[:2])
        os.makedirs(subdir, exist_ok=True)
        return os.path.join(subdir, f"{key}.json")

    def clear(self):
        """Clear all caches (memory and disk)"""
        # Clear memory cache
        self._memory_cache.clear()

        # Clear disk cache
        try:
            import shutil
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
        except Exception as e:
            print(f"Warning: Failed to clear disk cache: {e}")

        # Reset stats
        self._stats = {
            "memory_hits": 0,
            "disk_hits": 0,
            "misses": 0,
            "total_queries": 0,
            "cost_saved": 0.0,
        }
        self._save_stats()

    def clear_memory(self):
        """Clear only memory cache, keep disk cache"""
        self._memory_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        total_hits = self._stats["memory_hits"] + self._stats["disk_hits"]
        total_queries = self._stats["total_queries"]

        hit_rate = (total_hits / total_queries * 100) if total_queries > 0 else 0
        memory_hit_rate = (self._stats["memory_hits"] / total_queries * 100) if total_queries > 0 else 0
        disk_hit_rate = (self._stats["disk_hits"] / total_queries * 100) if total_queries > 0 else 0

        # Calculate disk cache size
        disk_size = self._get_disk_cache_size()

        return {
            "memory_entries": len(self._memory_cache),
            "max_memory_entries": self.max_memory_entries,
            "memory_hits": self._stats["memory_hits"],
            "disk_hits": self._stats["disk_hits"],
            "misses": self._stats["misses"],
            "total_queries": total_queries,
            "hit_rate": round(hit_rate, 2),
            "memory_hit_rate": round(memory_hit_rate, 2),
            "disk_hit_rate": round(disk_hit_rate, 2),
            "cost_saved": round(self._stats["cost_saved"], 4),
            "disk_cache_size_mb": round(disk_size / (1024 * 1024), 2),
            "cache_dir": self.cache_dir
        }

    def _get_disk_cache_size(self) -> int:
        """Get total size of disk cache in bytes"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    if file.endswith('.json') and file != 'cache_stats.json':
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
        except Exception:
            pass
        return total_size

    def warmup(self, queries: list):
        """
        Pre-load cache with common queries

        Args:
            queries: List of (query, model) tuples to warmup
        """
        for query, model in queries:
            key = self._generate_key(query, model)
            cache_file = self._get_cache_file_path(key)

            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    self._add_to_memory_cache(key, cached_data)
                except Exception:
                    pass

    def _load_stats(self):
        """Load statistics from disk"""
        stats_file = os.path.join(self.cache_dir, 'cache_stats.json')
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self._stats = json.load(f)
            except Exception:
                pass

    def _save_stats(self):
        """Save statistics to disk"""
        stats_file = os.path.join(self.cache_dir, 'cache_stats.json')
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self._stats, f, indent=2)
        except Exception:
            pass

    def record_cache_hit_savings(self, cost: float):
        """
        Record cost savings from cache hit

        Args:
            cost: Cost that would have been incurred
        """
        self._stats["cost_saved"] += cost
        self._save_stats()
