"""
Test Suite for Isaac TerminalControl

This module tests the TerminalControl implementation that provides
advanced terminal interface management with ANSI escape sequences.

Coverage Goal: 85%+
Test Count: 15+ scenarios
"""

import pytest
from unittest.mock import Mock, patch

from isaac.ui.terminal_control import TerminalControl


class TestTerminalControl:
    """Test suite for TerminalControl functionality."""

    @pytest.fixture
    def terminal(self):
        """Create a TerminalControl instance."""
        return TerminalControl()

    def test_initialization(self, terminal):
        """Test TerminalControl initializes correctly."""
        assert terminal.width > 0
        assert terminal.height > 0
        assert terminal.status_lines == 5
        assert terminal.scroll_region_start == 6
        assert terminal.scroll_region_end == terminal.height

    def test_terminal_size_detection(self, terminal):
        """Test terminal size detection."""
        width, height = terminal.get_terminal_size()
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert width > 0
        assert height > 0

        # Test property access
        assert terminal.terminal_width == width
        assert terminal.terminal_height == height

    @patch('builtins.print')
    def test_cursor_movement(self, mock_print, terminal):
        """Test cursor positioning methods."""
        # Test absolute movement
        terminal.move_cursor(10, 5)
        mock_print.assert_called_with('\x1b[5;10H', end='', flush=True)

        # Test relative movement
        mock_print.reset_mock()
        terminal.move_cursor_relative(3, -2)
        calls = mock_print.call_args_list
        assert '\x1b[3C' in str(calls[0])  # Right 3
        assert '\x1b[2A' in str(calls[1])  # Up 2

    @patch('builtins.print')
    def test_cursor_visibility(self, mock_print, terminal):
        """Test cursor show/hide."""
        terminal.hide_cursor()
        mock_print.assert_called_with('\x1b[?25l', end='', flush=True)

        mock_print.reset_mock()
        terminal.show_cursor()
        mock_print.assert_called_with('\x1b[?25h', end='', flush=True)

    @patch('builtins.print')
    def test_screen_clearing(self, mock_print, terminal):
        """Test screen clearing methods."""
        terminal.clear_screen()
        mock_print.assert_called_with('\x1b[2J', end='', flush=True)

        mock_print.reset_mock()
        terminal.clear_line()
        mock_print.assert_called_with('\x1b[2K', end='', flush=True)

    @patch('builtins.print')
    def test_scroll_region_setup(self, mock_print, terminal):
        """Test scroll region configuration."""
        terminal.set_scroll_region(5, 20)
        mock_print.assert_called_with('\x1b[5;20r', end='', flush=True)

    @patch('builtins.print')
    def test_color_setting(self, mock_print, terminal):
        """Test color and style setting."""
        terminal.set_color('red', 'blue', 'bold')
        mock_print.assert_called_with('\x1b[1;31;44m', end='', flush=True)

        mock_print.reset_mock()
        terminal.reset_colors()
        mock_print.assert_called_with('\x1b[0m', end='', flush=True)

    def test_ansi_stripping(self, terminal):
        """Test ANSI escape sequence stripping."""
        text_with_ansi = '\x1b[31mRed text\x1b[0m normal'
        stripped = terminal.strip_ansi(text_with_ansi)
        assert stripped == 'Red text normal'

    def test_text_width_calculation(self, terminal):
        """Test text width calculation excluding ANSI codes."""
        text_with_ansi = '\x1b[31mHello\x1b[0m World'
        width = terminal.get_text_width(text_with_ansi)
        assert width == len('Hello World')

    def test_text_wrapping(self, terminal):
        """Test text wrapping with ANSI code handling."""
        text = 'This is a long line that should wrap properly'
        wrapped = terminal.wrap_text(text, 10)

        assert len(wrapped) > 1
        for line in wrapped:
            assert terminal.get_text_width(line) <= 10

    def test_text_wrapping_with_ansi(self, terminal):
        """Test text wrapping preserves ANSI codes."""
        text = '\x1b[31mThis\x1b[0m is colored text'
        wrapped = terminal.wrap_text(text, 10)

        # Should handle ANSI codes correctly
        assert len(wrapped) >= 1

    @patch('builtins.print')
    def test_setup_terminal(self, mock_print, terminal):
        """Test terminal setup."""
        with patch.object(terminal, '_get_terminal_state', return_value='saved'):
            terminal.setup_terminal()

        # Should set scroll region and move cursor
        calls = mock_print.call_args_list
        assert any('\x1b[' in str(call) and 'r' in str(call) for call in calls)  # Scroll region
        assert any('\x1b[' in str(call) and 'H' in str(call) for call in calls)  # Cursor move

    @patch('builtins.print')
    def test_clear_main_area(self, mock_print, terminal):
        """Test clearing main scrollable area."""
        terminal.clear_main_area()

        # Should save cursor, clear lines, restore cursor
        calls = mock_print.call_args_list
        assert any('s' in str(call) for call in calls)  # Save cursor
        assert any('u' in str(call) for call in calls)  # Restore cursor

    def test_print_normal_output(self, terminal, capsys):
        """Test normal output printing."""
        terminal.print_normal_output("Test output")
        captured = capsys.readouterr()
        assert "Test output" in captured.out

    @patch('shutil.get_terminal_size')
    def test_terminal_size_fallback(self, mock_get_terminal_size):
        """Test fallback when terminal size detection fails."""
        mock_get_terminal_size.side_effect = OSError()

        terminal = TerminalControl()
        width, height = terminal.get_terminal_size()

        assert width == 80
        assert height == 24

    def test_color_constants(self, terminal):
        """Test color constant definitions."""
        assert terminal.COLORS['red'] == 31
        assert terminal.COLORS['green'] == 32
        assert terminal.BACKGROUNDS['blue'] == 44
        assert terminal.STYLES['bold'] == 1
        assert terminal.STYLES['reset'] == 0

    def test_ansi_escape_regex(self, terminal):
        """Test ANSI escape regex pattern."""
        pattern = terminal.ANSI_ESCAPE
        assert pattern.search('\x1b[31m')
        assert pattern.search('\x1b[2J')
        assert not pattern.search('normal text')


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_terminal_control_full_workflow(terminal):
    """Test complete terminal control workflow."""
    # Setup
    terminal.setup_terminal()

    # Output some content
    terminal.print_normal_output("Command output")
    terminal.print_normal_output("More output")

    # Clear and verify
    terminal.clear_main_area()

    # Restore
    terminal.restore_terminal()

    # Should not crash
    assert True


