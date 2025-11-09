"""
Time Machine Command - Standardized Implementation

Timeline navigation, workspace snapshots, and version history.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.commands.timemachine.timemachine_command import TimeMachineCommand as TimeMachineCommandLegacy


class TimeMachineCommand(BaseCommand):
    """Timeline navigation and workspace snapshots"""

    def __init__(self):
        """Initialize time machine command"""
        self.legacy_command = TimeMachineCommandLegacy()

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute time machine command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with time machine operation results
        """
        try:
            # Execute legacy command
            result = self.legacy_command.execute(args)

            # Convert result format to CommandResponse
            return CommandResponse(
                success=result["success"],
                data=result["output"],
                metadata={"exit_code": result["exit_code"]}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "TIMEMACHINE_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="timemachine",
            description="Timeline navigation, workspace snapshots, and version history",
            usage="/timemachine <action> [arguments]",
            examples=[
                "/timemachine snapshot -d \"Before refactor\" # Create manual snapshot",
                "/timemachine timeline -f manual -l 10       # Show timeline",
                "/timemachine restore 5                      # Restore to entry #5",
                "/timemachine restore 1640995200             # Restore to timestamp",
                "/timemachine search \"database\"             # Search timeline",
                "/timemachine browse                         # Interactive browser",
                "/timemachine stats                          # Show statistics"
            ],
            tier=3,  # AI validation - can restore/modify workspace state
            aliases=["tm", "timeline", "history"],
            category="system"
        )
