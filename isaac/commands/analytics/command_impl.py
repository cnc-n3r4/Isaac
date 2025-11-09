"""
Analytics Command - Standardized Implementation

Comprehensive analytics interface for Isaac.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, CommandResponse
from isaac.commands.analytics.analytics_command import AnalyticsCommand as OriginalAnalyticsCommand


class AnalyticsCommand(BaseCommand):
    """Analytics and metrics command"""

    def __init__(self):
        """Initialize analytics command"""
        self.original_command = OriginalAnalyticsCommand()

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute analytics command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with analytics output or error
        """
        try:
            # Execute original command
            output = self.original_command.execute(args)

            # Original command returns string directly
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
            name="analytics",
            description="Comprehensive analytics system - productivity, quality, learning, and team metrics",
            usage="/analytics <subcommand> [options]",
            examples=[
                "/analytics summary",
                "/analytics dashboard overview",
                "/analytics productivity 14",
                "/analytics quality 7",
                "/analytics insights",
                "/analytics export full html report.html"
            ],
            tier=1,  # Safe - read-only analytics
            aliases=["stats", "metrics"],
            category="analytics"
        )
