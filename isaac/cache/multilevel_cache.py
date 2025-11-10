"""
Phase 3: Multi-level Cache Implementation
L1 (hot, memory) → L2 (warm, memory) → L3 (cold, disk)
"""

import fnmatch
import hashlib
import os
import pickle
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional


class LRUCache:
    """
    Simple LRU (Least Recently Used) cache implementation
    O(1) for get/set operations using OrderedDict
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache

        Args:
            max_size: Maximum number of items to store
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Set item in cache

        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            # Update existing item and move to end
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.max_size:
            # Evict least recently used
            self.cache.popitem(last=False)

        self.cache[key] = value

    def clear(self) -> None:
        """Clear all items from cache"""
        self.cache.clear()

    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)

    def keys(self):
        """Get cache keys"""
        return self.cache.keys()


class DiskCache:
    """
    Persistent disk-based cache using pickle
    Organized by hash prefix for efficient lookup
    """

    def __init__(self, cache_dir: str = ".isaac_cache/disk"):
        """
        Initialize disk cache

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """
        Get file path for cache key

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        # Use hash for safe filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        # Organize by prefix (first 2 chars) for better filesystem performance
        prefix_dir = self.cache_dir / key_hash[:2]
        prefix_dir.mkdir(exist_ok=True)
        return prefix_dir / f"{key_hash}.pkl"

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from disk cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        cache_file = self._get_cache_path(key)
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                # Corrupted cache file, remove it
                cache_file.unlink(missing_ok=True)
                return None
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Set item in disk cache

        Args:
            key: Cache key
            value: Value to cache
        """
        cache_file = self._get_cache_path(key)
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            # Failed to write cache (disk full, etc.)
            pass

    def clear(self) -> None:
        """Clear all items from disk cache"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def size(self) -> int:
        """Get approximate cache size (count of files)"""
        count = 0
        for root, dirs, files in os.walk(self.cache_dir):
            count += len(files)
        return count


class MultiLevelCache:
    """
    Multi-level cache: L1 (hot) → L2 (warm) → L3 (cold/disk)

    Cache Strategy:
    - L1: Small, fast in-memory cache for hottest data (100 items)
    - L2: Larger in-memory cache for warm data (1000 items)
    - L3: Disk cache for cold data (persistent across sessions)

    Features:
    - Automatic promotion of frequently accessed items
    - TTL (Time To Live) support for cache invalidation
    - Pattern-based invalidation
    - Memory usage tracking
    - Hit rate statistics
    """

    def __init__(
        self,
        l1_size: int = 100,
        l2_size: int = 1000,
        cache_dir: str = ".isaac_cache/disk",
        default_ttl: int = 3600
    ):
        """
        Initialize multi-level cache

        Args:
            l1_size: L1 cache size (hot data)
            l2_size: L2 cache size (warm data)
            cache_dir: Directory for L3 disk cache
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.l1 = LRUCache(max_size=l1_size)
        self.l2 = LRUCache(max_size=l2_size)
        self.l3 = DiskCache(cache_dir=cache_dir)

        self.default_ttl = default_ttl
        self.timestamps: Dict[str, Dict[str, Any]] = {}

        # Statistics
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0,
            "sets": 0,
            "invalidations": 0,
        }

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache (checks L1 → L2 → L3)

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        # Check if expired
        if key in self.timestamps:
            created = self.timestamps[key]['created']
            ttl = self.timestamps[key]['ttl']
            if time.time() - created > ttl:
                # Expired - invalidate
                self.invalidate(key)
                self.stats["misses"] += 1
                return None

        # Check L1 (fastest)
        value = self.l1.get(key)
        if value is not None:
            self.stats["l1_hits"] += 1
            return value

        # Check L2
        value = self.l2.get(key)
        if value is not None:
            self.stats["l2_hits"] += 1
            # Promote to L1 (frequently accessed)
            self.l1.set(key, value)
            return value

        # Check L3 (disk)
        value = self.l3.get(key)
        if value is not None:
            self.stats["l3_hits"] += 1
            # Promote to L2 (not L1, it's cold data)
            self.l2.set(key, value)
            return value

        # Cache miss
        self.stats["misses"] += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set item in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live override (seconds)
        """
        # Store in L1 (hot) and L3 (persistent)
        self.l1.set(key, value)
        self.l3.set(key, value)

        # Track timestamp for TTL
        self.timestamps[key] = {
            'created': time.time(),
            'ttl': ttl or self.default_ttl
        }

        self.stats["sets"] += 1

    def invalidate(self, key: str) -> bool:
        """
        Manually invalidate a cache entry

        Args:
            key: Cache key to invalidate

        Returns:
            True if key was found and invalidated
        """
        found = False

        # Remove from L1
        if key in self.l1.cache:
            del self.l1.cache[key]
            found = True

        # Remove from L2
        if key in self.l2.cache:
            del self.l2.cache[key]
            found = True

        # Remove from L3 (disk)
        cache_file = self.l3._get_cache_path(key)
        if cache_file.exists():
            cache_file.unlink()
            found = True

        # Remove timestamp
        if key in self.timestamps:
            del self.timestamps[key]
            found = True

        if found:
            self.stats["invalidations"] += 1

        return found

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern (glob-style)

        Args:
            pattern: Glob pattern (e.g., "user:*", "cache:temp:*")

        Returns:
            Number of keys invalidated
        """
        keys_to_invalidate = []

        # Check all caches for matching keys
        for key in self.l1.keys():
            if fnmatch.fnmatch(key, pattern):
                keys_to_invalidate.append(key)

        for key in self.l2.keys():
            if fnmatch.fnmatch(key, pattern):
                if key not in keys_to_invalidate:
                    keys_to_invalidate.append(key)

        for key in list(self.timestamps.keys()):
            if fnmatch.fnmatch(key, pattern):
                if key not in keys_to_invalidate:
                    keys_to_invalidate.append(key)

        # Invalidate all matching keys
        for key in keys_to_invalidate:
            self.invalidate(key)

        return len(keys_to_invalidate)

    def clear(self) -> None:
        """Clear all caches"""
        self.l1.clear()
        self.l2.clear()
        self.l3.clear()
        self.timestamps.clear()

        # Reset stats
        for key in self.stats:
            self.stats[key] = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with hit rates, sizes, and performance metrics
        """
        total_hits = self.stats["l1_hits"] + self.stats["l2_hits"] + self.stats["l3_hits"]
        total_requests = total_hits + self.stats["misses"]

        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "total_hits": total_hits,
            "total_misses": self.stats["misses"],
            "l1_hits": self.stats["l1_hits"],
            "l2_hits": self.stats["l2_hits"],
            "l3_hits": self.stats["l3_hits"],
            "l1_size": self.l1.size(),
            "l2_size": self.l2.size(),
            "l3_size": self.l3.size(),
            "sets": self.stats["sets"],
            "invalidations": self.stats["invalidations"],
            "l1_hit_rate": (self.stats["l1_hits"] / total_requests * 100) if total_requests > 0 else 0.0,
            "l2_hit_rate": (self.stats["l2_hits"] / total_requests * 100) if total_requests > 0 else 0.0,
            "l3_hit_rate": (self.stats["l3_hits"] / total_requests * 100) if total_requests > 0 else 0.0,
        }

    def info(self) -> str:
        """
        Get human-readable cache information

        Returns:
            Formatted string with cache statistics
        """
        stats = self.get_stats()

        return f"""Multi-Level Cache Statistics:
  Total Requests: {stats['total_requests']}
  Hit Rate: {stats['hit_rate']:.1f}%

  L1 (Hot):   {stats['l1_hits']} hits ({stats['l1_hit_rate']:.1f}%) - {stats['l1_size']} items
  L2 (Warm):  {stats['l2_hits']} hits ({stats['l2_hit_rate']:.1f}%) - {stats['l2_size']} items
  L3 (Disk):  {stats['l3_hits']} hits ({stats['l3_hit_rate']:.1f}%) - {stats['l3_size']} items

  Misses: {stats['total_misses']}
  Sets: {stats['sets']}
  Invalidations: {stats['invalidations']}
"""
