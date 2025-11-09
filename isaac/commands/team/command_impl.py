"""
Team Command - Standardized Implementation

Team collaboration and shared resource management.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.commands.team.team_command import TeamCommand as TeamCommandLegacy


class TeamCommand(BaseCommand):
    """Team collaboration and shared resource management"""

    def __init__(self):
        """Initialize team command"""
        self.legacy_command = TeamCommandLegacy()

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute team command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with team operation results
        """
        try:
            # Execute legacy command (returns string output)
            result = self.legacy_command.run(args)

            return CommandResponse(
                success=True,
                data=result,
                metadata={}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "TEAM_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="team",
            description="Team collaboration and shared resource management",
            usage="/team <subcommand> [arguments]",
            examples=[
                "/team create MyTeam \"A collaborative team\"  # Create new team",
                "/team list                                   # List your teams",
                "/team invite <team_id> <user> <email> --role write",
                "/team share <team_id> workspace <bubble_id> # Share workspace",
                "/team resources <team_id>                   # List shared resources",
                "/team members <team_id>                     # List team members"
            ],
            tier=2,  # Needs validation - manages team data and permissions
            aliases=["teams", "collab"],
            category="collaboration"
        )
