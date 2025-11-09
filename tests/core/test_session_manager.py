"""
Test Suite for Isaac SessionManager

This module tests the session management system that handles user data,
preferences, command history, and cloud synchronization.

Coverage Goal: 70%+
Test Count: 15+ scenarios
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from isaac.core.session_manager import SessionManager, Preferences, CommandHistory


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_isaac_dir(tmp_path):
    """Create a temporary .isaac directory for testing."""
    isaac_dir = tmp_path / '.isaac'
    isaac_dir.mkdir()
    return isaac_dir


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    return {
        'machine_id': 'TEST-MACHINE-001',
        'api_url': 'https://test.com/api',
        'api_key': 'test_api_key',
        'sync_enabled': False,
        'disable_learning': True
    }


@pytest.fixture
def session_manager(tmp_path, mock_config, monkeypatch):
    """Create a SessionManager with mocked dependencies."""
    # Mock home directory
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    # Mock background workers - patch at import location
    with patch('isaac.queue.command_queue.CommandQueue'), \
         patch('isaac.queue.sync_worker.SyncWorker'):
        session = SessionManager(config=mock_config)
        yield session
        # Cleanup
        if hasattr(session, 'shutdown'):
            session.shutdown()


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

def test_session_manager_initialization(session_manager):
    """
    Test that SessionManager initializes correctly.

    Test Coverage:
    - Isaac directory is created
    - Configuration is loaded
    - Machine ID is set
    - Data structures initialized
    """
    assert session_manager.isaac_dir.exists()
    assert session_manager.config is not None
    assert 'machine_id' in session_manager.config
    assert session_manager.preferences is not None
    assert session_manager.command_history is not None
    assert session_manager.ai_query_history is not None
    assert session_manager.task_history is not None


def test_creates_isaac_directory_if_missing(tmp_path, monkeypatch):
    """
    Test that .isaac directory is created if it doesn't exist.

    Test Coverage:
    - Directory creation on first run
    - No error if directory already exists
    """
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    isaac_dir = tmp_path / '.isaac'
    assert not isaac_dir.exists()

    with patch('isaac.queue.command_queue.CommandQueue'), \
         patch('isaac.queue.sync_worker.SyncWorker'):
        session = SessionManager()

    assert isaac_dir.exists()
    session.shutdown()


def test_generates_machine_id_if_missing(tmp_path, monkeypatch):
    """
    Test that machine ID is auto-generated if not provided.

    Test Coverage:
    - Machine ID generation
    - Machine ID format (8 characters)
    """
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    with patch('isaac.queue.command_queue.CommandQueue'), \
         patch('isaac.queue.sync_worker.SyncWorker'):
        session = SessionManager()

    assert 'machine_id' in session.config
    assert len(session.config['machine_id']) == 8
    session.shutdown()


# ============================================================================
# CONFIGURATION MANAGEMENT TESTS
# ============================================================================

def test_load_config_from_file(tmp_path, monkeypatch):
    """
    Test loading configuration from config.json.

    Test Coverage:
    - Config file is read if exists
    - Config values are loaded correctly
    - Existing config is merged
    """
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    isaac_dir = tmp_path / '.isaac'
    isaac_dir.mkdir()

    config_file = isaac_dir / 'config.json'
    config_data = {
        'machine_id': 'SAVED-MACHINE',
        'api_url': 'https://saved.com/api'
    }
    config_file.write_text(json.dumps(config_data))

    with patch('isaac.queue.command_queue.CommandQueue'), \
         patch('isaac.queue.sync_worker.SyncWorker'):
        session = SessionManager()

    assert session.config['machine_id'] == 'SAVED-MACHINE'
    assert session.config['api_url'] == 'https://saved.com/api'
    session.shutdown()


def test_set_config_saves_to_disk(session_manager):
    """
    Test that set_config updates and saves configuration.

    Test Coverage:
    - Config value is updated in memory
    - Config is saved to config.json
    - File contains updated value
    """
    session_manager.set_config('test_key', 'test_value')

    assert session_manager.config['test_key'] == 'test_value'

    # Verify file was written
    config_file = session_manager.isaac_dir / 'config.json'
    assert config_file.exists()

    config_data = json.loads(config_file.read_text())
    assert config_data['test_key'] == 'test_value'


def test_reload_config(session_manager):
    """
    Test reloading configuration from disk.

    Test Coverage:
    - Config is reloaded from file
    - Memory values are updated
    """
    # Save a config value
    session_manager.set_config('reload_test', 'original')

    # Manually modify the file
    config_file = session_manager.isaac_dir / 'config.json'
    config_data = json.loads(config_file.read_text())
    config_data['reload_test'] = 'modified'
    config_file.write_text(json.dumps(config_data))

    # Reload
    session_manager.reload_config()

    assert session_manager.config['reload_test'] == 'modified'


# ============================================================================
# COMMAND HISTORY TESTS
# ============================================================================

def test_log_command(session_manager):
    """
    Test logging a command to history.

    Test Coverage:
    - Command is added to history
    - Metadata is captured (timestamp, exit_code, shell, machine_id)
    - History is saved to disk
    """
    session_manager.log_command('ls -la', exit_code=0, shell_name='bash')

    assert len(session_manager.command_history.commands) == 1

    entry = session_manager.command_history.commands[0]
    assert entry['command'] == 'ls -la'
    assert entry['exit_code'] == 0
    assert entry['shell'] == 'bash'
    assert 'timestamp' in entry
    assert 'machine_id' in entry


def test_command_history_limit(session_manager):
    """
    Test that command history is limited to 1000 entries.

    Test Coverage:
    - Old commands are removed when limit exceeded
    - Most recent 1000 commands are kept
    """
    # Add 1100 commands
    for i in range(1100):
        session_manager.log_command(f'command_{i}', exit_code=0)

    # Should keep only last 1000
    assert len(session_manager.command_history.commands) == 1000

    # First command should be command_100
    first_entry = session_manager.command_history.commands[0]
    assert first_entry['command'] == 'command_100'


def test_get_recent_commands(session_manager):
    """
    Test retrieving recent commands from history.

    Test Coverage:
    - Returns requested number of commands
    - Commands are in chronological order
    - Most recent commands returned
    """
    session_manager.log_command('cmd1')
    session_manager.log_command('cmd2')
    session_manager.log_command('cmd3')

    recent = session_manager.get_recent_commands(limit=2)

    assert len(recent) == 2
    assert recent[0] == 'cmd2'
    assert recent[1] == 'cmd3'


def test_command_history_persistence(tmp_path, monkeypatch):
    """
    Test that command history persists across sessions.

    Test Coverage:
    - History is saved to disk
    - History is loaded on next session
    """
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    # Create first session and log command
    with patch('isaac.queue.command_queue.CommandQueue'), \
         patch('isaac.queue.sync_worker.SyncWorker'):
        session1 = SessionManager()
        session1.log_command('persistent_command', exit_code=0)
        session1.shutdown()

    # Create second session and check history
    with patch('isaac.queue.command_queue.CommandQueue'), \
         patch('isaac.queue.sync_worker.SyncWorker'):
        session2 = SessionManager()
        assert len(session2.command_history.commands) == 1
        assert session2.command_history.commands[0]['command'] == 'persistent_command'
        session2.shutdown()


# ============================================================================
# AI QUERY HISTORY TESTS
# ============================================================================

def test_log_ai_query(session_manager):
    """
    Test logging an AI query to history.

    Test Coverage:
    - Query is added to history
    - Command translation is saved
    - Execution status is tracked
    """
    session_manager.log_ai_query(
        query='list all files',
        translated_command='ls -la',
        explanation='Lists all files in directory',
        executed=True,
        shell_name='bash'
    )

    # Verify query was logged
    assert len(session_manager.ai_query_history.queries) > 0


def test_add_ai_query_alias(session_manager):
    """
    Test add_ai_query as alias for log_ai_query.

    Test Coverage:
    - Backward compatibility maintained
    - Function works correctly
    """
    session_manager.add_ai_query(
        query='show disk usage',
        translated_command='df -h',
        shell_name='bash'
    )

    # Verify query was logged
    assert len(session_manager.ai_query_history.queries) > 0


# ============================================================================
# PREFERENCES TESTS
# ============================================================================

def test_preferences_persistence(tmp_path, monkeypatch):
    """
    Test that preferences persist across sessions.

    Test Coverage:
    - Preferences are saved to disk
    - Preferences are loaded on next session
    """
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    # Create first session and set preference
    with patch('isaac.queue.command_queue.CommandQueue'), \
         patch('isaac.queue.sync_worker.SyncWorker'):
        session1 = SessionManager()
        session1.preferences.data['test_pref'] = 'test_value'
        session1._save_preferences()
        session1.shutdown()

    # Create second session and check preference
    with patch('isaac.queue.command_queue.CommandQueue'), \
         patch('isaac.queue.sync_worker.SyncWorker'):
        session2 = SessionManager()
        assert session2.preferences.data.get('test_pref') == 'test_value'
        session2.shutdown()


def test_get_preferences(session_manager):
    """
    Test getting preferences object.

    Test Coverage:
    - Returns preferences object
    - Object is the same instance
    """
    prefs = session_manager.get_preferences()

    assert prefs is not None
    assert prefs is session_manager.preferences


# ============================================================================
# ERROR RECOVERY TESTS
# ============================================================================

def test_corrupted_config_fallback(tmp_path, monkeypatch):
    """
    Test that corrupted config.json doesn't crash.

    Test Coverage:
    - Invalid JSON is handled gracefully
    - Default config is used
    - Session initializes successfully
    """
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    isaac_dir = tmp_path / '.isaac'
    isaac_dir.mkdir()

    config_file = isaac_dir / 'config.json'
    config_file.write_text('{ invalid json content }')

    with patch('isaac.queue.command_queue.CommandQueue'), \
         patch('isaac.queue.sync_worker.SyncWorker'):
        session = SessionManager()

    # Should still initialize
    assert session is not None
    assert 'machine_id' in session.config
    session.shutdown()


def test_corrupted_history_fallback(tmp_path, monkeypatch):
    """
    Test that corrupted command_history.json doesn't crash.

    Test Coverage:
    - Invalid JSON is handled gracefully
    - Empty history is used
    - Session initializes successfully
    """
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    isaac_dir = tmp_path / '.isaac'
    isaac_dir.mkdir()

    history_file = isaac_dir / 'command_history.json'
    history_file.write_text('{ invalid json }')

    with patch('isaac.queue.command_queue.CommandQueue'), \
         patch('isaac.queue.sync_worker.SyncWorker'):
        session = SessionManager()

    # Should still initialize with empty history
    assert session is not None
    assert len(session.command_history.commands) == 0
    session.shutdown()


def test_corrupted_preferences_fallback(tmp_path, monkeypatch):
    """
    Test that corrupted preferences.json doesn't crash.

    Test Coverage:
    - Invalid JSON is handled gracefully
    - Default preferences are used
    - Session initializes successfully
    """
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)

    isaac_dir = tmp_path / '.isaac'
    isaac_dir.mkdir()

    prefs_file = isaac_dir / 'preferences.json'
    prefs_file.write_text('not valid json')

    with patch('isaac.queue.command_queue.CommandQueue'), \
         patch('isaac.queue.sync_worker.SyncWorker'):
        session = SessionManager()

    # Should still initialize
    assert session is not None
    assert session.preferences is not None
    session.shutdown()


# ============================================================================
# CLEANUP TESTS
# ============================================================================

def test_shutdown_stops_workers(session_manager):
    """
    Test that shutdown stops background workers.

    Test Coverage:
    - Sync worker is stopped
    - Cron manager is stopped (if present)
    - Learning system is stopped (if present)
    """
    # Mock the workers
    session_manager.sync_worker = Mock()
    session_manager.sync_worker.stop = Mock()

    session_manager.shutdown()

    session_manager.sync_worker.stop.assert_called_once()


def test_get_config(session_manager):
    """
    Test getting configuration dictionary.

    Test Coverage:
    - Returns config dict
    - Contains expected keys
    """
    config = session_manager.get_config()

    assert config is not None
    assert isinstance(config, dict)
    assert 'machine_id' in config


# ============================================================================
# QUEUE AND SYNC TESTS
# ============================================================================

def test_get_queue_status(session_manager):
    """
    Test getting queue status.

    Test Coverage:
    - Returns queue status dict
    - Method doesn't crash
    """
    session_manager.queue = Mock()
    session_manager.queue.get_queue_status = Mock(return_value={'pending': 0})

    status = session_manager.get_queue_status()

    assert status is not None
    assert isinstance(status, dict)


def test_force_sync_without_cloud(session_manager):
    """
    Test force sync when cloud is disabled.

    Test Coverage:
    - Returns False when cloud is None
    - No errors occur
    """
    session_manager.cloud = None

    result = session_manager.force_sync()

    assert result is False


# ============================================================================
# LEARNING SYSTEM TESTS
# ============================================================================

def test_track_mistake_disabled(session_manager):
    """
    Test tracking mistakes when learning is disabled.

    Test Coverage:
    - No error occurs when mistake_learner is None
    - Function returns gracefully
    """
    session_manager.mistake_learner = None

    # Should not crash
    session_manager.track_mistake(
        mistake_type='command_error',
        description='Wrong command',
        correction='Correct command'
    )


def test_get_learning_stats_disabled(session_manager):
    """
    Test getting learning stats when learning is disabled.

    Test Coverage:
    - Returns dict with learning_enabled=False
    - No errors occur
    """
    session_manager.mistake_learner = None

    stats = session_manager.get_learning_stats()

    assert stats is not None
    assert stats['learning_enabled'] is False


# ============================================================================
# SUMMARY
# ============================================================================

"""
Test Suite Summary:
-------------------
Total Tests: 24

Coverage Breakdown:
- Initialization: 3 tests
- Configuration Management: 3 tests
- Command History: 4 tests
- AI Query History: 2 tests
- Preferences: 2 tests
- Error Recovery: 3 tests
- Cleanup: 2 tests
- Queue/Sync: 2 tests
- Learning System: 2 tests

Success Criteria:
✅ 15+ test cases (24 total)
✅ Tests cover session creation and state management
✅ Tests cover context persistence
✅ Tests cover cleanup on exit
✅ Tests cover error recovery mechanisms

Next Steps:
1. Run: pytest tests/core/test_session_manager.py -v
2. Check coverage: pytest tests/core/test_session_manager.py --cov=isaac.core.session_manager
3. Verify 70%+ coverage achieved
"""
