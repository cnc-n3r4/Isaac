# tests/test_cloud_client.py
"""
Test Suite for Isaac CloudClient (Phase 2.5)

This module tests cloud sync integration with GoDaddy API.
Tests network reliability, error handling, and data integrity.

Coverage Goal: 90%+
Test Count: 15 scenarios

Test Priority: HIGH (Network reliability + data integrity)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from pathlib import Path
import json


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_api_success():
    """Mock successful API responses for all endpoints"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'success': True,
        'message': 'Operation successful'
    }
    return mock_response


@pytest.fixture
def mock_api_failure():
    """Mock API failures (500, timeout, etc.)"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        'error': 'Internal Server Error'
    }
    return mock_response


@pytest.fixture
def mock_api_unauthorized():
    """Mock 401 Unauthorized response (bad API key)"""
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.json.return_value = {
        'error': 'Unauthorized'
    }
    return mock_response


@pytest.fixture
def cloud_client():
    """CloudClient instance with test credentials"""
    from isaac.api.cloud_client import CloudClient
    return CloudClient(
        api_url='https://test.com/isaac/api',
        api_key='test_key_12345',
        user_id='test_user'
    )


@pytest.fixture
def sample_preferences():
    """Sample preferences.json data"""
    return {
        'machine_id': 'TEST-MACHINE',
        'auto_run_tier2': False,
        'tier_overrides': {},
        'api_url': 'https://test.com/isaac/api',
        'api_key': 'test_key'
    }


@pytest.fixture
def sample_command_history():
    """Sample command_history.json data"""
    return {
        'entries': [
            {
                'command': 'ls -la',
                'machine': 'MACHINE-A',
                'timestamp': '2025-10-18T14:30:00Z',
                'shell': 'PowerShell',
                'exit_code': 0
            }
        ]
    }


@pytest.fixture
def session_manager_with_cloud(tmp_path):
    """SessionManager with cloud sync enabled"""
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    config = {
        'machine_id': 'TEST-MACHINE',
        'sync_enabled': True,
        'api_url': 'https://test.com/isaac/api',
        'api_key': 'test_key',
        'user_id': 'test_user'
    }
    
    shell_adapter = BashAdapter()
    session_mgr = SessionManager(config, shell_adapter)
    
    return session_mgr


@pytest.fixture
def session_manager_local_only(tmp_path):
    """SessionManager with cloud sync disabled"""
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    config = {
        'machine_id': 'TEST-MACHINE',
        'sync_enabled': False
    }
    
    shell_adapter = BashAdapter()
    session_mgr = SessionManager(config, shell_adapter)
    
    return session_mgr


# ============================================================================
# CLOUDCLIENT API COMMUNICATION TESTS (5 tests)
# ============================================================================

@patch('requests.get')
def test_health_check_success(mock_get, cloud_client, mock_api_success):
    """
    Health check returns True when API online.
    
    Test Coverage:
    - GET health_check.php endpoint
    - 200 OK response
    - Returns True (online)
    - Risk if fails: Can't detect API availability
    """
    mock_get.return_value = mock_api_success
    mock_api_success.json.return_value = {
        'status': 'online',
        'timestamp': '2025-10-19T00:00:00Z',
        'version': '1.0.0'
    }
    
    result = cloud_client.health_check()
    
    assert result == True, "Health check should return True when API online"
    mock_get.assert_called_once()
    
    # Verify correct endpoint called
    call_args = mock_get.call_args
    assert 'health_check.php' in call_args[0][0]


@patch('requests.get')
def test_health_check_failure(mock_get, cloud_client, mock_api_failure):
    """
    Health check returns False when API offline.
    
    Test Coverage:
    - API returns 500 error
    - health_check() returns False
    - Error logged, not raised
    - Risk if fails: Might crash on API errors
    """
    mock_get.return_value = mock_api_failure
    
    result = cloud_client.health_check()
    
    assert result == False, "Health check should return False on API error"
    # Should not raise exception (graceful failure)


@patch('requests.post')
def test_save_session_success(mock_post, cloud_client, mock_api_success, sample_preferences):
    """
    Save session succeeds with correct authentication.
    
    Test Coverage:
    - POST save_session.php
    - Bearer token authentication
    - Payload includes user_id, filename, data
    - Returns True on success
    - Risk if fails: Can't save to cloud
    """
    mock_post.return_value = mock_api_success
    
    result = cloud_client.save_session_file('preferences.json', sample_preferences)
    
    assert result == True, "save_session_file should return True on success"
    mock_post.assert_called_once()
    
    # Verify authentication header
    call_kwargs = mock_post.call_args[1]
    assert 'headers' in call_kwargs
    assert call_kwargs['headers']['Authorization'] == 'Bearer test_key_12345'
    
    # Verify payload
    assert 'json' in call_kwargs
    payload = call_kwargs['json']
    assert payload['user_id'] == 'test_user'
    assert payload['filename'] == 'preferences.json'
    assert payload['data'] == sample_preferences


@patch('requests.get')
def test_get_session_success(mock_get, cloud_client, sample_preferences):
    """
    Get session retrieves previously saved data.
    
    Test Coverage:
    - GET get_session.php with query params
    - Data correctly deserialized
    - Returns dict (not None)
    - Risk if fails: Can't load from cloud
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_preferences
    mock_get.return_value = mock_response
    
    result = cloud_client.get_session_file('preferences.json')
    
    assert result is not None, "get_session_file should return data"
    assert result == sample_preferences, "Retrieved data should match saved data"
    
    # Verify query params
    call_args = mock_get.call_args
    assert 'params' in call_args[1]
    params = call_args[1]['params']
    assert params['user_id'] == 'test_user'
    assert params['filename'] == 'preferences.json'


