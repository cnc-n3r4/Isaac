"""
Grep Command - Standardized Implementation

Search files for regex patterns using the standardized BaseCommand interface.
"""

import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.tools import GrepTool


class GrepCommand(BaseCommand):
    """Search files for regex patterns"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute grep command.

        Args:
            args: Command arguments [pattern, --path, --glob, --ignore-case, --context, --output]
            context: Optional execution context

        Returns:
            CommandResponse with search results or error
        """
        parser = FlagParser(args)

        # Parse arguments
        pattern = parser.get_positional(0)
        path = parser.get_flag('path', default='.')
        glob_pattern = parser.get_flag('glob', default=None)
        ignore_case = parser.get_flag('ignore-case', default=False, aliases=['i'])
        context_lines = parser.get_flag('context', default=0, aliases=['C'])
        output_mode = parser.get_flag('output', default='files')

        # Validate
        if not pattern:
            return CommandResponse(
                success=False,
                error="Pattern required",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        # Convert string flags to appropriate types
        try:
            if isinstance(context_lines, str):
                context_lines = int(context_lines)
        except ValueError as e:
            return CommandResponse(
                success=False,
                error=f"Invalid context value: {e}",
                metadata={"error_code": "INVALID_ARGUMENT"}
            )

        # Map output mode
        output_mode_map = {
            "files": "files_with_matches",
            "content": "content",
            "count": "count"
        }
        tool_output_mode = output_mode_map.get(output_mode, "files_with_matches")

        # Execute tool
        try:
            tool = GrepTool()
            result = tool.execute(
                pattern=pattern,
                path=path,
                glob_pattern=glob_pattern,
                ignore_case=ignore_case,
                context_lines=context_lines,
                output_mode=tool_output_mode
            )

            if result["success"]:
                matches = result.get("matches", [])

                # Format output based on mode
                if output_mode == "files":
                    if matches:
                        output = f"Found in {len(matches)} files:\n"
                        output += "\n".join(f"  {file}" for file in matches)
                    else:
                        output = "No matches found"

                elif output_mode == "content":
                    if matches:
                        output = f"Found {len(matches)} matches:\n\n"
                        match_lines = []
                        for match in matches:
                            match_lines.append(f"{match['file']}:{match.get('line_number', '?')}")
                            if context_lines and "context_before" in match:
                                for line in match["context_before"]:
                                    match_lines.append(f"  -  {line}")
                            match_lines.append(f"  >  {match.get('content', '')}")
                            if context_lines and "context_after" in match:
                                for line in match["context_after"]:
                                    match_lines.append(f"  -  {line}")
                            match_lines.append("")  # Empty line between matches
                        output = output + "\n".join(match_lines)
                    else:
                        output = "No matches found"

                elif output_mode == "count":
                    if matches:
                        output = "Match counts:\n"
                        output += "\n".join(
                            f"  {item['file']}: {item['count']}" for item in matches
                        )
                    else:
                        output = "No matches found"
                else:
                    output = json.dumps(matches, indent=2)

                # Add summary
                total_files = result.get("total_files_searched", 0)
                output += f"\n\n[Searched {total_files} files]"

                metadata = {
                    "pattern": pattern,
                    "total_files_searched": total_files,
                    "match_count": len(matches),
                    "output_mode": output_mode,
                    "path": path
                }

                if glob_pattern:
                    metadata["glob_pattern"] = glob_pattern

                return CommandResponse(
                    success=True,
                    data=output,
                    metadata=metadata
                )
            else:
                return CommandResponse(
                    success=False,
                    error=result.get("error", "Unknown error"),
                    metadata={"error_code": "GREP_FAILED"}
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
            name="grep",
            description="Search files for regex patterns",
            usage="/grep <pattern> [--path DIR] [--glob PATTERN] [--ignore-case] [--context N] [--output MODE]",
            examples=[
                "/grep 'TODO'",
                "/grep 'error' --glob '*.log'",
                "/grep 'function' --glob '*.py' --context 3",
                "/grep 'pattern' --ignore-case",
                "/grep 'import' --output content",
                "/grep 'class' --path src --glob '*.py'"
            ],
            tier=1,  # Safe - read-only search operation
            aliases=["search", "find-text"],
            category="file"
        )
