"""
Force execution strategy - bypasses AI validation.
"""

from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy


class ForceExecutionStrategy(CommandStrategy):
    """Strategy for handling force execution commands (/f or /force)."""

    def can_handle(self, input_text: str) -> bool:
        """Check if command starts with /f or /force."""
        return input_text.startswith("/f ") or input_text.startswith("/force ")

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Execute command directly, bypassing AI validation."""
        # Extract actual command (skip /f or /force prefix)
        if input_text.startswith("/f "):
            actual_command = input_text[3:].lstrip()  # Skip '/f ' and any extra spaces
        else:
            actual_command = input_text[7:].lstrip()  # Skip '/force ' and any extra spaces

        print(f"Isaac > Force executing (bypassing AI validation): {actual_command}")
        return self.shell.execute(actual_command)

    def get_help(self) -> str:
        """Get help text for force execution."""
        return "Force execution: /f <command> or /force <command> (bypasses AI validation)"

    def get_priority(self) -> int:
        """High priority - force execution should be detected early."""
        return 20
