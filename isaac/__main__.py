"""
Isaac - AI-Enhanced Command-Line Assistant

Entry point for permanent shell mode and direct command execution.
"""

import sys
from isaac.ui.permanent_shell import PermanentShell
from isaac.core.session_manager import SessionManager
from isaac.core.command_router import CommandRouter
from isaac.adapters.powershell_adapter import PowerShellAdapter
from isaac.adapters.bash_adapter import BashAdapter


def main():
    """
    Main entry point.

    If arguments provided: execute command directly and exit
    If no arguments: launch interactive shell
    """
    try:
        # Check if we have command-line arguments (beyond script name)
        if len(sys.argv) > 1:
            # Direct command execution mode
            return execute_direct_command(sys.argv[1:])
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


def execute_direct_command(args):
    """
    Execute a command directly from command line arguments.

    Args:
        args: Command line arguments (excluding script name)
    """
    try:
        # Initialize session manager
        session_mgr = SessionManager()

        # Get shell adapter (same logic as PermanentShell)
        if sys.platform == "win32":
            shell_adapter = PowerShellAdapter()
        else:
            shell_adapter = BashAdapter()

        # Create command router
        router = CommandRouter(session_mgr, shell_adapter)

        # Join arguments back into a command string
        command = ' '.join(args)

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