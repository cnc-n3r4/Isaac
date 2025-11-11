#!/usr/bin/env python3
"""
Test script for Phases 8-10: Multi-file Ops, Command Consolidation, Performance
"""

import sys
import logging
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from isaac.core.multifile_ops import MultiFileOperationManager
from isaac.ai.unified_chat import UnifiedChatRouter, WorkspaceAwareDefaults
from isaac.core.performance import CacheManager, PerformanceMonitor, cached, LazyLoader

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_multifile_operations():
    """Test Phase 8: Multi-file operations"""
    print("\n=== Phase 8: Multi-file Operations ===\n")

    project_root = Path.cwd()
    mgr = MultiFileOperationManager(project_root)

    # Test batch search
    print("Test 1: Batch search")
    results = mgr.batch_search(r'def\s+\w+', ['**/test*.py'])
    assert isinstance(results, dict), "Should return dict of results"
    print(f"  ✓ Found matches in {len(results)} files")

    # Test dependency analysis
    print("\nTest 2: Dependency analysis")
    test_file = Path(__file__)
    deps = mgr.analyze_dependencies(test_file)
    assert 'dependencies' in deps, "Should return dependencies"
    print(f"  ✓ Analyzed dependencies: {deps.get('dependency_count', 0)}")

    # Test find definition
    print("\nTest 3: Find definition")
    defs = mgr.find_definition('CacheManager', ['**/*.py'])
    assert isinstance(defs, list), "Should return list of definitions"
    if defs:
        print(f"  ✓ Found {len(defs)} definitions")
    else:
        print(f"  ○ No definitions found (expected for test)")

    # Test batch replace (dry run)
    print("\nTest 4: Batch replace (dry-run)")
    result = mgr.batch_replace(
        r'test_pattern',
        'replacement',
        file_patterns=['**/nonexistent*.py'],
        dry_run=True
    )
    assert result['dry_run'] == True, "Should be dry-run"
    print(f"  ✓ Dry-run completed: {result['files_changed']} files affected")

    return True


def test_unified_chat_routing():
    """Test Phase 9: Unified chat routing"""
    print("\n=== Phase 9: Command Consolidation ===\n")

    # Create mock workspace context
    class MockWorkspaceContext:
        def __init__(self):
            self._current_workspace_path = Path.cwd()
            self._current_knowledge_base = None

        def _get_xai_client(self):
            return None

        def get_current_context(self):
            return {
                'active': True,
                'workspace': {'path': str(self._current_workspace_path)}
            }

    ctx = MockWorkspaceContext()
    router = UnifiedChatRouter(ctx)

    # Test mode detection
    print("Test 1: Query mode detection")
    test_cases = [
        ("How does the XaiClient class work?", "rag"),
        ("What is Python?", "direct"),
        ("Refactor authentication to use OAuth", "refactor"),
        ("Find the login function", "rag"),
    ]

    passed = 0
    for query, expected in test_cases:
        detected = router._detect_mode(query)
        match = "✓" if detected == expected else "✗"
        if detected == expected:
            passed += 1
        print(f"  {match} '{query[:35]}...' → {detected}")

    print(f"  {passed}/{len(test_cases)} correct detections")

    # Test workspace-aware defaults
    print("\nTest 2: Workspace-aware defaults")
    defaults = WorkspaceAwareDefaults(ctx)
    config = defaults.defaults

    assert isinstance(config, dict), "Should return config dict"
    assert 'use_codebase' in config, "Should have use_codebase setting"
    print(f"  ✓ Auto-configured: use_codebase={config['use_codebase']}")
    print(f"  ✓ Max context: {config.get('max_context', 5)}")

    return True


