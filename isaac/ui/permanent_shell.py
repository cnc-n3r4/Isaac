"""
Permanent Shell - Isaac's simplified terminal interface
Implements a simple prompt/output loop with meta-commands
"""

import logging
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style

from isaac.adapters.bash_adapter import BashAdapter
from isaac.adapters.powershell_adapter import PowerShellAdapter
from isaac.core.command_router import CommandRouter
from isaac.core.message_queue import MessageQueue
from isaac.core.session_manager import SessionManager
from isaac.monitoring.monitor_manager import MonitorManager
from isaac.ui.inline_suggestions import (
    InlineSuggestionCompleter,
    InlineSuggestionDisplay,
)
from isaac.ui.predictive_completer import PredictionContext, PredictiveCompleter


class PermanentShell:
    def __init__(self):
        # Configure logging to suppress monitoring warnings in interactive mode
        # Only show ERROR level and above for monitoring modules
        logging.getLogger('isaac.monitoring').setLevel(logging.ERROR)
        
        self.session = SessionManager()
        self.shell = self._detect_shell()
        self.router = CommandRouter(self.session, self.shell)
        self.message_queue = MessageQueue()
        self.monitor_manager = MonitorManager()

        # Initialize prompt_toolkit with history support
        self.history = InMemoryHistory()

        # Initialize predictive completion
        self.predictive_completer = PredictiveCompleter()
        self.inline_completer = InlineSuggestionCompleter(
            self.predictive_completer, self._get_prediction_context
        )
        self.inline_display = InlineSuggestionDisplay(self.inline_completer)

        # Create key bindings for tab completion
        self.key_bindings = self._create_key_bindings()

        self.prompt_session = PromptSession(
            history=self.history, completer=self.inline_completer, key_bindings=self.key_bindings
        )

        # Track session commands for learning
        self.session_commands = []

        # Multi-step execution state
        self.multi_step_sequence = []
        self.multi_step_index = 0

        # Load command history from session
        self._load_command_history()

        # Setup sync completion callback
        self._setup_sync_callback()

    def _load_command_history(self):
        """Load command history from session into prompt_toolkit history."""
        try:
            commands = self.session.command_history.commands
            for cmd in commands[-100:]:  # Load last 100 commands
                if isinstance(cmd, dict):
                    command_text = cmd.get("command", "")
                elif isinstance(cmd, str):
                    command_text = cmd
                else:
                    continue

                if command_text:
                    self.history.append_string(command_text)
        except Exception:
            pass  # Ignore errors loading history

    def _setup_sync_callback(self):
        """Register callback for sync completion notifications."""

        def on_sync_complete(count: int):
            # Print notification to terminal
            print(f"\n✅ {count} queued command(s) synced")

        self.session.sync_worker.on_sync_complete = on_sync_complete

    def _create_key_bindings(self) -> KeyBindings:
        """Create key bindings for enhanced input features."""
        kb = KeyBindings()

        @kb.add(Keys.Tab)
        def _(event):
            """Accept inline suggestion on Tab press."""
            current_text = event.current_buffer.text
            completed_text = self.inline_display.accept_suggestion(current_text)
            if completed_text != current_text:
                event.current_buffer.text = completed_text
                event.current_buffer.cursor_position = len(completed_text)
            else:
                # If no inline suggestion, try multi-step prediction
                self._handle_multi_step_prediction(event)

        # Only add Ctrl+Tab binding if supported (avoid "Invalid key: c-tab" error)
        try:
            @kb.add("c-tab")  # Ctrl+Tab
            def _(event):
                """Execute next command in multi-step sequence."""
                self._execute_next_in_sequence()
        except ValueError:
            # Skip Ctrl+Tab binding if not supported in this terminal
            pass

        return kb

    def _handle_multi_step_prediction(self, event) -> None:
        """Handle multi-step command prediction when Tab is pressed with no inline suggestion."""
        current_text = event.current_buffer.text

        if not current_text.strip():
            return

        # Create context for prediction
        context = self._get_prediction_context()

        # Get predicted sequence
        sequence = self.predictive_completer.get_command_sequence(current_text, context)

        if sequence:
            self.multi_step_sequence = [current_text] + sequence
            self.multi_step_index = 0
            print(f"\nPredicted sequence: {' → '.join(self.multi_step_sequence)}")
            print("Press Ctrl+Tab to execute next command, or continue typing to cancel")
            # Redisplay prompt
            print(f"\033[33m{self._get_prompt()}\033[0m", end="", flush=True)

    def _execute_next_in_sequence(self) -> None:
        """Execute the next command in the multi-step sequence."""
        if not self.multi_step_sequence or self.multi_step_index >= len(self.multi_step_sequence):
            return

        command = self.multi_step_sequence[self.multi_step_index]
        self.multi_step_index += 1

        print(f"\nExecuting: {command}")

        # Execute the command
        result = self.router.route_command(command)

        # Learn from the command
        if result.success:
            self._learn_from_command(command)

        # Print output
        if result.output:
            sys.stdout.write(result.output + "\n")
            sys.stdout.flush()

        # Print any errors
        if not result.success and result.exit_code != 0:
            sys.stderr.write(f"Error (exit code {result.exit_code})\n")
            sys.stderr.flush()

        # Check if sequence is complete
        if self.multi_step_index >= len(self.multi_step_sequence):
            print(f"Sequence complete ({len(self.multi_step_sequence)} commands executed)")
            self.multi_step_sequence = []
            self.multi_step_index = 0
        else:
            remaining = len(self.multi_step_sequence) - self.multi_step_index
            print(f"{remaining} commands remaining. Press Ctrl+Tab for next command.")

        # Redisplay prompt
        print(f"\033[33m{self._get_prompt()}\033[0m", end="", flush=True)

    def _learn_from_command(self, command: str) -> None:
        """Learn patterns from executed command for predictive completion."""
        try:
            import os
            from datetime import datetime

            # Create prediction context
            context = PredictionContext(
                current_directory=os.getcwd(),
                recent_commands=self.session_commands[-5:] if self.session_commands else [],
                project_type=self._detect_project_type(),
                time_of_day=self._get_time_of_day(),
                day_of_week=datetime.now().strftime("%A"),
                session_commands=self.session_commands.copy(),
            )

            # Learn from the command
            self.predictive_completer.learn_from_command(command, context)

            # Add to session commands
            self.session_commands.append(command)
            if len(self.session_commands) > 100:  # Keep last 100
                self.session_commands.pop(0)

        except Exception:
            # Don't let learning errors break the shell
            pass

    def _detect_project_type(self) -> str:
        """Detect the type of project in current directory."""
        try:
            import os

            cwd = os.getcwd()

            # Check for common project files
            if os.path.exists(os.path.join(cwd, "package.json")):
                return "node"
            elif os.path.exists(os.path.join(cwd, "requirements.txt")) or os.path.exists(
                os.path.join(cwd, "pyproject.toml")
            ):
                return "python"
            elif os.path.exists(os.path.join(cwd, ".git")):
                return "git"
            else:
                return "unknown"
        except:
            return "unknown"

    def _get_time_of_day(self) -> str:
        """Get time of day category."""
        from datetime import datetime

        hour = datetime.now().hour

        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"

    def _get_prediction_context(self) -> PredictionContext:
        """Get current prediction context for the completer."""
        import os
        from datetime import datetime

        return PredictionContext(
            current_directory=os.getcwd(),
            recent_commands=self.session_commands[-5:] if self.session_commands else [],
            project_type=self._detect_project_type(),
            time_of_day=self._get_time_of_day(),
            day_of_week=datetime.now().strftime("%A"),
            session_commands=self.session_commands.copy(),
        )

    def _learn_from_correction(self, command: str) -> None:
        """Learn from corrections when predictions were shown but not accepted."""
        try:
            import os
            from datetime import datetime

            # Create prediction context
            context = PredictionContext(
                current_directory=os.getcwd(),
                recent_commands=self.session_commands[-5:] if self.session_commands else [],
                project_type=self._detect_project_type(),
                time_of_day=self._get_time_of_day(),
                day_of_week=datetime.now().strftime("%A"),
                session_commands=self.session_commands.copy(),
            )

            # Learn from correction if a suggestion was shown
            self.inline_completer.learn_from_correction(command, context)

        except Exception:
            # Don't let learning errors break the shell
            pass

    def _detect_shell(self):
        """Detect and return appropriate shell adapter"""
        if sys.platform == "win32":
            return PowerShellAdapter()
        else:
            return BashAdapter()

    def _print_welcome(self):
        """Print startup banner with key info"""
        version = "2.0.0"  # Get from config
        session_id = self.session.config.get("machine_id", "unknown")[:6]

        cloud_status = "✓" if self.session.cloud else "✗"

        # Check for API keys in new nested structure or old flat structure
        xai_config = self.session.config.get("xai", {})
        chat_config = xai_config.get("chat", {})
        collections_config = xai_config.get("collections", {})
        has_chat_key = chat_config.get("api_key") or self.session.config.get("xai_api_key")
        has_collections_key = collections_config.get("api_key") or self.session.config.get(
            "xai_api_key"
        )
        ai_status = "✓" if (has_chat_key or has_collections_key) else "✗"

        print("=" * 60)
        print(f"ISAAC v{version}")
        print(f"Session: {session_id} | Cloud: {cloud_status} | AI: {ai_status}")
        print("Type /help for available commands")
        print("=" * 60)
        print()

    def _get_prompt(self) -> str:
        """Build color-coded prompt based on system status.

        Color coding:
        - Green: Normal state (no pending items)
        - Yellow: Pending messages (worth noticing)
        - Red: Queued sync commands (needs attention) OR both issues
        """
        base_prompt = "$> "

        # Check message queue status (pending notifications)
        message_counts = self.message_queue.get_pending_counts()
        total_messages = message_counts["system"] + message_counts["code"]

        # Check sync queue status (commands waiting to sync)
        queue_status = self.session.get_queue_status()
        pending_sync = queue_status["pending"]

        # Determine color based on status
        if pending_sync > 0 and total_messages > 0:
            # Both sync issues and messages - highest priority (red)
            color_code = "\033[31m"  # Red
        elif pending_sync > 0:
            # Sync issues - needs attention (red)
            color_code = "\033[31m"  # Red
        elif total_messages > 0:
            # Just pending messages - worth noticing (yellow)
            color_code = "\033[33m"  # Yellow
        else:
            # Normal state (green)
            color_code = "\033[32m"  # Green

        # Reset color at end
        reset_code = "\033[0m"

        return f"{color_code}{base_prompt}{reset_code}"

    def run(self):
        """Main shell loop - simplified"""
        self._print_welcome()

        # Start autonomous monitoring agents
        self.monitor_manager.start_all()

        while True:
            try:
                # Build prompt text with message indicators
                queue_status = self.session.get_queue_status()
                pending_count = queue_status["pending"]

                # Get message indicator from message queue
                message_indicator = self.message_queue.get_prompt_indicator()

                if pending_count > 0:
                    # Show offline indicator with count and messages
                    prompt_text = f"{message_indicator[:-1]} [OFFLINE: {pending_count} queued]> "
                else:
                    prompt_text = message_indicator + " "

                # Get user input with history support (arrow keys work!)
                user_input = self.prompt_session.prompt(
                    prompt_text, style=Style.from_dict({"prompt": "#ffff00"})  # Yellow prompt
                ).strip()

                # Skip empty input
                if not user_input:
                    continue

                # Route command through existing system
                result = self.router.route_command(user_input)

                # Learn from successful commands for prediction
                if result.success and user_input.strip():
                    self._learn_from_command(user_input)
                    # Learn from corrections if a suggestion was shown
                    self._learn_from_correction(user_input)

                # Handle exit commands
                if (user_input.lower() in ["/exit", "/quit", "exit", "quit", "q"] or "Goodbye" in result.output) and result.success:
                    print("Goodbye!")
                    self.monitor_manager.stop_all()
                    break

                # Print output
                if result.output:
                    sys.stdout.write(result.output + "\n")
                    sys.stdout.flush()

                # Print any errors
                if not result.success and result.exit_code != 0:
                    sys.stderr.write(f"Error (exit code {result.exit_code})\n")
                    sys.stderr.flush()

            except KeyboardInterrupt:
                print("\nUse 'exit' or '/exit' to quit")
                continue
            except EOFError:
                print("\nGoodbye!")
                self.monitor_manager.stop_all()
                break
            except Exception as e:
                print(f"Unexpected error: {e}", file=sys.stderr)
                continue


def main():
    """Entry point for isaac command"""
    shell = PermanentShell()
    shell.run()


if __name__ == "__main__":
    main()
