"""
Task mode strategy - handles "isaac task:" commands.
"""

from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy


class TaskModeStrategy(CommandStrategy):
    """Strategy for handling task mode commands."""

    def can_handle(self, input_text: str) -> bool:
        """Check if command starts with 'isaac task:'."""
        return input_text.lower().startswith("isaac task:")

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Execute task via task planner."""
        task_desc = input_text[11:].strip()  # Remove "isaac task:"

        from isaac.ai.task_planner import execute_task

        return execute_task(task_desc, self.shell, self.session)

    def get_help(self) -> str:
        """Get help text for task mode."""
        return "Task mode: isaac task: <description> - Execute complex multi-step tasks"

    def get_priority(self) -> int:
        """High priority - special mode."""
        return 45
