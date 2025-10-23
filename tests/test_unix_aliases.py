# tests/test_unix_aliases.py
"""
Test Suite for Unix Alias Translation System

Tests the translation of Unix commands to PowerShell equivalents
"""

import pytest
from pathlib import Path
import json
from unittest.mock import Mock, patch

from isaac.core.unix_aliases import UnixAliasTranslator


@pytest.fixture
def translator():
    """Create a UnixAliasTranslator instance"""
    return UnixAliasTranslator()


@pytest.fixture
def sample_config(tmp_path):
    """Create a sample config file"""
    config_data = {
        "grep": {
            "powershell": "Select-String",
            "bash": "grep",
            "description": "Search text patterns"
        },
        "ls": {
            "powershell": "Get-ChildItem",
            "bash": "ls",
            "description": "List directory",
            "arg_mapping": {
                "-l": "| Format-List",
                "-a": "-Force"
            }
        }
    }

    config_file = tmp_path / "unix_aliases.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f)

    return config_file


class TestUnixAliasTranslator:
    """Test UnixAliasTranslator functionality"""

    def test_translate_simple_command(self, translator):
        """Test simple command translation without args"""
        result = translator.translate("grep")
        assert result == "Select-String"

    def test_translate_command_with_args(self, translator):
        """Test command translation with arguments"""
        result = translator.translate("grep error log.txt")
        assert result == "Select-String error log.txt"

    def test_translate_unknown_command(self, translator):
        """Test unknown command returns None"""
        result = translator.translate("unknown_cmd")
        assert result is None

    def test_translate_with_arg_mapping_simple(self, translator):
        """Test command with simple arg mapping"""
        result = translator.translate("ls -a")
        assert result == "Get-ChildItem -Force"

    def test_translate_with_arg_mapping_complex(self, translator):
        """Test command with complex arg mapping"""
        result = translator.translate("ls -la")
        assert result == "Get-ChildItem -Force | Format-List"

    def test_get_description(self, translator):
        """Test getting command description"""
        desc = translator.get_description("grep")
        assert desc == "Search text patterns"

    def test_get_description_unknown(self, translator):
        """Test getting description for unknown command"""
        desc = translator.get_description("unknown")
        assert desc is None

    def test_list_aliases(self, translator):
        """Test listing all aliases"""
        aliases = translator.list_aliases()
        assert isinstance(aliases, dict)
        assert "grep" in aliases
        assert "ls" in aliases

    def test_get_examples(self, translator):
        """Test getting examples for a command"""
        examples = translator.get_examples("grep")
        assert isinstance(examples, list)
        if examples:
            assert "unix" in examples[0]
            assert "powershell" in examples[0]

    def test_disabled_translator(self, translator):
        """Test translator when disabled"""
        translator.set_enabled(False)
        result = translator.translate("grep")
        assert result is None

    def test_custom_config_file(self, sample_config):
        """Test loading custom config file"""
        translator = UnixAliasTranslator(sample_config)
        result = translator.translate("grep")
        assert result == "Select-String"

    def test_set_show_translation(self, translator):
        """Test setting show translation flag"""
        translator.set_show_translation(False)
        assert not translator.show_translation

        translator.set_show_translation(True)
        assert translator.show_translation


class TestArgMapping:
    """Test argument mapping functionality"""

    def test_kill_with_force_flag(self, translator):
        """Test kill command with -9 flag mapping"""
        result = translator.translate("kill -9 1234")
        assert result == "Stop-Process -Force -Id 1234"

    def test_kill_default_mapping(self, translator):
        """Test kill command default arg mapping"""
        result = translator.translate("kill 1234")
        assert result == "Stop-Process -Id 1234"

    def test_wc_with_line_flag(self, translator):
        """Test wc command with -l flag"""
        result = translator.translate("wc -l file.txt")
        assert result == "Get-Content file.txt | Measure-Object -Line"

    def test_head_with_count(self, translator):
        """Test head command with line count"""
        result = translator.translate("head -n 10 file.txt")
        assert result == "Get-Content file.txt | Select-Object -First 10"


class TestIntegration:
    """Integration tests with command router"""

    @patch('platform.system')
    def test_windows_only_translation(self, mock_platform):
        """Test that translation only happens on Windows"""
        from isaac.core.command_router import CommandRouter

        # Mock Windows
        mock_platform.return_value = 'Windows'

        # Create mock session and shell
        mock_session = Mock()
        mock_session.config = {'enable_unix_aliases': True, 'show_translated_command': True}
        mock_shell = Mock()

        router = CommandRouter(mock_session, mock_shell)

        # Should try translation on Windows
        assert router._is_windows() is True
        assert router._unix_aliases_enabled() is True

    @patch('platform.system')
    def test_no_translation_on_unix(self, mock_platform):
        """Test that no translation happens on Unix systems"""
        from isaac.core.command_router import CommandRouter

        # Mock Linux
        mock_platform.return_value = 'Linux'

        mock_session = Mock()
        mock_shell = Mock()

        router = CommandRouter(mock_session, mock_shell)

        # Should not try translation on Unix
        assert router._is_windows() is False