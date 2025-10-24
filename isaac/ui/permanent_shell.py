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
from isaac.ui.status_display import StatusDisplay
from isaac.adapters.powershell_adapter import PowerShellAdapter
from isaac.adapters.bash_adapter import BashAdapter


class PermanentShell:
    def __init__(self):
        print("Initializing permanent shell...")
        
        print("Loading session manager...")
        self.session = SessionManager()
        print("✓ Session manager loaded")
        
        print("Detecting shell environment...")
        self.shell = self._detect_shell()
        print(f"✓ {type(self.shell).__name__} adapter loaded")
        
        print("Initializing command router...")
        self.router = CommandRouter(self.session, self.shell)
        print("✓ Command router loaded")
        
        print("Setting up UI components...")
        # Initialize prompt_toolkit with history support
        self.history = InMemoryHistory()
        self.prompt_session = PromptSession(history=self.history)
        
        # Load command history from session
        self._load_command_history()
        print("✓ Command history loaded")

        # Setup sync completion callback
        self._setup_sync_callback()
        
        # Initialize status display
        self.status_display = StatusDisplay(self.session, self.shell)
        
        print("Isaac ready!")
        print()

    def _print_welcome(self):
        """Print comprehensive startup status header"""
        # Use the shared status display
        status_display = self.status_display.get_comprehensive_status()
        print(status_display)
        print()

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
        """Print comprehensive startup status header"""
        # Use the shared status display
        status_display = self.status_display.get_comprehensive_status()
        print(status_display)
        print()

    def _get_comprehensive_status(self):
        """Generate comprehensive status display for both startup and /status command"""
        lines = []
        
        # Header with version and external IP
        version = "1.0.23"
        external_ip = self._get_external_ip() or "177.31.23.102"
        lines.append(f"ISAAC v{version}{' ' * (44 - len(f'ISAAC v{version}'))}🌍{external_ip}")
        
        # AI model info and internal IP
        ai_model = self._get_ai_model_info()
        internal_ip = self._get_internal_ip() or "192.168.0.10"
        lines.append(f"{ai_model}{' ' * (44 - len(ai_model))}🏠{internal_ip}")
        
        # Email/workspace info
        workspace_info = self._get_workspace_info()
        lines.append(f"isaac@n3r4.xyz{' ' * (44 - len('isaac@n3r4.xyz'))}🖥️{workspace_info}")
        
        # Inbox status
        inbox_status = self._get_inbox_status()
        lines.append(f"inbox : {inbox_status}")
        
        # Last cloud sync and messages
        last_sync = self._get_last_sync_info()
        message_count = self._get_message_count()
        lines.append(f"last cloud sync: {last_sync}")
        lines.append(f"Messages: {message_count}")
        
        # Empty line for spacing
        lines.append("")
        
        # Bottom status line
        session_id = self.session.config.get('machine_id', 'unknown')[:6]
        cloud_status = self._check_cloud_status()
        ai_status = self._check_ai_status()
        history_count = self._get_history_count()
        lines.append(f"BS : {session_id} | Cloud: {cloud_status} | AI: {ai_status}")
        lines.append(f"Type /help or /status --help for more{' ' * (30 - len('Type /help or /status --help for more'))}[hist:{history_count}]")
        
        # Create the bordered display
        border = "=" * 62
        result = [border]
        result.extend(lines)
        result.append(border)
        
        return "\n".join(result)

    def _get_external_ip(self):
        """Get external IP address"""
        try:
            # Try to get external IP (simplified for now)
            import urllib.request
            with urllib.request.urlopen('https://api.ipify.org', timeout=2) as response:
                return response.read().decode('utf-8')
        except Exception:
            return None

    def _get_internal_ip(self):
        """Get internal IP address"""
        try:
            import socket
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return None

    def _get_ai_model_info(self):
        """Get current AI model information"""
        # Check config for AI model settings
        try:
            xai_config = self.session.config.get('xai', {})
            model = xai_config.get('model', 'Grok-bigdaddy-super_heavy_6000')
            return f"model: {model}"
        except Exception:
            return "model: Grok-bigdaddy-super_heavy_6000"

    def _get_workspace_info(self):
        """Get current workspace information"""
        # Check if workspace is active
        try:
            # This would check sandbox enforcer for active workspace
            return "@workspace"  # Placeholder
        except Exception:
            return "@workspace"

    def _get_inbox_status(self):
        """Get inbox status"""
        # Check for pending messages/emails
        try:
            # This would check message queue
            return "[full]"  # Placeholder
        except Exception:
            return "[empty]"

    def _get_last_sync_info(self):
        """Get last cloud sync timestamp"""
        try:
            # Check session data for last sync
            return "[2025-10-24 15:30]"  # Placeholder
        except Exception:
            return "[never]"

    def _get_message_count(self):
        """Get message count"""
        try:
            # Check message queue
            return "[many]"  # Placeholder
        except Exception:
            return "[0]"

    def _check_cloud_status(self):
        """Check cloud connectivity status"""
        try:
            if self.session.cloud:
                return "✓"
            return "✗"
        except Exception:
            return "✗"

    def _check_ai_status(self):
        """Check AI connectivity status"""
        try:
            # Check if xAI client is available
            return "xAI"
        except Exception:
            return "✗"

    def _get_history_count(self):
        """Get command history count"""
        try:
            return len(self.session.command_history.commands)
        except Exception:
            return 0

    def _check_connectivity(self) -> tuple[str, str]:
        """Check cloud and AI connectivity quietly.

        Returns:
            tuple: (cloud_status, ai_status) where each is '✓' or '✗'
        """
        # Check cloud connectivity
        cloud_status = "✗"
        try:
            if self.session.cloud:
                if self.session.cloud.health_check():
                    cloud_status = "✓"
        except Exception:
            pass

        # Check AI connectivity
        ai_status = "✗"
        try:
            # Check for API keys in new nested structure or old flat structure
            xai_config = self.session.config.get('xai', {})
            chat_config = xai_config.get('chat', {})
            collections_config = xai_config.get('collections', {})
            has_chat_key = chat_config.get('api_key') or self.session.config.get('xai_api_key')
            has_collections_key = collections_config.get('api_key') or self.session.config.get('xai_api_key')

            if has_chat_key or has_collections_key:
                # Try to initialize xAI client as a basic connectivity test
                try:
                    from isaac.ai.xai_client import XaiClient
                    # Just test client initialization, not actual API call
                    test_key = has_chat_key or has_collections_key
                    if test_key:  # Ensure we have a valid key
                        client = XaiClient(api_key=str(test_key))
                        ai_status = "✓"
                except Exception:
                    pass
        except Exception:
            pass

        return cloud_status, ai_status

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

        while True:
            try:
                # Build prompt text
                queue_status = self.session.get_queue_status()
                pending_count = queue_status['pending']
                
                if pending_count > 0:
                    prompt_text = f"$ [OFFLINE: {pending_count} queued]> "
                else:
                    prompt_text = "$> "

                # Get user input with history support (arrow keys work!)
                user_input = self.prompt_session.prompt(
                    prompt_text,
                    style=Style.from_dict({'prompt': '#ffff00'})  # Yellow prompt
                ).strip()

                # Skip empty input
                if not user_input:
                    continue

                # Handle exit
                if user_input.lower() in ["/exit", "/quit"]:
                    print("Goodbye!")
                    break

                # Route command through existing system
                result = self.router.route_command(user_input)

                # Print output
                if result.output:
                    print(result.output)

                # Print any errors
                if not result.success and result.exit_code != 0:
                    print(f"Error (exit code {result.exit_code})", file=sys.stderr)

            except KeyboardInterrupt:
                print("\nUse '/exit' or '/quit' to quit")
                continue
            except EOFError:
                print("\nGoodbye!")
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
