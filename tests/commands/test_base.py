"""
Tests for Base Command Classes

Tests the standardized command infrastructure including:
- CommandManifest
- CommandResponse
- FlagParser
- BaseCommand
"""

import json
import pytest
from typing import Any, Dict, List, Optional

# Import base classes
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.commands.base import (
    CommandManifest,
    CommandResponse,
    FlagParser,
    BaseCommand,
    detect_execution_mode
)


# ============================================================================
# CommandManifest Tests
# ============================================================================

class TestCommandManifest:
    """Test CommandManifest dataclass"""

    def test_manifest_creation(self):
        """Test creating a command manifest"""
        manifest = CommandManifest(
            name="test",
            description="Test command",
            usage="/test <arg>",
            examples=["/test example"],
            tier=1
        )

        assert manifest.name == "test"
        assert manifest.description == "Test command"
        assert manifest.tier == 1

    def test_manifest_with_defaults(self):
        """Test manifest with default values"""
        manifest = CommandManifest(
            name="test",
            description="Test",
            usage="/test",
            examples=[],
            tier=1
        )

        assert manifest.aliases == []
        assert manifest.category == "general"

    def test_manifest_with_aliases(self):
        """Test manifest with aliases"""
        manifest = CommandManifest(
            name="test",
            description="Test",
            usage="/test",
            examples=[],
            tier=1,
            aliases=["t", "tst"]
        )

        assert "t" in manifest.aliases
        assert "tst" in manifest.aliases


# ============================================================================
# CommandResponse Tests
# ============================================================================

class TestCommandResponse:
    """Test CommandResponse class"""

    def test_success_response(self):
        """Test creating a success response"""
        response = CommandResponse(
            success=True,
            data="test data"
        )

        assert response.success is True
        assert response.data == "test data"
        assert response.error is None

    def test_error_response(self):
        """Test creating an error response"""
        response = CommandResponse(
            success=False,
            error="Test error"
        )

        assert response.success is False
        assert response.error == "Test error"
        assert response.data is None

    def test_response_with_metadata(self):
        """Test response with metadata"""
        response = CommandResponse(
            success=True,
            data="result",
            metadata={"key": "value", "count": 5}
        )

        assert response.metadata["key"] == "value"
        assert response.metadata["count"] == 5

    def test_to_dict(self):
        """Test converting response to dictionary"""
        response = CommandResponse(
            success=True,
            data="test",
            metadata={"info": "meta"}
        )

        result = response.to_dict()

        assert result["success"] is True
        assert result["data"] == "test"
        assert result["metadata"]["info"] == "meta"

    def test_to_envelope_success(self):
        """Test converting to dispatcher envelope format (success)"""
        response = CommandResponse(
            success=True,
            data="output text"
        )

        envelope = response.to_envelope()

        assert envelope["ok"] is True
        assert envelope["stdout"] == "output text"

    def test_to_envelope_error(self):
        """Test converting to dispatcher envelope format (error)"""
        response = CommandResponse(
            success=False,
            error="Something went wrong",
            metadata={"error_code": "TEST_ERROR"}
        )

        envelope = response.to_envelope()

        assert envelope["ok"] is False
        assert envelope["error"]["code"] == "TEST_ERROR"
        assert envelope["error"]["message"] == "Something went wrong"

    def test_to_blob_success(self):
        """Test converting to blob format (success)"""
        response = CommandResponse(
            success=True,
            data="blob content",
            metadata={"kind": "text"}
        )

        blob = response.to_blob(command="/test")

        assert blob["kind"] == "text"
        assert blob["content"] == "blob content"
        assert blob["meta"]["command"] == "/test"

    def test_to_blob_error(self):
        """Test converting to blob format (error)"""
        response = CommandResponse(
            success=False,
            error="Test error"
        )

        blob = response.to_blob(command="/test")

        assert blob["kind"] == "error"
        assert "Test error" in blob["content"]


# ============================================================================
# FlagParser Tests
# ============================================================================

