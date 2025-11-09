# isaac/commands/status.py

from isaac.core.session_manager import SessionManager

class StatusCommand:
    def __init__(self, session: SessionManager):
        self.session = session

    def execute(self, args: list) -> str:
        """
        Quick status check with Phase 9 info

        Usage:
            /status       - One-line summary
            /status -v    - Verbose (same as /config status)
        """
        if args and args[0] == '-v':
            # Delegate to config command
            from isaac.commands.config import ConfigCommand
            return ConfigCommand(self.session)._show_status()

        # Enhanced one-line summary with Phase 9 info
        cloud = "\u2713" if self.session.cloud else "\u2717"

        # Check for API keys in new nested structure or old flat structure
        xai_config = self.session.config.get('xai', {})
        chat_config = xai_config.get('chat', {})
        collections_config = xai_config.get('collections', {})
        has_chat_key = chat_config.get('api_key') or self.session.config.get('xai_api_key')
        has_collections_key = collections_config.get('api_key') or self.session.config.get('xai_api_key')
        ai = "\u2713" if (has_chat_key or has_collections_key) else "\u2717"

        hist = len(self.session.command_history.commands)

        # Phase 9: Show consolidated commands status
        phase = "Phase 9: 6 Core Commands"

        return f"{phase} | Session: {self.session.config.get('machine_id', 'unknown')[:6]} | Cloud: {cloud} | AI: {ai} | History: {hist}"