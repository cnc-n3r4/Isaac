"""
File Operation Tools - Read, Write, Edit
Cross-platform file tools using pathlib
"""

from pathlib import Path
from typing import Dict, Any, Optional
from .base import BaseTool


class ReadTool(BaseTool):
    """Read files with line numbers - cross-platform"""

    @property
    def name(self) -> str:
        return "read"

    @property
    def description(self) -> str:
        return "Read file contents with line numbers. Supports offset and limit for large files."

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to file (absolute or relative)"
                },
                "offset": {
                    "type": "integer",
                    "description": "Line number to start from (0-indexed)",
                    "default": 0
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read",
                    "default": None
                }
            },
            "required": ["file_path"]
        }

    def execute(self, file_path: str, offset: int = 0, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Read file with optional offset/limit.

        Args:
            file_path: Path to file (absolute or relative)
            offset: Line number to start from (0-indexed)
            limit: Maximum number of lines to read

        Returns:
            dict: {
                'success': True,
                'content': 'file content with line numbers',
                'lines_read': 100,
                'total_lines': 500,
                'file_path': '/absolute/path/to/file'
            }
        """
        # Convert to Path object (cross-platform)
        try:
            path = Path(file_path).expanduser().resolve()
        except Exception as e:
            return {
                'success': False,
                'error': f'Invalid file path: {e}'
            }

        # Check exists
        if not path.exists():
            return {
                'success': False,
                'error': f'File not found: {file_path}'
            }

        if not path.is_file():
            return {
                'success': False,
                'error': f'Not a file: {file_path}'
            }

        # Read file (handles line endings automatically)
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            total_lines = len(lines)

            # Apply offset/limit
            if offset:
                lines = lines[offset:]
            if limit:
                lines = lines[:limit]

            # Format with line numbers (1-indexed for user)
            formatted = []
            start_line = offset + 1
            for i, line in enumerate(lines):
                line_num = start_line + i
                # Remove trailing newline for consistent display
                formatted.append(f"{line_num:6d}→{line.rstrip()}")

            return {
                'success': True,
                'content': '\n'.join(formatted),
                'lines_read': len(lines),
                'total_lines': total_lines,
                'file_path': str(path)
            }
        except UnicodeDecodeError:
            return {
                'success': False,
                'error': f'File is not text or uses unsupported encoding: {file_path}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error reading file: {e}'
            }


class WriteTool(BaseTool):
    """Write new files - cross-platform"""

    @property
    def name(self) -> str:
        return "write"

    @property
    def description(self) -> str:
        return "Create new file with content. Creates parent directories if needed."

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to file to create"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to file"
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "Allow overwriting existing files",
                    "default": False
                }
            },
            "required": ["file_path", "content"]
        }

    def execute(self, file_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        Write content to file.

        Args:
            file_path: Path to file
            content: Content to write
            overwrite: Allow overwriting existing files

        Returns:
            dict: {
                'success': True,
                'file_path': '/absolute/path/to/file',
                'bytes_written': 1234
            }
        """
        try:
            path = Path(file_path).expanduser().resolve()
        except Exception as e:
            return {
                'success': False,
                'error': f'Invalid file path: {e}'
            }

        # Check if exists
        if path.exists() and not overwrite:
            return {
                'success': False,
                'error': f'File already exists: {file_path}. Use overwrite=True to replace.'
            }

        # Create parent directories if needed
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return {
                'success': False,
                'error': f'Cannot create parent directories: {e}'
            }

        # Write file
        try:
            # Write with platform-appropriate line endings
            with open(path, 'w', encoding='utf-8', newline='') as f:
                bytes_written = f.write(content)

            return {
                'success': True,
                'file_path': str(path),
                'bytes_written': bytes_written
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error writing file: {e}'
            }


class EditTool(BaseTool):
    """Edit files with exact string replacement - cross-platform"""

    @property
    def name(self) -> str:
        return "edit"

    @property
    def description(self) -> str:
        return "Edit file by replacing exact string. SAFETY: old_string must match exactly."

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to file to edit"
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact string to find (must be unique unless replace_all=True)"
                },
                "new_string": {
                    "type": "string",
                    "description": "Replacement string"
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences (default: False, requires unique match)",
                    "default": False
                }
            },
            "required": ["file_path", "old_string", "new_string"]
        }

    def execute(self, file_path: str, old_string: str, new_string: str,
                replace_all: bool = False) -> Dict[str, Any]:
        """
        Edit file by replacing exact string.

        SAFETY: old_string must match exactly (including whitespace).
        This prevents accidental changes.

        Args:
            file_path: Path to file
            old_string: Exact string to find (must be unique unless replace_all=True)
            new_string: Replacement string
            replace_all: Replace all occurrences (default: False, requires unique match)

        Returns:
            dict: {
                'success': True,
                'file_path': '/absolute/path',
                'replacements': 1
            }
        """
        try:
            path = Path(file_path).expanduser().resolve()
        except Exception as e:
            return {
                'success': False,
                'error': f'Invalid file path: {e}'
            }

        if not path.exists():
            return {
                'success': False,
                'error': f'File not found: {file_path}'
            }

        if not path.is_file():
            return {
                'success': False,
                'error': f'Not a file: {file_path}'
            }

        try:
            # Read entire file
            with open(path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Count occurrences
            occurrences = original_content.count(old_string)

            if occurrences == 0:
                return {
                    'success': False,
                    'error': f'String not found in file. Searched for: {old_string[:100]}...'
                }

            # Safety check: if multiple occurrences and not replace_all, reject
            if occurrences > 1 and not replace_all:
                return {
                    'success': False,
                    'error': f'String appears {occurrences} times. Use replace_all=True or provide more context to make it unique.'
                }

            # Perform replacement
            if replace_all:
                new_content = original_content.replace(old_string, new_string)
                replacements = occurrences
            else:
                new_content = original_content.replace(old_string, new_string, 1)
                replacements = 1

            # Write back (preserve original line endings)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return {
                'success': True,
                'file_path': str(path),
                'replacements': replacements,
                'old_string': old_string[:100],
                'new_string': new_string[:100]
            }
        except UnicodeDecodeError:
            return {
                'success': False,
                'error': f'File is not text or uses unsupported encoding: {file_path}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error editing file: {e}'
            }
