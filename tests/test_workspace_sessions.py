#!/usr/bin/env python3
"""
Test script for Phase 5.3: Workspace-Session Binding
"""

import sys
import logging
import tempfile
import shutil
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from isaac.core.workspace_sessions import WorkspaceSessionManager
from isaac.core.workspace_integration import WorkspaceContext
from isaac.ai.session_manager import XAISessionManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_workspace_detection():
    """Test workspace detection from various paths"""
    print("\n=== Testing Workspace Detection ===\n")

    manager = WorkspaceSessionManager()

    # Test detection from current directory
    workspace = manager.detect_workspace()
    if workspace:
        print(f"✓ Detected workspace from current dir: {workspace}")
    else:
        print(f"✗ Failed to detect workspace from current dir")
        return False

    # Test detection from subdirectory
    subdirs = [d for d in Path.cwd().iterdir() if d.is_dir() and not d.name.startswith('.')]
    if subdirs:
        subdir = subdirs[0]
        workspace = manager.detect_workspace(subdir)
        if workspace:
            print(f"✓ Detected workspace from subdir: {workspace}")
        else:
            print(f"✗ Failed to detect workspace from subdir")

    return True


def test_workspace_registration():
    """Test workspace registration and metadata"""
    print("\n=== Testing Workspace Registration ===\n")

    manager = WorkspaceSessionManager()
    workspace_path = Path.cwd()

    # Register workspace
    name = manager.register_workspace(
        workspace_path,
        session_id="test_session_abc",
        collection_id="test_collection_xyz"
    )
    print(f"✓ Registered workspace: {name}")

    # Get workspace info
    info = manager.get_workspace_info(workspace_path)
    if not info:
        print(f"✗ Failed to get workspace info")
        return False

    print(f"  Name: {info['name']}")
    print(f"  Path: {info['path']}")
    print(f"  Session ID: {info.get('session_id')}")
    print(f"  Collection ID: {info.get('collection_id')}")

    # Verify bindings
    session_id = manager.get_session_for_workspace(workspace_path)
    collection_id = manager.get_collection_for_workspace(workspace_path)

    if session_id != "test_session_abc":
        print(f"✗ Session binding failed")
        return False

    if collection_id != "test_collection_xyz":
        print(f"✗ Collection binding failed")
        return False

    print(f"✓ Bindings verified")
    return True


def test_workspace_switching():
    """Test switching between workspaces"""
    print("\n=== Testing Workspace Switching ===\n")

    manager = WorkspaceSessionManager()

    # Create temporary workspaces
    temp_dir = Path(tempfile.mkdtemp(prefix="isaac_test_"))
    ws1 = temp_dir / "workspace1"
    ws2 = temp_dir / "workspace2"

    ws1.mkdir(parents=True)
    ws2.mkdir(parents=True)

    # Add project markers
    (ws1 / ".git").mkdir()
    (ws2 / "package.json").write_text("{}")

    try:
        # Register both
        name1 = manager.register_workspace(ws1, session_id="session_1")
        name2 = manager.register_workspace(ws2, session_id="session_2")

        print(f"Created workspaces:")
        print(f"  {name1}: {ws1}")
        print(f"  {name2}: {ws2}")

        # Switch to workspace 1
        success, msg = manager.switch_workspace(ws1)
        if not success:
            print(f"✗ Failed to switch to workspace 1: {msg}")
            return False

        current = manager.get_current_workspace()
        if not current or current['name'] != name1:
            print(f"✗ Current workspace not set correctly")
            return False

        print(f"✓ Switched to workspace 1: {msg}")

        # Switch to workspace 2
        success, msg = manager.switch_workspace(ws2)
        if not success:
            print(f"✗ Failed to switch to workspace 2: {msg}")
            return False

        current = manager.get_current_workspace()
        if not current or current['name'] != name2:
            print(f"✗ Current workspace not set correctly")
            return False

        print(f"✓ Switched to workspace 2: {msg}")

        # Verify session isolation
        session1 = manager.get_session_for_workspace(ws1)
        session2 = manager.get_session_for_workspace(ws2)

        if session1 == session2:
            print(f"✗ Sessions not isolated!")
            return False

        print(f"✓ Session isolation verified:")
        print(f"  Workspace 1 session: {session1}")
        print(f"  Workspace 2 session: {session2}")

        return True

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_session_workspace_integration():
    """Test integration between SessionManager and WorkspaceManager"""
    print("\n=== Testing Session-Workspace Integration ===\n")

    ws_manager = WorkspaceSessionManager()
    session_manager = XAISessionManager()

    workspace_path = Path.cwd()
    workspace_name = ws_manager.get_workspace_name(workspace_path)

    # Create session for workspace
    session_id = session_manager.get_or_create_session(workspace_name)
    print(f"Created session for workspace '{workspace_name}': {session_id}")

    # Bind to workspace
    ws_manager.bind_session(workspace_path, session_id)

    # Verify binding
    bound_session = ws_manager.get_session_for_workspace(workspace_path)
    if bound_session != session_id:
        print(f"✗ Session binding mismatch")
        return False

    print(f"✓ Session bound to workspace")

    # Get session info
    session_info = session_manager.get_session_info(workspace_name)
    if session_info:
        print(f"Session info:")
        print(f"  Age: {session_info['age']}")
        print(f"  Remaining: {session_info['remaining']}")
        print(f"  Rotations: {session_info['rotation_count']}")

    return True


def test_workspace_context():
    """Test unified WorkspaceContext"""
    print("\n=== Testing WorkspaceContext ===\n")

    # Create context (without API key for testing)
    ctx = WorkspaceContext(xai_api_key=None)

    # Activate current workspace
    result = ctx.activate_workspace()

    if not result['success']:
        print(f"✗ Failed to activate workspace: {result.get('error')}")
        return False

    print(f"✓ Activated workspace: {result['workspace']['name']}")
    print(f"  Session ID: {result['session']['id']}")

    # Get context
    context = ctx.get_current_context()
    if not context['active']:
        print(f"✗ Context not active")
        return False

    print(f"✓ Context active:")
    print(f"  Workspace: {context['workspace']['name']}")
    print(f"  Path: {context['workspace']['path']}")
    print(f"  Session age: {context['session']['age']}")

    # List workspaces
    workspaces = ctx.list_workspaces()
    print(f"✓ Found {len(workspaces)} workspace(s)")

    return True


def main():
    """Run all tests"""
    print("=" * 80)
    print("Phase 5.3: Workspace-Session Binding Test Suite")
    print("=" * 80)

    tests = [
        ("Workspace Detection", test_workspace_detection),
        ("Workspace Registration", test_workspace_registration),
        ("Workspace Switching", test_workspace_switching),
        ("Session-Workspace Integration", test_session_workspace_integration),
        ("WorkspaceContext", test_workspace_context),
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

    print("\n" + "=" * 80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
