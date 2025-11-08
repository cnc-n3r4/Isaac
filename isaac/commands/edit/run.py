"""
Edit Command - Edit files with exact string replacement
Wrapper for EditTool
"""

import sys
import json
import argparse
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.tools import EditTool


def main():
    """Main entry point for /edit command"""
    parser = argparse.ArgumentParser(description='Edit files with exact string replacement')
    parser.add_argument('file_path', help='Path to file to edit')
    parser.add_argument('old_string', help='Exact string to find')
    parser.add_argument('new_string', help='Replacement string')
    parser.add_argument('--replace-all', action='store_true', help='Replace all occurrences')
    parser.add_argument('--help-cmd', action='store_true', help='Show this help')

    try:
        if len(sys.argv) == 1:
            parser.print_help()
            print("\nExamples:")
            print("  /edit app.py 'old text' 'new text'")
            print("  /edit file.txt 'bug' 'fix' --replace-all")
            print("  /edit config.json '\"debug\": false' '\"debug\": true'")
            sys.exit(0)

        args = parser.parse_args()

        if args.help_cmd:
            parser.print_help()
            sys.exit(0)

        # Execute tool
        tool = EditTool()
        result = tool.execute(
            file_path=args.file_path,
            old_string=args.old_string,
            new_string=args.new_string,
            replace_all=args.replace_all
        )

        # Output result
        if result['success']:
            print(f"Edited: {result['file_path']}")
            print(f"Replacements: {result['replacements']}")
            print(f"  Old: {result['old_string']}")
            print(f"  New: {result['new_string']}")

            if not sys.stdout.isatty():
                envelope = {
                    "ok": True,
                    "stdout": f"Edited {result['file_path']}: {result['replacements']} replacements"
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
