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
        
        # Initialize session manager (it will load config from ~/.isaac/config.json)
        self.session_manager = SessionManager()
        
        # Get the loaded preferences from session manager
        self.preferences = self.session_manager.get_preferences()
        
        # Get the loaded config from session manager
        self.config = self.session_manager.get_config()
        
        self.tier_validator = TierValidator(self.preferences)

        # Output buffering for Windows scrolling simulation
        self.output_buffer = []
        self.max_buffer_lines = 100

        # Initialize AI client if configured
        self.ai_client = None
        claude_api_key = self.config.get('claude_api_key')
        claude_api_url = self.config.get('claude_api_url')
        ai_model = self.config.get('ai_model', 'grok')
        if claude_api_key and claude_api_url:
            try:
                from isaac.ai.claude_client import ClaudeClient
                self.ai_client = ClaudeClient(
                    api_key=claude_api_key,
                    api_url=claude_api_url,
                    model=ai_model
                )
                self._print_output_line("isaac> AI client initialized successfully")
            except Exception as e:
                self._print_output_line(f"isaac> Failed to initialize AI client: {e}")
        else:
            self._print_output_line("isaac> AI client not configured (missing claude_api_key or claude_api_url in config)")

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

            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully - just print newline and continue
                self._print_output_line("")
                continue
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self._print_output_line(error_msg)

    def _get_user_input(self) -> str:
        """Get user input with traditional prompt."""
        prompt = self.terminal.get_prompt_string()
        # Ensure cursor is positioned correctly for input
        if self.terminal.is_windows:
            # On Windows, position cursor at the bottom of the visible area
            available_lines = self.terminal.terminal_height - self.terminal.status_lines - 1
            start_idx = max(0, len(self.output_buffer) - available_lines)
            displayed_lines = len(self.output_buffer) - start_idx
            bottom_line = self.terminal.status_lines + 1 + displayed_lines
            if bottom_line > self.terminal.terminal_height:
                bottom_line = self.terminal.terminal_height
            print(f"\033[{bottom_line};1H", end="", flush=True)
        else:
            # On non-Windows, use scroll region positioning
            scroll_start = self.terminal.status_lines + 1  # Line 4
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
        # Handle isaac-prefixed commands as direct shell execution
        if command.lower().startswith("isaac "):
            actual_command = command[6:].strip()  # Remove "isaac " prefix
            self._handle_isaac_command(actual_command)
            return

        # Validate command tier
        tier = self.tier_validator.get_tier(command)

        # Handle different command types
        if self._is_ai_query(command):
            self._handle_ai_query(command)
        elif tier >= 3.0:
            self._handle_tier3_command(command, tier)
        else:
            self._execute_normal_command(command)

    def _handle_isaac_command(self, command: str) -> None:
        """Handle isaac-prefixed commands as direct shell execution."""
        # Check if command is valid (basic validation)
        if not command:
            self._print_output_line("isaac> No command provided")
            return

        # For now, treat all isaac commands as valid and execute them
        # TODO: Add history-based validation later
        self._print_output_line("isaac> Valid command, executing..")
        self._execute_normal_command(command)

    def _is_ai_query(self, command: str) -> bool:
        """Check if command is an AI query."""
        # Commands starting with "isaac " are shell commands, not AI queries
        if command.lower().startswith("isaac "):
            return False

        command_lower = command.lower().strip()

        # Check for question patterns
        question_words = ["what", "where", "when", "why", "how", "who", "which", "can you", "could you", "would you", "do you", "are you", "is it", "does it"]
        if any(command_lower.startswith(word) for word in question_words):
            return True

        # Check for conversational patterns
        conversational_starts = ["tell me", "explain", "describe", "help me", "i need", "i want", "can i", "should i"]
        if any(phrase in command_lower for phrase in conversational_starts):
            return True

        # Check for AI-specific prefixes
        ai_prefixes = ["ai", "grok", "hey isaac"]
        if any(command_lower.startswith(prefix) for prefix in ai_prefixes):
            return True

        # If it contains question marks or is longer than typical commands, likely AI query
        if "?" in command or len(command.split()) > 3:
            return True

        return False

    def _handle_ai_query(self, command: str) -> None:
        """Handle AI query in traditional style."""
        if not self.ai_client:
            self._print_output_line("isaac> AI client not configured. Please set api_key and api_url in preferences.")
            return

        try:
            # Use AI client to process the query
            response = self.ai_client._call_api(f"Process this user query and provide a helpful response: {command}")
            if response.get('success'):
                ai_response = response.get('text', 'No response from AI')
                # Split multi-line response into separate lines for proper cursor positioning
                response_lines = ai_response.splitlines()

                # Batch all AI response lines to avoid display corruption
                for line in response_lines:
                    self.output_buffer.append(f"isaac> {line}")
                    if len(self.output_buffer) > self.max_buffer_lines:
                        self.output_buffer.pop(0)

                # Refresh display only once after all lines are added
                if self.terminal.is_windows:
                    self._refresh_display()
                else:
                    # On non-Windows, print all lines at once
                    output_text = '\n'.join(f"isaac> {line}" for line in response_lines)
                    self.terminal.print_normal_output(output_text)
            else:
                self._print_output_line(f"isaac> AI error: {response.get('error', 'Unknown error')}")
        except Exception as e:
            self._print_output_line(f"isaac> AI query failed: {e}")

    def _handle_tier3_command(self, command: str, tier: float) -> None:
        """Handle Tier 3+ commands with confirmation."""
        self._print_output_line(f"isaac> Tier {tier} command requires confirmation. Proceed? (y/n)")

        try:
            response = input().strip().lower()
            if response in ['y', 'yes']:
                self._execute_normal_command(command)
            else:
                self._print_output_line("isaac> Command cancelled.")
        except KeyboardInterrupt:
            self._print_output_line("")
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

        except KeyboardInterrupt:
            # Handle Ctrl+C during command execution
            self._print_output_line("^C")
            self._print_output_line("isaac> Command interrupted")
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

        # Print all lines at once to avoid corruption
        output_text = '\n'.join(self.output_buffer[start_idx:])
        print(output_text)

        # Position cursor at bottom for next input
        displayed_lines = len(self.output_buffer) - start_idx
        bottom_line = self.terminal.status_lines + 1 + displayed_lines
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