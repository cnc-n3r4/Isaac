"""
Isaac - AI-Enhanced Command-Line Assistant

Entry point for permanent shell mode.
"""

import sys
from isaac.ui.permanent_shell import PermanentShell


def main():
    """
    Main entry point.

    Launches Isaac's simplified shell interface.
    """
    try:
        shell = PermanentShell()
        shell.run()
    except KeyboardInterrupt:
        print("\nIsaac terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Isaac failed to start: {e}")
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