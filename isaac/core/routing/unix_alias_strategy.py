"""
Unix alias translation strategy - translates Unix commands on Windows.
"""

import platform
from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy


class UnixAliasStrategy(CommandStrategy):
    """Strategy for translating Unix commands to Windows equivalents."""

    def can_handle(self, input_text: str) -> bool:
        """Check if command is a Unix command on Windows."""
        current_platform = platform.system().lower()
        return current_platform == "windows" and self._is_unix_command(input_text)

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Translate Unix command and route back through router."""
        try:
            from isaac.core.unix_aliases import UnixAliasTranslator

            translator = UnixAliasTranslator()
            translated = translator.translate(input_text)
            if translated:
                if translator.show_translation:
                    print(f"Isaac > Translating Unix command: {input_text} -> {translated}")

                # Route translated command back through router for tier processing
                router = context.get("router")
                if router:
                    return router.route_command(translated)
                else:
                    return self.shell.execute(translated)
            else:
                # Translation failed, continue with original
                router = context.get("router")
                if router:
                    return router.route_command(input_text)
                else:
                    return self.shell.execute(input_text)

        except Exception as e:
            # If translation fails, continue with original command
            print(f"Isaac > Warning: Unix alias translation failed: {e}")
            router = context.get("router")
            if router:
                return router.route_command(input_text)
            else:
                return self.shell.execute(input_text)

    def get_help(self) -> str:
        """Get help text for Unix alias translation."""
        return "Unix alias translation: Automatically translates Unix commands to Windows equivalents"

    def get_priority(self) -> int:
        """Medium-low priority - should come after special commands but before tier processing."""
        return 60

    def _is_unix_command(self, cmd: str) -> bool:
        """Check if command is a Unix command that needs translation on Windows."""
        unix_commands = {
            "ls",
            "grep",
            "ps",
            "kill",
            "find",
            "cat",
            "head",
            "tail",
            "cp",
            "mv",
            "rm",
            "pwd",
            "which",
            "echo",
            "touch",
            "mkdir",
            "wc",
            "sort",
            "uniq",
            "chmod",
            "chown",
            "du",
            "df",
        }
        first_word = cmd.strip().split()[0] if cmd.strip() else ""
        return first_word in unix_commands
