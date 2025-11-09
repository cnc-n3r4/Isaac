"""
Ambient Command - Standardized Implementation

Ambient intelligence interface providing access to proactive suggestions and learning features.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, CommandResponse
from isaac.commands.ambient.ambient_command import AmbientCommand as OriginalAmbientCommand


class AmbientCommand(BaseCommand):
    """Ambient intelligence features command"""

    def __init__(self):
        """Initialize ambient command"""
        self.original_command = OriginalAmbientCommand()

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute ambient command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with ambient intelligence output or error
        """
        try:
            # Execute original command
            result = self.original_command.execute(args)

            # Convert old format to new format
            return CommandResponse(
                success=result["success"],
                data=result["output"],
                metadata={
                    "exit_code": result.get("exit_code", 0)
                }
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
            name="ambient",
            description="Ambient intelligence features - proactive suggestions and learning",
            usage="/ambient <subcommand> [options]",
            examples=[
                "/ambient analyze",
                "/ambient suggestions",
                "/ambient patterns list",
                "/ambient stats",
                "/ambient learn"
            ],
            tier=2,  # Needs validation - accesses learning systems
            aliases=["ai", "suggest"],
            category="ai"
        )
