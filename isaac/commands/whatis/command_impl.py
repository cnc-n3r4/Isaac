"""
Whatis Command - Standardized Implementation

Display brief one-line command descriptions.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.core.man_pages import get_generator


class WhatisCommand(BaseCommand):
    """Display brief one-line command descriptions"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute whatis command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with command description
        """
        try:
            parser = FlagParser(args)
            command = parser.get_positional(0, "")

            if not command:
                return CommandResponse(
                    success=False,
                    error="Usage: /whatis <command>",
                    metadata={"error_code": "MISSING_COMMAND"}
                )

            # Get one-line summary
            generator = get_generator()
            summary = generator.whatis(command)

            if summary:
                return CommandResponse(
                    success=True,
                    data=summary,
                    metadata={"command": command}
                )
            else:
                return CommandResponse(
                    success=False,
                    error=f"{command}: nothing appropriate",
                    metadata={"error_code": "NOT_FOUND", "command": command}
                )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "WHATIS_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="whatis",
            description="Display brief one-line command descriptions",
            usage="/whatis <command>",
            examples=[
                "/whatis config     # Show brief description of config command",
                "/whatis mine       # Show brief description of mine command",
                "/whatis help       # Show brief description of help command"
            ],
            tier=1,  # Safe - read-only information
            aliases=["what"],
            category="general"
        )
