#!/usr/bin/env python3
"""
Test script for Phase 6: Enhanced Status & Fallback
"""

import sys
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from isaac.core.fallback_manager import FallbackManager, get_fallback_manager
from isaac.core.workspace_integration import WorkspaceContext

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_fallback_manager():
    """Test fallback manager with various scenarios"""
    print("\n=== Testing Fallback Manager ===\n")

    manager = FallbackManager()

    # Test 1: Successful service call
    print("Test 1: Successful service call")
    def success_fn():
        return {"data": "Success!"}

    result = manager.call_with_fallback('api_service', success_fn)
    assert result['success'], "Should succeed"
    assert result['source'] == 'primary', "Should use primary"
    print("  ✓ Primary service worked")

    # Test 2: Failing service with fallback
    print("\nTest 2: Failing service with fallback")
    def failing_fn():
        raise Exception("API unavailable")

    def fallback_fn():
        return {"data": "Cached result"}

    result = manager.call_with_fallback('cache_service', failing_fn, fallback_fn)
    assert result['success'], "Should succeed with fallback"
    assert result['source'] == 'fallback', "Should use fallback"
    assert result['fallback_used'], "Fallback should be marked as used"
    print("  ✓ Fallback worked when primary failed")

    # Test 3: Multiple failures -> service marked unavailable
    print("\nTest 3: Service degradation tracking")
    consecutive_failures = 0
    for i in range(5):
        result = manager.call_with_fallback('unreliable_api', failing_fn, queue_on_failure=True)
        if not result['success']:
            consecutive_failures += 1

    service = manager.get_service('unreliable_api')
    assert not service.available, "Service should be marked unavailable"
    assert service.consecutive_failures >= 3, "Should track consecutive failures"
    print(f"  ✓ Service marked unavailable after {service.consecutive_failures} failures")

    # Test 4: Offline queue
    print("\nTest 4: Offline operation queue")
    status = manager.get_all_status()
    queued_count = status['offline_queue']
    assert queued_count > 0, "Should have queued operations"
    print(f"  ✓ {queued_count} operations queued for later")

    # Test 5: Service reset
    print("\nTest 5: Service recovery")
    manager.reset_service('unreliable_api')
    service = manager.get_service('unreliable_api')
    assert service.available, "Service should be available after reset"
    print("  ✓ Service reset successful")

    return True


def test_enhanced_status():
    """Test enhanced status command integration"""
    print("\n=== Testing Enhanced Status Integration ===\n")

    # Activate workspace context
    ctx = WorkspaceContext()
    result = ctx.activate_workspace()

    if result['success']:
        print(f"✓ Workspace activated: {result['workspace']['name']}")

        # Get context (this is what /status --verbose would show)
        context = ctx.get_current_context()

        if context['active']:
            print("\nContext info (shown in /status --verbose):")
            print(f"  Workspace: {context['workspace']['name']}")
            print(f"  Path: {context['workspace']['path']}")

            if 'session' in context:
                sess = context['session']
                print(f"  AI Session ID: {sess['id'][:40]}...")
                print(f"  Session age: {sess.get('age', 'N/A')}")
                print(f"  Session remaining: {sess.get('remaining', 'N/A')}")

            if 'knowledge_base' in context and context['knowledge_base']:
                kb = context['knowledge_base']
                print(f"  Knowledge base: {kb['files_indexed']} files indexed")

            print("  ✓ All context info available for /status")
    else:
        print(f"  Note: No workspace detected (expected in non-project directories)")

    return True


def test_fallback_persistence():
    """Test fallback state persistence"""
    print("\n=== Testing Fallback Persistence ===\n")

    # Create manager, queue operations
    manager1 = FallbackManager()

    def failing_fn():
        raise Exception("Network error")

    for i in range(3):
        manager1.call_with_fallback(f'service_{i}', failing_fn, queue_on_failure=True)

    queued_before = len(manager1.offline_queue)
    config_path = manager1.config_path

    print(f"Queued {queued_before} operations")
    print(f"Config path: {config_path}")

    # Create new manager (simulates restart)
    manager2 = FallbackManager(config_path=config_path)
    queued_after = len(manager2.offline_queue)

    assert queued_after == queued_before, "Queue should persist across restarts"
    print(f"✓ Queue persisted: {queued_after} operations loaded")

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Phase 6: Enhanced Status & Fallback Test Suite")
    print("=" * 60)

    tests = [
        ("Fallback Manager", test_fallback_manager),
        ("Enhanced Status Integration", test_enhanced_status),
        ("Fallback Persistence", test_fallback_persistence),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {name} test passed")
            else:
                failed += 1
                print(f"\n✗ {name} test failed")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} test failed with error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
