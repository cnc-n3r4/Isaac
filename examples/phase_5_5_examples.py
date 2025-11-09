"""
Phase 5.5 Examples - Cross-Platform Excellence

This file contains practical examples demonstrating Phase 5.5 features.
"""

import asyncio
from pathlib import Path

# Example 1: Universal Bubbles - Cross-Platform Workspace
def example_universal_bubbles():
    """Demonstrate universal bubbles for cross-platform workspace state"""
    print("=== Example 1: Universal Bubbles ===\n")

    from isaac.crossplatform.bubbles import UniversalBubble, StateManager

    # Create a bubble for the current directory
    workspace_path = Path.cwd()
    bubble = UniversalBubble(str(workspace_path))

    print(f"Creating bubble for: {workspace_path}")

    # Capture workspace state
    state = bubble.capture()
    print(f"Captured state with {len(state.get('files', {}))} tracked files")

    # Save bubble
    bubble_file = workspace_path / 'my_workspace.bubble.json'
    bubble.save(str(bubble_file))
    print(f"Saved bubble to: {bubble_file}")

    # Use state manager
    manager = StateManager()
    bubble_id = manager.save_bubble(state, 'example-workspace')
    print(f"Registered bubble ID: {bubble_id}")

    # List all bubbles
    all_bubbles = manager.list_bubbles()
    print(f"\nTotal saved bubbles: {len(all_bubbles)}")

    # Check compatibility
    report = bubble.get_compatibility_report()
    print(f"\nCompatibility report:")
    print(f"  Current platform: {report['current_platform']['system']}")
    print(f"  Created on: {report['created_platform'].get('system', 'Unknown')}")
    print(f"  Compatible: {report['compatible']}")


# Example 2: Cloud-Native Mode
async def example_cloud_native():
    """Demonstrate cloud-native workspace management"""
    print("\n=== Example 2: Cloud-Native Mode ===\n")

    from isaac.crossplatform.cloud import CloudExecutor, CloudStorage, RemoteWorkspace

    # Initialize cloud components
    executor = CloudExecutor(cloud_provider='generic')
    storage = CloudStorage(provider='generic')
    workspace = RemoteWorkspace(executor, storage)

    # Create remote workspace
    print("Creating remote workspace...")
    workspace_id = await workspace.create_workspace(
        name='example-cloud-workspace',
        resources={'cpu': '2', 'memory': '4GB'}
    )
    print(f"Created workspace: {workspace_id}")

    # Execute command in cloud
    print("\nExecuting command in cloud workspace...")
    result = await workspace.execute_in_workspace(
        workspace_id,
        'echo "Hello from cloud!"'
    )
    print(f"Command status: {result['status']}")

    # Get workspace info
    info = await workspace.get_workspace_info(workspace_id)
    print(f"\nWorkspace endpoint: {info['endpoint']}")
    print(f"Status: {info['status']}")


# Example 3: RESTful API Usage
def example_rest_api():
    """Demonstrate RESTful API server"""
    print("\n=== Example 3: RESTful API ===\n")

    from isaac.crossplatform.api import RestAPI, APIAuth

    # Create API auth
    auth = APIAuth()

    # Generate API keys
    print("Creating API keys...")
    api_key_1 = auth.create_api_key(
        name='production-app',
        scopes=['workspaces:read', 'workspaces:write'],
        expires_in_days=365
    )
    print(f"Production key: {api_key_1[:20]}...")

    api_key_2 = auth.create_api_key(
        name='mobile-app',
        scopes=['workspaces:read'],
        expires_in_days=30
    )
    print(f"Mobile key: {api_key_2[:20]}...")

    # Validate keys
    print("\nValidating keys...")
    key_info = auth.validate_api_key(api_key_1)
    if key_info:
        print(f"  Key '{key_info['name']}' is valid")
        print(f"  Scopes: {key_info['scopes']}")
        print(f"  Usage count: {key_info['usage_count']}")

    # List all keys
    all_keys = auth.list_api_keys()
    print(f"\nTotal API keys: {len(all_keys)}")

    # API server (commented out to avoid blocking)
    # api = RestAPI(isaac_core=None, port=8080)
    # print("\nAPI server ready at http://localhost:8080")
    # api.run()


# Example 4: Web Interface
def example_web_interface():
    """Demonstrate web interface"""
    print("\n=== Example 4: Web Interface ===\n")

    from isaac.crossplatform.web import WebTerminal, TerminalEmulator

    # Create web terminal
    terminal = WebTerminal(isaac_core=None)

    # Create multiple sessions
    print("Creating terminal sessions...")
    session_1 = terminal.create_session(workspace_id='workspace-1')
    session_2 = terminal.create_session(workspace_id='workspace-2')

    print(f"Session 1: {session_1}")
    print(f"Session 2: {session_2}")

    # List sessions
    sessions = terminal.list_sessions()
    print(f"\nActive sessions: {len(sessions)}")

    # Terminal emulator for ANSI codes
    emulator = TerminalEmulator(width=80, height=24)

    # Process ANSI output
    test_output = "\033[31mError:\033[0m Something went wrong"
    html_output = emulator.process_output(test_output)
    print(f"\nANSI to HTML conversion:")
    print(f"  Input: {test_output}")
    print(f"  HTML: {html_output[:50]}...")

    # Web server (commented out to avoid blocking)
    # from isaac.crossplatform.web import WebServer
    # server = WebServer(isaac_core=None, port=8000)
    # print("\nWeb interface at http://localhost:8000")
    # server.run()


