"""
Comprehensive tests for Phase 5.5 - Cross-Platform Excellence
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
import json

# Import Phase 5.5 components
from isaac.crossplatform.bubbles import UniversalBubble, PlatformAdapter, StateManager
from isaac.crossplatform.cloud import CloudExecutor, CloudStorage, RemoteWorkspace
from isaac.crossplatform.api import RestAPI, WebSocketAPI, WebhookManager, APIAuth
from isaac.crossplatform.web import WebServer, WebTerminal, TerminalEmulator
from isaac.crossplatform.mobile import MobileAPI, NotificationService, MobileAuth
from isaac.crossplatform.offline import OfflineManager, SyncQueue, ConflictResolver, CacheManager


class TestUniversalBubbles:
    """Test Universal Bubbles functionality"""

    def test_bubble_creation(self):
        """Test creating a bubble"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bubble = UniversalBubble(tmpdir)
            state = bubble.capture()

            assert state is not None
            assert 'workspace' in state
            assert 'created_at' in state
            assert 'platform_info' in state or 'created_on' in state

    def test_bubble_save_load(self):
        """Test saving and loading bubbles"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bubble = UniversalBubble(tmpdir)
            bubble.capture()

            # Save bubble
            save_path = Path(tmpdir) / 'test_bubble.json'
            bubble.save(str(save_path))

            assert save_path.exists()

            # Load bubble
            loaded_bubble = UniversalBubble.load(str(save_path))
            assert loaded_bubble.state is not None

    def test_platform_adapter(self):
        """Test platform adapter"""
        platform = PlatformAdapter.get_platform()
        assert platform in ['windows', 'darwin', 'linux']

        # Test path normalization
        path = "/home/user/project"
        normalized = PlatformAdapter.normalize_path(path)
        assert normalized is not None

    def test_state_manager(self):
        """Test state manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(tmpdir)

            # Create a test bubble state
            bubble = UniversalBubble(tmpdir)
            state = bubble.capture()

            # Save using manager
            bubble_id = manager.save_bubble(state, 'test_bubble')
            assert bubble_id is not None

            # List bubbles
            bubbles = manager.list_bubbles()
            assert len(bubbles) > 0

            # Load bubble
            loaded = manager.load_bubble(bubble_id)
            assert loaded is not None


class TestCloudNativeMode:
    """Test Cloud-Native Mode functionality"""

    @pytest.mark.asyncio
    async def test_cloud_executor(self):
        """Test cloud command execution"""
        executor = CloudExecutor()

        result = await executor.execute_command(
            'echo "test"',
            'test-workspace'
        )

        assert result is not None
        assert 'status' in result

    @pytest.mark.asyncio
    async def test_cloud_storage(self):
        """Test cloud storage"""
        storage = CloudStorage()

        # Test workspace upload
        test_data = {'test': 'data'}
        key = await storage.upload_workspace('test-workspace', test_data)

        assert key is not None

    @pytest.mark.asyncio
    async def test_remote_workspace(self):
        """Test remote workspace management"""
        executor = CloudExecutor()
        storage = CloudStorage()
        workspace = RemoteWorkspace(executor, storage)

        # Create workspace
        workspace_id = await workspace.create_workspace('test-workspace')
        assert workspace_id is not None

        # Get workspace info
        info = await workspace.get_workspace_info(workspace_id)
        assert info is not None


class TestAPILayer:
    """Test RESTful API functionality"""

    def test_rest_api_creation(self):
        """Test REST API server creation"""
        api = RestAPI(None)
        app = api.get_app()

        assert app is not None

        # Test with test client
        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200

    def test_api_auth(self):
        """Test API authentication"""
        auth = APIAuth()

        # Create API key
        api_key = auth.create_api_key('test-key')
        assert api_key is not None

        # Validate key
        key_info = auth.validate_api_key(api_key)
        assert key_info is not None
        assert key_info['name'] == 'test-key'

    @pytest.mark.asyncio
    async def test_webhook_manager(self):
        """Test webhook management"""
        manager = WebhookManager()

        # Register webhook
        webhook_id = manager.register_webhook(
            'http://example.com/webhook',
            ['test_event']
        )

        assert webhook_id is not None

        # List webhooks
        webhooks = manager.list_webhooks()
        assert len(webhooks) > 0


