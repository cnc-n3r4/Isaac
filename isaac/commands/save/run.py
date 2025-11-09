"""
Save Handler - Save piped data to files
Provides /save command for saving blob content to files
"""

import json
import sys
from pathlib import Path


def main():
    """Main entry point for save command"""
    try:
        # Check if we're being called through dispatcher (stdin has JSON) or standalone
        if not sys.stdin.isatty():
            # Called through dispatcher - read JSON payload from stdin
            stdin_data = sys.stdin.read()

            # Try to parse as blob format first (for piping)
            try:
                blob = json.loads(stdin_data)
                if isinstance(blob, dict) and "kind" in blob:
                    # This is piped input in blob format
                    content = blob.get("content", "")
                    kind = blob.get("kind", "text")
                    meta = blob.get("meta", {})

                    # Extract command from blob meta if available
                    command = meta.get("command", "/save")

                    # Parse command to get filename
                    filename = None
                    if command.startswith("/save "):
                        filename = command[6:].strip()

                    if not filename:
                        # Try to get filename from args or use default
                        filename = "saved_output.txt"

                    # Save content to file
                    result = save_content(content, filename, kind)

                    # Return blob result
                    print(
                        json.dumps(
                            {
                                "kind": "text",
                                "content": result,
                                "meta": {"command": command, "saved_file": filename},
                            }
                        )
                    )
                else:
                    # This is dispatcher JSON payload
                    payload = blob
                    command = payload.get("command", "")

                    # Strip the trigger to get filename
                    filename = ""
                    if command.startswith("/save "):
                        filename = command[6:].strip()

                    if not filename:
                        print(
                            json.dumps(
                                {
                                    "kind": "error",
                                    "content": "Error: No filename provided. Usage: /save <filename>",
                                    "meta": {"command": command},
                                }
                            )
                        )
                        return

                    # For dispatcher mode without piped input, create empty file or show usage
                    result = save_content("", filename, "text")

                    print(
                        json.dumps(
                            {
                                "kind": "text",
                                "content": result,
                                "meta": {"command": command, "saved_file": filename},
                            }
                        )
                    )
            except json.JSONDecodeError:
                # Not JSON, treat as plain text content to save
                content = stdin_data
                filename = "saved_output.txt"  # Default filename

                result = save_content(content, filename, "text")

                print(
                    json.dumps(
                        {
                            "kind": "text",
                            "content": result,
                            "meta": {"command": "/save", "saved_file": filename},
                        }
                    )
                )
        else:
            # Standalone execution - get filename from command line args
            if len(sys.argv) < 2:
                print("Usage: python -m isaac.commands.save.run <filename>")
                print("Or: <command> | /save <filename> (within Isaac shell)")
                sys.exit(1)

            filename = sys.argv[1]

            # For standalone mode, read from stdin if available
            if not sys.stdin.isatty():
                content = sys.stdin.read()
                kind = "text"
            else:
                content = ""
                kind = "text"

            result = save_content(content, filename, kind)
            print(result)

    except Exception as e:
        if not sys.stdin.isatty():
            # Piped/dispatcher mode - return blob error
            print(
                json.dumps(
                    {"kind": "error", "content": f"Error: {e}", "meta": {"command": "/save"}}
                )
            )
        else:
            # Standalone mode - print error directly
            print(f"Error: {e}")


def save_content(content: str, filename: str, kind: str = "text") -> str:
    """Save content to a file."""
    try:
        # Expand user home directory if needed
        expanded_path = Path(filename).expanduser()

        # Create directory if it doesn't exist
        expanded_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine file mode based on content kind
        mode = "w"
        if kind in ["binary", "json"] and isinstance(content, str):
            # For binary/json content that comes as string, we still write as text
            mode = "w"
        elif kind == "binary":
            mode = "wb"

        # Write content to file
        with open(expanded_path, mode, encoding="utf-8") as f:
            f.write(content)

        return f"Content saved to: {expanded_path}"

    except Exception as e:
        return f"Error saving to {filename}: {e}"


if __name__ == "__main__":
    main()
