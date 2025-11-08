"""
Write Command - Create new files
Wrapper for WriteTool
"""

import sys
import json
import argparse
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.tools import WriteTool


def main():
    """Main entry point for /write command"""
    parser = argparse.ArgumentParser(description='Create new files')
    parser.add_argument('file_path', help='Path to file to create')
    parser.add_argument('content', nargs='?', default=None, help='Content to write (or use stdin)')
    parser.add_argument('--overwrite', action='store_true', help='Allow overwriting existing files')
    parser.add_argument('--help-cmd', action='store_true', help='Show this help')

    try:
        # Parse args
        if len(sys.argv) == 1:
            parser.print_help()
            print("\nExamples:")
            print("  /write newfile.txt 'Hello World'")
            print("  /write file.txt 'content' --overwrite")
            print("  echo 'test' | /write output.txt")
            sys.exit(0)

        args = parser.parse_args()

        if args.help_cmd:
            parser.print_help()
            sys.exit(0)

        # Get content from args or stdin
        content = args.content
        if content is None:
            # Check if stdin has data (piping)
            if not sys.stdin.isatty():
                content = sys.stdin.read()
            else:
                print("Error: No content provided. Use argument or pipe content.", file=sys.stderr)
                sys.exit(1)

        # Execute tool
        tool = WriteTool()
        result = tool.execute(
            file_path=args.file_path,
            content=content,
            overwrite=args.overwrite
        )

        # Output result
        if result['success']:
            print(f"File written: {result['file_path']} ({result['bytes_written']} bytes)")

            # Return success envelope
            if not sys.stdout.isatty():
                envelope = {
                    "ok": True,
                    "stdout": f"File written: {result['file_path']}"
                }
                print(json.dumps(envelope))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)

            if not sys.stdout.isatty():
                envelope = {
                    "ok": False,
                    "error": {"message": result['error']}
                }
                print(json.dumps(envelope))

            sys.exit(1)

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
