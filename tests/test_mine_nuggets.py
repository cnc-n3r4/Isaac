#!/usr/bin/env python3
"""Test nuggets functionality for /mine command."""

import pytest
from unittest.mock import Mock, patch
from isaac.commands.mine.run import MineHandler


class TestNuggets:
    """Test nugget management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cmd = MineHandler(self.cmd.session_manager)
        self.cmd.session_manager = Mock()
        self.cmd.client = Mock()

    def test_list_nuggets_empty(self):
        """Test listing nuggets when none exist."""
        # Mock empty config
        self.cmd.session_manager.get_config.return_value = {}

        result = self.cmd._list_nuggets()
        assert "No nuggets saved" in result

    def test_list_nuggets_with_data(self):
        """Test listing nuggets with saved data."""
        config = {
            'xai': {
                'collections': {
                    'nuggets': {
                        'song1': {
                            'file_id': 'file_123',
                            'filename': 'test.mp3',
                            'collection': 'music'
                        }
                    }
                }
            }
        }
        self.cmd.session_manager.get_config.return_value = config

        result = self.cmd._list_nuggets()
        assert "song1" in result
        assert "test.mp3" in result
        assert "file_123" in result

    def test_create_nugget_name(self):
        """Test creating readable nugget names."""
        # Test basic filename
        name = self.cmd._create_nugget_name("test.mp3", [])
        assert name == "test"

        # Test uniqueness
        name = self.cmd._create_nugget_name("test.mp3", ["test"])
        assert name == "test_1"

        # Test special characters
        name = self.cmd._create_nugget_name("my-song (2023).mp3", [])
        assert name == "my_song__2023_"

    def test_handle_haul_with_nugget(self):
        """Test hauling by nugget name."""
        config = {
            'xai': {
                'collections': {
                    'nuggets': {
                        'myfile': {
                            'file_id': 'file_123',
                            'filename': 'test.txt',
                            'collection': 'docs'
                        }
                    }
                }
            }
        }
        self.cmd.session_manager.get_config.return_value = config

        # Mock the extract method
        with patch.object(self.cmd, '_handle_haul_extract') as mock_extract:
            mock_extract.return_value = "File content"

            result = self.cmd._handle_haul(['myfile'])
            mock_extract.assert_called_once_with('file_123')
            assert result == "File content"

    def test_handle_haul_with_file_id(self):
        """Test hauling by file_id."""
        with patch.object(self.cmd, '_handle_haul_extract') as mock_extract:
            mock_extract.return_value = "File content"

            result = self.cmd._handle_haul(['file_123'])
            mock_extract.assert_called_once_with('file_123')
            assert result == "File content"


if __name__ == "__main__":
    pytest.main([__file__])