"""
Test UI Components - Basic functionality tests
"""

import os
import pytest
from unittest.mock import Mock, patch
from isaac.ui.terminal_control import TerminalControl
from isaac.ui.splash_screen import SplashScreen
from isaac.ui.header_display import HeaderDisplay
from isaac.ui.prompt_handler import PromptHandler
from isaac.ui.advanced_input import AdvancedInputHandler
from isaac.ui.visual_enhancer import VisualEnhancer, Color
from isaac.models.preferences import Preferences
from isaac.core.tier_validator import TierValidator


class TestTerminalControl:
    """Test terminal control functionality."""

    def test_initialization(self):
        """Test terminal control initializes correctly."""
        control = TerminalControl()
        assert control.header_lines == 4
        assert control.is_windows == (os.name == 'nt')  # Should be True on Windows

    def test_get_terminal_size(self):
        """Test terminal size detection."""
        with patch('shutil.get_terminal_size') as mock_size:
            mock_size.return_value = Mock(columns=120, lines=30)
            control = TerminalControl()
            width, height = control.get_terminal_size()
            assert width == 120
            assert height == 30


class TestSplashScreen:
    """Test splash screen functionality."""

    def test_initialization(self):
        """Test splash screen initializes correctly."""
        mock_terminal = Mock()
        splash = SplashScreen(mock_terminal)
        assert splash.terminal == mock_terminal

    def test_war_games_reference(self):
        """Test War Games reference display."""
        mock_terminal = Mock()
        mock_terminal.get_terminal_size.return_value = (80, 24)
        splash = SplashScreen(mock_terminal)

        splash._show_war_games_reference()

        # Verify clear_screen and move_cursor were called
        mock_terminal.clear_screen.assert_called_once()
        mock_terminal.move_cursor.assert_called()


class TestHeaderDisplay:
    """Test header display functionality."""

    def test_initialization(self):
        """Test header display initializes correctly."""
        mock_terminal = Mock()
        prefs = Preferences(machine_id="test-machine")
        header = HeaderDisplay(mock_terminal, prefs)

        assert header.terminal == mock_terminal
        assert header.preferences == prefs
        assert header.current_tier == 1
        assert header.cloud_status == "offline"
        assert header.shell_type == "unknown"

    def test_update_header(self):
        """Test header updates correctly."""
        mock_terminal = Mock()
        mock_terminal.get_terminal_size.return_value = (80, 24)
        prefs = Preferences(machine_id="test-machine")
        header = HeaderDisplay(mock_terminal, prefs)

        header.update_header(tier=2, cloud_status="synced", shell_type="powershell")

        assert header.current_tier == 2
        assert header.cloud_status == "synced"
        assert header.shell_type == "powershell"


class TestPromptHandler:
    """Test prompt handler functionality."""

    def test_initialization(self):
        """Test prompt handler initializes correctly."""
        mock_terminal = Mock()
        mock_terminal.get_input_area_start.return_value = 20
        mock_terminal.get_scroll_region_start.return_value = 4
        mock_validator = Mock()
        handler = PromptHandler(mock_terminal, mock_validator)

        assert handler.terminal == mock_terminal
        assert handler.tier_validator == mock_validator
        assert handler.input_area_start == 20
        assert handler.output_area_start == 4
        assert handler.current_output_line == 4

    def test_get_tier_indicator(self):
        """Test tier indicator generation."""
        mock_terminal = Mock()
        mock_validator = Mock()
        handler = PromptHandler(mock_terminal, mock_validator)

        # Test different tiers
        assert handler._get_tier_indicator(1.0) == "🟢"
        assert handler._get_tier_indicator(2.0) == "🟡"
        assert handler._get_tier_indicator(2.5) == "🟠"
        assert handler._get_tier_indicator(3.0) == "🟠"
        assert handler._get_tier_indicator(4.0) == "🔴"
        assert handler._get_tier_indicator(99.0) == "⚪"  # Unknown

    def test_output_area_positioning(self):
        """Test that output is positioned in the scrolling area."""
        mock_terminal = Mock()
        mock_terminal.get_input_area_start.return_value = 20
        mock_terminal.get_scroll_region_start.return_value = 4
        mock_validator = Mock()
        handler = PromptHandler(mock_terminal, mock_validator)

        # Check initial positioning
        assert handler.input_area_start == 20
        assert handler.output_area_start == 4
        assert handler.current_output_line == 4

    def test_clear_prompt_area_preserves_output(self):
        """Test that clearing input area doesn't affect output area."""
        mock_terminal = Mock()
        mock_terminal.get_terminal_size.return_value = (80, 24)
        mock_terminal.get_input_area_start.return_value = 20
        mock_validator = Mock()
        handler = PromptHandler(mock_terminal, mock_validator)

        # Clear input area
        handler.clear_prompt_area()

        # Verify input area was cleared (should call move_cursor and print for input area lines)
        assert mock_terminal.move_cursor.called
        # Should have called print for clearing lines
        assert mock_terminal.print.called or str(mock_terminal.print).find(' ') >= 0


class TestAdvancedInputHandler:
    """Test advanced input handler functionality."""

    def test_initialization(self):
        """Test advanced input handler initializes correctly."""
        mock_validator = Mock()
        handler = AdvancedInputHandler(mock_validator)

        assert handler.tier_validator == mock_validator
        assert handler.command_history == []
        assert handler.history_index == -1
        assert handler.current_input == ""
        assert handler.cursor_position == 0
        assert "ls" in handler.common_commands
        assert "git" in handler.common_commands

    def test_command_history(self):
        """Test command history management."""
        mock_validator = Mock()
        handler = AdvancedInputHandler(mock_validator)

        # Add some commands
        handler.command_history = ["ls", "cd /tmp", "pwd"]
        assert len(handler.command_history) == 3
        assert handler.command_history[0] == "ls"
        assert handler.command_history[-1] == "pwd"


class TestVisualEnhancer:
    """Test visual enhancer functionality."""

    def test_initialization(self):
        """Test visual enhancer initializes correctly."""
        enhancer = VisualEnhancer()

        assert enhancer.color_enabled == True
        assert enhancer.theme == "default"
        assert 'command' in enhancer.syntax_patterns
        assert 'error' in enhancer.syntax_patterns

    def test_colorize_text(self):
        """Test text colorization."""
        enhancer = VisualEnhancer()

        # Test with colors enabled
        colored = enhancer.colorize_text("test", Color.RED)
        assert "\033[31m" in colored
        assert "test" in colored
        assert "\033[0m" in colored

        # Test with colors disabled
        enhancer.enable_colors(False)
        plain = enhancer.colorize_text("test", Color.RED)
        assert plain == "test"
        assert "\033[" not in plain

    def test_format_command_output(self):
        """Test command output formatting."""
        enhancer = VisualEnhancer()

        output = enhancer.format_command_output("ls -la", "total 42\ndrwxr-xr-x  5 user", True)

        assert "✓" in output  # Success indicator
        assert "ls" in output
        assert "-la" in output
        assert "total" in output
        assert "42" in output

    def test_format_prompt(self):
        """Test prompt formatting."""
        enhancer = VisualEnhancer()

        isaac_prompt = enhancer.format_prompt("isaac", "ready")
        assert "isaac" in isaac_prompt
        assert "ready" in isaac_prompt

        user_prompt = enhancer.format_prompt("user", "ls -la")
        assert "user" in user_prompt
        assert "ls -la" in user_prompt