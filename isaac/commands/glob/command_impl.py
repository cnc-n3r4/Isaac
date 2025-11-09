"""
Glob Command - Standardized Implementation

Find files by pattern matching using the standardized BaseCommand interface.
"""

import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.tools import GlobTool


class GlobCommand(BaseCommand):
    """Find files by pattern matching"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute glob command.

        Args:
            args: Command arguments [pattern, --path]
            context: Optional execution context

        Returns:
            CommandResponse with list of matching files or error
        """
        parser = FlagParser(args)

        # Parse arguments
        pattern = parser.get_positional(0)
        path = parser.get_flag('path', default=None)

        # Validate
        if not pattern:
            return CommandResponse(
                success=False,
                error="Pattern required",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        # Execute tool
        try:
            tool = GlobTool()
            result = tool.execute(pattern=pattern, path=path)

            if result["success"]:
                files = result.get("files", [])
                count = result.get("count", 0)

                # Format output
                if count > 0:
                    output = f"Found {count} files:\n"
                    output += "\n".join(f"  {file_info['path']}" for file_info in files)
                else:
                    output = "No files found"

                # Extract file paths for structured data
                file_paths = [f["path"] for f in files]

                metadata = {
                    "pattern": pattern,
                    "path": path or str(Path.cwd()),
                    "count": count,
                    "files": file_paths
                }

                return CommandResponse(
                    success=True,
                    data=output,
                    metadata=metadata
                )
            else:
                return CommandResponse(
                    success=False,
                    error=result.get("error", "Unknown error"),
                    metadata={"error_code": "GLOB_FAILED"}
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
            name="glob",
            description="Find files by pattern matching",
            usage="/glob <pattern> [--path DIR]",
            examples=[
                "/glob '**/*.py'",
                "/glob 'src/**/*.js' --path ~/project",
                "/glob '*.md'",
                "/glob 'tests/**/*.test.js'",
                "/glob '*.{js,ts}' --path src"
            ],
            tier=1,  # Safe - read-only file listing
            aliases=["find-files", "ls-pattern"],
            category="file"
        )
