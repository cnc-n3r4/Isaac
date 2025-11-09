"""
Pair Command - Standardized Implementation

Collaborative pair programming features with AI assistance.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.commands.pair.pair_command import PairCommand as PairCommandLegacy
from isaac.core.session_manager import SessionManager


class PairCommand(BaseCommand):
    """Collaborative pair programming with AI"""

    def __init__(self):
        """Initialize pair command"""
        self.session_manager = SessionManager()
        self.legacy_command = PairCommandLegacy(self.session_manager)

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute pair command.

        Args:
            args: Command arguments
            context: Optional execution context with session data

        Returns:
            CommandResponse with pair operation results
        """
        try:
            # Execute legacy command
            result = self.legacy_command.execute(args)

            # Cleanup
            self.legacy_command.cleanup()

            # Convert result format to CommandResponse
            return CommandResponse(
                success=result["success"],
                data=result["output"],
                metadata={"exit_code": result["exit_code"]}
            )

        except KeyboardInterrupt:
            return CommandResponse(
                success=False,
                error="Operation cancelled",
                metadata={"error_code": "CANCELLED"}
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "PAIR_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="pair",
            description="Collaborative pair programming with AI assistance",
            usage="/pair [start|end|switch|tasks|divide|review|suggest|learn|metrics|history]",
            examples=[
                "/pair                                # Show current pairing status",
                "/pair start \"Implement authentication\" # Start new pairing session",
                "/pair start \"Fix bug\" --style ping-pong --role driver",
                "/pair divide \"Add payment integration\" # Divide task into subtasks",
                "/pair review src/main.py            # Review code in file",
                "/pair switch                        # Switch roles",
                "/pair metrics                       # Show pairing metrics"
            ],
            tier=2,  # Needs validation - creates sessions and modifies state
            aliases=["pairing"],
            category="ai"
        )
