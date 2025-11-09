#!/usr/bin/env python3
"""
/glob command - Find files by pattern matching

Wrapper for GlobTool that integrates with Isaac's command architecture.
"""

import argparse
import json
import sys
from pathlib import Path

# Add Isaac tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools import GlobTool


def main():
    """Main entry point for /glob command"""
    parser = argparse.ArgumentParser(
        description="Find files by pattern matching",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  /glob '**/*.py'                    Find all Python files
  /glob 'src/**/*.js' --path ~/project   Find JS files in specific directory
  /glob '*.md'                       Find markdown files in current directory

Output:
  Returns list of matching file paths with metadata (size, modified time).
        """,
    )

    parser.add_argument("pattern", help='Glob pattern to match files (e.g., "**/*.py", "*.txt")')
    parser.add_argument(
        "--path", default=None, help="Directory to search in (defaults to current directory)"
    )

    args = parser.parse_args()

    # Execute glob tool
    tool = GlobTool()
    result = tool.execute(pattern=args.pattern, path=args.path)

    # Format for Isaac dispatcher
    if result["success"]:
        # Format file list for output
        files = result.get("files", [])
        count = result.get("count", 0)

        # Create human-readable output
        output_lines = [f"Found {count} files:"]
        for file_info in files:
            output_lines.append(f"  {file_info['path']}")
        output = "\n".join(output_lines)

        # Print human-readable output
        print(output)

        # Create file list for JSON
        file_paths = [f["path"] for f in files]

        response = {
            "ok": True,
            "stdout": json.dumps(file_paths),
            "meta": {
                "command": "/glob",
                "pattern": args.pattern,
                "path": args.path or str(Path.cwd()),
                "count": count,
            },
        }
    else:
        response = {
            "ok": False,
            "error": {"code": "GLOB_ERROR", "message": result["error"]},
            "meta": {"command": "/glob"},
        }

    # Output JSON envelope
    print(json.dumps(response, indent=2))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
