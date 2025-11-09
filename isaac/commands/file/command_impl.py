"""
File Command - Standardized Implementation

Unified file operations (read/write/edit/append) using the BaseCommand interface.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.tools import EditTool, ReadTool, WriteTool


class FileCommand(BaseCommand):
    """Unified file operations - read, write, edit, append"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute file command.

        Args:
            args: Command arguments
            context: Optional execution context (includes piped_input for stdin content)

        Returns:
            CommandResponse with file operation result
        """
        parser = FlagParser(args)

        # Determine operation based on flags or subcommand
        if parser.has_flag('help', ['h']):
            return CommandResponse(
                success=True,
                data=self.get_help()
            )

        # Check for subcommands (read, write, edit, append)
        operation = parser.get_positional(0)

        # Handle subcommands
        if operation in ['read', 'write', 'edit', 'append']:
            if operation == 'read':
                return self._cmd_read(parser, context)
            elif operation == 'write':
                return self._cmd_write(parser, context)
            elif operation == 'edit':
                return self._cmd_edit(parser, context)
            elif operation == 'append':
                return self._cmd_append(parser, context)
        else:
            # Smart mode - first positional is the file path
            return self._cmd_smart(parser, context)

    def _cmd_read(self, parser: FlagParser, context: Optional[Dict[str, Any]]) -> CommandResponse:
        """Read file operation"""
        file_path = parser.get_positional(1)  # After 'read' subcommand
        offset = parser.get_flag('offset', default=0)
        limit = parser.get_flag('limit', default=None)

        if not file_path:
            return CommandResponse(
                success=False,
                error="File path required for read operation",
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

        try:
            tool = ReadTool()
            result = tool.execute(file_path=file_path, offset=offset, limit=limit)

            if result["success"]:
                metadata = {
                    "file_path": result["file_path"],
                    "lines_read": result.get("lines_read", 0),
                    "total_lines": result.get("total_lines", 0),
                    "operation": "read"
                }

                if offset or limit:
                    metadata["offset"] = offset
                    metadata["limit"] = limit

                return CommandResponse(
                    success=True,
                    data=result["content"],
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

    def _cmd_write(self, parser: FlagParser, context: Optional[Dict[str, Any]]) -> CommandResponse:
        """Write file operation"""
        file_path = parser.get_positional(1)  # After 'write' subcommand
        content = parser.get_positional(2)  # Content argument
        overwrite = parser.has_flag('overwrite', ['f', 'force'])

        if not file_path:
            return CommandResponse(
                success=False,
                error="File path required for write operation",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        # Get content from args or piped input
        if content is None:
            if context and "piped_input" in context:
                content = context["piped_input"]
            else:
                return CommandResponse(
                    success=False,
                    error="No content provided. Use argument or pipe content.",
                    metadata={"error_code": "MISSING_CONTENT"}
                )

        try:
            tool = WriteTool()
            result = tool.execute(file_path=file_path, content=content, overwrite=overwrite)

            if result["success"]:
                output = f"File written: {result['file_path']} ({result['bytes_written']} bytes)"
                return CommandResponse(
                    success=True,
                    data=output,
                    metadata={
                        "file_path": result["file_path"],
                        "bytes_written": result["bytes_written"],
                        "operation": "write"
                    }
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

    def _cmd_edit(self, parser: FlagParser, context: Optional[Dict[str, Any]]) -> CommandResponse:
        """Edit file operation"""
        file_path = parser.get_positional(1)
        old_string = parser.get_positional(2)
        new_string = parser.get_positional(3)
        replace_all = parser.has_flag('replace-all', ['a', 'all'])

        if not file_path or not old_string or new_string is None:
            return CommandResponse(
                success=False,
                error="File path, old string, and new string required for edit operation",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        try:
            tool = EditTool()
            result = tool.execute(
                file_path=file_path,
                old_string=old_string,
                new_string=new_string,
                replace_all=replace_all
            )

            if result["success"]:
                output = f"Edited: {result['file_path']}\n"
                output += f"Replacements: {result['replacements']}\n"
                output += f"  Old: {result['old_string']}\n"
                output += f"  New: {result['new_string']}"

                return CommandResponse(
                    success=True,
                    data=output,
                    metadata={
                        "file_path": result["file_path"],
                        "replacements": result["replacements"],
                        "operation": "edit"
                    }
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

    def _cmd_append(self, parser: FlagParser, context: Optional[Dict[str, Any]]) -> CommandResponse:
        """Append to file operation"""
        file_path = parser.get_positional(1)
        content = parser.get_positional(2)

        if not file_path:
            return CommandResponse(
                success=False,
                error="File path required for append operation",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        # Get content from args or piped input
        if content is None:
            if context and "piped_input" in context:
                content = context["piped_input"]
            else:
                return CommandResponse(
                    success=False,
                    error="No content provided. Use argument or pipe content.",
                    metadata={"error_code": "MISSING_CONTENT"}
                )

        # Read existing content if file exists
        file_path_obj = Path(file_path)
        existing_content = ""
        if file_path_obj.exists():
            try:
                existing_content = file_path_obj.read_text()
            except Exception as e:
                return CommandResponse(
                    success=False,
                    error=f"Error reading file: {e}",
                    metadata={"error_code": "READ_ERROR"}
                )

        # Append content
        new_content = existing_content + content
        if not new_content.endswith("\n"):
            new_content += "\n"

        try:
            tool = WriteTool()
            result = tool.execute(file_path=file_path, content=new_content, overwrite=True)

            if result["success"]:
                output = f"Appended to: {result['file_path']} (+{len(content)} bytes)"
                return CommandResponse(
                    success=True,
                    data=output,
                    metadata={
                        "file_path": result["file_path"],
                        "bytes_appended": len(content),
                        "operation": "append"
                    }
                )
            else:
                return CommandResponse(
                    success=False,
                    error=result.get("error", "Unknown error"),
                    metadata={"error_code": "APPEND_FAILED"}
                )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "EXECUTION_ERROR"}
            )

    def _cmd_smart(self, parser: FlagParser, context: Optional[Dict[str, Any]]) -> CommandResponse:
        """Smart operation - auto-detect based on args"""
        file_path = parser.get_positional(0)
        content = parser.get_positional(1)

        if not file_path:
            return CommandResponse(
                success=True,
                data=self.get_help()
            )

        file_path_obj = Path(file_path)

        # If file exists and no content provided -> read
        if file_path_obj.exists() and content is None:
            # Use read operation
            read_parser = FlagParser(['read', file_path])
            return self._cmd_read(read_parser, context)

        # If content provided -> write
        elif content is not None:
            # Use write operation (smart mode always overwrites)
            write_parser = FlagParser(['write', file_path, content, '--overwrite'])
            return self._cmd_write(write_parser, context)

        # File doesn't exist and no content -> error
        else:
            return CommandResponse(
                success=False,
                error=f"File does not exist: {file_path}. Provide content to create it.",
                metadata={"error_code": "FILE_NOT_FOUND"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="file",
            description="Unified file operations - read, write, edit, append",
            usage="/file <operation> <path> [options]",
            examples=[
                "/file read myfile.py",
                "/file write newfile.txt \"Hello World\"",
                "/file edit app.py \"old\" \"new\"",
                "/file append log.txt \"New entry\"",
                "/file myfile.txt  # Smart mode: read if exists",
                "/file myfile.txt \"content\"  # Smart mode: write"
            ],
            tier=2,  # Needs validation - writes files
            aliases=["f"],
            category="file"
        )
