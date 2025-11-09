"""
Code Search Tools - Grep, Glob
Cross-platform file search tools using pathlib and regex
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional
from .base import BaseTool


class GrepTool(BaseTool):
    """Search files for patterns - cross-platform"""

    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return "Search files for regex patterns. Returns matching lines with context."

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for"
                },
                "path": {
                    "type": "string",
                    "description": "Directory or file to search (default: current directory)",
                    "default": "."
                },
                "glob_pattern": {
                    "type": "string",
                    "description": "File pattern to match (e.g., '*.py', '**/*.js')",
                    "default": None
                },
                "ignore_case": {
                    "type": "boolean",
                    "description": "Case-insensitive search",
                    "default": False
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of context lines before/after match",
                    "default": 0
                },
                "output_mode": {
                    "type": "string",
                    "description": "Output mode: 'files_with_matches', 'content', or 'count'",
                    "enum": ["files_with_matches", "content", "count"],
                    "default": "files_with_matches"
                }
            },
            "required": ["pattern"]
        }

    def execute(self, pattern: str, path: str = ".",
                glob_pattern: Optional[str] = None,
                ignore_case: bool = False,
                context_lines: int = 0,
                output_mode: str = "files_with_matches") -> Dict[str, Any]:
        """
        Search files for regex pattern.

        Args:
            pattern: Regex pattern to search for
            path: Directory to search (default: current directory)
            glob_pattern: File pattern to match (e.g., "*.py", "**/*.js")
            ignore_case: Case-insensitive search
            context_lines: Number of context lines before/after match
            output_mode: "files_with_matches", "content", or "count"

        Returns:
            dict: {
                'success': True,
                'matches': [...],
                'total_files_searched': 123,
                'pattern': 'regex pattern'
            }
        """
        try:
            search_path = Path(path).expanduser().resolve()
        except Exception as e:
            return {
                'success': False,
                'error': f'Invalid path: {e}'
            }

        if not search_path.exists():
            return {
                'success': False,
                'error': f'Path not found: {path}'
            }

        # Compile regex
        flags = re.IGNORECASE if ignore_case else 0
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return {
                'success': False,
                'error': f'Invalid regex pattern: {e}'
            }

        # Determine files to search
        try:
            if glob_pattern:
                if search_path.is_file():
                    files = [search_path] if search_path.match(glob_pattern) else []
                else:
                    files = list(search_path.glob(glob_pattern))
            elif search_path.is_file():
                files = [search_path]
            else:
                # Default: search all text files recursively
                files = [f for f in search_path.rglob('*') if f.is_file()]
        except Exception as e:
            return {
                'success': False,
                'error': f'Error searching files: {e}'
            }

        matches = []
        files_searched = 0

        for file_path in files:
            # Skip binary files
            if not self._is_text_file(file_path):
                continue

            files_searched += 1

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                file_matches = []
                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        match_info = {
                            'line_number': line_num,
                            'content': line.rstrip(),
                            'file': str(file_path.relative_to(search_path)) if file_path != search_path else str(file_path.name)
                        }

                        # Add context lines if requested
                        if context_lines > 0:
                            before = max(0, line_num - context_lines - 1)
                            after = min(len(lines), line_num + context_lines)
                            match_info['context_before'] = [l.rstrip() for l in lines[before:line_num-1]]
                            match_info['context_after'] = [l.rstrip() for l in lines[line_num:after]]

                        file_matches.append(match_info)

                if file_matches:
                    if output_mode == "files_with_matches":
                        rel_path = str(file_path.relative_to(search_path)) if file_path != search_path else str(file_path.name)
                        matches.append(rel_path)
                    elif output_mode == "content":
                        matches.extend(file_matches)
                    elif output_mode == "count":
                        rel_path = str(file_path.relative_to(search_path)) if file_path != search_path else str(file_path.name)
                        matches.append({
                            'file': rel_path,
                            'count': len(file_matches)
                        })
            except Exception:
                continue  # Skip files we can't read

        return {
            'success': True,
            'matches': matches,
            'total_files_searched': files_searched,
            'pattern': pattern,
            'output_mode': output_mode
        }

    def _is_text_file(self, path: Path) -> bool:
        """Check if file is likely text (cross-platform heuristic)"""
        # Check extension
        text_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.txt', '.md', '.markdown',
            '.json', '.yaml', '.yml', '.xml', '.html', '.htm', '.css', '.scss',
            '.sh', '.bash', '.bat', '.ps1', '.c', '.cpp', '.h', '.hpp',
            '.java', '.go', '.rs', '.toml', '.ini', '.cfg', '.conf',
            '.sql', '.php', '.rb', '.pl', '.lua', '.r', '.m', '.swift',
            '.kt', '.scala', '.clj', '.ex', '.exs', '.erl', '.hs',
            '.vim', '.el', '.lisp', '.rkt', '.scm'
        }

        if path.suffix.lower() in text_extensions:
            return True

        # Check first 1KB for binary content
        try:
            with open(path, 'rb') as f:
                chunk = f.read(1024)
                # If contains null bytes, likely binary
                if b'\x00' in chunk:
                    return False
                # Check for high ratio of non-printable chars
                non_printable = sum(1 for b in chunk if b < 32 and b not in (9, 10, 13))
                if non_printable > len(chunk) * 0.3:  # >30% non-printable
                    return False
                return True
        except:
            return False


class GlobTool(BaseTool):
    """Find files by pattern - cross-platform"""

    @property
    def name(self) -> str:
        return "glob"

    @property
    def description(self) -> str:
        return "Find files matching glob pattern. Returns file paths with metadata."

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern (e.g., '*.py', '**/*.js', 'test_*.py')"
                },
                "path": {
                    "type": "string",
                    "description": "Base directory to search (default: current directory)",
                    "default": "."
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files (starting with .)",
                    "default": False
                },
                "sort_by": {
                    "type": "string",
                    "description": "Sort by: 'name', 'size', or 'modified'",
                    "enum": ["name", "size", "modified"],
                    "default": "name"
                }
            },
            "required": ["pattern"]
        }

    def execute(self, pattern: str, path: str = ".",
                include_hidden: bool = False,
                sort_by: str = "name") -> Dict[str, Any]:
        """
        Find files matching glob pattern.

        Args:
            pattern: Glob pattern (e.g., "*.py", "**/*.js", "test_*.py")
            path: Base directory to search
            include_hidden: Include hidden files (starting with .)
            sort_by: "name", "size", "modified" (default: "name")

        Returns:
            dict: {
                'success': True,
                'files': [
                    {
                        'path': 'relative/path/to/file.py',
                        'absolute_path': '/absolute/path/to/file.py',
                        'size': 1234,
                        'modified': 1699123456.789
                    },
                    ...
                ],
                'count': 10,
                'pattern': '*.py'
            }
        """
        try:
            search_path = Path(path).expanduser().resolve()
        except Exception as e:
            return {
                'success': False,
                'error': f'Invalid path: {e}'
            }

        if not search_path.exists():
            return {
                'success': False,
                'error': f'Path not found: {path}'
            }

        if not search_path.is_dir():
            return {
                'success': False,
                'error': f'Not a directory: {path}'
            }

        try:
            # Use pathlib.glob (cross-platform)
            matches = list(search_path.glob(pattern))

            # Filter hidden files if requested
            if not include_hidden:
                matches = [f for f in matches if not any(
                    part.startswith('.') for part in f.parts
                )]

            # Get file info
            file_info = []
            for file_path in matches:
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        file_info.append({
                            'path': str(file_path.relative_to(search_path)),
                            'absolute_path': str(file_path),
                            'size': stat.st_size,
                            'modified': stat.st_mtime
                        })
                    except Exception:
                        # Skip files we can't stat
                        continue

            # Sort
            if sort_by == "size":
                file_info.sort(key=lambda x: x['size'], reverse=True)
            elif sort_by == "modified":
                file_info.sort(key=lambda x: x['modified'], reverse=True)
            else:  # name
                file_info.sort(key=lambda x: x['path'])

            return {
                'success': True,
                'files': file_info,
                'count': len(file_info),
                'pattern': pattern
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error searching files: {e}'
            }
