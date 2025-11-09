"""
File Operation Tools - Read, Write, Edit
Cross-platform file tools using pathlib with intelligent features
"""

import re
from pathlib import Path
from typing import Dict, Any
from .base import BaseTool


class ReadTool(BaseTool):
    """Read files with intelligent features - cross-platform"""

    @property
    def name(self) -> str:
        return "read"

    @property
    def description(self) -> str:
        return "Read file contents with intelligent features. Supports syntax highlighting, focus areas, and smart context."

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to file (absolute or relative)"
                },
                "focus_lines": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Specific line numbers to focus on (1-indexed)",
                    "default": None
                },
                "start_line": {
                    "type": "integer",
                    "description": "Starting line number (1-indexed)",
                    "default": 1
                },
                "end_line": {
                    "type": "integer",
                    "description": "Ending line number (1-indexed, 0 = end of file)",
                    "default": 0
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Lines of context around focus areas",
                    "default": 3
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum lines to return (0 = no limit)",
                    "default": 100
                },
                "syntax_highlight": {
                    "type": "boolean",
                    "description": "Enable syntax highlighting hints",
                    "default": True
                },
                "show_line_numbers": {
                    "type": "boolean",
                    "description": "Show line numbers",
                    "default": True
                }
            },
            "required": ["file_path"]
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Read file with intelligent features.

        Args:
            file_path: Path to file (absolute or relative)
            focus_lines: Specific line numbers to focus on (1-indexed)
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (1-indexed, 0 = end of file)
            context_lines: Lines of context around focus areas
            max_lines: Maximum lines to return (0 = no limit)
            syntax_highlight: Enable syntax highlighting hints
            show_line_numbers: Show line numbers

        Returns:
            dict: {
                'success': True,
                'content': 'file content with line numbers',
                'lines_read': 100,
                'total_lines': 500,
                'file_path': '/absolute/path/to/file',
                'focus_areas': [...],
                'language': 'python'
            }
        """
        file_path = kwargs.get('file_path')
        focus_lines = kwargs.get('focus_lines')
        start_line = kwargs.get('start_line', 1)
        end_line = kwargs.get('end_line', 0)
        context_lines = kwargs.get('context_lines', 3)
        max_lines = kwargs.get('max_lines', 100)
        syntax_highlight = kwargs.get('syntax_highlight', True)
        show_line_numbers = kwargs.get('show_line_numbers', True)
        
        if not file_path:
            return {
                'success': False,
                'error': 'file_path is required'
            }
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
                all_lines = f.readlines()

            total_lines = len(all_lines)
            
            # Determine which lines to read
            if focus_lines:
                # Focus on specific lines with context
                line_ranges = []
                for focus_line in focus_lines:
                    if 1 <= focus_line <= total_lines:
                        start = max(1, focus_line - context_lines)
                        end = min(total_lines, focus_line + context_lines)
                        line_ranges.append((start, end))
                
                # Merge overlapping ranges
                if line_ranges:
                    line_ranges.sort()
                    merged_ranges = [line_ranges[0]]
                    for start, end in line_ranges[1:]:
                        last_start, last_end = merged_ranges[-1]
                        if start <= last_end + 1:
                            merged_ranges[-1] = (last_start, max(last_end, end))
                        else:
                            merged_ranges.append((start, end))
                    line_ranges = merged_ranges
            else:
                # Use start_line/end_line range
                actual_start = max(1, start_line)
                actual_end = end_line if end_line > 0 else total_lines
                actual_end = min(actual_end, total_lines)
                line_ranges = [(actual_start, actual_end)] if actual_start <= actual_end else []

            # Extract lines from ranges
            selected_lines = []
            for start, end in line_ranges:
                selected_lines.extend(all_lines[start-1:end])  # Convert to 0-indexed
            
            # Apply max_lines limit
            if max_lines > 0 and len(selected_lines) > max_lines:
                selected_lines = selected_lines[:max_lines]

            # Detect language for syntax highlighting hints
            language = self._detect_language(path)
            
            # Format output
            if show_line_numbers:
                formatted = []
                current_line_num = line_ranges[0][0] if line_ranges else start_line
                for line in selected_lines:
                    formatted.append(f"{current_line_num:6d}→{line.rstrip()}")
                    current_line_num += 1
                content = '\n'.join(formatted)
            else:
                content = ''.join(selected_lines)

            # Build focus areas info
            focus_areas = []
            if focus_lines:
                for focus_line in focus_lines:
                    if 1 <= focus_line <= total_lines:
                        focus_areas.append({
                            'line': focus_line,
                            'context_start': max(1, focus_line - context_lines),
                            'context_end': min(total_lines, focus_line + context_lines)
                        })

            return {
                'success': True,
                'content': content,
                'lines_read': len(selected_lines),
                'total_lines': total_lines,
                'file_path': str(path),
                'language': language,
                'focus_areas': focus_areas,
                'line_ranges': line_ranges,
                'syntax_highlight': syntax_highlight
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

    def _detect_language(self, path: Path) -> str:
        """Detect programming language from file extension"""
        ext = path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sh': 'bash',
            '.bash': 'bash',
            '.ps1': 'powershell',
            '.sql': 'sql',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'config',
            '.conf': 'config',
            '.md': 'markdown',
            '.txt': 'text'
        }
        return language_map.get(ext, 'text')


class SearchReplaceTool(BaseTool):
    """Advanced search and replace with regex support - cross-platform"""

    @property
    def name(self) -> str:
        return "search_replace"

    @property
    def description(self) -> str:
        return "Search and replace text in files with regex support, preview mode, and safety features."

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to file to modify"
                },
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (regex if regex=True, literal otherwise)"
                },
                "replacement": {
                    "type": "string",
                    "description": "Replacement text"
                },
                "regex": {
                    "type": "boolean",
                    "description": "Treat pattern as regex",
                    "default": False
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Case-sensitive search",
                    "default": True
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences",
                    "default": False
                },
                "preview": {
                    "type": "boolean",
                    "description": "Preview changes without applying them",
                    "default": True
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Lines of context to show in preview",
                    "default": 2
                }
            },
            "required": ["file_path", "pattern", "replacement"]
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Search and replace with advanced features.

        Args:
            file_path: Path to file
            pattern: Search pattern
            replacement: Replacement text
            regex: Use regex matching
            case_sensitive: Case-sensitive search
            replace_all: Replace all occurrences
            preview: Preview changes without applying
            context_lines: Context lines for preview

        Returns:
            dict: {
                'success': True,
                'matches': [...],
                'replacements': 1,
                'preview': 'diff output'
            }
        """
        file_path = kwargs.get('file_path')
        pattern = kwargs.get('pattern')
        replacement = kwargs.get('replacement')
        regex = kwargs.get('regex', False)
        case_sensitive = kwargs.get('case_sensitive', True)
        replace_all = kwargs.get('replace_all', False)
        preview = kwargs.get('preview', True)
        context_lines = kwargs.get('context_lines', 2)
        
        if not file_path:
            return {
                'success': False,
                'error': 'file_path is required'
            }
        
        if pattern is None:
            return {
                'success': False,
                'error': 'pattern is required'
            }
        
        if replacement is None:
            return {
                'success': False,
                'error': 'replacement is required'
            }

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
            # Read file
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Compile search pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            if regex:
                try:
                    search_pattern = re.compile(pattern, flags)
                except re.error as e:
                    return {
                        'success': False,
                        'error': f'Invalid regex pattern: {e}'
                    }
            else:
                # Escape special regex chars for literal search
                escaped_pattern = re.escape(pattern)
                search_pattern = re.compile(escaped_pattern, flags)

            # Find all matches with context
            lines = content.splitlines(keepends=True)
            matches = []
            
            for i, line in enumerate(lines):
                line_matches = list(search_pattern.finditer(line))
                for match in line_matches:
                    match_info = {
                        'line_number': i + 1,
                        'start_col': match.start(),
                        'end_col': match.end(),
                        'matched_text': match.group(),
                        'line_content': line.rstrip('\n\r'),
                        'context_before': lines[max(0, i - context_lines):i],
                        'context_after': lines[i + 1:i + 1 + context_lines]
                    }
                    matches.append(match_info)

            if not matches:
                return {
                    'success': False,
                    'error': f'No matches found for pattern: {pattern}',
                    'matches': []
                }

            # Safety check for multiple matches
            if len(matches) > 1 and not replace_all:
                return {
                    'success': False,
                    'error': f'Pattern matches {len(matches)} times. Use replace_all=True to replace all, or provide more specific pattern.',
                    'matches': matches[:10]  # Show first 10 matches
                }

            # Generate preview/diff
            preview_lines = []
            for match in matches[:5]:  # Show first 5 matches in preview
                preview_lines.append(f"Line {match['line_number']}:")
                preview_lines.append(f"  - {match['matched_text']}")
                preview_lines.append(f"  + {replacement}")
                preview_lines.append("")

            preview_text = '\n'.join(preview_lines)

            # Apply replacements if not preview mode
            replacements = 0
            if not preview:
                if replace_all:
                    new_content = search_pattern.sub(replacement, content)
                    replacements = len(matches)
                else:
                    new_content = search_pattern.sub(replacement, content, count=1)
                    replacements = 1
                
                # Write back
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

            return {
                'success': True,
                'matches': matches,
                'total_matches': len(matches),
                'replacements': replacements if not preview else 0,
                'preview': preview_text,
                'applied': not preview,
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
                'error': f'Error in search/replace: {e}'
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

    def execute(self, **kwargs) -> Dict[str, Any]:
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
        file_path = kwargs.get('file_path')
        content = kwargs.get('content')
        overwrite = kwargs.get('overwrite', False)
        
        if not file_path:
            return {
                'success': False,
                'error': 'file_path is required'
            }
        
        if content is None:
            return {
                'success': False,
                'error': 'content is required'
            }
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

    def execute(self, **kwargs) -> Dict[str, Any]:
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
        file_path = kwargs.get('file_path')
        old_string = kwargs.get('old_string')
        new_string = kwargs.get('new_string')
        replace_all = kwargs.get('replace_all', False)
        
        if not file_path:
            return {
                'success': False,
                'error': 'file_path is required'
            }
        
        if old_string is None:
            return {
                'success': False,
                'error': 'old_string is required'
            }
        
        if new_string is None:
            return {
                'success': False,
                'error': 'new_string is required'
            }
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
