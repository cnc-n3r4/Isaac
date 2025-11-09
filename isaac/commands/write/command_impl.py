"""
Write Command - Standardized Implementation

Create new files using the standardized BaseCommand interface.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.tools import WriteTool


class WriteCommand(BaseCommand):
    """Create new files with content"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute write command.

        Args:
            args: Command arguments [file_path, content, --overwrite]
            context: Optional execution context (may contain piped_input)

        Returns:
            CommandResponse with success message or error
        """
        parser = FlagParser(args)

        # Parse arguments
        file_path = parser.get_positional(0)
        content = parser.get_positional(1)
        overwrite = parser.get_flag('overwrite', default=False)

        # Check for piped content
        if content is None and context and "piped_input" in context:
            content = context["piped_input"]

        # Validate
        if not file_path:
            return CommandResponse(
                success=False,
                error="File path required",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        if content is None:
            return CommandResponse(
                success=False,
                error="Content required. Provide as argument or pipe from another command.",
                metadata={"error_code": "MISSING_CONTENT"}
            )

        # Execute tool
        try:
            tool = WriteTool()
            result = tool.execute(
                file_path=file_path,
                content=content,
                overwrite=overwrite
            )

            if result["success"]:
                # Prepare response
                message = f"File written: {result['file_path']} ({result.get('bytes_written', 0)} bytes)"

                metadata = {
                    "file_path": result["file_path"],
                    "bytes_written": result.get("bytes_written", 0),
                    "overwrite": overwrite
                }

                return CommandResponse(
                    success=True,
                    data=message,
                    metadata=metadata
                )
            else:
                return CommandResponse(
                    success=False,
                    error=result.get("error", "Unknown error"),
                    metadata={"error_code": "WRITE_FAILED"}
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
            name="write",
            description="Create new files with content",
            usage="/write <file_path> <content> [--overwrite]",
            examples=[
                "/write newfile.txt 'Hello World'",
                "/write config.json '{\"key\": \"value\"}' --overwrite",
                "echo 'test content' | /write output.txt",
                "/read input.txt | /write output.txt"
            ],
            tier=2,  # Needs validation - creates/modifies files
            aliases=["w"],
            category="file"
        )
