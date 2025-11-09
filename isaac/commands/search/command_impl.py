"""
Search Command - Standardized Implementation

Universal search combining glob (file finding) and grep (content search) with smart detection.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.tools import GlobTool, GrepTool


class SearchCommand(BaseCommand):
    """Unified search - find files or search content with smart detection"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute search command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with search results
        """
        parser = FlagParser(args)

        # Check for help
        if parser.has_flag('help', ['h']):
            return CommandResponse(
                success=True,
                data=self.get_help()
            )

        # Get all positional args for query parsing
        query_args = parser.get_all_positional()

        if not query_args:
            return CommandResponse(
                success=True,
                data=self.get_help()
            )

        # Parse query with "in" syntax support
        pattern, file_pattern = self._parse_search_query(query_args)

        # Get mode flag
        mode = parser.get_flag('mode', default='auto')
        path = parser.get_flag('path', default='.')

        # Determine search mode
        if mode == 'auto':
            search_mode = self._detect_search_mode(pattern, file_pattern)
        else:
            search_mode = mode

        # Execute appropriate search
        if search_mode == 'glob':
            return self._execute_glob_search(pattern, path)
        else:  # grep
            ignore_case = parser.has_flag('ignore-case', ['i'])
            context_lines = parser.get_flag('context', aliases=['C'], default=0)
            output_mode = parser.get_flag('output', default='files')

            # Convert context to int
            try:
                if isinstance(context_lines, str):
                    context_lines = int(context_lines)
            except ValueError:
                context_lines = 0

            return self._execute_grep_search(
                pattern, path, file_pattern, ignore_case, context_lines, output_mode
            )

    def _parse_search_query(self, args_list: List[str]) -> tuple:
        """
        Parse search query with support for "in" syntax.

        Examples:
            ["TODO"] → pattern="TODO", file_pattern=None
            ["TODO", "in", "*.py"] → pattern="TODO", file_pattern="*.py"
        """
        if "in" in args_list:
            in_index = args_list.index("in")
            pattern_parts = args_list[:in_index]
            file_pattern_parts = args_list[in_index + 1:]

            pattern = " ".join(pattern_parts)
            file_pattern = " ".join(file_pattern_parts) if file_pattern_parts else None
        else:
            pattern = " ".join(args_list)
            file_pattern = None

        return pattern, file_pattern

    def _detect_search_mode(self, pattern: str, file_pattern: str = None) -> str:
        """
        Intelligently detect search mode based on pattern.

        Returns:
            'glob' or 'grep'
        """
        # If file_pattern specified with "in", it's grep
        if file_pattern:
            return "grep"

        # Glob indicators: *, ?, **, [, ]
        glob_indicators = ["*", "?", "[", "]"]
        if any(indicator in pattern for indicator in glob_indicators):
            return "glob"

        # File extension patterns like ".py" or "*.py"
        if pattern.startswith(".") and "/" not in pattern:
            return "glob"

        # Path-like patterns
        if "/" in pattern or "\\" in pattern:
            return "glob"

        # Default to content search (grep)
        return "grep"

    def _execute_glob_search(self, pattern: str, path: str = ".") -> CommandResponse:
        """Execute file pattern search (glob mode)"""
        try:
            tool = GlobTool()
            result = tool.execute(pattern=pattern, path=path)

            if result["success"]:
                files = result.get("files", [])
                count = result.get("count", 0)

                if files:
                    output = f"Found {count} files:\n"
                    for file_info in files:
                        output += f"  {file_info['path']}\n"
                else:
                    output = "No files found"

                return CommandResponse(
                    success=True,
                    data=output,
                    metadata={
                        "mode": "glob",
                        "count": count,
                        "files": [f["path"] for f in files]
                    }
                )
            else:
                return CommandResponse(
                    success=False,
                    error=result.get("error", "Unknown error"),
                    metadata={"error_code": "GLOB_FAILED", "mode": "glob"}
                )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "EXECUTION_ERROR", "mode": "glob"}
            )

    def _execute_grep_search(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = None,
        ignore_case: bool = False,
        context: int = 0,
        output: str = "files"
    ) -> CommandResponse:
        """Execute content search (grep mode)"""
        output_mode_map = {
            "files": "files_with_matches",
            "content": "content",
            "count": "count"
        }

        try:
            tool = GrepTool()
            result = tool.execute(
                pattern=pattern,
                path=path,
                glob_pattern=file_pattern,
                ignore_case=ignore_case,
                context_lines=context,
                output_mode=output_mode_map.get(output, "files_with_matches")
            )

            if result["success"]:
                matches = result["matches"]
                output_text = ""

                if output == "files":
                    if matches:
                        output_text = f"Found in {len(matches)} files:\n"
                        for file in matches:
                            output_text += f"  {file}\n"
                    else:
                        output_text = "No matches found"

                elif output == "content":
                    if matches:
                        output_text = f"Found {len(matches)} matches:\n"
                        for match in matches:
                            output_text += f"\n{match['file']}:{match['line_number']}\n"
                            if context and "context_before" in match:
                                for line in match["context_before"]:
                                    output_text += f"  -  {line}\n"
                            output_text += f"  >  {match['content']}\n"
                            if context and "context_after" in match:
                                for line in match["context_after"]:
                                    output_text += f"  -  {line}\n"
                    else:
                        output_text = "No matches found"

                elif output == "count":
                    if matches:
                        output_text = "Match counts:\n"
                        for item in matches:
                            output_text += f"  {item['file']}: {item['count']}\n"
                    else:
                        output_text = "No matches found"

                return CommandResponse(
                    success=True,
                    data=output_text,
                    metadata={
                        "mode": "grep",
                        "matches": matches,
                        "total_files_searched": result.get("total_files_searched", 0),
                        "file_pattern": file_pattern
                    }
                )
            else:
                return CommandResponse(
                    success=False,
                    error=result.get("error", "Unknown error"),
                    metadata={"error_code": "GREP_FAILED", "mode": "grep"}
                )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "EXECUTION_ERROR", "mode": "grep"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="search",
            description="Universal search - find files or search content with smart detection",
            usage="/search <pattern> [in <file_pattern>] [options]",
            examples=[
                "/search \"*.py\"  # Find Python files",
                "/search \"TODO\"  # Search for TODO in content",
                "/search \"TODO\" in \"*.py\"  # Search TODO in Python files",
                "/search \"error\" --mode grep -i  # Case-insensitive content search",
                "/search \"function\" -C 3  # Show 3 lines of context"
            ],
            tier=1,  # Safe - read-only operation
            aliases=["s", "find"],
            category="file"
        )