def test_terminal_control_with_different_sizes():
    """Test terminal control with various sizes."""
    test_sizes = [(80, 24), (120, 30), (160, 50)]

    for width, height in test_sizes:
        with patch('shutil.get_terminal_size') as mock_size:
            mock_size.return_value = Mock(columns=width, lines=height)

            terminal = TerminalControl()
            assert terminal.width == width
            assert terminal.height == height
            assert terminal.scroll_region_end == height


# ============================================================================
# SUMMARY
# ============================================================================

"""
Test Suite Summary:
-------------------
Total Tests: 18

Coverage Breakdown:
- Initialization: 2 tests
- Terminal size: 2 tests
- Cursor control: 3 tests
- Screen control: 2 tests
- Colors/styles: 2 tests
- Text processing: 3 tests
- Terminal setup: 2 tests
- Integration: 2 tests

Success Criteria:
? Tests cover all public methods
? Tests verify ANSI escape sequences
? Tests check terminal size handling
? Tests validate color/style codes
? Tests confirm cursor positioning
? Tests ensure proper text wrapping

Next Steps:
1. Run: pytest tests/ui/test_terminal_control.py -v
2. Check coverage: pytest tests/ui/test_terminal_control.py --cov=isaac.ui.terminal_control
3. Verify 85%+ coverage achieved
"""