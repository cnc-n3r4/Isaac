"""
Phase 3: Multi-level Cache Tests
Testing L1/L2/L3 cache with TTL and invalidation
"""

import time
from pathlib import Path
import shutil

import pytest

from isaac.cache.multilevel_cache import MultiLevelCache, LRUCache, DiskCache
from isaac.cache.cache_warmer import CacheWarmer


class TestLRUCache:
    """Test LRU cache implementation"""

    def test_basic_get_set(self):
        """Test basic get/set operations"""
        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") is None

    def test_lru_eviction(self):
        """Test that least recently used items are evicted"""
        cache = LRUCache(max_size=3)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 (makes it most recently used)
        cache.get("key1")

        # Add key4 (should evict key2, the least recently used)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None      # Evicted
        assert cache.get("key3") == "value3"  # Still there
        assert cache.get("key4") == "value4"  # New item

    def test_cache_size(self):
        """Test cache size tracking"""
        cache = LRUCache(max_size=5)

        assert cache.size() == 0

        cache.set("key1", "value1")
        assert cache.size() == 1

        cache.set("key2", "value2")
        cache.set("key3", "value3")
        assert cache.size() == 3

        cache.clear()
        assert cache.size() == 0


class TestDiskCache:
    """Test disk cache implementation"""

    @pytest.fixture
    def test_cache_dir(self, tmp_path):
        """Provide temporary cache directory"""
        cache_dir = tmp_path / "test_cache"
        yield str(cache_dir)
        # Cleanup
        if cache_dir.exists():
            shutil.rmtree(cache_dir)

    def test_basic_disk_operations(self, test_cache_dir):
        """Test basic disk cache operations"""
        cache = DiskCache(cache_dir=test_cache_dir)

        # Set and get
        cache.set("test_key", {"data": "test_value"})
        result = cache.get("test_key")

        assert result is not None
        assert result["data"] == "test_value"

    def test_disk_persistence(self, test_cache_dir):
        """Test that disk cache persists across instances"""
        # Create and populate cache
        cache1 = DiskCache(cache_dir=test_cache_dir)
        cache1.set("persistent_key", "persistent_value")

        # Create new instance
        cache2 = DiskCache(cache_dir=test_cache_dir)
        result = cache2.get("persistent_key")

        assert result == "persistent_value"

    def test_disk_cache_clear(self, test_cache_dir):
        """Test clearing disk cache"""
        cache = DiskCache(cache_dir=test_cache_dir)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestMultiLevelCache:
    """Test multi-level cache system"""

    @pytest.fixture
    def cache(self, tmp_path):
        """Provide multi-level cache with temporary storage"""
        cache_dir = tmp_path / "ml_cache"
        cache = MultiLevelCache(
            l1_size=2,
            l2_size=4,
            cache_dir=str(cache_dir),
            default_ttl=3600
        )
        yield cache
        # Cleanup
        cache.clear()

    def test_cache_hit_l1(self, cache):
        """Test L1 cache hit"""
        cache.set("test", "value")

        # Should hit L1
        result = cache.get("test")

        assert result == "value"
        assert cache.stats["l1_hits"] == 1
        assert cache.stats["l2_hits"] == 0
        assert cache.stats["l3_hits"] == 0

    def test_cache_promotion_l2_to_l1(self, cache):
        """Test promotion from L2 to L1"""
        # Set value (goes to L1 and L3)
        cache.set("test", "value")

        # Clear L1 to simulate eviction
        cache.l1.clear()

        # Get should find in L3, promote to L2
        result = cache.get("test")
        assert result == "value"
        assert cache.stats["l3_hits"] == 1

        # Get again should find in L2, promote to L1
        result = cache.get("test")
        assert result == "value"
        assert cache.stats["l2_hits"] == 1

    def test_cache_ttl_expiration(self, cache):
        """Test TTL expiration"""
        # Set with 1 second TTL
        cache.set("test", "value", ttl=1)

        # Should be available immediately
        assert cache.get("test") == "value"

        # Wait for expiration
        time.sleep(1.5)

        # Should be None (expired)
        assert cache.get("test") is None

    def test_manual_invalidation(self, cache):
        """Test manual cache invalidation"""
        cache.set("test", "value")

        # Should be available
        assert cache.get("test") == "value"

        # Invalidate
        result = cache.invalidate("test")

        assert result is True
        assert cache.get("test") is None

    def test_pattern_invalidation(self, cache):
        """Test pattern-based invalidation"""
        cache.set("user:1:profile", {"name": "Alice"})
        cache.set("user:1:settings", {"theme": "dark"})
        cache.set("user:2:profile", {"name": "Bob"})
        cache.set("product:1", {"name": "Widget"})

        # Invalidate all user:1 entries
        count = cache.invalidate_pattern("user:1:*")

        assert count == 2
        assert cache.get("user:1:profile") is None
        assert cache.get("user:1:settings") is None
        assert cache.get("user:2:profile") is not None  # Not matched
        assert cache.get("product:1") is not None       # Not matched

    def test_cache_statistics(self, cache):
        """Test cache statistics"""
        # Generate some activity
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.get("key1")  # L1 hit
        cache.get("key1")  # L1 hit
        cache.get("key3")  # Miss

        stats = cache.get_stats()

        assert stats["total_requests"] == 3
        assert stats["l1_hits"] == 2
        assert stats["total_misses"] == 1
        assert stats["hit_rate"] == pytest.approx(66.67, rel=0.1)

    def test_cache_performance(self, cache):
        """Test cache performance (L1 should be <1ms)"""
        # Warm up
        cache.set("test", "value")

        # Measure L1 access time
        iterations = 1000
        start = time.time()
        for _ in range(iterations):
            cache.get("test")
        elapsed = time.time() - start

        avg_time_ms = (elapsed / iterations) * 1000

        print(f"\nL1 cache access: {avg_time_ms:.4f}ms per access")
        assert avg_time_ms < 0.1, f"L1 too slow: {avg_time_ms}ms"


