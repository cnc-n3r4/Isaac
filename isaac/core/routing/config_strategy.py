"""
Config command strategy.
"""

import shlex
from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy


class ConfigStrategy(CommandStrategy):
    """Strategy for handling /config commands."""

    def can_handle(self, input_text: str) -> bool:
        """Check if command is /config."""
        return input_text.startswith("/config")

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Execute config command."""
        try:
            # Special case: /config console launches TUI
            if input_text == "/config console":
                from isaac.ui.config_console import show_config_console

                message = show_config_console(self.session)
                return CommandResult(success=True, output=message, exit_code=0)

            # Parse the command: /config [args...]
            parts = input_text.split()
            if len(parts) < 2:
                # Just /config - show overview
                from isaac.commands.config.run import show_overview

                output = show_overview(self.session)
                return CommandResult(success=True, output=output, exit_code=0)

            # Parse arguments
            args_raw = " ".join(parts[1:])
            parsed_parts = shlex.split(args_raw)

            # Simple flag parsing for --flag format
            flags = {}
            i = 0
            while i < len(parsed_parts):
                part = parsed_parts[i]
                if part.startswith("--"):
                    flag_name = part[2:]  # Remove --
                    if i + 1 < len(parsed_parts) and not parsed_parts[i + 1].startswith("--"):
                        flags[flag_name] = parsed_parts[i + 1]
                        i += 1  # Skip the value
                    else:
                        flags[flag_name] = True
                i += 1

            # Call the appropriate config function
            from isaac.commands.config.run import (
                set_api_key,
                set_config,
                show_ai_details,
                show_cloud_details,
                show_collections_config,
                show_overview,
                show_plugins,
                show_status,
            )

            # Convert session to dict format expected by config functions
            session_dict = {
                "machine_id": getattr(self.session.config, "machine_id", "unknown"),
                "user_prefs": getattr(self.session.preferences, "data", {}),
            }

            if "help" in flags:
                # Show detailed help for config command
                from isaac.commands.help.run import get_detailed_help

                output = get_detailed_help("/config")
            elif "status" in flags:
                output = show_status(session_dict)
            elif "ai" in flags:
                output = show_ai_details(session_dict)
            elif "cloud" in flags:
                output = show_cloud_details(session_dict)
            elif "plugins" in flags:
                output = show_plugins()
            elif "collections" in flags:
                output = show_collections_config(session_dict)
            elif "set" in flags:
                key = flags["set"]
                # Find the value (everything after the key)
                key_index = parsed_parts.index("--set")
                if key_index + 1 < len(parsed_parts):
                    value = parsed_parts[key_index + 1]
                    output = set_config(session_dict, key, value)
                else:
                    output = "Usage: /config --set <key> <value>"
            elif "apikey" in flags or "key" in flags:
                service = flags.get("apikey") or flags.get("key")
                # Find the API key (next argument after the service in parsed_parts)
                service_index = None
                for i, part in enumerate(parsed_parts):
                    if part == service:  # Only match the service name, not the flag
                        service_index = i + 1
                        break
                if service_index and service_index < len(parsed_parts):
                    api_key = parsed_parts[service_index]
                    output = set_api_key(session_dict, service, api_key)
                else:
                    output = "Usage: /config --apikey <service> <api_key>\n\nSupported services:\n  xai-chat        - xAI API key for chat completion\n  xai-collections - xAI API key for collections\n  claude          - Anthropic Claude API key\n  openai          - OpenAI API key"
            else:
                output = show_overview(session_dict)

            return CommandResult(success=True, output=output, exit_code=0)

        except Exception as e:
            return CommandResult(
                success=False, output=f"Config command error: {str(e)}", exit_code=1
            )

    def get_help(self) -> str:
        """Get help text for config command."""
        return "/config - Show configuration\n/config console - Launch config TUI\n/config --help - Show detailed help"

    def get_priority(self) -> int:
        """Medium priority - meta command."""
        return 30