# Example 5: Mobile API
async def example_mobile_api():
    """Demonstrate mobile companion API"""
    print("\n=== Example 5: Mobile API ===\n")

    from isaac.crossplatform.mobile import NotificationService, MobileAuth

    # Mobile authentication
    auth = MobileAuth()

    # Generate pairing code
    print("Mobile device pairing...")
    pairing_code = auth.generate_pairing_code('instance-123')
    print(f"Pairing code: {pairing_code}")
    print("(Enter this code in your mobile app)")

    # Simulate mobile app validation
    session_token = auth.validate_pairing_code(pairing_code, 'device-456')
    if session_token:
        print(f"Device paired! Session token: {session_token[:20]}...")

    # Notification service
    notifications = NotificationService()

    # Register devices
    print("\nRegistering mobile devices...")
    ios_device = notifications.register_device(
        device_token='ios-token-123',
        platform='ios',
        user_id='user-1'
    )
    print(f"iOS device registered: {ios_device}")

    android_device = notifications.register_device(
        device_token='android-token-456',
        platform='android',
        user_id='user-1'
    )
    print(f"Android device registered: {android_device}")

    # Send notification
    print("\nSending notification...")
    await notifications.send_notification(
        user_id='user-1',
        notification_type='suggestion',
        title='Optimization Tip',
        message='Consider enabling auto-sync for better performance',
        data={'workspace_id': 'workspace-1'}
    )
    print("Notification sent to all user devices")

    # Get stats
    stats = notifications.get_stats()
    print(f"\nNotification stats:")
    print(f"  Total devices: {stats['total_devices']}")
    print(f"  iOS devices: {stats['ios_devices']}")
    print(f"  Android devices: {stats['android_devices']}")


# Example 6: Offline Mode
async def example_offline_mode():
    """Demonstrate offline mode functionality"""
    print("\n=== Example 6: Offline Mode ===\n")

    from isaac.crossplatform.offline import SyncQueue, CacheManager, ConflictResolver
    import tempfile

    # Create sync queue
    with tempfile.TemporaryDirectory() as tmpdir:
        queue = SyncQueue(tmpdir)

        print("Queuing offline operations...")

        # Add operations to queue
        op1 = await queue.add('file_upload', {
            'file': 'document.pdf',
            'size': 1024000
        }, priority=8)
        print(f"Queued high-priority upload: {op1[:8]}...")

        op2 = await queue.add('git_push', {
            'branch': 'feature-x',
            'commits': 3
        }, priority=10)
        print(f"Queued critical git push: {op2[:8]}...")

        op3 = await queue.add('sync_settings', {
            'theme': 'dark'
        }, priority=3)
        print(f"Queued low-priority sync: {op3[:8]}...")

        # Check queue
        stats = queue.get_stats()
        print(f"\nQueue statistics:")
        print(f"  Pending: {stats['pending']}")
        print(f"  Total: {stats['total']}")

        # Process queue
        print("\nProcessing queue...")
        result = await queue.process_all()
        print(f"Processed: {result['processed']}, Failed: {result['failed']}")

    # Cache manager
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(tmpdir, max_size_mb=10)

        print("\n\nCaching data for offline use...")

        # Cache various types of data
        cache.set('user_preferences', {
            'theme': 'dark',
            'language': 'en',
            'auto_sync': True
        }, category='config')

        cache.set('recent_files', [
            '/path/to/file1.py',
            '/path/to/file2.js'
        ], category='history', ttl_seconds=3600)

        cache.set('workspace_state', {
            'current_branch': 'main',
            'modified_files': 5
        }, category='workspace')

        # Retrieve cached data
        prefs = cache.get('user_preferences')
        print(f"Retrieved preferences: {prefs}")

        # Get cache stats
        stats = cache.get_stats()
        print(f"\nCache statistics:")
        print(f"  Total entries: {stats['total_entries']}")
        print(f"  Total size: {stats['total_size']} bytes")
        print(f"  Usage: {stats['usage_percent']:.1f}%")
        print(f"  Categories: {list(stats['categories'].keys())}")

    # Conflict resolution
    resolver = ConflictResolver()

    print("\n\nTesting conflict resolution...")

    # Simulate conflict
    local_version = {
        'content': 'def hello():\n    print("Hello from local")',
        'modified_at': '2024-01-15T10:00:00'
    }

    remote_version = {
        'content': 'def hello():\n    print("Hello from remote")',
        'modified_at': '2024-01-15T11:00:00'
    }

    conflict = resolver.detect_conflict(
        local_version,
        remote_version,
        'hello.py'
    )

    if conflict:
        print(f"Conflict detected: {conflict['id']}")

        # Resolve by timestamp (most recent wins)
        resolution = resolver.resolve_conflict(
            conflict['id'],
            strategy='timestamp'
        )
        print(f"Resolved using timestamp strategy")
        print(f"Winner: {resolution['modified_at']}")


# Main runner
def main():
    """Run all examples"""
    print("=" * 60)
    print("PHASE 5.5 EXAMPLES - CROSS-PLATFORM EXCELLENCE")
    print("=" * 60)

    # Synchronous examples
    example_universal_bubbles()
    example_rest_api()
    example_web_interface()

    # Asynchronous examples
    print("\n" + "=" * 60)
    print("ASYNCHRONOUS EXAMPLES")
    print("=" * 60)

    asyncio.run(example_cloud_native())
    asyncio.run(example_mobile_api())
    asyncio.run(example_offline_mode())

    print("\n" + "=" * 60)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    main()
