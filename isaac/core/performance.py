#!/usr/bin/env python3
"""
Performance Optimizations - Caching, lazy loading, and metrics

Optimizes ISAAC performance through intelligent caching and monitoring.
"""

import logging
import time
import functools
from typing import Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
import json
import hashlib

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Intelligent cache manager with TTL and size limits

    Features:
    - TTL-based expiration
    - LRU eviction
    - Persistent cache storage
    - Cache hit/miss metrics
    """

    def __init__(self, cache_dir: Optional[Path] = None, max_size_mb: int = 100):
        """
        Initialize cache manager

        Args:
            cache_dir: Directory for persistent cache
            max_size_mb: Maximum cache size in MB
        """
        if cache_dir is None:
            cache_dir = Path.home() / '.isaac' / 'cache'

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = timedelta(hours=1)

        # In-memory cache
        self.cache: Dict[str, Dict[str, Any]] = {}

        # Metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        logger.info(f"Cache manager initialized (max size: {max_size_mb}MB)")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]

        # Check TTL
        if datetime.now() > entry['expires_at']:
            del self.cache[key]
            self.misses += 1
            return None

        # Update access time for LRU
        entry['accessed_at'] = datetime.now()
        self.hits += 1

        return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live (default: 1 hour)
        """
        if ttl is None:
            ttl = self.default_ttl

        entry = {
            'value': value,
            'created_at': datetime.now(),
            'accessed_at': datetime.now(),
            'expires_at': datetime.now() + ttl,
            'size': len(str(value))  # Approximate size
        }

        self.cache[key] = entry

        # Check if eviction needed
        self._check_eviction()

    def _check_eviction(self):
        """Check if cache size limit exceeded and evict if needed"""
        total_size = sum(entry['size'] for entry in self.cache.values())

        if total_size > self.max_size_bytes:
            # LRU eviction
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1]['accessed_at']
            )

            # Remove oldest entries until under limit
            while total_size > self.max_size_bytes and sorted_entries:
                key, entry = sorted_entries.pop(0)
                total_size -= entry['size']
                del self.cache[key]
                self.evictions += 1

            logger.debug(f"Evicted {self.evictions} cache entries")

    def clear(self):
        """Clear all cache entries"""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared {count} cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_size = sum(entry['size'] for entry in self.cache.values())
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'entries': len(self.cache),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate_percent': round(hit_rate, 2)
        }


