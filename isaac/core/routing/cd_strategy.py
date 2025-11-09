"""
CD (change directory) command strategy.
"""

import os
from pathlib import Path
from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy


class CdStrategy(CommandStrategy):
    """Strategy for handling cd (change directory) commands."""

    def can_handle(self, input_text: str) -> bool:
        """Check if command is cd."""
        stripped = input_text.strip()
        return stripped.startswith("cd ") or stripped == "cd"

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Execute cd command - changes Isaac's working directory."""
        parts = input_text.strip().split(maxsplit=1)
        if len(parts) == 1:
            # Just 'cd' - go to home directory
            target = str(Path.home())
        else:
            target = parts[1].strip('"').strip("'")  # Remove quotes
            # Expand ~ and environment variables
            target = os.path.expanduser(target)
            target = os.path.expandvars(target)

        try:
            os.chdir(target)
            new_dir = os.getcwd()
            return CommandResult(success=True, output=new_dir, exit_code=0)
        except Exception as e:
            return CommandResult(success=False, output=f"cd: {e}", exit_code=1)

    def get_help(self) -> str:
        """Get help text for cd command."""
        return "Change directory: cd <path> or cd (go to home)"

    def get_priority(self) -> int:
        """High priority - cd should be handled before general commands."""
        return 15
