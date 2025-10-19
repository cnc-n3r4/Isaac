"""Isaac 2.0 - Multi-platform shell assistant entry point."""

from isaac.core.session_manager import SessionManager


def main():
    """Main entry point."""
    # Initialize session manager
    session = SessionManager()

    # Load session data
    session.load_from_local()
    session.load_from_cloud()

    # Test command logging
    session._log_command("echo 'test cloud sync'")

    # Start REPL (placeholder)
    print("Isaac > Ready.")


if __name__ == '__main__':
    main()