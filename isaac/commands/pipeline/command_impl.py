"""
Pipeline Command - Standardized Implementation

Intelligent workflow automation and pipeline management.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.commands.pipeline.pipeline_command import PipelineCommand as PipelineCommandLegacy


class PipelineCommand(BaseCommand):
    """Intelligent workflow automation and pipeline management"""

    def __init__(self):
        """Initialize pipeline command"""
        self.legacy_command = PipelineCommandLegacy()

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute pipeline command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with pipeline operation results
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
                metadata={"error_code": "PIPELINE_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="pipeline",
            description="Intelligent workflow automation and pipeline management",
            usage="/pipeline <action> [arguments]",
            examples=[
                "/pipeline list                           # List all pipelines",
                "/pipeline create \"Build App\" -d \"Build and test\"",
                "/pipeline create \"Deploy\" -t deploy   # Create from template",
                "/pipeline run build_app version=1.2.3   # Run pipeline with variables",
                "/pipeline status                         # Show execution status",
                "/pipeline templates                      # List available templates"
            ],
            tier=3,  # AI validation - can execute arbitrary workflows
            aliases=["pipelines", "workflow"],
            category="automation"
        )
