"""
Tests for newly migrated standardized commands (Task 2.5 - Part 2)

Tests for: ask, analyze, status, config, help
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.commands.ask.command_impl import AskCommand
from isaac.commands.analyze.command_impl import AnalyzeCommand
from isaac.commands.status.command_impl import StatusCommand
from isaac.commands.config.command_impl import ConfigCommand
from isaac.commands.help.command_impl import HelpCommand


class TestAskCommand:
    """Tests for AskCommand"""

    def test_ask_manifest(self):
        """Test that manifest is correct"""
        cmd = AskCommand()
        manifest = cmd.get_manifest()

        assert manifest.name == "ask"
        assert manifest.tier == 1
        assert "a" in manifest.aliases
        assert manifest.category == "ai"

    def test_ask_missing_query(self):
        """Test that missing query returns error"""
        cmd = AskCommand()
        result = cmd.execute([])

        assert result.success is False
        assert "No query provided" in result.error

    def test_ask_with_piped_input(self):
        """Test ask with piped content"""
        cmd = AskCommand()
        context = {
            "piped_input": "some data",
            "piped_kind": "text"
        }

        result = cmd.execute(["what is this"], context)

        # Will fail due to missing API key, but validates structure
        assert result.success is False
        assert "API key" in result.error or "XaiClient" in str(result.error)

    def test_ask_help_generation(self):
        """Test that help can be generated"""
        cmd = AskCommand()
        help_text = cmd.get_help()

        assert "ask" in help_text
        assert "Usage:" in help_text


class TestAnalyzeCommand:
    """Tests for AnalyzeCommand"""

    def test_analyze_manifest(self):
        """Test that manifest is correct"""
        cmd = AnalyzeCommand()
        manifest = cmd.get_manifest()

        assert manifest.name == "analyze"
        assert manifest.tier == 1
        assert manifest.category == "ai"

    def test_analyze_missing_piped_input(self):
        """Test that missing piped input returns error"""
        cmd = AnalyzeCommand()
        result = cmd.execute([])

        assert result.success is False
        assert "piped" in result.error.lower() or "content" in result.error.lower()

    def test_analyze_with_type(self):
        """Test analyze with analysis type"""
        cmd = AnalyzeCommand()
        context = {
            "piped_input": "test data",
            "piped_kind": "text"
        }

        result = cmd.execute(["sentiment"], context)

        # Will fail due to missing dependency or API key, but validates structure
        assert result.success is False

    def test_analyze_help_generation(self):
        """Test that help can be generated"""
        cmd = AnalyzeCommand()
        help_text = cmd.get_help()

        assert "analyze" in help_text
        assert "Usage:" in help_text


class TestStatusCommand:
    """Tests for StatusCommand"""

    def test_status_manifest(self):
        """Test that manifest is correct"""
        cmd = StatusCommand()
        manifest = cmd.get_manifest()

        assert manifest.name == "status"
        assert manifest.tier == 1
        assert manifest.category == "system"

    def test_status_summary(self):
        """Test status summary output"""
        cmd = StatusCommand()
        context = {
            "session": {
                "machine_id": "test123"
            }
        }

        result = cmd.execute([], context)

        assert result.success is True
        assert "Session" in result.data
        assert "test" in result.data  # Part of machine_id

    def test_status_verbose(self):
        """Test verbose status output"""
        cmd = StatusCommand()
        context = {
            "session": {
                "machine_id": "test123"
            }
        }

        result = cmd.execute(["-v"], context)

        assert result.success is True
        assert "ISAAC System Status" in result.data
        assert result.metadata.get("verbose") is True

    def test_status_help_generation(self):
        """Test that help can be generated"""
        cmd = StatusCommand()
        help_text = cmd.get_help()

        assert "status" in help_text
        assert "Usage:" in help_text


class TestConfigCommand:
    """Tests for ConfigCommand"""

    def test_config_manifest(self):
        """Test that manifest is correct"""
        cmd = ConfigCommand()
        manifest = cmd.get_manifest()

        assert manifest.name == "config"
        assert manifest.tier == 1
        assert manifest.category == "system"

    def test_config_overview(self):
        """Test config overview display"""
        cmd = ConfigCommand()
        context = {
            "session": {
                "machine_id": "test123"
            }
        }

        result = cmd.execute([], context)

        assert result.success is True
        assert "ISAAC Configuration" in result.data
        assert "test123" in result.data

    def test_config_status_flag(self):
        """Test config --status flag"""
        cmd = ConfigCommand()
        context = {
            "session": {
                "machine_id": "test123"
            }
        }

        result = cmd.execute(["--status"], context)

        assert result.success is True
        assert "System Status" in result.data

    def test_config_ai_flag(self):
        """Test config --ai flag"""
        cmd = ConfigCommand()

        result = cmd.execute(["--ai"])

        assert result.success is True
        assert "AI Provider" in result.data

    def test_config_plugins_flag(self):
        """Test config --plugins flag"""
        cmd = ConfigCommand()

        result = cmd.execute(["--plugins"])

        assert result.success is True
        assert "Available Plugins" in result.data

    def test_config_unknown_flag(self):
        """Test config with unknown flag"""
        cmd = ConfigCommand()

        result = cmd.execute(["--unknown-flag-xyz"])

        assert result.success is True
        assert "Unknown flag" in result.data

    def test_config_help_generation(self):
        """Test that help can be generated"""
        cmd = ConfigCommand()
        help_text = cmd.get_help()

        assert "config" in help_text
        assert "Usage:" in help_text


class TestHelpCommand:
    """Tests for HelpCommand"""

    def test_help_manifest(self):
        """Test that manifest is correct"""
        cmd = HelpCommand()
        manifest = cmd.get_manifest()

        assert manifest.name == "help"
        assert manifest.tier == 1
        assert "h" in manifest.aliases
        assert "?" in manifest.aliases
        assert manifest.category == "system"

    def test_help_overview(self):
        """Test help overview display"""
        cmd = HelpCommand()

        result = cmd.execute([])

        assert result.success is True
        assert "Isaac Command Reference" in result.data
        assert "CORE COMMANDS" in result.data

    def test_help_specific_command(self):
        """Test help for specific command"""
        cmd = HelpCommand()

        result = cmd.execute(["/config"])

        assert result.success is True
        assert "Config Command" in result.data
        assert "USAGE:" in result.data

    def test_help_nonexistent_command(self):
        """Test help for nonexistent command"""
        cmd = HelpCommand()

        result = cmd.execute(["/nonexistent"])

        assert result.success is True
        assert "No detailed help available" in result.data

    def test_help_generation(self):
        """Test that help can be generated"""
        cmd = HelpCommand()
        help_text = cmd.get_help()

        assert "help" in help_text
        assert "Usage:" in help_text


class TestCommandResponseFormat:
    """Tests for standardized response format"""

    def test_response_to_dict(self):
        """Test response dict conversion"""
        cmd = StatusCommand()
        context = {"session": {"machine_id": "test"}}
        result = cmd.execute([], context)

        result_dict = result.to_dict()
        assert "success" in result_dict
        assert "data" in result_dict

    def test_response_to_envelope(self):
        """Test response envelope conversion"""
        cmd = StatusCommand()
        context = {"session": {"machine_id": "test"}}
        result = cmd.execute([], context)

        envelope = result.to_envelope()
        assert "ok" in envelope
        assert envelope["ok"] is True
        assert "stdout" in envelope

    def test_error_response_envelope(self):
        """Test error response envelope"""
        cmd = AskCommand()
        result = cmd.execute([])  # Missing query

        envelope = result.to_envelope()
        assert "ok" in envelope
        assert envelope["ok"] is False
        assert "error" in envelope
        assert "message" in envelope["error"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
