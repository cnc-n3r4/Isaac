"""
Learn Command - Standardized Implementation

Self-improving learning system interface for Isaac.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, CommandResponse
from isaac.commands.learn.learn_command import LearnCommand as OriginalLearnCommand


class LearnCommand(BaseCommand):
    """Learning system command"""

    def __init__(self):
        """Initialize learn command"""
        self.original_command = OriginalLearnCommand()

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute learn command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with learning output or error
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
        finally:
            # Always cleanup
            if hasattr(self.original_command, 'cleanup'):
                self.original_command.cleanup()

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="learn",
            description="Self-improving learning system - mistakes, patterns, behavior, and preferences",
            usage="/learn [subcommand] [options]",
            examples=[
                "/learn",
                "/learn stats",
                "/learn mistakes 20",
                "/learn patterns",
                "/learn behavior",
                "/learn metrics 30",
                "/learn track command_error 'typo' 'correct command'"
            ],
            tier=2,  # Needs validation - accesses learning data
            aliases=["learning", "self-improve"],
            category="ai"
        )
