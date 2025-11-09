"""
Grep Command - Search files for regex patterns
Wrapper for GrepTool
"""

import argparse
import json
import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.tools import GrepTool


def main():
    """Main entry point for /grep command"""
    parser = argparse.ArgumentParser(description="Search files for regex patterns")
    parser.add_argument("pattern", help="Regex pattern to search for")
    parser.add_argument("--path", default=".", help="Directory to search (default: current)")
    parser.add_argument("--glob", dest="glob_pattern", help="File pattern (e.g., *.py, **/*.js)")
    parser.add_argument("--ignore-case", "-i", action="store_true", help="Case-insensitive search")
    parser.add_argument("--context", "-C", type=int, default=0, help="Lines of context")
    parser.add_argument(
        "--output",
        choices=["files", "content", "count"],
        default="files",
        help="Output mode (default: files)",
    )
    parser.add_argument("--help-cmd", action="store_true", help="Show this help")

    try:
        if len(sys.argv) == 1:
            parser.print_help()
            print("\nExamples:")
            print("  /grep 'TODO'")
            print("  /grep 'error' --glob '*.log'")
            print("  /grep 'function' --glob '*.py' --context 3")
            print("  /grep 'pattern' --ignore-case")
            print("  /grep 'import' --output content")
            sys.exit(0)

        args = parser.parse_args()

        if args.help_cmd:
            parser.print_help()
            sys.exit(0)

        # Map output mode
        output_mode_map = {"files": "files_with_matches", "content": "content", "count": "count"}

        # Execute tool
        tool = GrepTool()
        result = tool.execute(
            pattern=args.pattern,
            path=args.path,
            glob_pattern=args.glob_pattern,
            ignore_case=args.ignore_case,
            context_lines=args.context,
            output_mode=output_mode_map[args.output],
        )

        # Output result
        if result["success"]:
            matches = result["matches"]

            if args.output == "files":
                # List of files
                if matches:
                    print(f"Found in {len(matches)} files:")
                    for file in matches:
                        print(f"  {file}")
                else:
                    print("No matches found")

            elif args.output == "content":
                # Detailed matches
                if matches:
                    print(f"Found {len(matches)} matches:")
                    for match in matches:
                        print(f"\n{match['file']}:{match['line_number']}")
                        if args.context and "context_before" in match:
                            for line in match["context_before"]:
                                print(f"  -  {line}")
                        print(f"  >  {match['content']}")
                        if args.context and "context_after" in match:
                            for line in match["context_after"]:
                                print(f"  -  {line}")
                else:
                    print("No matches found")

            elif args.output == "count":
                # Count per file
                if matches:
                    print(f"Match counts:")
                    for item in matches:
                        print(f"  {item['file']}: {item['count']}")
                else:
                    print("No matches found")

            print(f"\n[Searched {result['total_files_searched']} files]", file=sys.stderr)

            if not sys.stdout.isatty():
                envelope = {"ok": True, "stdout": json.dumps(matches, indent=2)}
                print(json.dumps(envelope))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)

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
