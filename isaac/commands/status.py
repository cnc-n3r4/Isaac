# isaac/commands/status.py

from isaac.core.session_manager import SessionManager

class StatusCommand:
    def __init__(self, session: SessionManager):
        self.session = session

    def execute(self, args: list) -> str:
        """
        Quick status check

        Usage:
            /status       - One-line summary
            /status -v    - Verbose (same as /config status)
        """
        if args and args[0] == '-v':
            # Delegate to config command
            from isaac.commands.config import ConfigCommand
            return ConfigCommand(self.session)._show_status()

        # One-line summary
        cloud = "✓" if self.session.cloud else "✗"
        ai = "✓" if self.session.config.get('xai_api_key') else "✗"
        hist = len(self.session.command_history.commands)

        return f"Session: {self.session.config.get('machine_id', 'unknown')[:6]} | Cloud: {cloud} | AI: {ai} | History: {hist}"