"""
AR/VR Command - Standardized Implementation

AR/VR preparation features and spatial computing interface.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, CommandResponse
from isaac.commands.arvr.arvr_command import ARVRCommand as OriginalARVRCommand


class ARVRCommand(BaseCommand):
    """AR/VR features command"""

    def __init__(self):
        """Initialize AR/VR command"""
        self.original_command = OriginalARVRCommand()

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute AR/VR command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with AR/VR output or error
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
            name="arvr",
            description="AR/VR preparation features - spatial computing, workspaces, and multimodal input",
            usage="/arvr <subcommand> [options]",
            examples=[
                "/arvr workspace create my_workspace",
                "/arvr layout create my_layout circular Item1,Item2,Item3",
                "/arvr gesture simulate swipe",
                "/arvr platform init terminal",
                "/arvr demo interactive",
                "/arvr status"
            ],
            tier=1,  # Safe - visualization and preparation features
            aliases=["vr", "spatial"],
            category="arvr"
        )
