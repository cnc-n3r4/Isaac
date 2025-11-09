"""
Tests for Standardized Commands

Tests the migrated commands to ensure they work correctly with the
new standardized base classes.
"""

import json
import pytest
import tempfile
import os
from pathlib import Path

# Import commands
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.commands.read.command_impl import ReadCommand
from isaac.commands.write.command_impl import WriteCommand
from isaac.commands.edit.command_impl import EditCommand
from isaac.commands.grep.command_impl import GrepCommand
from isaac.commands.glob.command_impl import GlobCommand


# ============================================================================
# ReadCommand Tests
# ============================================================================

class TestReadCommand:
    """Test standardized ReadCommand"""

    @pytest.fixture
    def test_file(self):
        """Create a temporary test file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_read_success(self, test_file):
        """Test successful file read"""
        command = ReadCommand()
        result = command.execute([test_file])

        assert result.success is True
        assert "Line 1" in result.data
        assert result.metadata["file_path"] == test_file

    def test_read_missing_file(self):
        """Test reading non-existent file"""
        command = ReadCommand()
        result = command.execute(['/nonexistent/file.txt'])

        assert result.success is False
        assert result.error is not None

    def test_read_no_args(self):
        """Test read with no arguments"""
        command = ReadCommand()
        result = command.execute([])

        assert result.success is False
        assert "required" in result.error.lower()

    def test_read_with_offset(self, test_file):
        """Test read with offset"""
        command = ReadCommand()
        result = command.execute([test_file, '--offset', '2'])

        assert result.success is True
        assert result.metadata["offset"] == 2

    def test_read_with_limit(self, test_file):
        """Test read with limit"""
        command = ReadCommand()
        result = command.execute([test_file, '--limit', '2'])

        assert result.success is True
        assert result.metadata["limit"] == 2

    def test_read_manifest(self):
        """Test read command manifest"""
        command = ReadCommand()
        manifest = command.get_manifest()

        assert manifest.name == "read"
        assert manifest.tier == 1  # Safe operation


# ============================================================================
# WriteCommand Tests
# ============================================================================

class TestWriteCommand:
    """Test standardized WriteCommand"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir

        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    def test_write_success(self, temp_dir):
        """Test successful file write"""
        command = WriteCommand()
        file_path = os.path.join(temp_dir, 'test.txt')

        result = command.execute([file_path, 'test content'])

        assert result.success is True
        assert os.path.exists(file_path)
        assert result.metadata["bytes_written"] > 0

    def test_write_no_args(self):
        """Test write with no arguments"""
        command = WriteCommand()
        result = command.execute([])

        assert result.success is False
        assert "required" in result.error.lower()

    def test_write_no_content(self, temp_dir):
        """Test write without content"""
        command = WriteCommand()
        file_path = os.path.join(temp_dir, 'test.txt')

        result = command.execute([file_path])

        assert result.success is False
        assert "content" in result.error.lower()

    def test_write_with_piped_input(self, temp_dir):
        """Test write with piped input"""
        command = WriteCommand()
        file_path = os.path.join(temp_dir, 'test.txt')

        context = {"piped_input": "piped content"}
        result = command.execute([file_path], context=context)

        assert result.success is True
        assert os.path.exists(file_path)

    def test_write_manifest(self):
        """Test write command manifest"""
        command = WriteCommand()
        manifest = command.get_manifest()

        assert manifest.name == "write"
        assert manifest.tier == 2  # Needs validation


# ============================================================================
# EditCommand Tests
# ============================================================================

