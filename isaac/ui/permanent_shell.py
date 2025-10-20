"""
Permanent Shell - Isaac's traditional terminal interface
Implements a traditional terminal experience with status bar
"""

import sys
import signal
import platform
import os
from typing import Optional
from pathlib import Path
from isaac.ui.terminal_control import TerminalControl
from isaac.core.tier_validator import TierValidator
from isaac.core.session_manager import SessionManager
from isaac.adapters.shell_detector import detect_shell
from isaac.models.preferences import Preferences


class PermanentShell:
    """Isaac's traditional terminal interface."""

    def __init__(self):
        """Initialize the permanent shell."""
        # Core components
        self.terminal = TerminalControl()
        self.preferences = Preferences(machine_id=platform.node())
        self.tier_validator = TierValidator(self.preferences)
        self.session_manager = SessionManager(self.preferences.to_dict())

        # Shell detection
        self.shell_adapter = None

        # State
        self.running = False
        self.current_directory = Path.cwd()

        # Output buffering for Windows scrolling simulation
        self.output_buffer = []
        self.max_buffer_lines = 100

    def start(self) -> None:
        """Start the traditional terminal session."""
        try:
            # Setup signal handlers for graceful exit
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            # Setup terminal
            self.terminal.setup_terminal()

            # Detect and setup shell
            self._setup_shell()

            # Start main loop
            self.running = True
            self._main_loop()

        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def _setup_shell(self) -> None:
        """Detect and setup the appropriate shell adapter."""
        self.shell_adapter = detect_shell()

    def _main_loop(self) -> None:
        """Main interactive loop - traditional terminal style."""
        while self.running:
            try:
                # Show prompt and get command
                command = self._get_user_input()

                # Handle exit commands
                if command.lower() in ["exit", "quit", "q"]:
                    break

                # Process the command
                self._process_command(command)

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self._print_output_line(error_msg)

    def _get_user_input(self) -> str:
        """Get user input with traditional prompt."""
        prompt = self.terminal.get_prompt_string()
        # Ensure cursor is at the start of the scroll region (line 4)
        scroll_start = self.terminal.status_lines + 1  # Line 4
        if not self.terminal.is_windows:
            print(f"\033[{scroll_start};1H", end="", flush=True)
        try:
            return input(prompt).strip()
        except EOFError:
            return "exit"

    def _process_command(self, command: str) -> None:
        """Process a command in traditional terminal style."""
        if not command:
            return

        # Validate command tier
        tier = self.tier_validator.get_tier(command)

        # Update status bar with current tier
        tier_display = self._format_tier_display(tier)
        self.terminal.update_status(tier=tier_display)

        # Process the command
        self._execute_command_logic(command)

    def _execute_command_logic(self, command: str) -> None:
        """Execute the command logic."""
        # Validate command tier
        tier = self.tier_validator.get_tier(command)

        # Handle different command types
        if self._is_ai_query(command):
            self._handle_ai_query(command)
        elif tier >= 3.0:
            self._handle_tier3_command(command, tier)
        else:
            self._execute_normal_command(command)

    def _is_ai_query(self, command: str) -> bool:
        """Check if command is an AI query."""
        ai_prefixes = ["isaac", "ai", "tell me", "what is", "how do", "why does"]
        return any(command.lower().startswith(prefix) for prefix in ai_prefixes)

    def _handle_ai_query(self, command: str) -> None:
        """Handle AI query in traditional style."""
        # For now, just show a placeholder response
        # This would integrate with the AI system
        self._print_output_line(f"isaac> I understand you're asking about: {command}")

        # Simulate AI processing
        if "who won the baseball game" in command.lower():
            self._print_output_line("isaac> The Chicago Cubs won the World Series in 2016.")
        elif "whois" in command.lower():
            # Simulate whois command
            self._print_output_line("isaac> Executing whois lookup...")
            # In real implementation, this would run actual whois
            self._execute_normal_command("whois babe-ruth.com")
        else:
            self._print_output_line("isaac> I'm processing your AI query...")

    def _handle_tier3_command(self, command: str, tier: float) -> None:
        """Handle Tier 3+ commands with confirmation."""
        self._print_output_line(f"isaac> Tier {tier} command requires confirmation. Proceed? (y/n)")

        try:
            response = input().strip().lower()
            if response in ['y', 'yes']:
                self._execute_normal_command(command)
            else:
                self._print_output_line("isaac> Command cancelled.")
        except EOFError:
            self._print_output_line("isaac> Command cancelled.")

    def _execute_normal_command(self, command: str) -> None:
        """Execute a normal shell command."""
        if not self.shell_adapter:
            self._print_output_line("isaac> No shell adapter available")
            return

        # Handle special commands that interfere with our UI
        if self._handle_special_command(command):
            return

        try:
            # Show command being executed (like normal terminal)
            self._print_output_line(f"{self.terminal.get_prompt_string()}{command}")

            result = self.shell_adapter.execute(command)

            # Show output as normal terminal output
            if result.output.strip():
                for line in result.output.splitlines():
                    self._print_output_line(line)

            # Update working directory if cd command
            if command.startswith("cd "):
                new_path = command[3:].strip()
                if new_path:
                    try:
                        os.chdir(new_path)
                        self.current_directory = Path.cwd()
                        self.terminal.update_working_directory(str(self.current_directory))
                    except:
                        pass  # Keep current directory on error

            # Save to session if successful
            if result.success:
                self.session_manager.log_command(command, result.exit_code)

        except Exception as e:
            self._print_output_line(f"isaac> Execution failed: {str(e)}")

    def _print_output_line(self, line: str):
        """Print a line of output, handling buffering for Windows."""
        self.output_buffer.append(line)
        if len(self.output_buffer) > self.max_buffer_lines:
            self.output_buffer.pop(0)

        if self.terminal.is_windows:
            # On Windows, refresh the entire display to simulate scroll region
            self._refresh_display()
        else:
            # On non-Windows, just print (scroll region handles scrolling)
            self.terminal.print_normal_output(line)

    def _refresh_display(self):
        """Refresh the entire display for Windows (simulate scroll region)."""
        # Clear screen
        os.system('cls')

        # Redraw status bar
        self.terminal._draw_status_bar()

        # Print buffered output, limited to available lines
        available_lines = self.terminal.terminal_height - self.terminal.status_lines - 1
        start_idx = max(0, len(self.output_buffer) - available_lines)

        for line in self.output_buffer[start_idx:]:
            print(line)

        # Position cursor at bottom for next input
        bottom_line = self.terminal.status_lines + 1 + (len(self.output_buffer) - start_idx)
        if bottom_line > self.terminal.terminal_height:
            bottom_line = self.terminal.terminal_height
        print(f"\033[{bottom_line};1H", end="", flush=True)

    def _handle_clear_command(self) -> None:
        """Handle clear/cls commands by clearing the output buffer and refreshing display."""
        # Show the command being executed
        self._print_output_line(f"{self.terminal.get_prompt_string()}{self._get_clear_command_name()}")

        # Clear the output buffer
        self.output_buffer.clear()

        # Refresh the display (clears screen and redraws status bar)
        if self.terminal.is_windows:
            self._refresh_display()
        else:
            self.terminal.clear_main_area()

    def _handle_reset_command(self) -> None:
        """Handle reset command by clearing output buffer and refreshing display."""
        # Show the command being executed
        self._print_output_line(f"{self.terminal.get_prompt_string()}reset")

        # Clear the output buffer
        self.output_buffer.clear()

        # Refresh the display
        if self.terminal.is_windows:
            self._refresh_display()
        else:
            self.terminal.clear_main_area()
            self.terminal._draw_status_bar()

    def _handle_special_command(self, command: str) -> bool:
        """Handle commands that need special treatment to preserve UI.

        Returns:
            True if command was handled specially, False if normal execution should continue
        """
        cmd_lower = command.lower().strip()

        # Handle clear/cls commands - only clear below status bar
        if cmd_lower in ["clear", "cls"]:
            self._handle_clear_command()
            return True
        elif cmd_lower == "reset":
            self._handle_reset_command()
            return True

        return False

    def _get_clear_command_name(self) -> str:
        """Get the appropriate clear command name for current shell."""
        if self.terminal.is_windows:
            return "cls"
        else:
            return "clear"

    def _format_tier_display(self, tier: float) -> str:
        """Format tier for status display."""
        if tier == 1.0:
            return "1 (Safe)"
        elif tier == 2.0:
            return "2 (Auto-correct)"
        elif tier == 2.5:
            return "2.5 (Confirm)"
        elif tier == 3.0:
            return "3 (Validate)"
        elif tier == 4.0:
            return "4 (Lockdown)"
        else:
            return f"{tier} (Unknown)"

    def _signal_handler(self, signum, frame) -> None:
        """Handle termination signals."""
        self.running = False

    def _cleanup(self) -> None:
        """Clean up terminal state."""
        try:
            self.terminal.restore_terminal()
            print("\nIsaac session ended. Goodbye!")
        except:
            pass  # Best effort cleanup