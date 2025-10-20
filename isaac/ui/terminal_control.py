"""
Terminal Control - Traditional terminal interface for Isaac
Provides a clean, traditional terminal experience with status bar
"""

import os
import sys
import time
import datetime
from typing import Optional, Tuple
from pathlib import Path


class TerminalControl:
    """Controls terminal display in traditional style."""

    def __init__(self):
        """Initialize terminal control."""
        self.terminal_width = 80
        self.terminal_height = 24
        self.status_lines = 3  # Top 3 lines for status
        self.working_directory = Path.cwd()
        self.current_tier = "1 (Safe)"
        self.connection_status = "Online"
        self.session_id = self._generate_session_id()
        self.is_windows = os.name == 'nt'

    def _generate_session_id(self) -> str:
        """Generate a unique session identifier."""
        return f"Session-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def setup_terminal(self):
        """Set up the terminal for traditional Isaac experience."""
        self._update_terminal_size()
        self._clear_screen()
        self._setup_scroll_region()
        self._draw_status_bar()
        self._position_cursor_for_input()

    def _update_terminal_size(self):
        """Get current terminal dimensions."""
        try:
            if self.is_windows:
                import shutil
                size = shutil.get_terminal_size()
                self.terminal_width = size.columns
                self.terminal_height = size.lines
            else:
                import shutil
                size = shutil.get_terminal_size()
                self.terminal_width = size.columns
                self.terminal_height = size.lines
        except:
            # Default fallback
            self.terminal_width = 80
            self.terminal_height = 24

    def _clear_screen(self):
        """Clear the entire screen."""
        if self.is_windows:
            os.system('cls')
        else:
            print("\033[2J\033[H", end="", flush=True)

    def _setup_scroll_region(self):
        """Set up scroll region for the main terminal area."""
        # Set scroll region from line 4 (after status bar) to bottom of terminal
        scroll_start = self.status_lines + 1  # Line 4
        scroll_end = self.terminal_height     # Bottom of terminal
        if scroll_end > scroll_start:
            print(f"\033[{scroll_start};{scroll_end}r", end="", flush=True)

    def _position_cursor_for_input(self):
        """Position cursor at the start of the scroll region for input."""
        scroll_start = self.status_lines + 1  # Line 4
        if not self.is_windows:
            # Move cursor to start of scroll region (line 4)
            print(f"\033[{scroll_start};1H", end="", flush=True)
        else:
            # For Windows, position at start of scroll region
            print(f"\033[{scroll_start};1H", end="", flush=True)

    def _draw_status_bar(self):
        """Draw the 3-line status bar at the top."""
        # Move cursor to top
        if not self.is_windows:
            print("\033[H", end="", flush=True)
        else:
            print("\033[1;1H", end="", flush=True)

        # Line 1: Session info
        session_line = f"Isaac Session: {self.session_id}"
        self._print_status_line(session_line, 0)

        # Line 2: Current tier and status
        tier_line = f"Tier: {self.current_tier} | Status: Active"
        self._print_status_line(tier_line, 1)

        # Line 3: Connection and shell info
        shell_info = f"Shell: {self._get_shell_type()} | Online: {self.connection_status}"
        self._print_status_line(shell_info, 2)

        # Position cursor below status bar
        if not self.is_windows:
            print(f"\033[{self.status_lines + 1};1H", end="", flush=True)
        else:
            print(f"\033[{self.status_lines + 1};1H", end="", flush=True)

    def _print_status_line(self, text: str, line_num: int):
        """Print a status line with background color."""
        if not self.is_windows:
            # Blue background, white text for status lines
            padded_text = text.ljust(self.terminal_width)
            print(f"\033[{line_num + 1};1H\033[1;37;44m{padded_text}\033[0m", end="", flush=True)
        else:
            # Windows - simpler approach
            padded_text = text.ljust(self.terminal_width)
            print(f"\033[{line_num + 1};1H{padded_text}", flush=True)

    def _get_shell_type(self) -> str:
        """Get current shell type."""
        if self.is_windows:
            return "PowerShell"
        else:
            return "Bash"

    def update_status(self, tier: Optional[str] = None, status: Optional[str] = None,
                     connection: Optional[str] = None):
        """Update status bar information."""
        if tier:
            self.current_tier = tier
        if connection:
            self.connection_status = connection
        self._draw_status_bar()

    def get_main_area_start(self) -> int:
        """Get the line number where main terminal area starts."""
        return self.status_lines + 1

    def clear_main_area(self):
        """Clear everything below the status bar."""
        scroll_start = self.status_lines + 1  # Line 4

        if not self.is_windows:
            # Clear from status bar down to end of scroll region
            for line in range(scroll_start, self.terminal_height + 1):
                print(f"\033[{line};1H\033[K", end="", flush=True)

            # Position cursor at start of cleared area (line 4)
            print(f"\033[{scroll_start};1H", end="", flush=True)
        else:
            # Windows - clear entire screen and redraw status bar
            os.system('cls')
            self._draw_status_bar()
            # Position cursor at start of scroll region (line 4)
            print(f"\033[{scroll_start};1H", end="", flush=True)

    def print_normal_output(self, text: str):
        """Print text as normal terminal output (no special formatting)."""
        print(text, flush=True)

    def print_isaac_response(self, response: str):
        """Print Isaac response as if it's normal terminal output."""
        print(response, flush=True)

    def get_prompt_string(self) -> str:
        """Get the current prompt string for the terminal."""
        if self.is_windows:
            # PowerShell style prompt
            return f"PS {self.working_directory}> "
        else:
            # Bash style prompt
            try:
                import platform
                username = os.environ.get('USER', 'user')
                hostname = platform.node()
                return f"{username}@{hostname}:{self.working_directory}$ "
            except:
                return f"bash:{self.working_directory}$ "

    def update_working_directory(self, new_path: str):
        """Update the current working directory display."""
        self.working_directory = Path(new_path)

    def get_terminal_size(self) -> Tuple[int, int]:
        """Get current terminal size."""
        return (self.terminal_width, self.terminal_height)

    def restore_terminal(self):
        """Restore terminal to normal state."""
        if not self.is_windows:
            # Clear status lines
            for line in range(1, self.status_lines + 1):
                print(f"\033[{line};1H\033[K", end="", flush=True)
            # Reset scroll region
            print("\033[r", end="", flush=True)
            # Show cursor
            print("\033[?25h", end="", flush=True)