"""
Permanent Shell - Isaac's simplified terminal interface
Implements a simple prompt/output loop with meta-commands
"""

import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from isaac.core.command_router import CommandRouter
from isaac.core.session_manager import SessionManager
from isaac.core.message_queue import MessageQueue
from isaac.adapters.powershell_adapter import PowerShellAdapter
from isaac.adapters.bash_adapter import BashAdapter
from isaac.monitoring.monitor_manager import MonitorManager


class PermanentShell:
    def __init__(self):
        self.session = SessionManager()
        self.shell = self._detect_shell()
        self.router = CommandRouter(self.session, self.shell)
        self.message_queue = MessageQueue()
        self.monitor_manager = MonitorManager()
        
        # Initialize prompt_toolkit with history support
        self.history = InMemoryHistory()
        self.prompt_session = PromptSession(history=self.history)
        
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
                    command_text = cmd.get('command', '')
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

    def _detect_shell(self):
        """Detect and return appropriate shell adapter"""
        if sys.platform == "win32":
            return PowerShellAdapter()
        else:
            return BashAdapter()

    def _print_welcome(self):
        """Print startup banner with key info"""
        version = "2.0.0"  # Get from config
        session_id = self.session.config.get('machine_id', 'unknown')[:6]

        cloud_status = "✓" if self.session.cloud else "✗"
        
        # Check for API keys in new nested structure or old flat structure
        xai_config = self.session.config.get('xai', {})
        chat_config = xai_config.get('chat', {})
        collections_config = xai_config.get('collections', {})
        has_chat_key = chat_config.get('api_key') or self.session.config.get('xai_api_key')
        has_collections_key = collections_config.get('api_key') or self.session.config.get('xai_api_key')
        ai_status = "✓" if (has_chat_key or has_collections_key) else "✗"

        print("=" * 60)
        print(f"ISAAC v{version}")
        print(f"Session: {session_id} | Cloud: {cloud_status} | AI: {ai_status}")
        print("Type /help for available commands")
        print("=" * 60)
        print()

    def _get_prompt(self) -> str:
        """Build prompt with queue status."""
        base_prompt = "$"

        # Check queue status
        queue_status = self.session.get_queue_status()
        pending_count = queue_status['pending']

        if pending_count > 0:
            # Show offline indicator with count
            prompt = f"{base_prompt} [OFFLINE: {pending_count} queued]> "
        else:
            prompt = f"{base_prompt}> "

        # Make prompt yellow
        return f"\033[33m{prompt}\033[0m"

    def run(self):
        """Main shell loop - simplified"""
        self._print_welcome()
        
        # Start autonomous monitoring agents
        self.monitor_manager.start_all()

        while True:
            try:
                # Build prompt text with message indicators
                queue_status = self.session.get_queue_status()
                pending_count = queue_status['pending']
                
                # Get message indicator from message queue
                message_indicator = self.message_queue.get_prompt_indicator()
                
                if pending_count > 0:
                    # Show offline indicator with count and messages
                    prompt_text = f"{message_indicator[:-1]} [OFFLINE: {pending_count} queued]> "
                else:
                    prompt_text = message_indicator + " "

                # Get user input with history support (arrow keys work!)
                user_input = self.prompt_session.prompt(
                    prompt_text,
                    style=Style.from_dict({'prompt': '#ffff00'})  # Yellow prompt
                ).strip()

                # Skip empty input
                if not user_input:
                    continue

                # Route command through existing system
                result = self.router.route_command(user_input)

                # Handle exit commands
                if user_input.lower() in ["/exit", "/quit"] and result.success:
                    print("Goodbye!")
                    self.monitor_manager.stop_all()
                    break

                # Print output
                if result.output:
                    print(result.output)

                # Print any errors
                if not result.success and result.exit_code != 0:
                    print(f"Error (exit code {result.exit_code})", file=sys.stderr)

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