class TestEditCommand:
    """Test standardized EditCommand"""

    @pytest.fixture
    def test_file(self):
        """Create a temporary test file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello World\nTest Line\nHello Again\n")
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_edit_success(self, test_file):
        """Test successful file edit"""
        command = EditCommand()
        result = command.execute([test_file, 'Hello', 'Hi'])

        assert result.success is True
        assert result.metadata["replacements"] >= 1

    def test_edit_no_args(self):
        """Test edit with no arguments"""
        command = EditCommand()
        result = command.execute([])

        assert result.success is False

    def test_edit_replace_all(self, test_file):
        """Test edit with replace-all flag"""
        command = EditCommand()
        result = command.execute([test_file, 'Hello', 'Hi', '--replace-all'])

        assert result.success is True
        assert result.metadata["replace_all"] is True

    def test_edit_manifest(self):
        """Test edit command manifest"""
        command = EditCommand()
        manifest = command.get_manifest()

        assert manifest.name == "edit"
        assert manifest.tier == 2  # Needs validation


# ============================================================================
# GrepCommand Tests
# ============================================================================

class TestGrepCommand:
    """Test standardized GrepCommand"""

    @pytest.fixture
    def test_dir(self):
        """Create temporary directory with test files"""
        temp_dir = tempfile.mkdtemp()

        # Create test files
        with open(os.path.join(temp_dir, 'file1.txt'), 'w') as f:
            f.write("TODO: Fix this\nSome content\nTODO: Another task\n")

        with open(os.path.join(temp_dir, 'file2.py'), 'w') as f:
            f.write("def test():\n    # TODO: Implement\n    pass\n")

        yield temp_dir

        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    def test_grep_success(self, test_dir):
        """Test successful grep"""
        command = GrepCommand()
        result = command.execute(['TODO', '--path', test_dir])

        assert result.success is True
        assert result.metadata["match_count"] >= 0

    def test_grep_no_pattern(self):
        """Test grep without pattern"""
        command = GrepCommand()
        result = command.execute([])

        assert result.success is False
        assert "required" in result.error.lower()

    def test_grep_with_glob(self, test_dir):
        """Test grep with glob pattern"""
        command = GrepCommand()
        result = command.execute(['TODO', '--path', test_dir, '--glob', '*.txt'])

        assert result.success is True

    def test_grep_manifest(self):
        """Test grep command manifest"""
        command = GrepCommand()
        manifest = command.get_manifest()

        assert manifest.name == "grep"
        assert manifest.tier == 1  # Safe operation


# ============================================================================
# GlobCommand Tests
# ============================================================================

class TestGlobCommand:
    """Test standardized GlobCommand"""

    @pytest.fixture
    def test_dir(self):
        """Create temporary directory with test files"""
        temp_dir = tempfile.mkdtemp()

        # Create test files
        Path(os.path.join(temp_dir, 'file1.txt')).touch()
        Path(os.path.join(temp_dir, 'file2.py')).touch()
        Path(os.path.join(temp_dir, 'file3.md')).touch()

        yield temp_dir

        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    def test_glob_success(self, test_dir):
        """Test successful glob"""
        command = GlobCommand()
        result = command.execute(['*.txt', '--path', test_dir])

        assert result.success is True
        assert result.metadata["count"] >= 0

    def test_glob_no_pattern(self):
        """Test glob without pattern"""
        command = GlobCommand()
        result = command.execute([])

        assert result.success is False
        assert "required" in result.error.lower()

    def test_glob_manifest(self):
        """Test glob command manifest"""
        command = GlobCommand()
        manifest = command.get_manifest()

        assert manifest.name == "glob"
        assert manifest.tier == 1  # Safe operation


# ============================================================================
# Integration Tests
# ============================================================================

class TestCommandIntegration:
    """Integration tests for command interactions"""

    def test_read_write_pipeline(self, tmp_path):
        """Test read -> write pipeline"""
        # Create source file
        source = tmp_path / "source.txt"
        source.write_text("Test content")

        # Read file
        read_cmd = ReadCommand()
        read_result = read_cmd.execute([str(source)])

        assert read_result.success is True

        # Write to destination using read output
        dest = tmp_path / "dest.txt"
        write_cmd = WriteCommand()
        write_context = {"piped_input": read_result.data}
        write_result = write_cmd.execute([str(dest)], context=write_context)

        assert write_result.success is True
        assert dest.read_text() == "Test content"

    def test_all_commands_have_manifest(self):
        """Test that all commands have valid manifests"""
        commands = [
            ReadCommand(),
            WriteCommand(),
            EditCommand(),
            GrepCommand(),
            GlobCommand()
        ]

        for cmd in commands:
            manifest = cmd.get_manifest()

            # Verify required fields
            assert manifest.name
            assert manifest.description
            assert manifest.usage
            assert manifest.tier in [1, 2, 3, 4]
            assert isinstance(manifest.examples, list)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
