"""
Resources Command - Standardized Implementation

Resource optimization, monitoring, and management.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.commands.resources.resources_command import ResourcesCommand as ResourcesCommandLegacy


class ResourcesCommand(BaseCommand):
    """Resource optimization and monitoring"""

    def __init__(self):
        """Initialize resources command"""
        self.legacy_command = ResourcesCommandLegacy()

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute resources command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with resource operation results
        """
        try:
            # Execute legacy command (expects string or list)
            result = self.legacy_command.execute(args)

            # Result is a string output
            return CommandResponse(
                success=True,
                data=result,
                metadata={}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "RESOURCES_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="resources",
            description="Resource optimization, monitoring, and management",
            usage="/resources <subcommand> [options]",
            examples=[
                "/resources monitor              # Show current resource usage",
                "/resources monitor --verbose    # Show detailed resource info",
                "/resources optimize             # Get optimization suggestions",
                "/resources cleanup docker --confirm  # Clean Docker resources",
                "/resources predict cpu --minutes 120  # Predict CPU usage",
                "/resources costs summary --days 7     # Show cost summary",
                "/resources alerts list          # List active resource alerts",
                "/resources start                # Start background monitoring"
            ],
            tier=3,  # AI validation - can execute cleanup operations
            aliases=["resource", "res"],
            category="system"
        )