def test_performance_optimizations():
    """Test Phase 10: Performance optimizations"""
    print("\n=== Phase 10: Performance & Polish ===\n")

    # Test cache manager
    print("Test 1: Cache Manager")
    cache = CacheManager(max_size_mb=1)

    # Set and get
    cache.set("test_key", {"data": "test_value"})
    value = cache.get("test_key")
    assert value is not None, "Should retrieve cached value"
    assert value['data'] == "test_value", "Should match original value"

    stats = cache.get_stats()
    assert stats['hits'] > 0, "Should record cache hits"
    print(f"  ✓ Cache hit rate: {stats['hit_rate_percent']}%")

    # Test cache miss
    missing = cache.get("nonexistent_key")
    assert missing is None, "Should return None for missing key"
    print(f"  ✓ Cache miss handling works")

    # Test performance monitor
    print("\nTest 2: Performance Monitor")
    monitor = PerformanceMonitor()

    monitor.start_timer("test_operation")
    time.sleep(0.05)  # Simulate work
    duration = monitor.end_timer("test_operation")

    assert duration is not None, "Should measure duration"
    assert duration >= 0.05, "Duration should be at least 50ms"

    op_stats = monitor.get_stats("test_operation")
    assert op_stats['count'] == 1, "Should record 1 execution"
    print(f"  ✓ Operation timing: {op_stats['avg_ms']}ms")

    # Test caching decorator
    print("\nTest 3: Caching Decorator")

    call_count = [0]

    @cached(ttl_hours=1)
    def expensive_operation(x):
        call_count[0] += 1
        time.sleep(0.02)
        return x * 2

    # First call
    result1 = expensive_operation(5)
    first_count = call_count[0]

    # Second call (should be cached)
    result2 = expensive_operation(5)
    second_count = call_count[0]

    assert result1 == result2 == 10, "Should return correct result"
    assert first_count == 1, "Should call function once"
    assert second_count == 1, "Should not call function again (cached)"
    print(f"  ✓ Function called {second_count} time(s) for 2 invocations")

    # Test lazy loader
    print("\nTest 4: Lazy Loader")

    init_count = [0]

    def expensive_init():
        init_count[0] += 1
        return "expensive_result"

    lazy = LazyLoader(expensive_init)

    assert init_count[0] == 0, "Should not initialize immediately"

    value1 = lazy.get()
    assert init_count[0] == 1, "Should initialize on first get"
    assert value1 == "expensive_result", "Should return correct value"

    value2 = lazy.get()
    assert init_count[0] == 1, "Should not re-initialize"
    assert value2 == value1, "Should return same value"

    print(f"  ✓ Lazy initialization: {init_count[0]} initialization(s)")

    return True


def test_integration():
    """Test integration between phases"""
    print("\n=== Integration Testing ===\n")

    # Test: Performance monitoring with multi-file operations
    print("Test 1: Perf monitor + Multi-file ops")

    monitor = PerformanceMonitor()
    mgr = MultiFileOperationManager(Path.cwd())

    monitor.start_timer("batch_search")
    results = mgr.batch_search(r'class\s+\w+', ['**/*.py'])
    duration = monitor.end_timer("batch_search")

    assert duration is not None, "Should measure batch search time"
    print(f"  ✓ Batch search completed in {duration*1000:.2f}ms")
    print(f"  ✓ Found {len(results)} files with matches")

    # Test: Cache + expensive operations
    print("\nTest 2: Caching expensive operations")

    cache = CacheManager()

    # Simulate expensive dependency analysis
    test_file = Path(__file__)

    # First call (uncached)
    start = time.time()
    deps1 = mgr.analyze_dependencies(test_file)
    time1 = time.time() - start

    # Cache the result
    cache_key = f"deps_{test_file.name}"
    cache.set(cache_key, deps1)

    # Second call (from cache)
    start = time.time()
    deps2 = cache.get(cache_key)
    time2 = time.time() - start

    assert deps2 is not None, "Should retrieve from cache"
    assert time2 < time1 / 10, "Cached retrieval should be much faster"

    print(f"  ✓ Analysis time: {time1*1000:.2f}ms → {time2*1000:.2f}ms (cached)")
    print(f"  ✓ Speedup: {time1/time2:.1f}x faster")

    return True


def main():
    """Run all tests"""
    print("=" * 70)
    print("Phases 8-10: Multi-file Ops, Command Consolidation, Performance")
    print("=" * 70)

    tests = [
        ("Phase 8: Multi-file Operations", test_multifile_operations),
        ("Phase 9: Unified Chat Routing", test_unified_chat_routing),
        ("Phase 10: Performance Optimizations", test_performance_optimizations),
        ("Integration Testing", test_integration),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {name} passed")
            else:
                failed += 1
                print(f"\n✗ {name} failed")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} failed with error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
