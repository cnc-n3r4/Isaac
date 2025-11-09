#!/usr/bin/env python3
"""
Unified Search Command - Smart search for files and content

Intelligently combines /glob (find files) and /grep (search content).

Smart Detection:
  /search "*.py"              → Find Python files (glob pattern detected)
  /search "TODO"              → Search for TODO in files (content search)
  /search "TODO" in "*.py"    → Search TODO in Python files (explicit)
  /search --mode glob "*.md"  → Force glob mode
  /search --mode grep "error" → Force grep mode
"""

import sys
import json
import argparse
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.tools import GrepTool, GlobTool


def detect_search_mode(pattern: str, file_pattern: str = None) -> str:
    """
    Intelligently detect search mode based on pattern.

    Args:
        pattern: The search pattern
        file_pattern: Optional file pattern (if "in" syntax used)

    Returns:
        'glob' or 'grep'
    """
    # If file_pattern specified with "in", it's grep
    if file_pattern:
        return 'grep'

    # Glob indicators: *, ?, **, [, ]
    glob_indicators = ['*', '?', '[', ']']
    if any(indicator in pattern for indicator in glob_indicators):
        return 'glob'

    # File extension patterns like ".py" or "*.py"
    if pattern.startswith('.') and '/' not in pattern:
        return 'glob'

    # Path-like patterns
    if '/' in pattern or '\\' in pattern:
        return 'glob'

    # Default to content search (grep)
    return 'grep'


def parse_search_query(args_list):
    """
    Parse search query with support for "in" syntax.

    Examples:
        ["TODO"] → pattern="TODO", file_pattern=None
        ["TODO", "in", "*.py"] → pattern="TODO", file_pattern="*.py"
        ["import", "re", "in", "**/*.py"] → pattern="import re", file_pattern="**/*.py"
    """
    # Find "in" keyword
    if 'in' in args_list:
        in_index = args_list.index('in')
        pattern_parts = args_list[:in_index]
        file_pattern_parts = args_list[in_index + 1:]

        pattern = ' '.join(pattern_parts)
        file_pattern = ' '.join(file_pattern_parts) if file_pattern_parts else None
    else:
        pattern = ' '.join(args_list)
        file_pattern = None

    return pattern, file_pattern


def execute_glob_search(pattern: str, path: str = '.'):
    """Execute file pattern search (glob mode)"""
    tool = GlobTool()
    result = tool.execute(pattern=pattern, path=path)

    if result['success']:
        files = result.get('files', [])
        count = result.get('count', 0)

        if files:
            print(f"Found {count} files:")
            for file_info in files:
                print(f"  {file_info['path']}")
        else:
            print("No files found")

        return {
            'success': True,
            'mode': 'glob',
            'count': count,
            'files': [f['path'] for f in files]
        }
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return {
            'success': False,
            'mode': 'glob',
            'error': result['error']
        }


def execute_grep_search(pattern: str, path: str = '.', file_pattern: str = None,
                       ignore_case: bool = False, context: int = 0, output: str = 'files'):
    """Execute content search (grep mode)"""
    output_mode_map = {
        'files': 'files_with_matches',
        'content': 'content',
        'count': 'count'
    }

    tool = GrepTool()
    result = tool.execute(
        pattern=pattern,
        path=path,
        glob_pattern=file_pattern,
        ignore_case=ignore_case,
        context_lines=context,
        output_mode=output_mode_map[output]
    )

    if result['success']:
        matches = result['matches']

        if output == 'files':
            if matches:
                print(f"Found in {len(matches)} files:")
                for file in matches:
                    print(f"  {file}")
            else:
                print("No matches found")

        elif output == 'content':
            if matches:
                print(f"Found {len(matches)} matches:")
                for match in matches:
                    print(f"\n{match['file']}:{match['line_number']}")
                    if context and 'context_before' in match:
                        for line in match['context_before']:
                            print(f"  -  {line}")
                    print(f"  >  {match['content']}")
                    if context and 'context_after' in match:
                        for line in match['context_after']:
                            print(f"  -  {line}")
            else:
                print("No matches found")

        elif output == 'count':
            if matches:
                print("Match counts:")
                for item in matches:
                    print(f"  {item['file']}: {item['count']}")
            else:
                print("No matches found")

        search_info = f"\n[Searched {result['total_files_searched']} files"
        if file_pattern:
            search_info += f" matching '{file_pattern}'"
        search_info += "]"
        print(search_info, file=sys.stderr)

        return {
            'success': True,
            'mode': 'grep',
            'matches': matches,
            'total_files_searched': result['total_files_searched']
        }
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return {
            'success': False,
            'mode': 'grep',
            'error': result['error']
        }


def main():
    """Main entry point for unified /search command"""
    parser = argparse.ArgumentParser(
        description='Unified search - Find files or search content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Smart detection (automatically chooses mode)
  /search "*.py"                      Find Python files (glob detected)
  /search "TODO"                      Search for TODO (content search)
  /search "**/*.md"                   Find all markdown files (glob detected)

  # Explicit "in" syntax (search content in specific files)
  /search "TODO" in "*.py"            Search TODO in Python files
  /search "error" in "**/*.log"       Search error in all log files
  /search "import re" in "src/**/*.py" Search imports in src Python files

  # Force specific mode
  /search --mode glob "test"          Find files named 'test' (force glob)
  /search --mode grep "*.py"          Search for "*.py" text (force grep)

  # Advanced grep options
  /search "error" -i                  Case-insensitive search
  /search "function" -C 3             Show 3 lines of context
  /search "TODO" --output content     Show matching lines (not just files)

Output Modes (grep only):
  --output files     List files with matches (default)
  --output content   Show matching lines with context
  --output count     Show match counts per file
        """
    )

    # Positional arguments (variable, handles "in" syntax)
    parser.add_argument('query', nargs='+', help='Search query (supports "pattern in files" syntax)')

    # Mode control
    parser.add_argument('--mode', choices=['auto', 'glob', 'grep'], default='auto',
                       help='Search mode (default: auto-detect)')

    # Common options
    parser.add_argument('--path', default='.',
                       help='Directory to search (default: current)')

    # Grep-specific options
    parser.add_argument('--ignore-case', '-i', action='store_true',
                       help='Case-insensitive search (grep mode)')
    parser.add_argument('--context', '-C', type=int, default=0,
                       help='Lines of context (grep mode)')
    parser.add_argument('--output', choices=['files', 'content', 'count'], default='files',
                       help='Output mode (grep mode, default: files)')

    try:
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(0)

        args = parser.parse_args()

        # Parse query with "in" syntax support
        pattern, file_pattern = parse_search_query(args.query)

        # Determine mode
        if args.mode == 'auto':
            mode = detect_search_mode(pattern, file_pattern)
        else:
            mode = args.mode

        # Execute appropriate search
        if mode == 'glob':
            result = execute_glob_search(pattern, args.path)
        else:  # grep
            result = execute_grep_search(
                pattern,
                args.path,
                file_pattern,
                args.ignore_case,
                args.context,
                args.output
            )

        # Output JSON envelope for non-TTY
        if not sys.stdout.isatty():
            envelope = {
                "ok": result['success'],
                "mode": result.get('mode'),
                "result": result
            }
            print(json.dumps(envelope))

        sys.exit(0 if result['success'] else 1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

        if not sys.stdout.isatty():
            envelope = {
                "ok": False,
                "error": {"message": str(e)}
            }
            print(json.dumps(envelope))

        sys.exit(1)


if __name__ == "__main__":
    main()