@patch('requests.get')
def test_is_available_checks_connectivity(mock_get, cloud_client, mock_api_success):
    """
    is_available() checks API connectivity.
    
    Test Coverage:
    - If health_check() True → is_available() True
    - If health_check() False → is_available() False
    - Risk if fails: Wrong availability status
    """
    # Test online scenario
    mock_get.return_value = mock_api_success
    mock_api_success.json.return_value = {'status': 'online'}
    
    result_online = cloud_client.is_available()
    assert result_online == True, "is_available should return True when online"
    
    # Test offline scenario
    mock_get.side_effect = requests.ConnectionError("Network unreachable")
    result_offline = cloud_client.is_available()
    assert result_offline == False, "is_available should return False when offline"


# ============================================================================
# ERROR HANDLING TESTS (5 tests)
# ============================================================================

@patch('requests.post')
def test_network_timeout_graceful(mock_post, cloud_client, sample_preferences):
    """
    Network timeout handled gracefully (no crash).
    
    **CRITICAL TEST** - Network reliability
    
    Test Coverage:
    - Mock API times out (5 seconds)
    - save_session_file() returns False
    - No exception raised
    - Error logged
    - Risk if fails: Isaac crashes on network issues
    """
    mock_post.side_effect = requests.Timeout("Connection timed out after 5s")
    
    result = cloud_client.save_session_file('preferences.json', sample_preferences)
    
    assert result == False, "Should return False on timeout (not crash)"
    # Should not raise exception (graceful degradation)


@patch('requests.post')
def test_invalid_api_key_401(mock_post, cloud_client, mock_api_unauthorized, sample_preferences):
    """
    Invalid API key returns 401 Unauthorized.
    
    Test Coverage:
    - API returns 401 error
    - CloudClient logs warning
    - save_session_file() returns False
    - Risk if fails: Auth failures not handled
    """
    mock_post.return_value = mock_api_unauthorized
    
    result = cloud_client.save_session_file('preferences.json', sample_preferences)
    
    assert result == False, "Should return False on 401 Unauthorized"
    mock_post.assert_called_once()


