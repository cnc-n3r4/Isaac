"""
Save Command - Standardized Implementation

Save piped data or content to files.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse


class SaveCommand(BaseCommand):
    """Save piped data or content to files"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute save command.

        Args:
            args: Command arguments [filename]
            context: Optional execution context with piped input

        Returns:
            CommandResponse with save result or error
        """
        parser = FlagParser(args)

        # Get filename from positional argument
        filename = parser.get_positional(0)

        if not filename:
            return CommandResponse(
                success=False,
                error="No filename provided. Usage: /save <filename>",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        # Get piped content from context if available
        content = ""
        kind = "text"

        if context:
            content = context.get("piped_input", "")
            kind = context.get("piped_kind", "text")

        # Save content to file
        try:
            result = self._save_content(content, filename, kind)
            return CommandResponse(
                success=True,
                data=result,
                metadata={
                    "saved_file": filename,
                    "content_kind": kind,
                    "content_length": len(content)
                }
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error saving to {filename}: {e}",
                metadata={"error_code": "SAVE_ERROR", "filename": filename}
            )

    def _save_content(self, content: str, filename: str, kind: str = "text") -> str:
        """
        Save content to a file.

        Args:
            content: Content to save
            filename: Target filename
            kind: Content type (text, binary, json)

        Returns:
            Success message with file path
        """
        # Expand user home directory if needed
        expanded_path = Path(filename).expanduser()

        # Create directory if it doesn't exist
        expanded_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine file mode based on content kind
        mode = "w"
        if kind in ["binary", "json"] and isinstance(content, str):
            # For binary/json content that comes as string, we still write as text
            mode = "w"
        elif kind == "binary":
            mode = "wb"

        # Write content to file
        with open(expanded_path, mode, encoding="utf-8" if mode == "w" else None) as f:
            f.write(content)

        return f"Content saved to: {expanded_path}"

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="save",
            description="Save piped data or content to files",
            usage="/save <filename>",
            examples=[
                "/read file.txt | /save output.txt",
                "/grep pattern *.py | /save results.txt",
                "/save saved_output.txt",
                "/ls | /save directory_listing.txt"
            ],
            tier=2,  # Needs validation - creates files
            aliases=["write", "output"],
            category="file"
        )
