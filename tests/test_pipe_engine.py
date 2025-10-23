"""
Unit tests for PipeEngine hybrid piping functionality
"""

import pytest
import json
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.core.pipe_engine import PipeEngine


class TestPipeEngine:
    """Test cases for PipeEngine functionality."""

    @pytest.fixture
    def mock_session(self):
        """Mock session manager."""
        session = Mock()
        session.get_config.return_value = {}
        return session

    @pytest.fixture
    def mock_shell_adapter(self):
        """Mock shell adapter."""
        shell = Mock()
        shell.name = "PowerShell"
        shell.execute.return_value = Mock(success=True, output="shell output", exit_code=0)
        return shell

    @pytest.fixture
    def pipe_engine(self, mock_session, mock_shell_adapter):
        """Create PipeEngine instance with mocks."""
        return PipeEngine(mock_session, mock_shell_adapter)

    def test_parse_pipe_segments_simple(self, pipe_engine):
        """Test parsing simple pipe commands."""
        cmd = "ls | grep test"
        segments = pipe_engine._parse_pipe_segments(cmd)
        assert segments == ["ls", "grep test"]

    def test_parse_pipe_segments_quoted(self, pipe_engine):
        """Test parsing commands with quoted pipes."""
        cmd = 'echo "hello|world" | cat'
        segments = pipe_engine._parse_pipe_segments(cmd)
        assert segments == ['echo "hello|world"', "cat"]

    def test_parse_pipe_segments_multiple(self, pipe_engine):
        """Test parsing multiple pipe segments."""
        cmd = "cmd1 | cmd2 | cmd3"
        segments = pipe_engine._parse_pipe_segments(cmd)
        assert segments == ["cmd1", "cmd2", "cmd3"]

    def test_is_isaac_command(self, pipe_engine):
        """Test Isaac command detection."""
        assert pipe_engine._is_isaac_command("/ask hello") == True
        assert pipe_engine._is_isaac_command("/mine dig test") == True
        assert pipe_engine._is_isaac_command("ls -la") == False
        assert pipe_engine._is_isaac_command("grep test") == False

    @patch('subprocess.run')
    def test_execute_isaac_command_success(self, mock_subprocess, pipe_engine):
        """Test successful Isaac command execution."""
        # Mock subprocess to simulate successful command execution
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = '{"kind": "text", "content": "test output", "meta": {}}'
        mock_process.stderr = ""
        mock_subprocess.return_value = mock_process

        result = pipe_engine._execute_isaac_command("/save test.txt")

        assert result["kind"] == "text"
        assert result["content"] == "test output"

    @patch('subprocess.run')
    def test_execute_isaac_command_with_stdin(self, mock_subprocess, pipe_engine):
        """Test Isaac command execution with stdin blob."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = '{"kind": "text", "content": "processed output", "meta": {}}'
        mock_process.stderr = ""
        mock_subprocess.return_value = mock_process

        stdin_blob = {"kind": "text", "content": "input data", "meta": {}}
        result = pipe_engine._execute_isaac_command("/save output.txt", stdin_blob)

        assert result["kind"] == "text"
        assert result["content"] == "processed output"

        # Verify subprocess was called with correct stdin
        call_args = mock_subprocess.call_args
        stdin_data = json.loads(call_args[1]["input"])
        assert stdin_data["piped_blob"]["kind"] == "text"
        assert stdin_data["piped_blob"]["content"] == "input data"
        assert stdin_data["args"]["args"] == "output.txt"

    def test_execute_shell_command_success(self, pipe_engine, mock_shell_adapter):
        """Test successful shell command execution."""
        mock_shell_adapter.execute.return_value = Mock(
            success=True, output="directory listing", exit_code=0
        )

        result = pipe_engine._execute_shell_command("ls")

        assert result["kind"] == "text"
        assert result["content"] == "directory listing"
        assert result["meta"]["exit_code"] == 0
        assert result["meta"]["shell"] == "PowerShell"

    def test_execute_shell_command_failure(self, pipe_engine, mock_shell_adapter):
        """Test failed shell command execution."""
        mock_shell_adapter.execute.return_value = Mock(
            success=False, output="command not found", exit_code=1
        )

        result = pipe_engine._execute_shell_command("invalid_cmd")

        assert result["kind"] == "error"
        assert "command not found" in result["content"]
        assert result["meta"]["exit_code"] == 1

    def test_execute_shell_command_with_stdin(self, pipe_engine, mock_shell_adapter):
        """Test shell command execution with stdin."""
        mock_shell_adapter.execute.return_value = Mock(
            success=True, output="processed", exit_code=0
        )

        stdin_blob = {"kind": "text", "content": "input text", "meta": {}}
        result = pipe_engine._execute_shell_command("grep test", stdin_blob)

        # Verify shell adapter was called with stdin
        mock_shell_adapter.execute.assert_called_with("grep test", stdin="input text")

    @patch('subprocess.run')
    def test_execute_pipeline_shell_to_isaac(self, mock_subprocess, pipe_engine, mock_shell_adapter):
        """Test pipeline: shell command -> Isaac command."""
        # Mock shell command output
        mock_shell_adapter.execute.return_value = Mock(
            success=True, output="file contents", exit_code=0
        )

        # Mock Isaac command processing
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = '{"kind": "text", "content": "analyzed content", "meta": {}}'
        mock_process.stderr = ""
        mock_subprocess.return_value = mock_process

        result = pipe_engine.execute_pipeline("cat file.txt | /analyze")

        assert result["kind"] == "text"
        assert result["content"] == "analyzed content"

    @patch('subprocess.run')
    def test_execute_pipeline_isaac_to_shell(self, mock_subprocess, pipe_engine, mock_shell_adapter):
        """Test pipeline: Isaac command -> shell command."""
        # Mock Isaac command output
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = '{"kind": "text", "content": "query results", "meta": {}}'
        mock_process.stderr = ""
        mock_subprocess.return_value = mock_process

        # Mock shell command processing
        mock_shell_adapter.execute.return_value = Mock(
            success=True, output="filtered results", exit_code=0
        )

        result = pipe_engine.execute_pipeline("/mine dig test | grep important")

        assert result["kind"] == "text"
        assert result["content"] == "filtered results"

    def test_execute_pipeline_error_propagation(self, pipe_engine, mock_shell_adapter):
        """Test that errors stop pipeline execution."""
        # Mock first command to fail
        mock_shell_adapter.execute.return_value = Mock(
            success=False, output="command failed", exit_code=1
        )

        result = pipe_engine.execute_pipeline("failing_cmd | /save result.txt")

        assert result["kind"] == "error"
        assert "command failed" in result["content"]

        # Verify second command was not executed
        assert mock_shell_adapter.execute.call_count == 1