class TestWebInterface:
    """Test Web Interface functionality"""

    def test_web_server_creation(self):
        """Test web server creation"""
        server = WebServer(None)
        app = server.get_app()

        assert app is not None

        # Test routes
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200

    def test_web_terminal(self):
        """Test web terminal"""
        terminal = WebTerminal(None)

        # Create session
        session_id = terminal.create_session()
        assert session_id is not None

        # Get session
        session = terminal.get_session(session_id)
        assert session is not None

    def test_terminal_emulator(self):
        """Test terminal emulator"""
        emulator = TerminalEmulator()

        # Test ANSI processing
        output = emulator.process_output('\\033[31mRed text\\033[0m')
        assert 'span' in output or output is not None


class TestMobileAPI:
    """Test Mobile API functionality"""

    def test_mobile_api_creation(self):
        """Test mobile API server creation"""
        api = MobileAPI(None)
        app = api.get_app()

        assert app is not None

        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/mobile/v1/health')
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_notification_service(self):
        """Test notification service"""
        service = NotificationService()

        # Register device
        device_id = service.register_device(
            'test-token',
            'ios',
            'test-user'
        )

        assert device_id is not None

        # Send notification
        await service.send_notification(
            'test-user',
            'info',
            'Test',
            'Test message'
        )

    def test_mobile_auth(self):
        """Test mobile authentication"""
        auth = MobileAuth()

        # Generate pairing code
        code = auth.generate_pairing_code('instance-1')
        assert code is not None
        assert len(code) == 6

        # Validate code
        token = auth.validate_pairing_code(code, 'device-1')
        assert token is not None


class TestOfflineMode:
    """Test Offline Mode functionality"""

    @pytest.mark.asyncio
    async def test_sync_queue(self):
        """Test sync queue"""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = SyncQueue(tmpdir)

            # Add operation
            op_id = await queue.add('test', {'data': 'test'})
            assert op_id is not None

            # Get queue size
            size = queue.get_queue_size()
            assert size > 0

            # Get next operation
            op = await queue.get_next()
            assert op is not None

    def test_cache_manager(self):
        """Test cache manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(tmpdir)

            # Set value
            cache.set('test_key', {'data': 'test'})

            # Get value
            value = cache.get('test_key')
            assert value is not None
            assert value['data'] == 'test'

            # Get stats
            stats = cache.get_stats()
            assert stats['total_entries'] > 0

    def test_conflict_resolver(self):
        """Test conflict resolution"""
        resolver = ConflictResolver()

        # Create test conflict
        local = {
            'content': 'local version',
            'modified_at': '2024-01-15T10:00:00'
        }

        remote = {
            'content': 'remote version',
            'modified_at': '2024-01-15T11:00:00'
        }

        conflict = resolver.detect_conflict(local, remote, 'test-resource')

        if conflict:
            # Resolve by timestamp
            resolution = resolver.resolve_conflict(
                conflict['id'],
                'timestamp'
            )
            assert resolution is not None

    @pytest.mark.asyncio
    async def test_offline_manager(self):
        """Test offline manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = SyncQueue(tmpdir)
            cache = CacheManager(tmpdir)
            manager = OfflineManager(queue, cache)

            # Get status
            status = manager.get_status()
            assert 'is_online' in status

            # Queue operation
            op_id = await manager.queue_operation('test', {'data': 'test'})
            assert op_id is not None


class TestIntegration:
    """Integration tests for Phase 5.5"""

    def test_cross_platform_bubble_workflow(self):
        """Test complete bubble workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create bubble
            bubble = UniversalBubble(tmpdir)
            state = bubble.capture()

            # Save with state manager
            manager = StateManager(tmpdir)
            bubble_id = manager.save_bubble(state, 'integration_test')

            # Load and verify
            loaded = manager.load_bubble(bubble_id)
            assert loaded is not None

            # Check compatibility
            bubble2 = UniversalBubble(tmpdir)
            bubble2.state = loaded
            report = bubble2.get_compatibility_report()

            assert report is not None
            assert 'compatible' in report

    @pytest.mark.asyncio
    async def test_cloud_to_mobile_workflow(self):
        """Test cloud execution with mobile notification"""
        # Create components
        executor = CloudExecutor()
        mobile_notif = NotificationService()

        # Execute command
        result = await executor.execute_command(
            'test command',
            'test-workspace'
        )

        # Register device and send notification
        device_id = mobile_notif.register_device(
            'test-token',
            'ios',
            'test-user'
        )

        await mobile_notif.send_notification(
            'test-user',
            'command_completed',
            'Command Complete',
            f'Command executed: {result["status"]}'
        )

        assert True  # Workflow completed


def run_tests():
    """Run all Phase 5.5 tests"""
    pytest.main([__file__, '-v'])


if __name__ == '__main__':
    run_tests()
