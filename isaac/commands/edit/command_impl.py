"""
Edit Command - Standardized Implementation

Edit files with exact string replacement using the standardized BaseCommand interface.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.tools import EditTool


class EditCommand(BaseCommand):
    """Edit files with exact string replacement"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute edit command.

        Args:
            args: Command arguments [file_path, old_string, new_string, --replace-all]
            context: Optional execution context

        Returns:
            CommandResponse with edit summary or error
        """
        parser = FlagParser(args)

        # Parse arguments
        file_path = parser.get_positional(0)
        old_string = parser.get_positional(1)
        new_string = parser.get_positional(2)
        replace_all = parser.get_flag('replace-all', default=False)

        # Validate
        if not file_path:
            return CommandResponse(
                success=False,
                error="File path required",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        if not old_string:
            return CommandResponse(
                success=False,
                error="Old string required",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        if not new_string:
            return CommandResponse(
                success=False,
                error="New string required",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        # Execute tool
        try:
            tool = EditTool()
            result = tool.execute(
                file_path=file_path,
                old_string=old_string,
                new_string=new_string,
                replace_all=replace_all
            )

            if result["success"]:
                # Prepare response
                replacements = result.get("replacements", 0)
                message = f"""Edited: {result['file_path']}
Replacements: {replacements}
  Old: {result.get('old_string', old_string)}
  New: {result.get('new_string', new_string)}"""

                metadata = {
                    "file_path": result["file_path"],
                    "replacements": replacements,
                    "old_string": old_string,
                    "new_string": new_string,
                    "replace_all": replace_all
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
                    metadata={"error_code": "EDIT_FAILED"}
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
            name="edit",
            description="Edit files with exact string replacement",
            usage="/edit <file_path> <old_string> <new_string> [--replace-all]",
            examples=[
                "/edit app.py 'old text' 'new text'",
                "/edit file.txt 'bug' 'fix' --replace-all",
                "/edit config.json '\"debug\": false' '\"debug\": true'",
                "/edit main.py 'TODO' 'DONE'"
            ],
            tier=2,  # Needs validation - modifies files
            aliases=["e", "sed"],
            category="file"
        )
