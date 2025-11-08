# tests/conftest.py
"""
Pytest Configuration and Shared Fixtures

This file contains pytest fixtures that are available to all test modules.
"""

import pytest
from pathlib import Path
import json


@pytest.fixture
def temp_isaac_dir(tmp_path):
    """
    Create temporary ~/.isaac directory for testing.
    
    Returns:
        Path: Temporary isaac directory with structure:
            ~/.isaac/
            ├── cache/
            ├── config.json
            └── .warm_restart (optional)
    """
    isaac_dir = tmp_path / '.isaac'
    isaac_dir.mkdir()
    
    cache_dir = isaac_dir / 'cache'
    cache_dir.mkdir()
    
    return isaac_dir


@pytest.fixture
def mock_api_client():
    """
    Mock CloudClient for offline testing.
    
    Returns:
        Mock object with save/get/health methods
    """
    from unittest.mock import Mock
    
    client = Mock()
    client.health_check.return_value = {'status': 'online'}
    client.save_session_file.return_value = {'success': True}
    client.get_session_file.return_value = {}
    client.is_synced.return_value = True
    
    return client


@pytest.fixture
def sample_preferences():
    """
    Sample preferences.json data for testing.
    
    Returns:
        dict: Preferences configuration
    """
    return {
        'machine_id': 'TEST-MACHINE',
        'auto_run_tier2': False,
        'tier_overrides': {},
        'api_url': 'https://test.com/isaac/api',
        'api_key': 'test_key'
    }


@pytest.fixture
def sample_command_history():
    """
    Sample command_history.json data for testing.
    
    Returns:
        dict: Command history with multi-machine entries
    """
    return {
        'entries': [
            {
                'command': 'ls -la',
                'machine': 'MACHINE-A',
                'timestamp': '2025-10-18T14:30:00Z',
                'shell': 'PowerShell',
                'exit_code': 0
            },
            {
                'command': 'git status',
                'machine': 'MACHINE-B',
                'timestamp': '2025-10-18T14:31:00Z',
                'shell': 'bash',
                'exit_code': 0
            }
        ]
    }


@pytest.fixture
def tier_defaults_json(tmp_path):
    """
    Create mock tier_defaults.json file for testing.
    
    Returns:
        Path: Path to temporary tier_defaults.json
    """
    tier_data = {
        "1": ["ls", "cd", "pwd", "echo", "cat", "type", "Get-ChildItem", "Set-Location"],
        "2": ["grep", "Select-String", "head", "tail"],
        "2.5": ["find", "sed", "awk", "Where-Object"],
        "3": ["cp", "mv", "git", "npm", "pip", "Copy-Item", "Move-Item"],
        "4": ["rm", "del", "format", "dd", "Remove-Item", "Format-Volume"]
    }
    
    tier_file = tmp_path / 'tier_defaults.json'
    tier_file.write_text(json.dumps(tier_data, indent=2))
    
    return tier_file
