"""
Status Display Utilities - Shared status display functions
"""

import socket


class StatusDisplay:
    """Shared status display utilities for both startup and /status command"""

    def __init__(self, session, shell_adapter=None):
        self.session = session
        self.shell_adapter = shell_adapter

    def get_comprehensive_status(self):
        """Generate comprehensive status display"""
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
        
        # Detect shell type
        shell_prefix = "PS" if self._is_powershell() else "BS"
        lines.append(f"{shell_prefix} : {session_id} | Cloud: {cloud_status} | AI: {ai_status}")
        lines.append("Type /help or /status --help for more")

        # Create the bordered display
        border = "=" * 62
        result = [border]
        result.extend(lines)
        # Add history count to the bottom border
        result.append(f"{border[:-len(f'[hist:{history_count}]')]}[hist:{history_count}]")

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
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return None

    def _get_ai_model_info(self):
        """Get current AI model information"""
        # Check config for AI model settings
        try:
            xai_config = self.session.config.get('xai', {})
            chat_config = xai_config.get('chat', {})
            model = chat_config.get('model', 'grok-3')
            return f"model: {model}"
        except Exception:
            return "model: grok-3"

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

    def _is_powershell(self):
        """Check if we're running on PowerShell"""
        try:
            if self.shell_adapter:
                # Check the class name of the shell adapter
                return "PowerShell" in type(self.shell_adapter).__name__
            # Fallback: check platform
            import sys
            return sys.platform == "win32"
        except Exception:
            return False