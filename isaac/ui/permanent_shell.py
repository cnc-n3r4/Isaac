"""
Permanent Shell - Isaac's simplified terminal interface
Implements a simple prompt/output loop with meta-commands
"""

import sys
from isaac.core.command_router import CommandRouter
from isaac.core.session_manager import SessionManager
from isaac.adapters.powershell_adapter import PowerShellAdapter
from isaac.adapters.bash_adapter import BashAdapter


class PermanentShell:
    def __init__(self):
        self.session = SessionManager()
        self.shell = self._detect_shell()
        self.router = CommandRouter(self.session, self.shell)

    def _detect_shell(self):
        """Detect and return appropriate shell adapter"""
        if sys.platform == "win32":
            return PowerShellAdapter()
        else:
            return BashAdapter()

    def _print_welcome(self):
        """Print startup banner with key info"""
        version = "1.0.2"  # Get from config
        session_id = self.session.config.get('machine_id', 'unknown')[:6]

        cloud_status = "✓" if self.session.cloud else "✗"
        ai_status = "✓" if self.session.config.get('xai_api_key') else "✗"

        print("=" * 60)
        print(f"ISAAC v{version}")
        print(f"Session: {session_id} | Cloud: {cloud_status} | AI: {ai_status}")
        print("Type /help for available commands")
        print("=" * 60)
        print()

    def run(self):
        """Main shell loop - simplified"""
        self._print_welcome()

        while True:
            try:
                # Print prompt
                print("> ", end="", flush=True)

                # Get user input
                user_input = input().strip()

                # Skip empty input
                if not user_input:
                    continue

                # Handle exit
                if user_input.lower() in ["exit", "quit", "/exit", "/quit"]:
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
                print("\nUse 'exit' or '/exit' to quit")
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
