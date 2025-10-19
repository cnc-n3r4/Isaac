"""
Isaac - AI-Enhanced Command-Line Assistant

Entry point for both CLI and interactive REPL modes.
"""

import sys
from isaac.core.session_manager import SessionManager
from isaac.core.cli_command_router import create_router


def main():
    """
    Main entry point.

    Modes:
    - CLI: isaac <command> <args>  (executes and exits)
    - REPL: isaac  (enters interactive loop)
    """
    # Initialize session
    session = SessionManager()
    session.load_from_local()
    session.load_from_cloud()

    # Create command router
    router = create_router(session)

    print("Isaac > Ready.")

    # Determine mode based on arguments
    if len(sys.argv) > 1:
        # CLI mode - execute single command and exit
        command = ' '.join(sys.argv[1:])
        result = router.execute(command)
        print(result)

        # Exit with appropriate status code
        sys.exit(0 if result.success else 1)
    else:
        # REPL mode - interactive loop
        repl_loop(router)


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