class TestFlagParser:
    """Test FlagParser class"""

    def test_parse_positional_args(self):
        """Test parsing positional arguments"""
        parser = FlagParser(['arg1', 'arg2', 'arg3'])

        assert parser.get_positional(0) == 'arg1'
        assert parser.get_positional(1) == 'arg2'
        assert parser.get_positional(2) == 'arg3'

    def test_parse_positional_with_default(self):
        """Test positional argument with default"""
        parser = FlagParser(['arg1'])

        assert parser.get_positional(0) == 'arg1'
        assert parser.get_positional(1, default='default') == 'default'
        assert parser.get_positional(5) is None

    def test_parse_boolean_flags(self):
        """Test parsing boolean flags"""
        parser = FlagParser(['arg1', '--flag1', '--flag2'])

        assert parser.get_flag('flag1') is True
        assert parser.get_flag('flag2') is True
        assert parser.get_flag('flag3') is None

    def test_parse_flags_with_values(self):
        """Test parsing flags with values"""
        parser = FlagParser(['--output', 'json', '--count', '5'])

        assert parser.get_flag('output') == 'json'
        assert parser.get_flag('count') == '5'

    def test_parse_short_flags(self):
        """Test parsing short flags"""
        parser = FlagParser(['-i', '-C', '3'])

        assert parser.get_flag('i') is True
        assert parser.get_flag('C') == '3'

    def test_parse_mixed_args(self):
        """Test parsing mixed positional and flags"""
        parser = FlagParser(['file.txt', '--overwrite', 'content', '--verbose'])

        assert parser.get_positional(0) == 'file.txt'
        assert parser.get_positional(1) == 'content'
        assert parser.get_flag('overwrite') is True
        assert parser.get_flag('verbose') is True

    def test_flag_aliases(self):
        """Test flag with aliases"""
        parser = FlagParser(['-i'])

        assert parser.get_flag('ignore-case', aliases=['i']) is True
        assert parser.has_flag('ignore-case', aliases=['i']) is True

    def test_get_all_positional(self):
        """Test getting all positional arguments"""
        parser = FlagParser(['a', 'b', '--flag', 'c'])

        positional = parser.get_all_positional()

        assert positional == ['a', 'b', 'c']

    def test_get_all_flags(self):
        """Test getting all flags"""
        parser = FlagParser(['--flag1', 'value1', '--flag2'])

        flags = parser.get_all_flags()

        assert flags['flag1'] == 'value1'
        assert flags['flag2'] is True


# ============================================================================
# BaseCommand Tests
# ============================================================================

class MockCommand(BaseCommand):
    """Mock command for testing"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        parser = FlagParser(args)
        arg1 = parser.get_positional(0)

        if not arg1:
            return CommandResponse(
                success=False,
                error="Argument required",
                metadata={"error_code": "MISSING_ARG"}
            )

        return CommandResponse(
            success=True,
            data=f"Processed: {arg1}",
            metadata={"arg1": arg1}
        )

    def get_manifest(self) -> CommandManifest:
        return CommandManifest(
            name="mock",
            description="Mock command for testing",
            usage="/mock <arg>",
            examples=["/mock test"],
            tier=1,
            aliases=["m"],
            category="test"
        )


class TestBaseCommand:
    """Test BaseCommand abstract class"""

    def test_command_execution_success(self):
        """Test successful command execution"""
        command = MockCommand()
        result = command.execute(['test_arg'])

        assert result.success is True
        assert result.data == "Processed: test_arg"

    def test_command_execution_failure(self):
        """Test failed command execution"""
        command = MockCommand()
        result = command.execute([])

        assert result.success is False
        assert "required" in result.error.lower()

    def test_get_manifest(self):
        """Test getting command manifest"""
        command = MockCommand()
        manifest = command.get_manifest()

        assert manifest.name == "mock"
        assert manifest.tier == 1
        assert "m" in manifest.aliases

    def test_get_help(self):
        """Test auto-generated help text"""
        command = MockCommand()
        help_text = command.get_help()

        assert "mock" in help_text
        assert "Mock command for testing" in help_text
        assert "/mock <arg>" in help_text
        assert "/mock test" in help_text

    def test_execution_with_context(self):
        """Test execution with context"""
        command = MockCommand()
        context = {"session": "test_session", "config": {}}

        result = command.execute(['arg'], context=context)

        assert result.success is True


# ============================================================================
# Integration Tests
# ============================================================================

class TestCommandIntegration:
    """Integration tests for command flow"""

    def test_full_command_flow(self):
        """Test complete command flow from parsing to response"""
        command = MockCommand()

        # Parse args
        args = ['test_file', '--verbose']

        # Execute
        result = command.execute(args)

        # Verify
        assert result.success is True

        # Convert to envelope
        envelope = result.to_envelope()
        assert envelope["ok"] is True

    def test_error_flow(self):
        """Test error handling flow"""
        command = MockCommand()

        # Execute with missing arg
        result = command.execute([])

        # Verify error
        assert result.success is False
        assert result.error is not None

        # Convert to envelope
        envelope = result.to_envelope()
        assert envelope["ok"] is False
        assert "error" in envelope

    def test_piped_context(self):
        """Test execution with piped input context"""
        command = MockCommand()

        context = {
            "piped_input": "piped data",
            "piped_kind": "text",
            "piped_meta": {"command": "/previous"}
        }

        result = command.execute(['arg'], context=context)

        assert result.success is True


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_args(self):
        """Test with empty argument list"""
        parser = FlagParser([])

        assert parser.get_positional(0) is None
        assert parser.get_all_positional() == []
        assert parser.get_all_flags() == {}

    def test_flag_without_value(self):
        """Test flag that should have value but doesn't"""
        parser = FlagParser(['--output'])

        # Should be treated as boolean
        assert parser.get_flag('output') is True

    def test_response_with_none_data(self):
        """Test response with None data"""
        response = CommandResponse(success=True, data=None)

        envelope = response.to_envelope()
        assert envelope["stdout"] == ""

    def test_response_with_complex_data(self):
        """Test response with complex data structure"""
        data = {"files": ["a.txt", "b.txt"], "count": 2}
        response = CommandResponse(success=True, data=data)

        envelope = response.to_envelope()
        # Should be JSON serialized
        assert '"files"' in envelope["stdout"]


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
