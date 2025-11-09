"""
Exit blocker strategy - prevents exit/quit without / prefix.
"""

from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy


class ExitBlockerStrategy(CommandStrategy):
    """Strategy to block exit/quit commands without / prefix."""

    def can_handle(self, input_text: str) -> bool:
        """Check if command is exit or quit without /."""
        return input_text.strip() in ["exit", "quit"]

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Block the command and show helpful message."""
        return CommandResult(
            success=False, output="Isaac > Use /exit or /quit to exit Isaac", exit_code=1
        )

    def get_help(self) -> str:
        """Get help text."""
        return "Use /exit or /quit to exit Isaac (not 'exit' or 'quit')"

    def get_priority(self) -> int:
        """High priority - should catch before tier processing."""
        return 40
