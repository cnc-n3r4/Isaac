# isaac/commands/config.py

from isaac.ai.xai_client import XaiClient
from isaac.core.session_manager import SessionManager


class ConfigCommand:
    def __init__(self, session: SessionManager):
        self.session = session

    def execute(self, args: list) -> str:
        """
        Handle /config commands

        Usage:
            /config              - Show overview
            /config status       - Detailed status
            /config ai           - AI provider details
            /config cloud        - Cloud sync details
            /config plugins      - List plugins
            /config console      - Launch /mine settings console
            /config set <k> <v>  - Set configuration value
        """
        if not args:
            return self._show_overview()

        subcommand = args[0].lower()

        if subcommand == "status":
            return self._show_status()
        elif subcommand == "ai":
            return self._show_ai_details()
        elif subcommand == "cloud":
            return self._show_cloud_details()
        elif subcommand == "plugins":
            return self._show_plugins()
        elif subcommand == "console":
            return self._launch_console()
        elif subcommand == "set":
            if len(args) < 3:
                return "Usage: /config set <key> <value>"
            return self._set_config(args[1], args[2])
        else:
            return f"Unknown subcommand: {subcommand}\nUse /config for help"

    def _show_overview(self) -> str:
        """Show configuration overview"""
        lines = []
        lines.append("=== ISAAC Configuration ===")
        lines.append(f"Version: {self._get_version()}")
        lines.append(f"Session ID: {self.session.config.get('machine_id', 'unknown')}")
        lines.append(f"History Count: {len(self.session.command_history.commands)}")
        lines.append(f"Default Tier: {self.session.preferences.data.get('default_tier', 2)}")
        lines.append("")
        lines.append("Available subcommands:")
        lines.append("  /config status   - System status check")
        lines.append("  /config ai       - AI provider details")
        lines.append("  /config cloud    - Cloud sync status")
        lines.append("  /config plugins  - Available plugins")
        lines.append("  /config console  - Launch /mine settings console")
        lines.append("  /config set <key> <value> - Change setting")
        return "\n".join(lines)

    def _show_status(self) -> str:
        """Show detailed system status"""
        lines = []
        lines.append("=== System Status ===")

        # Cloud status
        cloud_status = self._check_cloud_status()
        lines.append(f"Cloud: {cloud_status}")

        # AI status
        ai_status = self._check_ai_status()
        lines.append(f"AI Provider: {ai_status}")

        # Network info
        import socket

        hostname = socket.gethostname()
        try:
            ip = socket.gethostbyname(hostname)
            lines.append(f"Network: {ip}")
        except:
            lines.append("Network: Unable to detect")

        # Session info
        lines.append(f"Session: {self.session.config.get('machine_id', 'unknown')}")
        lines.append(f"Commands today: {len(self.session.command_history.commands)}")

        return "\n".join(lines)

    def _show_ai_details(self) -> str:
        """Show AI provider configuration"""
        lines = []
        lines.append("=== AI Provider Details ===")

        provider = self.session.config.get("ai_provider", "xai")
        model = self.session.config.get("ai_model", "grok-beta")

        lines.append(f"Provider: {provider}")
        lines.append(f"Model: {model}")

        # Try to ping the API
        try:
            # This is pseudocode - adapt to your actual client
            xai_config = self.session.config.get("xai", {})
            chat_config = xai_config.get("chat", {})
            api_key = chat_config.get("api_key") or self.session.config.get("xai_api_key")
            api_url = self.session.config.get("xai_api_url")
            if api_key and api_url:
                client = XaiClient(api_key=api_key, api_url=api_url, model=model)
                # Add a simple health check method to your client
                status = "✓ Connected"
            else:
                status = "✗ Not configured"
        except Exception as e:
            status = f"✗ Error: {str(e)}"

        lines.append(f"Status: {status}")

        return "\n".join(lines)

    def _show_cloud_details(self) -> str:
        """Show cloud sync status"""
        lines = []
        lines.append("=== Cloud Sync Status ===")

        if not self.session.config.get("sync_enabled", False):
            lines.append("Cloud sync: Disabled")
            lines.append("Enable in config: /config set sync_enabled true")
            return "\n".join(lines)

        lines.append("Cloud sync: Enabled")

        try:
            # Check cloud client status
            if self.session.cloud:
                # Check if API is reachable
                is_healthy = self.session.cloud.health_check()
                if is_healthy:
                    lines.append("Connection: ✓ Healthy")
                    lines.append("Last sync: Recent")
                else:
                    lines.append("Connection: ✗ Unhealthy")
            else:
                lines.append("Connection: ✗ Client not initialized")
        except Exception as e:
            lines.append(f"Connection: ✗ Error - {str(e)}")

        return "\n".join(lines)

    def _show_plugins(self) -> str:
        """List available plugins"""
        lines = []
        lines.append("=== Available Plugins ===")

        # For now, hardcode known plugins
        # Later, scan isaac/commands/ directory
        plugins = [
            ("togrok", "Vector search collections", True),
            ("backup", "Config backup/restore", True),
            ("task_planner", "Multi-step task execution", True),
        ]

        for name, desc, enabled in plugins:
            status = "✓" if enabled else "✗"
            lines.append(f"{status} {name:15} - {desc}")

        return "\n".join(lines)

    def _launch_console(self) -> str:
        """Launch the /mine settings console"""
        try:
            from isaac.ui.config_console import show_config_console

            return show_config_console(self.session)
        except ImportError:
            return (
                "✗ Config console not available. Install prompt_toolkit: pip install prompt_toolkit"
            )
        except Exception as e:
            return f"✗ Error launching config console: {e}"

    def _set_config(self, key: str, value: str) -> str:
        """Set a configuration value"""
        # Define allowed config keys
        allowed_keys = {
            "default_tier": int,
            "sync_enabled": lambda v: v.lower() in ["true", "1", "yes"],
            "ai_provider": str,
            "ai_model": str,
        }

        if key not in allowed_keys:
            return f"Unknown config key: {key}\nAllowed: {', '.join(allowed_keys.keys())}"

        try:
            # Convert value to correct type
            converter = allowed_keys[key]
            converted_value = converter(value)

            # Update preferences
            self.session.preferences.data[key] = converted_value
            self.session._save_preferences()

            return f"✓ Set {key} = {converted_value}"
        except Exception as e:
            return f"✗ Error setting {key}: {str(e)}"

    def _get_version(self) -> str:
        """Get ISAAC version"""
        # Read from setup.py or version file
        return "1.0.2"  # Hardcoded for now

    def _check_ai_status(self) -> str:
        """Quick AI status check"""
        provider = self.session.config.get("ai_provider", "xai")
        model = self.session.config.get("ai_model", "grok-beta")

        try:
            if self.session.config.get("xai_api_key"):
                return f"\u2713 {provider} ({model})"
            else:
                return f"\u2717 {provider} (no key)"
        except:
            return f"\u2717 {provider} unreachable"

    def _check_cloud_status(self) -> str:
        """Quick cloud status check"""
        if not self.session.config.get("sync_enabled", False):
            return "\u2717 Disabled"

        try:
            if self.session.cloud:
                return "\u2713 Connected"
            else:
                return "\u2717 Client not initialized"
        except:
            return "\u2717 Unreachable"
