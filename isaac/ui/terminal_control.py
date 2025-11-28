"""
Terminal Control - Advanced terminal interface management for Isaac

Provides comprehensive terminal control including:
- ANSI escape sequence handling
- Terminal size detection and monitoring
- Cursor positioning and movement
- Color and style management
- Scroll region management
- Screen clearing and restoration
"""

import os
import re
import shutil
import sys
from typing import Optional, Tuple


class TerminalControl:
    """
    Advanced terminal control with ANSI escape sequences and size management.
    """

    # ANSI Escape Sequences
    ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[mGKHJ]')

    # Cursor Control
    CURSOR_HOME = '\x1b[H'
    CURSOR_SAVE = '\x1b[s'
    CURSOR_RESTORE = '\x1b[u'
    CURSOR_HIDE = '\x1b[?25l'
    CURSOR_SHOW = '\x1b[?25h'

    # Screen Control
    CLEAR_SCREEN = '\x1b[2J'
    CLEAR_LINE = '\x1b[2K'
    CLEAR_TO_END = '\x1b[0J'
    CLEAR_TO_START = '\x1b[1J'

    # Color Codes
    COLORS = {
        'black': 30,
        'red': 31,
        'green': 32,
        'yellow': 33,
        'blue': 34,
        'magenta': 35,
        'cyan': 36,
        'white': 37,
        'bright_black': 90,
        'bright_red': 91,
        'bright_green': 92,
        'bright_yellow': 93,
        'bright_blue': 94,
        'bright_magenta': 95,
        'bright_cyan': 96,
        'bright_white': 97,
    }

    BACKGROUNDS = {
        'black': 40,
        'red': 41,
        'green': 42,
        'yellow': 43,
        'blue': 44,
        'magenta': 45,
        'cyan': 46,
        'white': 47,
        'bright_black': 100,
        'bright_red': 101,
        'bright_green': 102,
        'bright_yellow': 103,
        'bright_blue': 104,
        'bright_magenta': 105,
        'bright_cyan': 106,
        'bright_white': 107,
    }

    STYLES = {
        'reset': 0,
        'bold': 1,
        'dim': 2,
        'italic': 3,
        'underline': 4,
        'blink': 5,
        'reverse': 7,
        'strikethrough': 9,
    }

    def __init__(self):
        """Initialize terminal control with current size detection."""
        self.width, self.height = self.get_terminal_size()
        self.status_lines = 5  # Header area height
        self.scroll_region_start = self.status_lines + 1
        self.scroll_region_end = self.height
        self.original_terminal_state = None

    def get_terminal_size(self) -> Tuple[int, int]:
        """
        Get current terminal size (width, height).

        Returns:
            Tuple of (width, height) in characters
        """
        try:
            size = shutil.get_terminal_size()
            return size.columns, size.lines
        except (OSError, AttributeError):
            # Fallback for systems without terminal size detection
            return 80, 24

    def setup_terminal(self):
        """
        Set up terminal for Isaac interface.
        Configures scroll region and saves original state.
        """
        # Save current terminal state
        self.original_terminal_state = self._get_terminal_state()

        # Set up scroll region (leave header area fixed)
        self.set_scroll_region(self.scroll_region_start, self.scroll_region_end)

        # Move cursor to input position
        self.move_cursor(1, self.scroll_region_start)

    def restore_terminal(self):
        """
        Restore terminal to original state.
        """
        if self.original_terminal_state:
            # Reset scroll region to full screen
            self.set_scroll_region(1, self.height)
            # Restore cursor
            self.show_cursor()
            # Clear any remaining escape sequences
            print('\x1b[0m', end='', flush=True)

    def set_scroll_region(self, top: int, bottom: int):
        """
        Set the scrollable region of the terminal.

        Args:
            top: Top line of scroll region (1-based)
            bottom: Bottom line of scroll region (1-based)
        """
        print(f'\x1b[{top};{bottom}r', end='', flush=True)

    def move_cursor(self, x: int, y: int):
        """
        Move cursor to absolute position.

        Args:
            x: Column position (1-based)
            y: Row position (1-based)
        """
        print(f'\x1b[{y};{x}H', end='', flush=True)

    def move_cursor_relative(self, x: int, y: int):
        """
        Move cursor relative to current position.

        Args:
            x: Columns to move (positive = right, negative = left)
            y: Rows to move (positive = down, negative = up)
        """
        if x > 0:
            print(f'\x1b[{x}C', end='', flush=True)
        elif x < 0:
            print(f'\x1b[{-x}D', end='', flush=True)

        if y > 0:
            print(f'\x1b[{y}B', end='', flush=True)
        elif y < 0:
            print(f'\x1b[{-y}A', end='', flush=True)

    def hide_cursor(self):
        """Hide the cursor."""
        print(self.CURSOR_HIDE, end='', flush=True)

    def show_cursor(self):
        """Show the cursor."""
        print(self.CURSOR_SHOW, end='', flush=True)

    def clear_screen(self):
        """Clear the entire screen."""
        print(self.CLEAR_SCREEN, end='', flush=True)

    def clear_line(self):
        """Clear the current line."""
        print(self.CLEAR_LINE, end='', flush=True)

    def clear_to_end_of_screen(self):
        """Clear from cursor to end of screen."""
        print(self.CLEAR_TO_END, end='', flush=True)

    def clear_main_area(self):
        """
        Clear the main scrollable area (below header).
        Moves cursor to start of scrollable region.
        """
        # Save cursor position
        print(self.CURSOR_SAVE, end='', flush=True)

        # Clear each line in the scrollable region
        for line in range(self.scroll_region_start, self.scroll_region_end + 1):
            self.move_cursor(1, line)
            print(self.CLEAR_LINE, end='', flush=True)

        # Restore cursor to input position
        self.move_cursor(1, self.scroll_region_start)
        print(self.CURSOR_RESTORE, end='', flush=True)

    def print_normal_output(self, text: str):
        """
        Print normal output text with proper formatting.

        Args:
            text: Text to print
        """
        # Ensure we're in the scrollable region
        print(text)

    def set_color(self, foreground: Optional[str] = None, background: Optional[str] = None,
                  style: Optional[str] = None):
        """
        Set text color and style.

        Args:
            foreground: Foreground color name
            background: Background color name
            style: Text style name
        """
        codes = []

        if style and style in self.STYLES:
            codes.append(self.STYLES[style])

        if foreground and foreground in self.COLORS:
            codes.append(self.COLORS[foreground])

        if background and background in self.BACKGROUNDS:
            codes.append(self.BACKGROUNDS[background])

        if codes:
            print(f'\x1b[{";".join(map(str, codes))}m', end='', flush=True)

    def reset_colors(self):
        """Reset all color and style formatting."""
        print('\x1b[0m', end='', flush=True)

    def strip_ansi(self, text: str) -> str:
        """
        Strip ANSI escape sequences from text.

        Args:
            text: Text with potential ANSI codes

        Returns:
            Text with ANSI codes removed
        """
        return self.ANSI_ESCAPE.sub('', text)

    def get_text_width(self, text: str) -> int:
        """
        Get the display width of text (excluding ANSI codes).

        Args:
            text: Text that may contain ANSI codes

        Returns:
            Display width in characters
        """
        return len(self.strip_ansi(text))

    def wrap_text(self, text: str, width: int) -> list:
        """
        Wrap text to specified width, respecting ANSI codes.

        Args:
            text: Text to wrap
            width: Maximum width per line

        Returns:
            List of wrapped lines
        """
        if not text or width <= 0:
            return ['']

        lines = []
        current_line = ''
        current_width = 0

        words = text.split()
        for word in words:
            word_width = self.get_text_width(word)

            # If word is too long for a line, force break it
            if word_width > width:
                if current_line:
                    lines.append(current_line)
                    current_line = ''
                    current_width = 0
                # Break long word
                for i in range(0, len(word), width):
                    lines.append(word[i:i+width])
                continue

            # Check if adding word would exceed line width
            if current_line and current_width + 1 + word_width > width:
                lines.append(current_line)
                current_line = word
                current_width = word_width
            elif current_line:
                current_line += ' ' + word
                current_width += 1 + word_width
            else:
                current_line = word
                current_width = word_width

        if current_line:
            lines.append(current_line)

        return lines if lines else ['']

    def _get_terminal_state(self) -> Optional[str]:
        """
        Get current terminal state (for restoration).
        This is a placeholder - full implementation would save/restore terminal state.
        """
        return None

    @property
    def terminal_height(self) -> int:
        """Get current terminal height."""
        return self.height

    @property
    def terminal_width(self) -> int:
        """Get current terminal width."""
        return self.width