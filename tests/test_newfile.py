# tests/test_newfile.py
"""
Test Suite for Newfile Command

Tests the /newfile command for creating files with templates
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from isaac.core.session_manager import SessionManager
from isaac.commands.newfile.run import (
    main, handle_create_file, handle_list_templates,
    handle_set_template, handle_help, get_templates,
    get_default_templates, get_template_content
)


@pytest.fixture
def session_manager():
    """Create a mock session manager"""
    manager = Mock(spec=SessionManager)
    manager.get_config.return_value = {}
    manager.config = {}
    return manager


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing"""
    return tmp_path


class TestNewfileCommand:
    """Test newfile command functionality"""

    def test_handle_help(self):
        """Test help display"""
        result = handle_help()
        assert "Newfile Command - Create files with templates" in result
        assert "USAGE:" in result
        assert "EXAMPLES:" in result

    def test_get_default_templates(self):
        """Test default templates"""
        templates = get_default_templates()
        assert ".py" in templates
        assert ".txt" in templates
        assert ".md" in templates
        assert ".json" in templates
        assert ".html" in templates

        # Check Python template
        py_template = templates[".py"][0]
        assert "Python starter" in py_template["desc"]
        assert "#!/usr/bin/env python" in py_template["body"]

    def test_get_template_content(self, session_manager):
        """Test template content retrieval"""
        templates = get_default_templates()

        # Test exact match
        content = get_template_content(templates, ".py", ".txt")
        assert content is not None
        assert "#!/usr/bin/env python" in content

        # Test file extension fallback
        content = get_template_content(templates, ".unknown", ".py")
        assert content is not None
        assert "#!/usr/bin/env python" in content

        # Test no match
        content = get_template_content(templates, ".unknown", ".unknown")
        assert content is None

    def test_handle_list_templates(self, session_manager):
        """Test template listing"""
        result = handle_list_templates(session_manager)
        assert "Available templates:" in result
        assert ".py" in result
        assert ".txt" in result
        assert ".md" in result

    def test_handle_set_template(self, session_manager):
        """Test setting custom template"""
        result = handle_set_template(session_manager, "py", "custom content")
        assert "Template set for .py" in result

        # Check that session was updated
        assert ".py" in session_manager.config["newfile_templates"]
        assert session_manager.config["newfile_templates"][".py"][0]["body"] == "custom content"

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    def test_handle_create_file_with_content(self, mock_mkdir, mock_file, session_manager, temp_dir):
        """Test creating file with inline content"""
        test_file = temp_dir / "test.txt"

        with patch('isaac.commands.newfile.run.Path') as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.expanduser.return_value.resolve.return_value = test_file
            mock_path_instance.exists.return_value = False
            mock_path_instance.parent.mkdir.return_value = None
            mock_path.return_value = mock_path_instance

            result = handle_create_file(session_manager, "test.txt", None, "Hello World", False)

            assert "File created:" in result
            mock_file.assert_called_once_with(test_file, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with("Hello World")

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    def test_handle_create_file_with_template(self, mock_mkdir, mock_file, session_manager, temp_dir):
        """Test creating file with template"""
        test_file = temp_dir / "test.py"

        with patch('isaac.commands.newfile.run.Path') as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.expanduser.return_value.resolve.return_value = test_file
            mock_path_instance.exists.return_value = False
            mock_path_instance.suffix = ".py"
            mock_path_instance.parent.mkdir.return_value = None
            mock_path.return_value = mock_path_instance

            result = handle_create_file(session_manager, "test.py", ".py", None, False)

            assert "File created:" in result
            mock_file.assert_called_once_with(test_file, "w", encoding="utf-8")
            # Should have written Python template content
            written_content = mock_file().write.call_args[0][0]
            assert "#!/usr/bin/env python" in written_content

    @patch('isaac.commands.newfile.run.Path')
    def test_handle_create_file_exists_no_force(self, mock_path_class, session_manager, temp_dir):
        """Test creating file that exists without force flag"""
        # Mock the Path instance
        mock_path_instance = Mock()
        mock_path_instance.expanduser.return_value.resolve.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True  # File exists
        mock_path_class.return_value = mock_path_instance

        result = handle_create_file(session_manager, "existing.txt", None, "content", False)

        assert "exists. Use --force to overwrite" in result
        # Should not try to open file for writing
        with patch('builtins.open') as mock_open:
            handle_create_file(session_manager, "existing.txt", None, "content", False)
            mock_open.assert_not_called()

    def test_main_help(self, session_manager):
        """Test main function with help flag"""
        payload = {
            "args": {"args": "--help"},
            "session": {}
        }

        with patch('sys.stdin.read', return_value=json.dumps(payload)), \
             patch('argparse.ArgumentParser.parse_args') as mock_parse:
            mock_args = Mock()
            mock_args.help = True
            mock_args.file = None
            mock_args.list_templates = False
            mock_args.set_template = None
            mock_parse.return_value = mock_args
            
            with patch('builtins.print') as mock_print:
                main()
                # Check that print was called with help output
                call_args = mock_print.call_args[0][0]
                output = json.loads(call_args)
                assert "Newfile Command" in output["stdout"]

    def test_main_no_args_shows_help(self, session_manager):
        """Test main function with no arguments shows help"""
        payload = {
            "args": {"args": ""},
            "session": {}
        }

        with patch('sys.stdin.read', return_value=json.dumps(payload)), \
             patch('argparse.ArgumentParser.parse_args') as mock_parse:
            mock_args = Mock()
            mock_args.help = False
            mock_args.file = None
            mock_args.template = None
            mock_args.content = None
            mock_args.force = False
            mock_args.list_templates = False
            mock_args.set_template = None
            mock_parse.return_value = mock_args
            
            with patch('builtins.print') as mock_print:
                main()
                # Check that print was called with help output
                call_args = mock_print.call_args[0][0]
                output = json.loads(call_args)
                assert "Newfile Command" in output["stdout"]

    def test_main_create_file(self, session_manager):
        """Test main function creating a file"""
        payload = {
            "args": {"args": "test.txt --content test content"},
            "session": {}
        }

        with patch('sys.stdin.read', return_value=json.dumps(payload)), \
             patch('argparse.ArgumentParser.parse_args') as mock_parse, \
             patch('isaac.commands.newfile.run.handle_create_file', return_value="File created"):
            mock_args = Mock()
            mock_args.file = "test.txt"
            mock_args.template = None
            mock_args.content = "test content"
            mock_args.force = False
            mock_args.list_templates = False
            mock_args.set_template = None
            mock_args.help = False
            mock_parse.return_value = mock_args
            
            with patch('builtins.print') as mock_print:
                main()
                call_args = mock_print.call_args[0][0]
                output = json.loads(call_args)
                assert output["ok"] is True
                assert output["stdout"] == "File created"

    def test_main_missing_file(self, session_manager):
        """Test main function with missing file argument"""
        payload = {
            "args": {"args": "--template .py"},
            "session": {}
        }

        with patch('sys.stdin.read', return_value=json.dumps(payload)), \
             patch('argparse.ArgumentParser.parse_args') as mock_parse:
            mock_args = Mock()
            mock_args.file = None
            mock_args.template = ".py"
            mock_args.content = None
            mock_args.force = False
            mock_args.list_templates = False
            mock_args.set_template = None
            mock_args.help = False
            mock_parse.return_value = mock_args
            
            with patch('builtins.print') as mock_print:
                main()
                call_args = mock_print.call_args[0][0]
                output = json.loads(call_args)
                assert output["ok"] is True
                assert "File name required" in output["stdout"]

    def test_main_list_templates(self, session_manager):
        """Test main function listing templates"""
        payload = {
            "args": {"args": "--list-templates"},
            "session": {}
        }

        with patch('sys.stdin.read', return_value=json.dumps(payload)), \
             patch('argparse.ArgumentParser.parse_args') as mock_parse, \
             patch('isaac.commands.newfile.run.handle_list_templates', return_value="templates"):
            mock_args = Mock()
            mock_args.list_templates = True
            mock_args.file = None
            mock_args.template = None
            mock_args.content = None
            mock_args.force = False
            mock_args.set_template = None
            mock_args.help = False
            mock_parse.return_value = mock_args
            
            with patch('builtins.print') as mock_print:
                main()
                call_args = mock_print.call_args[0][0]
                output = json.loads(call_args)
                assert output["ok"] is True
                assert output["stdout"] == "templates"

    def test_main_set_template(self, session_manager):
        """Test main function setting template"""
        payload = {
            "args": {"args": "--set-template .py 'custom content'"},
            "session": {}
        }

        with patch('sys.stdin.read', return_value=json.dumps(payload)), \
             patch('argparse.ArgumentParser.parse_args') as mock_parse, \
             patch('isaac.commands.newfile.run.handle_set_template', return_value="set"):
            mock_args = Mock()
            mock_args.set_template = [".py", "custom content"]
            mock_args.file = None
            mock_args.template = None
            mock_args.content = None
            mock_args.force = False
            mock_args.list_templates = False
            mock_args.help = False
            mock_parse.return_value = mock_args
            
            with patch('builtins.print') as mock_print:
                main()
                call_args = mock_print.call_args[0][0]
                output = json.loads(call_args)
                assert output["ok"] is True
                assert output["stdout"] == "set"

    def test_main_piped_content(self, session_manager):
        """Test main function with piped content"""
        piped_payload = {
            "args": {"args": '"test.txt"'},
            "session": {},
            "piped_blob": {
                "kind": "text",
                "content": "This is piped content from another command",
                "meta": {"command": "/ask test"}
            }
        }

        with patch('sys.stdin.read', return_value=json.dumps(piped_payload)), \
             patch('argparse.ArgumentParser.parse_args') as mock_parse, \
             patch('isaac.commands.newfile.run.handle_create_file', return_value="File created: test.txt"):
            mock_args = Mock()
            mock_args.file = "test.txt"
            mock_args.force = False
            mock_parse.return_value = mock_args
            
            with patch('builtins.print') as mock_print:
                main()
                call_args = mock_print.call_args[0][0]
                output = json.loads(call_args)
                assert output["ok"] is True
                assert output["stdout"] == "File created: test.txt"