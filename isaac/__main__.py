"""
Isaac - AI-Enhanced Command-Line Assistant

Entry point for permanent shell mode and direct command execution.
"""

import sys
import argparse
from isaac.ui.permanent_shell import PermanentShell
from isaac.core.session_manager import SessionManager
from isaac.core.command_router import CommandRouter
from isaac.core.key_manager import KeyManager
from isaac.adapters.powershell_adapter import PowerShellAdapter
from isaac.adapters.bash_adapter import BashAdapter


def main():
    """
    Main entry point.

    If arguments provided: execute command directly and exit
    If no arguments: launch interactive shell
    """
    try:
        print("Isaac - AI-Enhanced Command-Line Assistant")
        print("Loading...")

        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Isaac - AI-Enhanced Command-Line Assistant')
        parser.add_argument('-key', '--key', help='Authentication key for access')
        parser.add_argument('-daemon', '--daemon', action='store_true', help='Run in daemon mode for webhooks')
        parser.add_argument('-oneshot', '--oneshot', action='store_true', help='Execute command and exit (no session persistence)')

        # Parse known args first, leave the rest as command
        args, unknown = parser.parse_known_args()
        command = unknown

        print("✓ Arguments parsed")

        # Initialize key manager for authentication
        print("Loading key manager...")
        key_manager = KeyManager()
        print("✓ Key manager loaded")

        # Authenticate if key provided or required
        if args.key:
            print("Authenticating...")
            if not key_manager.authenticate(args.key):
                print(key_manager.get_rejection_message())
                sys.exit(1)
            print("✓ Authentication successful")
        elif not args.daemon and not args.oneshot:
            # Interactive mode requires authentication unless explicitly bypassed
            print("Isaac requires authentication. Use -key <your_key> to authenticate.")
            print("Create a key with: isaac /config keys create")
            sys.exit(1)

        # Check if we have a direct command to execute
        if command:
            # Direct command execution mode
            return execute_direct_command(command, key_manager, args.oneshot)
        else:
            # Interactive shell mode
            shell = PermanentShell()
            shell.run()
    except KeyboardInterrupt:
        print("\nIsaac terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Isaac failed to start: {e}")
        sys.exit(1)


def execute_direct_command(args, key_manager=None, oneshot=False):
    """
    Execute a command directly from command line arguments.

    Args:
        args: Command line arguments (command to execute)
        key_manager: KeyManager instance for authentication
        oneshot: Whether to run in oneshot mode (no session persistence)
    """
    try:
        print("Initializing session manager...")
        # Initialize session manager
        config = {'sync_enabled': False} if oneshot else None
        session_mgr = SessionManager(config)
        print("✓ Session manager initialized")

        print("Detecting shell environment...")
        # Get shell adapter (same logic as PermanentShell)
        if sys.platform == "win32":
            shell_adapter = PowerShellAdapter()
            print("✓ PowerShell adapter loaded")
        else:
            shell_adapter = BashAdapter()
            print("✓ Bash adapter loaded")

        print("Initializing command router...")
        # Create command router
        router = CommandRouter(session_mgr, shell_adapter)
        print("✓ Command router initialized")

        # Join arguments back into a command string
        command = ' '.join(args)
        print(f"Executing command: {command}")

        # Route and execute the command
        result = router.route_command(command)

        # Output the result
        print(result.output)

        # Exit with appropriate code
        sys.exit(0 if result.success else 1)

    except Exception as e:
        print(f"Command execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


def repl_loop(router):
    """
    Interactive REPL (Read-Eval-Print Loop).

    Continuously reads commands, executes them, and displays results
    until user exits.

    Args:
        router: CommandRouter instance for command execution
    """
    print("Type 'exit' or 'quit' to exit. Type 'help' for commands.\n")

    while True:
        try:
            # Display prompt and read input
            user_input = input("isaac> ").strip()

            # Skip empty input
            if not user_input:
                continue

            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Isaac > Goodbye.")
                break

            # Execute command
            result = router.execute(user_input)

            # Display result
            print(result)
            print()  # Blank line for readability

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n\nIsaac > Use 'exit' to quit.")
            print()
            continue

        except EOFError:
            # Handle Ctrl+D or end of input
            print("\n\nIsaac > Goodbye.")
            break

        except Exception as e:
            # Catch-all for unexpected errors
            print(f"\n✗ Unexpected error: {str(e)}")
            print("   💡 Please report this issue if it persists\n")
            continue


if __name__ == "__main__":
    main()