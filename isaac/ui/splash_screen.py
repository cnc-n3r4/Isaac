"""
Splash Screen - Isaac's startup display
Shows War Games reference, ASCII art, and loading sequence
"""

import time
import os
from isaac.ui.terminal_control import TerminalControl


class SplashScreen:
    """Display Isaac's splash screen on startup."""

    def __init__(self, terminal: TerminalControl):
        """Initialize splash screen."""
        self.terminal = terminal

    def show(self, duration: float = 5.5) -> None:
        """Display the full splash screen sequence.

        Args:
            duration: Total duration in seconds (default 5.5s)
        """
        start_time = time.time()

        # Phase 1: War Games reference (2 seconds)
        self._show_war_games_reference()
        time.sleep(2.0)

        # Phase 2: ASCII Logo (3 seconds)
        self._show_ascii_logo()
        time.sleep(3.0)

        # Phase 3: Loading messages (0.5 seconds)
        self._show_loading_messages()

        # Wait for total duration
        elapsed = time.time() - start_time
        if elapsed < duration:
            time.sleep(duration - elapsed)

    def _show_war_games_reference(self):
        """Show War Games movie reference."""
        self.terminal.clear_screen()
        self.terminal.move_cursor(0, 0)

        # Center the text
        width, height = self.terminal.get_terminal_size()
        center_y = height // 2 - 2

        lines = [
            "",
            "Shall we play a game?",
            "",
            "... nah!!",
            ""
        ]

        for i, line in enumerate(lines):
            x = (width - len(line)) // 2
            y = center_y + i
            self.terminal.print_at(max(0, x), y, line)

    def _show_ascii_logo(self):
        """Show Isaac ASCII art logo."""
        self.terminal.clear_screen()
        self.terminal.move_cursor(0, 0)

        width, height = self.terminal.get_terminal_size()
        center_y = height // 2 - 4

        logo_lines = [
            "   _____ _____         _____",
            "  |_   _/  ___|  /\\   /  __ \\",
            "    | | \\ `--.  /  \\  | /  \\/",
            "    | |  `--. \\/  /\\ \\ | |",
            "   _| |_ /\\__/ /  __  \\ \\__ /\\",
            "   \\___/ \\____/_/    \\_\\____/",
            "",
            "   Intelligent System Agent And Control"
        ]

        for i, line in enumerate(logo_lines):
            x = (width - len(line)) // 2
            y = center_y + i
            self.terminal.print_at(max(0, x), y, line)

    def _show_loading_messages(self):
        """Show loading messages."""
        width, height = self.terminal.get_terminal_size()
        y = height - 3

        messages = [
            "Loading session data...",
            "Connecting to cloud storage...",
            "Initializing AI layer..."
        ]

        for message in messages:
            x = (width - len(message)) // 2
            self.terminal.print_at(max(0, x), y, message)
            time.sleep(0.1)  # Brief pause between messages