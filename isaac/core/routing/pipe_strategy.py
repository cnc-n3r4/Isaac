"""
Pipe command strategy - handles commands with pipe operators.
"""

from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy


class PipeStrategy(CommandStrategy):
    """Strategy for handling pipe commands (|)."""

    def can_handle(self, input_text: str) -> bool:
        """Check if command contains pipes (not in quotes)."""
        return "|" in input_text and not self._is_quoted_pipe(input_text)

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Execute pipeline using PipeEngine."""
        from isaac.core.pipe_engine import PipeEngine

        engine = PipeEngine(self.session, self.shell)
        result_blob = engine.execute_pipeline(input_text)

        # Convert blob to CommandResult
        if result_blob["kind"] == "error":
            return CommandResult(success=False, output=result_blob["content"], exit_code=1)
        else:
            return CommandResult(success=True, output=result_blob["content"], exit_code=0)

    def get_help(self) -> str:
        """Get help text for pipe commands."""
        return "Pipe commands: Use | to chain commands together (e.g., 'ls | grep pattern')"

    def get_priority(self) -> int:
        """High priority - pipes should be detected early."""
        return 10

    def _is_quoted_pipe(self, cmd: str) -> bool:
        """Check if all pipes are inside quotes."""
        in_quotes = False
        quote_char = None

        for char in cmd:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == "|" and not in_quotes:
                return False  # Found pipe outside quotes

        return True  # All pipes are quoted
