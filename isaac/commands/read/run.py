"""
Read Command - Read files with line numbers
Wrapper for ReadTool
"""

import argparse
import json
import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.tools import ReadTool


def main():
    """Main entry point for /read command"""
    parser = argparse.ArgumentParser(description="Read files with line numbers")
    parser.add_argument("file_path", help="Path to file to read")
    parser.add_argument(
        "--offset", type=int, default=0, help="Line number to start from (0-indexed)"
    )
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of lines to read")
    parser.add_argument("--help-cmd", action="store_true", help="Show this help")

    try:
        # Parse args
        if len(sys.argv) == 1:
            # No arguments - show help
            parser.print_help()
            print("\nExamples:")
            print("  /read myfile.py")
            print("  /read myfile.py --offset 100")
            print("  /read myfile.py --limit 50")
            print("  /read myfile.py --offset 100 --limit 50")
            sys.exit(0)

        args = parser.parse_args()

        if args.help_cmd:
            parser.print_help()
            sys.exit(0)

        # Execute tool
        tool = ReadTool()
        result = tool.execute(file_path=args.file_path, offset=args.offset, limit=args.limit)

        # Output result
        if result["success"]:
            # Print content
            print(result["content"])

            # Print summary to stderr (doesn't interfere with piping)
            if args.limit or args.offset:
                summary = f"\n[Read {result['lines_read']} of {result['total_lines']} lines from {result['file_path']}]"
                print(summary, file=sys.stderr)

            # Return success envelope for dispatcher
            if not sys.stdout.isatty():
                envelope = {"ok": True, "stdout": result["content"]}
                print(json.dumps(envelope))
        else:
            # Print error
            print(f"Error: {result['error']}", file=sys.stderr)

            # Return error envelope for dispatcher
            if not sys.stdout.isatty():
                envelope = {"ok": False, "error": {"message": result["error"]}}
                print(json.dumps(envelope))

            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

        if not sys.stdout.isatty():
            envelope = {"ok": False, "error": {"message": str(e)}}
            print(json.dumps(envelope))

        sys.exit(1)


if __name__ == "__main__":
    main()
