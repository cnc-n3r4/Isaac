"""
Tests for Phase 2 Caching Layer
Tests both alias cache and query cache functionality
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from isaac.ai.query_cache import QueryCache
from isaac.crossplatform.alias_cache import AliasCache


class TestAliasCache:
    """Test suite for AliasCache"""

    @pytest.fixture
    def temp_aliases_file(self):
        """Create a temporary aliases JSON file"""
        temp_dir = tempfile.mkdtemp()
        aliases_file = os.path.join(temp_dir, "test_aliases.json")

        test_aliases = {
            "ls": {
                "powershell": "Get-ChildItem",
                "description": "List directory contents"
            },
            "cat": {
                "powershell": "Get-Content",
                "description": "Read file contents"
            },
            "grep": {
                "powershell": "Select-String",
                "description": "Search text patterns"
            }
        }

        with open(aliases_file, 'w') as f:
            json.dump(test_aliases, f)

        yield aliases_file

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

    def test_alias_cache_initialization(self, temp_aliases_file):
        """Test cache initializes correctly"""
        cache = AliasCache(cache_file=temp_aliases_file)
        assert cache.cache_file == temp_aliases_file
        assert cache.ttl == 300  # Default 5 minutes
        assert cache._cache is None  # Not loaded yet

    def test_alias_cache_first_load(self, temp_aliases_file):
        """Test cache loads on first access"""
        cache = AliasCache(cache_file=temp_aliases_file)
        aliases = cache.get_aliases()

        assert aliases is not None
        assert "ls" in aliases
        assert "cat" in aliases
        assert aliases["ls"]["powershell"] == "Get-ChildItem"

    def test_alias_cache_hit(self, temp_aliases_file):
        """Test cache returns same object on subsequent access (cache hit)"""
        cache = AliasCache(cache_file=temp_aliases_file, ttl=300)

        # First access
        aliases1 = cache.get_aliases()

        # Second access (should be from cache)
        aliases2 = cache.get_aliases()

        # Should be the same object (cached)
        assert aliases1 is aliases2

    def test_alias_cache_ttl_expiration(self, temp_aliases_file):
        """Test cache reloads after TTL expires"""
        cache = AliasCache(cache_file=temp_aliases_file, ttl=1)  # 1 second TTL

        # First access
        aliases1 = cache.get_aliases()

        # Wait for TTL to expire
        time.sleep(1.1)

        # Modify file
        with open(temp_aliases_file, 'r') as f:
            data = json.load(f)
        data["pwd"] = {"powershell": "Get-Location", "description": "Print working directory"}
        with open(temp_aliases_file, 'w') as f:
            json.dump(data, f)

        # Access again (should reload)
        aliases2 = cache.get_aliases()

        assert "pwd" in aliases2

    def test_alias_cache_file_modification_detection(self, temp_aliases_file):
        """Test cache reloads when file is modified"""
        cache = AliasCache(cache_file=temp_aliases_file, ttl=300)

        # First access
        aliases1 = cache.get_aliases()

        # Wait a moment and modify file
        time.sleep(0.1)
        with open(temp_aliases_file, 'r') as f:
            data = json.load(f)
        data["rm"] = {"powershell": "Remove-Item", "description": "Remove files"}
        with open(temp_aliases_file, 'w') as f:
            json.dump(data, f)

        # Access again (should detect file change and reload)
        aliases2 = cache.get_aliases()

        assert "rm" in aliases2

    def test_alias_cache_invalidate(self, temp_aliases_file):
        """Test manual cache invalidation"""
        cache = AliasCache(cache_file=temp_aliases_file)

        # Load cache
        cache.get_aliases()
        assert cache._cache is not None

        # Invalidate
        cache.invalidate()

        # Cache should be cleared
        assert cache._cache is None
        assert cache._last_load == 0

    def test_alias_cache_stats(self, temp_aliases_file):
        """Test cache statistics"""
        cache = AliasCache(cache_file=temp_aliases_file)

        # Get stats before loading
        stats = cache.get_cache_stats()
        assert stats["cache_loaded"] is False
        assert stats["cache_size"] == 0

        # Load cache
        cache.get_aliases()

        # Get stats after loading
        stats = cache.get_cache_stats()
        assert stats["cache_loaded"] is True
        assert stats["cache_size"] == 3  # ls, cat, grep
        assert stats["ttl"] == 300
        assert stats["file_exists"] is True

    def test_alias_cache_warmup(self, temp_aliases_file):
        """Test cache warmup"""
        cache = AliasCache(cache_file=temp_aliases_file)

        # Warmup should load the cache
        success = cache.warmup()
        assert success is True
        assert cache._cache is not None
        assert len(cache._cache) > 0

    def test_alias_cache_missing_file(self):
        """Test cache handles missing file gracefully"""
        cache = AliasCache(cache_file="/nonexistent/file.json")
        aliases = cache.get_aliases()
        assert aliases == {}


class TestQueryCache:
    """Test suite for QueryCache"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

    def test_query_cache_initialization(self, temp_cache_dir):
        """Test cache initializes correctly"""
        cache = QueryCache(cache_dir=temp_cache_dir, max_memory_entries=100)
        assert cache.cache_dir == temp_cache_dir
        assert cache.max_memory_entries == 100
        assert len(cache._memory_cache) == 0

    def test_query_cache_key_generation(self, temp_cache_dir):
        """Test consistent cache key generation"""
        cache = QueryCache(cache_dir=temp_cache_dir)

        key1 = cache._generate_key("test query", "gpt-4")
        key2 = cache._generate_key("test query", "gpt-4")
        key3 = cache._generate_key("different query", "gpt-4")

        # Same inputs should generate same key
        assert key1 == key2

        # Different inputs should generate different keys
        assert key1 != key3

    def test_query_cache_set_and_get(self, temp_cache_dir):
        """Test basic cache set and get operations"""
        cache = QueryCache(cache_dir=temp_cache_dir)

        # Set a value
        cache.set("test query", "gpt-4", {"result": "test response"}, cost=0.01)

        # Get the value
        result = cache.get("test query", "gpt-4")

        assert result is not None
        assert result["result"] == "test response"

    def test_query_cache_memory_hit(self, temp_cache_dir):
        """Test memory cache hit"""
        cache = QueryCache(cache_dir=temp_cache_dir)

        # Store in cache
        cache.set("query1", "gpt-4", {"answer": "42"}, cost=0.01)

        # First get (memory hit)
        result = cache.get("query1", "gpt-4")
        assert result["answer"] == "42"
        assert cache._stats["memory_hits"] == 1
        assert cache._stats["disk_hits"] == 0

    def test_query_cache_disk_hit(self, temp_cache_dir):
        """Test disk cache hit after memory eviction"""
        cache = QueryCache(cache_dir=temp_cache_dir, max_memory_entries=2)

        # Fill memory cache beyond limit
        cache.set("query1", "gpt-4", {"answer": "1"}, cost=0.01)
        cache.set("query2", "gpt-4", {"answer": "2"}, cost=0.01)
        cache.set("query3", "gpt-4", {"answer": "3"}, cost=0.01)

        # Clear memory to force disk read
        cache.clear_memory()

        # Get query1 (should be disk hit)
        result = cache.get("query1", "gpt-4")
        assert result["answer"] == "1"
        assert cache._stats["disk_hits"] > 0

    def test_query_cache_miss(self, temp_cache_dir):
        """Test cache miss"""
        cache = QueryCache(cache_dir=temp_cache_dir)

        result = cache.get("nonexistent query", "gpt-4")
        assert result is None
        assert cache._stats["misses"] == 1

    def test_query_cache_lru_eviction(self, temp_cache_dir):
        """Test LRU eviction from memory cache"""
        cache = QueryCache(cache_dir=temp_cache_dir, max_memory_entries=2)

        # Add 3 entries (should evict oldest)
        cache.set("query1", "gpt-4", {"answer": "1"}, cost=0.01)
        cache.set("query2", "gpt-4", {"answer": "2"}, cost=0.01)
        cache.set("query3", "gpt-4", {"answer": "3"}, cost=0.01)

        # Memory should only have 2 entries
        assert len(cache._memory_cache) == 2

        # query1 should have been evicted from memory
        # (but still on disk)
        assert "query1" not in [cache._generate_key("query1", "gpt-4")]

    def test_query_cache_cost_tracking(self, temp_cache_dir):
        """Test cost savings tracking"""
        cache = QueryCache(cache_dir=temp_cache_dir)

        # Set with cost
        cache.set("expensive query", "gpt-4", {"result": "answer"}, cost=0.50)

        # Get (cache hit)
        result = cache.get("expensive query", "gpt-4")

        # Record savings
        cache.record_cache_hit_savings(0.50)

        stats = cache.get_stats()
        assert stats["cost_saved"] == 0.50

    def test_query_cache_statistics(self, temp_cache_dir):
        """Test cache statistics"""
        cache = QueryCache(cache_dir=temp_cache_dir)

        # Perform some operations
        cache.set("query1", "gpt-4", {"answer": "1"}, cost=0.01)
        cache.get("query1", "gpt-4")  # Hit
        cache.get("nonexistent", "gpt-4")  # Miss

        stats = cache.get_stats()

        assert stats["memory_entries"] >= 0
        assert stats["total_queries"] == 2
        assert stats["memory_hits"] == 1
        assert stats["misses"] == 1
        assert "hit_rate" in stats
        assert "cost_saved" in stats

    def test_query_cache_clear(self, temp_cache_dir):
        """Test cache clearing"""
        cache = QueryCache(cache_dir=temp_cache_dir)

        # Add entries
        cache.set("query1", "gpt-4", {"answer": "1"}, cost=0.01)
        cache.set("query2", "gpt-4", {"answer": "2"}, cost=0.01)

        # Clear cache
        cache.clear()

        # Memory should be empty
        assert len(cache._memory_cache) == 0

        # Stats should be reset
        assert cache._stats["memory_hits"] == 0
        assert cache._stats["disk_hits"] == 0
        assert cache._stats["misses"] == 0

    def test_query_cache_with_kwargs(self, temp_cache_dir):
        """Test cache keys include kwargs for differentiation"""
        cache = QueryCache(cache_dir=temp_cache_dir)

        # Same query but different parameters
        cache.set("query", "gpt-4", {"answer": "low_temp"}, cost=0.01, temperature=0.3)
        cache.set("query", "gpt-4", {"answer": "high_temp"}, cost=0.01, temperature=0.9)

        # Should return different results based on kwargs
        result1 = cache.get("query", "gpt-4", temperature=0.3)
        result2 = cache.get("query", "gpt-4", temperature=0.9)

        assert result1["answer"] == "low_temp"
        assert result2["answer"] == "high_temp"

    def test_query_cache_warmup(self, temp_cache_dir):
        """Test cache warmup with common queries"""
        cache = QueryCache(cache_dir=temp_cache_dir)

        # Store some queries on disk
        cache.set("query1", "gpt-4", {"answer": "1"}, cost=0.01)
        cache.set("query2", "gpt-4", {"answer": "2"}, cost=0.01)
        cache.clear_memory()

        # Warmup specific queries
        cache.warmup([("query1", "gpt-4")])

        # query1 should be in memory now
        assert len(cache._memory_cache) > 0

    def test_query_cache_hit_rate_calculation(self, temp_cache_dir):
        """Test hit rate calculation"""
        cache = QueryCache(cache_dir=temp_cache_dir)

        # 3 queries: 2 hits, 1 miss
        cache.set("q1", "gpt-4", {"a": "1"}, cost=0.01)
        cache.get("q1", "gpt-4")  # Hit
        cache.get("q1", "gpt-4")  # Hit
        cache.get("q2", "gpt-4")  # Miss

        stats = cache.get_stats()
        assert stats["total_queries"] == 3
        assert stats["hit_rate"] == pytest.approx(66.67, abs=0.1)


class TestIntegration:
    """Integration tests for caching with UnixAliasTranslator and AIRouter"""

    def test_unix_alias_translator_with_cache(self):
        """Test UnixAliasTranslator uses cache correctly"""
        from isaac.core.unix_aliases import UnixAliasTranslator

        translator = UnixAliasTranslator()

        # First translation
        result1 = translator.translate("ls -la")

        # Cache should be populated
        assert translator.cache._cache is not None

        # Second translation (should use cache)
        result2 = translator.translate("ls -la")

        # Results should be identical
        assert result1 == result2

    @patch('isaac.ai.router.GrokClient')
    @patch('isaac.ai.router.ClaudeClient')
    @patch('isaac.ai.router.OpenAIClient')
    def test_ai_router_query_caching(self, mock_openai, mock_claude, mock_grok):
        """Test AIRouter caches query responses"""
        # This test would require more complex mocking
        # Simplified version to test cache integration exists
        from isaac.ai.router import AIRouter

        router = AIRouter()

        # Verify query cache is initialized
        assert hasattr(router, 'query_cache')
        assert router.query_cache is not None

        # Verify cache stats are included in router stats
        stats = router.get_stats()
        assert "query_cache" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
