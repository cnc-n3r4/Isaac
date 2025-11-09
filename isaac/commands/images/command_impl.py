"""
Images Command - Standardized Implementation

Cloud image storage with history, search, and OCR capabilities.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse


class ImagesCommand(BaseCommand):
    """Image processing and cloud storage command"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute images command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with images output or error
        """
        parser = FlagParser(args)

        # Parse arguments
        action = parser.get_flag("action", default="history")
        query = parser.get_flag("query")
        checksum = parser.get_flag("checksum")
        limit_str = parser.get_flag("limit", default="10")

        try:
            limit = int(limit_str)
        except ValueError:
            limit = 10

        # Build args for original implementation
        sys.argv = ["images", "--action", action]
        if query:
            sys.argv.extend(["--query", query])
        if checksum:
            sys.argv.extend(["--checksum", checksum])
        sys.argv.extend(["--limit", str(limit)])

        try:
            # Import and call original main function
            from isaac.commands.images import run

            # Capture output
            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                exit_code = run.main()

            output = f.getvalue()

            return CommandResponse(
                success=(exit_code == 0 or exit_code is None),
                data=output,
                metadata={"action": action}
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
            name="images",
            description="Image processing - cloud storage, history, search, and OCR",
            usage="/images [--action <action>] [--query <query>] [--checksum <checksum>] [--limit <n>]",
            examples=[
                "/images",
                "/images --action history --limit 20",
                "/images --action search --query 'diagram'",
                "/images --action ocrsearch --query 'error message'",
                "/images --action info --checksum abc123def"
            ],
            tier=1,  # Safe - read-only image browsing
            aliases=["img", "pics"],
            category="file"
        )
