"""
Meta command strategy - handles all other / commands via dispatcher.
"""

from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy


class MetaCommandStrategy(CommandStrategy):
    """Strategy for handling meta commands (/) via plugin dispatcher."""

    def can_handle(self, input_text: str) -> bool:
        """Check if command starts with /."""
        return input_text.startswith("/")

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Execute meta command using plugin dispatcher or PipeEngine for pipes."""
        try:
            # Check for pipes - use PipeEngine for all piping
            if "|" in input_text and not self._is_quoted_pipe(input_text):
                from isaac.core.pipe_engine import PipeEngine

                engine = PipeEngine(self.session, self.shell)
                result_blob = engine.execute_pipeline(input_text)

                # Validate blob structure
                if not isinstance(result_blob, dict):
                    return CommandResult(
                        success=False, 
                        output=f"Invalid pipe result: expected dict, got {type(result_blob).__name__}", 
                        exit_code=1
                    )
                
                if "kind" not in result_blob:
                    return CommandResult(
                        success=False, 
                        output=f"Invalid pipe result: missing 'kind' field. Got: {result_blob}", 
                        exit_code=1
                    )

                # Convert blob to CommandResult
                if result_blob["kind"] == "error":
                    return CommandResult(success=False, output=result_blob.get("content", "Unknown error"), exit_code=1)
                else:
                    return CommandResult(success=True, output=result_blob.get("content", ""), exit_code=0)
            else:
                # Single command - use dispatcher
                dispatcher = context.get("dispatcher")
                if not dispatcher:
                    return CommandResult(
                        success=False, output="Dispatcher not available", exit_code=1
                    )

                result = dispatcher.execute(input_text)

                # Convert dispatcher result to CommandResult
                if result.get("ok", False):
                    return CommandResult(success=True, output=result.get("stdout", ""), exit_code=0)
                else:
                    # Handle error case
                    error_info = result.get("error", {})
                    error_msg = (
                        error_info.get("message", "Unknown error")
                        if isinstance(error_info, dict)
                        else str(error_info)
                    )
                    return CommandResult(
                        success=False, output=f"Command failed: {error_msg}", exit_code=1
                    )

        except Exception as e:
            return CommandResult(
                success=False, output=f"Command execution error: {str(e)}", exit_code=1
            )

    def get_help(self) -> str:
        """Get help text for meta commands."""
        return "Meta commands: Use /help to see available commands"

    def get_priority(self) -> int:
        """Low priority - catch-all for / commands after specific handlers."""
        return 50

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
