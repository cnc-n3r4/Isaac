"""
Advanced Input Handler - Enhanced input processing for Isaac
Provides tab completion, history navigation, and keyboard shortcuts
"""

import sys
import os
from typing import List, Optional, Tuple
from isaac.core.tier_validator import TierValidator


class AdvancedInputHandler:
    """Handle advanced input features like tab completion and history."""

    def __init__(self, tier_validator: TierValidator):
        """Initialize advanced input handler."""
        self.tier_validator = tier_validator
        self.command_history: List[str] = []
        self.history_index = -1
        self.current_input = ""
        self.cursor_position = 0

        # Common commands for tab completion
        self.common_commands = [
            "ls", "cd", "pwd", "echo", "cat", "grep", "find", "head", "tail",
            "cp", "mv", "mkdir", "rmdir", "touch", "chmod", "chown", "ps",
            "git", "npm", "pip", "python", "node", "docker", "kubectl"
        ]

    def get_input_with_advanced_features(self, prompt: str = "isaac> ") -> Tuple[str, str]:
        """Get input with advanced features enabled.

        Returns:
            Tuple of (command, display_text) where display_text includes
            any special formatting or suggestions
        """
        print(prompt, end="", flush=True)
        self.current_input = ""
        self.cursor_position = 0
        self.history_index = -1

        while True:
            try:
                # Read single character
                char = self._get_char()

                if char == '\t':  # Tab completion
                    self._handle_tab_completion()
                elif char == '\x1b[A':  # Up arrow - history previous
                    self._navigate_history(-1)
                elif char == '\x1b[B':  # Down arrow - history next
                    self._navigate_history(1)
                elif char == '\x1b[C':  # Right arrow
                    self._move_cursor_right()
                elif char == '\x1b[D':  # Left arrow
                    self._move_cursor_left()
                elif char == '\x7f' or char == '\b':  # Backspace
                    self._handle_backspace()
                elif char == '\r' or char == '\n':  # Enter
                    print()  # New line
                    command = self.current_input.strip()
                    if command and command not in self.command_history[-5:]:  # Avoid duplicates
                        self.command_history.append(command)
                    return command, self.current_input
                elif len(char) == 1 and ord(char) >= 32:  # Printable character
                    self._insert_character(char)
                # Ignore other control characters

            except KeyboardInterrupt:
                print("^C")
                return "", ""

    def _get_char(self) -> str:
        """Get a single character from stdin."""
        if os.name == 'nt':  # Windows
            import msvcrt
            return msvcrt.getch().decode('utf-8', errors='ignore')
        else:  # Unix-like
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                if ch == '\x1b':  # Escape sequence
                    ch += sys.stdin.read(2)
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _handle_tab_completion(self):
        """Handle tab completion."""
        if not self.current_input.strip():
            return

        # Get current word being typed
        words = self.current_input[:self.cursor_position].split()
        if not words:
            return

        current_word = words[-1]
        if not current_word:
            return

        # Find completions
        completions = [cmd for cmd in self.common_commands if cmd.startswith(current_word)]
        if not completions:
            return

        if len(completions) == 1:
            # Single completion - complete it
            completion = completions[0]
            prefix = self.current_input[:self.cursor_position - len(current_word)]
            self.current_input = prefix + completion + self.current_input[self.cursor_position:]
            self.cursor_position = len(prefix) + len(completion)
            self._redraw_input()
        else:
            # Multiple completions - show options
            print()  # New line
            print("  ".join(completions[:10]))  # Show first 10
            if len(completions) > 10:
                print(f"... and {len(completions) - 10} more")
            print(f"isaac> {self.current_input}", end="", flush=True)

    def _navigate_history(self, direction: int):
        """Navigate command history."""
        if not self.command_history:
            return

        if self.history_index == -1 and direction == -1:
            # Save current input before navigating
            self.temp_input = self.current_input
            self.history_index = len(self.command_history) - 1
        elif self.history_index >= 0:
            self.history_index += direction
            if self.history_index < 0:
                # Back to current input
                self.history_index = -1
                self.current_input = self.temp_input
            elif self.history_index >= len(self.command_history):
                self.history_index = len(self.command_history) - 1
            else:
                self.current_input = self.command_history[self.history_index]

        self.cursor_position = len(self.current_input)
        self._redraw_input()

    def _move_cursor_right(self):
        """Move cursor right."""
        if self.cursor_position < len(self.current_input):
            self.cursor_position += 1
            self._redraw_input()

    def _move_cursor_left(self):
        """Move cursor left."""
        if self.cursor_position > 0:
            self.cursor_position -= 1
            self._redraw_input()

    def _handle_backspace(self):
        """Handle backspace key."""
        if self.cursor_position > 0:
            self.current_input = (self.current_input[:self.cursor_position - 1] +
                                self.current_input[self.cursor_position:])
            self.cursor_position -= 1
            self._redraw_input()

    def _insert_character(self, char: str):
        """Insert character at cursor position."""
        self.current_input = (self.current_input[:self.cursor_position] + char +
                            self.current_input[self.cursor_position:])
        self.cursor_position += 1
        self._redraw_input()

    def _redraw_input(self):
        """Redraw the current input line."""
        # Clear current line
        print(f"\r{' ' * (len('isaac> ') + len(self.current_input) + 10)}\r", end="", flush=True)

        # Redraw prompt and input
        print(f"isaac> {self.current_input}", end="", flush=True)

        # Position cursor
        if self.cursor_position < len(self.current_input):
            # Move cursor back to correct position
            print(f"\x1b[{len(self.current_input) - self.cursor_position}D", end="", flush=True)