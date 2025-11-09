"""
Agentic mode strategy - handles "isaac agent:" commands.
"""

from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy


class AgenticModeStrategy(CommandStrategy):
    """Strategy for handling agentic mode commands."""

    def can_handle(self, input_text: str) -> bool:
        """Check if command starts with 'isaac agent:' or 'isaac agentic:'."""
        lower = input_text.lower()
        return lower.startswith("isaac agent:") or lower.startswith("isaac agentic:")

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Execute agentic task via orchestrator."""
        agentic_query = input_text.split(":", 1)[1].strip()  # Remove "isaac agent:" prefix

        from isaac.core.agentic_orchestrator import AgenticOrchestrator
        from isaac.ui.progress_indicator import ProgressIndicator, ProgressStyle
        from isaac.ui.streaming_display import StreamingDisplay

        # Initialize UI components
        display = StreamingDisplay()
        progress = ProgressIndicator(style=ProgressStyle.SPINNER)

        # Initialize orchestrator with UI components
        orchestrator = AgenticOrchestrator(
            session_mgr=self.session, streaming_display=display, progress_indicator=progress
        )

        # Execute agentic task
        return orchestrator.execute_agentic_task_sync(agentic_query)

    def get_help(self) -> str:
        """Get help text for agentic mode."""
        return "Agentic mode: isaac agent: <task> - Execute task with autonomous agent"

    def get_priority(self) -> int:
        """High priority - special mode."""
        return 46