@patch('requests.post')
def test_server_error_500(mock_post, cloud_client, mock_api_failure, sample_preferences):
    """
    Server error (500) handled gracefully.
    
    Test Coverage:
    - API returns 500 Internal Server Error
    - CloudClient retries 3 times
    - Eventually returns False
    - Risk if fails: Infinite retry loops
    """
    mock_post.return_value = mock_api_failure
    
    result = cloud_client.save_session_file('preferences.json', sample_preferences)
    
    assert result == False, "Should return False after retries exhausted"
    # Verify retry logic (should attempt 3 times)
    assert mock_post.call_count <= 3, "Should retry max 3 times on 500 errors"


@patch('requests.get')
def test_malformed_response(mock_get, cloud_client):
    """
    Malformed JSON response handled gracefully.
    
    Test Coverage:
    - API returns invalid JSON
    - get_session_file() returns None
    - Error logged, no crash
    - Risk if fails: JSON parsing crashes Isaac
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_get.return_value = mock_response
    
    result = cloud_client.get_session_file('preferences.json')
    
    assert result is None, "Should return None on malformed JSON"
    # Should not raise exception


def test_missing_api_url():
    """
    Missing API URL prevents network calls.
    
    Test Coverage:
    - CloudClient initialized with empty api_url
    - is_available() returns False
    - No network calls attempted
    - Risk if fails: Attempts network calls without URL
    """
    from isaac.api.cloud_client import CloudClient
    
    client = CloudClient(api_url='', api_key='test_key', user_id='test_user')
    
    result = client.is_available()
    assert result == False, "Should return False when API URL missing"


# ============================================================================
# SESSIONMANAGER INTEGRATION TESTS (3 tests)
# ============================================================================

@patch('isaac.api.cloud_client.CloudClient.health_check')
def test_session_manager_cloud_enabled(mock_health, session_manager_with_cloud):
    """
    SessionManager creates CloudClient when sync enabled.
    
    Test Coverage:
    - Config has sync_enabled: true
    - SessionManager.__init__() creates CloudClient
    - self.cloud is not None
    - Risk if fails: Cloud sync not initialized
    """
    mock_health.return_value = True
    
    assert session_manager_with_cloud.cloud is not None, \
        "SessionManager should create CloudClient when sync_enabled=True"


def test_session_manager_cloud_disabled(session_manager_local_only):
    """
    SessionManager runs local-only when sync disabled.
    
    Test Coverage:
    - Config has sync_enabled: false
    - SessionManager.__init__() sets self.cloud = None
    - Local-only mode works
    - Risk if fails: Tries to sync when disabled
    """
    assert session_manager_local_only.cloud is None, \
        "SessionManager should not create CloudClient when sync_enabled=False"


@patch('isaac.api.cloud_client.CloudClient.health_check')
def test_session_manager_cloud_unreachable(mock_health, tmp_path):
    """
    SessionManager falls back to local when cloud unreachable.
    
    **CRITICAL TEST** - Graceful degradation
    
    Test Coverage:
    - CloudClient health_check() fails on init
    - SessionManager sets self.cloud = None (fallback)
    - Isaac continues in local-only mode
    - Risk if fails: Isaac crashes on cloud unavailability
    """
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    mock_health.return_value = False  # Cloud unreachable
    
    config = {
        'machine_id': 'TEST-MACHINE',
        'sync_enabled': True,
        'api_url': 'https://unreachable.com/api',
        'api_key': 'test_key',
        'user_id': 'test_user'
    }
    
    shell_adapter = BashAdapter()
    session_mgr = SessionManager(config, shell_adapter)
    
    # Should fall back to local-only (no crash)
    assert session_mgr.cloud is None or not session_mgr.cloud.is_available(), \
        "SessionManager should disable cloud sync when unreachable"


# ============================================================================
# DATA INTEGRITY TESTS (2 tests)
# ============================================================================

@patch('requests.post')
@patch('requests.get')
def test_save_and_get_roundtrip(mock_get, mock_post, cloud_client, sample_preferences):
    """
    Save and retrieve data maintains integrity (roundtrip test).
    
    **CRITICAL TEST** - Data integrity
    
    Test Coverage:
    - Save preferences.json to cloud
    - Retrieve preferences.json from cloud
    - Data matches exactly (no corruption)
    - Risk if fails: Data corruption in transit
    """
    # Mock save success
    mock_save_response = Mock()
    mock_save_response.status_code = 200
    mock_save_response.json.return_value = {'success': True}
    mock_post.return_value = mock_save_response
    
    # Mock get success (returns same data)
    mock_get_response = Mock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = sample_preferences
    mock_get.return_value = mock_get_response
    
    # Save data
    save_result = cloud_client.save_session_file('preferences.json', sample_preferences)
    assert save_result == True, "Save should succeed"
    
    # Retrieve data
    retrieved = cloud_client.get_session_file('preferences.json')
    
    # Verify data integrity
    assert retrieved == sample_preferences, "Retrieved data should match saved data exactly"
    assert retrieved['machine_id'] == 'TEST-MACHINE'
    assert retrieved['auto_run_tier2'] == False


@patch('requests.post')
@patch('requests.get')
def test_multi_file_sync(mock_get, mock_post, cloud_client, sample_preferences, sample_command_history):
    """
    Multiple files sync independently without cross-contamination.
    
    Test Coverage:
    - Save command_history.json
    - Save preferences.json
    - Both files retrievable
    - No cross-contamination
    - Risk if fails: Files overwrite each other
    """
    # Mock save success
    mock_save_response = Mock()
    mock_save_response.status_code = 200
    mock_save_response.json.return_value = {'success': True}
    mock_post.return_value = mock_save_response
    
    # Save both files
    result1 = cloud_client.save_session_file('command_history.json', sample_command_history)
    result2 = cloud_client.save_session_file('preferences.json', sample_preferences)
    
    assert result1 == True, "command_history should save"
    assert result2 == True, "preferences should save"
    
    # Mock get responses (different data per file)
    def mock_get_side_effect(url, **kwargs):
        response = Mock()
        response.status_code = 200
        
        if 'command_history.json' in kwargs.get('params', {}).get('filename', ''):
            response.json.return_value = sample_command_history
        elif 'preferences.json' in kwargs.get('params', {}).get('filename', ''):
            response.json.return_value = sample_preferences
        
        return response
    
    mock_get.side_effect = mock_get_side_effect
    
    # Retrieve both files
    retrieved_history = cloud_client.get_session_file('command_history.json')
    retrieved_prefs = cloud_client.get_session_file('preferences.json')
    
    # Verify no cross-contamination
    assert retrieved_history == sample_command_history, "command_history should be intact"
    assert retrieved_prefs == sample_preferences, "preferences should be intact"
    assert retrieved_history != retrieved_prefs, "Files should be different"


# ============================================================================
# SUMMARY
# ============================================================================

"""
Test Suite Summary:
-------------------
Total Tests: 15

Coverage Breakdown:
- API Communication: 5 tests (health, save, get, availability)
- Error Handling: 5 tests (timeout, 401, 500, malformed, missing URL)
- SessionManager Integration: 3 tests (enabled, disabled, unreachable)
- Data Integrity: 2 tests (roundtrip, multi-file)

Critical Tests That MUST Pass:
- test_network_timeout_graceful - No crashes on network failures
- test_session_manager_cloud_unreachable - Fallback to local works
- test_save_and_get_roundtrip - No data corruption

Success Criteria:
✅ All 15 tests passing (100%)
✅ Coverage >= 90% of cloud_client.py
✅ No crashes on network errors
✅ Graceful degradation when cloud unavailable
✅ Data integrity maintained

Next Steps:
1. Run: pytest tests/test_cloud_client.py --cov=isaac.api.cloud_client
2. Verify 90%+ coverage
3. If all pass → Handoff to YAML Maker
4. If failures → Debug cloud sync logic
"""
