"""
Bubble Command - Standardized Implementation

Workspace state management and bubble visualization.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.bubbles import BubbleManager


class BubbleCommand(BaseCommand):
    """Workspace bubble management command"""

    def __init__(self):
        """Initialize bubble command"""
        self.manager = BubbleManager()

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute bubble command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with bubble output or error
        """
        parser = FlagParser(args)

        # Get action (first positional argument)
        action = parser.get_positional(0)

        if not action:
            return CommandResponse(
                success=False,
                error="Action required. Use: create, list, show, restore, delete, export, import, suspend, resume, version, versions",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        try:
            # Build args dict from parser
            args_dict = {
                "action": action,
                "name": parser.get_flag("name"),
                "description": parser.get_flag("description"),
                "bubble_id": parser.get_flag("bubble-id", aliases=["bubble_id"]),
                "tags": parser.get_flag("tags"),
                "file": parser.get_flag("file"),
                "suspend_processes": parser.get_flag("suspend-processes", default=False),
            }

            # Import the original BubbleCommand class logic
            from isaac.commands.bubble.run import BubbleCommand as OriginalBubbleCommand

            original_command = OriginalBubbleCommand()
            output = original_command.execute(args_dict)

            return CommandResponse(
                success=True,
                data=output,
                metadata={}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "EXECUTION_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="bubble",
            description="Workspace state management - create, restore, and manage workspace bubbles",
            usage="/bubble <action> [options]",
            examples=[
                "/bubble create --name my_work --description 'Project work'",
                "/bubble list",
                "/bubble show --bubble-id abc123",
                "/bubble restore --bubble-id abc123",
                "/bubble export --bubble-id abc123 --file backup.json",
                "/bubble suspend --bubble-id abc123"
            ],
            tier=2,  # Needs validation - captures and modifies system state
            aliases=["ws", "workspace-state"],
            category="workspace"
        )
