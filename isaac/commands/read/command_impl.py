"""
Read Command - Standardized Implementation

Read files with line numbers using the standardized BaseCommand interface.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.tools import ReadTool


class ReadCommand(BaseCommand):
    """Read files with line numbers and optional offset/limit"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute read command.

        Args:
            args: Command arguments [file_path, --offset N, --limit N]
            context: Optional execution context

        Returns:
            CommandResponse with file content or error
        """
        parser = FlagParser(args)

        # Parse arguments
        file_path = parser.get_positional(0)
        offset = parser.get_flag('offset', default=0)
        limit = parser.get_flag('limit', default=None)

        # Validate
        if not file_path:
            return CommandResponse(
                success=False,
                error="File path required",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        # Convert string flags to int
        try:
            if isinstance(offset, str):
                offset = int(offset)
            if limit is not None and isinstance(limit, str):
                limit = int(limit)
        except ValueError as e:
            return CommandResponse(
                success=False,
                error=f"Invalid numeric argument: {e}",
                metadata={"error_code": "INVALID_ARGUMENT"}
            )

        # Execute tool
        try:
            tool = ReadTool()
            result = tool.execute(file_path=file_path, offset=offset, limit=limit)

            if result["success"]:
                # Prepare response data
                content = result["content"]

                # Add metadata
                metadata = {
                    "file_path": result["file_path"],
                    "lines_read": result.get("lines_read", 0),
                    "total_lines": result.get("total_lines", 0),
                }

                if offset or limit:
                    metadata["offset"] = offset
                    metadata["limit"] = limit

                return CommandResponse(
                    success=True,
                    data=content,
                    metadata=metadata
                )
            else:
                return CommandResponse(
                    success=False,
                    error=result.get("error", "Unknown error"),
                    metadata={"error_code": "READ_FAILED"}
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
            name="read",
            description="Read contents of a file with line numbers",
            usage="/read <file_path> [--offset N] [--limit N]",
            examples=[
                "/read config.json",
                "/read log.txt --limit 50",
                "/read myfile.py --offset 100",
                "/read data.txt --offset 100 --limit 50"
            ],
            tier=1,  # Safe - read-only operation
            aliases=["r", "cat"],
            category="file"
        )