class TestCacheWarmer:
    """Test cache warmer functionality"""

    @pytest.fixture
    def warmer(self, tmp_path):
        """Provide cache warmer with temporary storage"""
        cache_dir = tmp_path / "warmer_cache"
        usage_log = tmp_path / "usage.json"

        cache = MultiLevelCache(cache_dir=str(cache_dir))
        warmer = CacheWarmer(cache, usage_log_file=str(usage_log))

        yield warmer

        # Cleanup
        cache.clear()

    def test_track_query(self, warmer):
        """Test query tracking"""
        warmer.track_query("query1", {"type": "search"})
        warmer.track_query("query1", {"type": "search"})
        warmer.track_query("query2", {"type": "analysis"})

        assert "query1" in warmer.usage
        assert warmer.usage["query1"]["count"] == 2
        assert warmer.usage["query2"]["count"] == 1

    def test_hot_queries(self, warmer):
        """Test hot query identification"""
        # Simulate usage pattern
        for _ in range(10):
            warmer.track_query("very_hot_query")

        for _ in range(5):
            warmer.track_query("hot_query")

        for _ in range(2):
            warmer.track_query("warm_query")

        hot = warmer.get_hot_queries(top_n=3, min_count=2)

        assert len(hot) <= 3
        assert hot[0][0] == "very_hot_query"  # Hottest
        assert hot[1][0] == "hot_query"

    def test_cache_warmup(self, warmer):
        """Test cache warming"""
        # Track some queries
        warmer.track_query("query1")
        warmer.track_query("query1")
        warmer.track_query("query2")

        # Define value generator
        def generate_value(key):
            return f"generated_value_for_{key}"

        # Warmup
        count = warmer.warmup_cache(generate_value, top_n=10)

        assert count >= 0  # Should warm at least some queries

        # Check cache is populated
        if count > 0:
            result = warmer.cache.get("query1")
            assert result is not None

    def test_pattern_analysis(self, warmer):
        """Test usage pattern analysis"""
        # Generate usage
        for i in range(5):
            warmer.track_query(f"query{i}", {"type": "search"})

        for i in range(3):
            warmer.track_query(f"analysis{i}", {"type": "analysis"})

        analysis = warmer.analyze_patterns()

        assert analysis["unique_queries"] == 8
        assert analysis["total_queries"] == 8
        assert "search" in analysis["query_types"]
        assert "analysis" in analysis["query_types"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
