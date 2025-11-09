"""
Apropos Command - Standardized Implementation

Search manual pages by keyword.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.core.man_pages import get_generator


class AproposCommand(BaseCommand):
    """Search manual pages by keyword"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute apropos command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with search results
        """
        try:
            parser = FlagParser(args)
            keyword = parser.get_positional(0, "")

            if not keyword:
                return CommandResponse(
                    success=False,
                    error="Usage: /apropos <keyword>",
                    metadata={"error_code": "MISSING_KEYWORD"}
                )

            # Search for commands
            generator = get_generator()
            results = generator.search(keyword)

            if not results:
                return CommandResponse(
                    success=True,
                    data=f"No matches found for: {keyword}",
                    metadata={"keyword": keyword, "matches": 0}
                )

            # Display results
            output = []
            output.append(f"Commands matching '{keyword}':")
            output.append("━" * 70)
            output.append("")

            for result in results:
                trigger = result["trigger"]
                version = result["version"]
                summary = result["summary"]

                # Truncate long summaries
                if len(summary) > 50:
                    summary = summary[:47] + "..."

                output.append(f"{trigger:<20} ({version})  - {summary}")

            output.append("")
            output.append(f"Found {len(results)} match(es)")
            output.append("Use '/man <command>' for detailed information")

            return CommandResponse(
                success=True,
                data="\n".join(output),
                metadata={"keyword": keyword, "matches": len(results)}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "APROPOS_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="apropos",
            description="Search manual pages by keyword",
            usage="/apropos <keyword>",
            examples=[
                "/apropos config    # Search for commands related to 'config'",
                "/apropos ai        # Search for AI-related commands",
                "/apropos debug     # Search for debugging commands"
            ],
            tier=1,  # Safe - read-only search
            aliases=["search-man"],
            category="general"
        )