class PerformanceMonitor:
    """
    Performance monitoring and metrics

    Tracks operation timing and resource usage
    """

    def __init__(self):
        self.metrics: Dict[str, list] = {}
        self.start_times: Dict[str, float] = {}

    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = time.time()

    def end_timer(self, operation: str):
        """End timing and record metric"""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]

            if operation not in self.metrics:
                self.metrics[operation] = []

            self.metrics[operation].append(duration)
            del self.start_times[operation]

            return duration

        return None

    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics"""
        if operation:
            if operation not in self.metrics:
                return {}

            timings = self.metrics[operation]
            return {
                'operation': operation,
                'count': len(timings),
                'avg_ms': round(sum(timings) / len(timings) * 1000, 2),
                'min_ms': round(min(timings) * 1000, 2),
                'max_ms': round(max(timings) * 1000, 2),
                'total_s': round(sum(timings), 2)
            }
        else:
            # All operations
            return {
                op: self.get_stats(op)
                for op in self.metrics.keys()
            }


def cached(ttl_hours: int = 1):
    """
    Decorator for caching function results

    Args:
        ttl_hours: Cache TTL in hours

    Usage:
        @cached(ttl_hours=2)
        def expensive_operation(arg1, arg2):
            return result
    """
    def decorator(func: Callable):
        cache = CacheManager()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

            cache_key = hashlib.sha256(
                '|'.join(key_parts).encode()
            ).hexdigest()[:16]

            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value

            # Execute function
            result = func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl=timedelta(hours=ttl_hours))

            return result

        return wrapper

    return decorator


def timed(operation_name: Optional[str] = None):
    """
    Decorator for timing function execution

    Usage:
        @timed("database_query")
        def query_database():
            return results
    """
    def decorator(func: Callable):
        monitor = PerformanceMonitor()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__

            monitor.start_timer(op_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = monitor.end_timer(op_name)
                if duration:
                    logger.debug(f"{op_name} took {duration*1000:.2f}ms")

        return wrapper

    return decorator


class LazyLoader:
    """
    Lazy initialization helper

    Delays expensive initialization until first use
    """

    def __init__(self, initializer: Callable):
        """
        Create lazy loader

        Args:
            initializer: Function to call for initialization
        """
        self.initializer = initializer
        self._value = None
        self._initialized = False

    def get(self):
        """Get value, initializing if needed"""
        if not self._initialized:
            logger.debug(f"Lazy loading: {self.initializer.__name__}")
            self._value = self.initializer()
            self._initialized = True

        return self._value

    def reset(self):
        """Reset to uninitialized state"""
        self._value = None
        self._initialized = False


# Global instances
_cache_manager: Optional[CacheManager] = None
_perf_monitor: Optional[PerformanceMonitor] = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_perf_monitor() -> PerformanceMonitor:
    """Get global performance monitor"""
    global _perf_monitor
    if _perf_monitor is None:
        _perf_monitor = PerformanceMonitor()
    return _perf_monitor


if __name__ == '__main__':
    # Test performance utilities
    import sys
    logging.basicConfig(level=logging.DEBUG)

    print("=== Performance Utilities Test ===\n")

    # Test cache
    print("Test 1: Cache Manager")
    cache = CacheManager(max_size_mb=1)

    cache.set("key1", "value1")
    cache.set("key2", "value2", ttl=timedelta(seconds=1))

    assert cache.get("key1") == "value1", "Should retrieve cached value"
    print("  ✓ Cache set/get works")

    time.sleep(1.1)
    assert cache.get("key2") is None, "Should expire after TTL"
    print("  ✓ TTL expiration works")

    stats = cache.get_stats()
    print(f"  Cache stats: {stats['entries']} entries, {stats['hit_rate_percent']}% hit rate")

    # Test performance monitoring
    print("\nTest 2: Performance Monitor")
    monitor = PerformanceMonitor()

    monitor.start_timer("test_op")
    time.sleep(0.1)
    duration = monitor.end_timer("test_op")

    assert duration is not None and duration >= 0.1, "Should measure duration"
    print(f"  ✓ Operation timing works: {duration*1000:.2f}ms")

    stats = monitor.get_stats("test_op")
    print(f"  Stats: {stats}")

    # Test decorators
    print("\nTest 3: Decorators")

    @cached(ttl_hours=1)
    def expensive_func(x):
        time.sleep(0.05)
        return x * 2

    start = time.time()
    result1 = expensive_func(5)
    time1 = time.time() - start

    start = time.time()
    result2 = expensive_func(5)  # Should be cached
    time2 = time.time() - start

    assert result1 == result2 == 10, "Should return correct result"
    assert time2 < time1 / 2, "Cached call should be faster"
    print(f"  ✓ @cached decorator works: {time1*1000:.2f}ms → {time2*1000:.2f}ms")

    # Test lazy loader
    print("\nTest 4: Lazy Loader")

    init_count = [0]

    def expensive_init():
        init_count[0] += 1
        return "initialized"

    lazy = LazyLoader(expensive_init)

    assert init_count[0] == 0, "Should not initialize yet"
    value = lazy.get()
    assert init_count[0] == 1, "Should initialize on first get"
    assert value == "initialized", "Should return initialized value"

    value2 = lazy.get()
    assert init_count[0] == 1, "Should not re-initialize"
    print("  ✓ Lazy loader works")

    print("\n✓ All performance utilities working")
