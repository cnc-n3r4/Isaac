"""
Exit/Quit/Clear command strategy.
"""

import os
from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy


class ExitQuitStrategy(CommandStrategy):
    """Strategy for handling /exit, /quit, and /clear commands."""

    def can_handle(self, input_text: str) -> bool:
        """Check if command is /exit, /quit, or /clear."""
        return input_text in ["/exit", "/quit", "/clear"]

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Execute exit, quit, or clear command."""
        if input_text == "/clear":
            os.system("cls" if os.name == "nt" else "clear")
        # For /exit and /quit, just return success - the main loop will handle actual exit
        return CommandResult(success=True, output="", exit_code=0)

    def get_help(self) -> str:
        """Get help text for exit/quit/clear."""
        return "/exit, /quit - Exit Isaac\n/clear - Clear the screen"

    def get_priority(self) -> int:
        """High priority - special commands."""
        return 25
