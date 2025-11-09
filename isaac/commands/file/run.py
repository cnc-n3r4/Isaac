#!/usr/bin/env python3
"""
Unified File Command - All file operations in one command

Consolidates /read, /write, /edit, and /newfile into a single interface.

Operations:
  /file read <path>                    Read a file
  /file write <path> <content>         Create/write a file
  /file edit <path> <old> <new>        Edit with string replacement
  /file create <path>                  Create new file (from template if available)
  /file append <path> <content>        Append to file

Smart defaults:
  /file myfile.txt                     Reads the file (if exists)
  /file myfile.txt "content"           Writes content to file
"""

import argparse
import json
import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.tools import EditTool, ReadTool, WriteTool


def cmd_read(args):
    """Read file operation"""
    tool = ReadTool()
    result = tool.execute(file_path=args.path, offset=args.offset or 0, limit=args.limit)

    if result["success"]:
        print(result["content"])

        if args.limit or args.offset:
            summary = f"\n[Read {result['lines_read']} of {result['total_lines']} lines from {result['file_path']}]"
            print(summary, file=sys.stderr)

        return result
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return result


def cmd_write(args):
    """Write file operation"""
    # Get content from args or stdin
    content = args.content
    if content is None:
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            print("Error: No content provided. Use argument or pipe content.", file=sys.stderr)
            return {"success": False, "error": "No content provided"}

    tool = WriteTool()
    result = tool.execute(file_path=args.path, content=content, overwrite=args.overwrite)

    if result["success"]:
        print(f"File written: {result['file_path']} ({result['bytes_written']} bytes)")
        return result
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return result


def cmd_edit(args):
    """Edit file operation"""
    tool = EditTool()
    result = tool.execute(
        file_path=args.path,
        old_string=args.old_string,
        new_string=args.new_string,
        replace_all=args.replace_all,
    )

    if result["success"]:
        print(f"Edited: {result['file_path']}")
        print(f"Replacements: {result['replacements']}")
        print(f"  Old: {result['old_string']}")
        print(f"  New: {result['new_string']}")
        return result
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return result


def cmd_append(args):
    """Append to file operation"""
    # Get content from args or stdin
    content = args.content
    if content is None:
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            print("Error: No content provided. Use argument or pipe content.", file=sys.stderr)
            return {"success": False, "error": "No content provided"}

    # Read existing content if file exists
    file_path = Path(args.path)
    existing_content = ""
    if file_path.exists():
        try:
            existing_content = file_path.read_text()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    # Append content
    new_content = existing_content + content
    if not new_content.endswith("\n"):
        new_content += "\n"

    tool = WriteTool()
    result = tool.execute(file_path=args.path, content=new_content, overwrite=True)

    if result["success"]:
        print(f"Appended to: {result['file_path']} (+{len(content)} bytes)")
        return result
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return result


def cmd_smart(args):
    """Smart operation - auto-detect based on args"""
    file_path = Path(args.path)

    # If file exists and no content provided -> read
    if file_path.exists() and args.content is None:
        print(f"[Smart mode: Reading existing file]", file=sys.stderr)
        args.offset = 0
        args.limit = None
        return cmd_read(args)

    # If content provided -> write
    elif args.content is not None:
        print(f"[Smart mode: Writing to file]", file=sys.stderr)
        args.overwrite = True  # Smart mode always overwrites
        return cmd_write(args)

    # File doesn't exist and no content -> error
    else:
        error_msg = f"File does not exist: {args.path}. Provide content to create it."
        print(f"Error: {error_msg}", file=sys.stderr)
        return {"success": False, "error": error_msg}


def main():
    """Main entry point for unified /file command"""
    parser = argparse.ArgumentParser(
        description="Unified file operations - read, write, edit, append",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Read operations
  /file read myfile.py                     Read entire file
  /file read myfile.py --offset 10         Start from line 10
  /file read myfile.py --limit 50          Read first 50 lines

  # Write operations
  /file write newfile.txt "Hello World"    Create new file
  /file write file.txt "content" --overwrite   Overwrite existing
  echo "data" | /file write output.txt     Write from stdin

  # Edit operations
  /file edit app.py "old" "new"            Replace first occurrence
  /file edit app.py "bug" "fix" --replace-all  Replace all occurrences

  # Append operations
  /file append log.txt "New entry"         Append to file
  echo "data" | /file append output.txt    Append from stdin

  # Smart mode (auto-detect)
  /file myfile.txt                         Reads if exists
  /file myfile.txt "content"               Writes content

Subcommands:
  read      Read file contents with line numbers
  write     Create or overwrite file
  edit      Edit file with exact string replacement
  append    Append content to file
  (none)    Smart mode - auto-detect operation
        """,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="operation", help="File operation")

    # Read subcommand
    read_parser = subparsers.add_parser("read", help="Read file")
    read_parser.add_argument("path", help="File path")
    read_parser.add_argument("--offset", type=int, help="Line offset to start from")
    read_parser.add_argument("--limit", type=int, help="Maximum lines to read")

    # Write subcommand
    write_parser = subparsers.add_parser("write", help="Write file")
    write_parser.add_argument("path", help="File path")
    write_parser.add_argument("content", nargs="?", help="Content to write")
    write_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing file")

    # Edit subcommand
    edit_parser = subparsers.add_parser("edit", help="Edit file")
    edit_parser.add_argument("path", help="File path")
    edit_parser.add_argument("old_string", help="String to find")
    edit_parser.add_argument("new_string", help="Replacement string")
    edit_parser.add_argument("--replace-all", action="store_true", help="Replace all occurrences")

    # Append subcommand
    append_parser = subparsers.add_parser("append", help="Append to file")
    append_parser.add_argument("path", help="File path")
    append_parser.add_argument("content", nargs="?", help="Content to append")

    # Smart mode (no subcommand)
    parser.add_argument("path", nargs="?", help="File path (smart mode)")
    parser.add_argument("content", nargs="?", help="Content (smart mode)")

    try:
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(0)

        args = parser.parse_args()

        # Route to appropriate handler
        if args.operation == "read":
            result = cmd_read(args)
        elif args.operation == "write":
            result = cmd_write(args)
        elif args.operation == "edit":
            result = cmd_edit(args)
        elif args.operation == "append":
            result = cmd_append(args)
        elif args.path:  # Smart mode
            result = cmd_smart(args)
        else:
            parser.print_help()
            sys.exit(0)

        # Output JSON envelope for non-TTY
        if not sys.stdout.isatty():
            envelope = {"ok": result["success"], "result": result}
            print(json.dumps(envelope))

        sys.exit(0 if result["success"] else 1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

        if not sys.stdout.isatty():
            envelope = {"ok": False, "error": {"message": str(e)}}
            print(json.dumps(envelope))

        sys.exit(1)


if __name__ == "__main__":
    main()
