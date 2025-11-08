#!/usr/bin/env python3
"""
Newfile Command Handler - Create and manage files with templates
Provides /newfile command for creating files with templates and proper path handling
"""

import os
import json
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.core.session_manager import SessionManager


def main():
    """Main entry point for newfile command"""
    try:
        # Read payload from stdin
        stdin_content = sys.stdin.read()

        # Try to parse as JSON (normal Isaac command invocation)
        try:
            payload = json.loads(stdin_content)

            # Check if this is a piped command or normal command payload
            if 'piped_blob' in payload:
                # Piped command - extract blob and args
                piped_blob = payload['piped_blob']
                if piped_blob['kind'] == 'text':
                    piped_content = piped_blob['content']
                    args_list = payload.get("args", [])
                    args_raw = " ".join(args_list) if args_list else ""
                elif piped_blob['kind'] == 'error':
                    # Propagate error from previous command
                    print(json.dumps({
                        "ok": False,
                        "error": {
                            "code": "PIPE_ERROR",
                            "message": f"Previous command failed: {piped_blob.get('content', 'Unknown error')}"
                        }
                    }))
                    return
                else:
                    # Unknown blob type
                    print(json.dumps({
                        "ok": False,
                        "error": {
                            "code": "UNSUPPORTED_BLOB",
                            "message": f"Unsupported blob type: {piped_blob['kind']}"
                        }
                    }))
                    return
            elif 'stdin' in payload and payload.get('stdin'):
                # PipeEngine format - piped content in stdin field
                piped_content = payload['stdin']
                args_list = payload.get("args", [])
                args_raw = " ".join(args_list) if args_list else ""
            elif 'kind' in payload:
                # Legacy pipe blob format (fallback)
                if payload['kind'] == 'text':
                    piped_content = payload['content']
                    args_raw = payload.get('meta', {}).get('command', '').replace('/newfile', '').strip()
                    payload = None
                elif payload['kind'] == 'error':
                    print(json.dumps({
                        "ok": False,
                        "error": {
                            "code": "PIPE_ERROR",
                            "message": f"Previous command failed: {payload.get('content', 'Unknown error')}"
                        }
                    }))
                    return
                else:
                    print(json.dumps({
                        "ok": False,
                        "error": {
                            "code": "UNSUPPORTED_BLOB",
                            "message": f"Unsupported blob type: {payload['kind']}"
                        }
                    }))
                    return
            else:
                # Normal command payload
                args_list = payload.get("args", [])
                args_raw = " ".join(args_list) if args_list else ""
                piped_content = None

        except json.JSONDecodeError:
            # Not JSON - treat as piped content (fallback for compatibility)
            payload = None
            args_raw = ""
            piped_content = stdin_content.strip()

        # Parse arguments using argparse
        parser = argparse.ArgumentParser(
            prog="/newfile",
            description="Create files with templates",
            add_help=False
        )

        if piped_content is not None:
            # When piped content is provided, require a filename
            parser.add_argument("file", help="File to create")
            parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing files")
        else:
            # Normal mode with all options
            parser.add_argument("file", nargs="?", help="File to create")
            parser.add_argument("--template", "-t", help="Template extension to use")
            parser.add_argument("--content", "-c", help="Inline content for the file")
            parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing files")
            parser.add_argument("--list-templates", "-l", action="store_true", help="List available templates")
            parser.add_argument("--set-template", "-s", nargs=2, metavar=("EXT", "CONTENT"), help="Set template for extension")
            parser.add_argument("--help", "-h", action="store_true", help="Show help")

        # Parse the arguments
        import io
        old_stderr = sys.stderr
        try:
            # Temporarily redirect stderr to suppress argparse error messages
            sys.stderr = io.StringIO()
            parsed_args = parser.parse_args(args_raw.split() if args_raw else [])
        except SystemExit:
            # Argparse calls sys.exit on error, catch it and show help
            result = handle_help()
            print(json.dumps({"ok": True, "stdout": result, "meta": {"command": "/newfile"}}))
            return
        finally:
            # Restore stderr
            sys.stderr = old_stderr

        # Get session manager
        session_manager = SessionManager()

        # Route to appropriate handler
        if piped_content is not None:
            # Piped content mode - create file with piped content
            if not parsed_args.file:
                result = "File name required for piped content. Usage: command | /newfile <filename>"
            else:
                result = handle_create_file(session_manager, parsed_args.file,
                                          None, piped_content, parsed_args.force)
        elif parsed_args.help:
            result = handle_help()
        elif parsed_args.list_templates:
            result = handle_list_templates(session_manager)
        elif parsed_args.set_template:
            ext, content = parsed_args.set_template
            result = handle_set_template(session_manager, ext, content)
        elif not parsed_args.file and not parsed_args.template and not parsed_args.content and not parsed_args.force:
            # No arguments provided at all - show help
            result = handle_help()
        elif not parsed_args.file:
            result = "File name required. Usage: /newfile <filename> [options]"
        else:
            # Create file operation
            result = handle_create_file(session_manager, parsed_args.file,
                                      parsed_args.template,
                                      parsed_args.content,
                                      parsed_args.force)

        # Return Isaac envelope
        print(json.dumps({
            "ok": True,
            "stdout": result,
            "meta": {"command": "/newfile"}
        }))

    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": {
                "code": "NEWFILE_ERROR",
                "message": str(e)
            }
        }))


def handle_list_templates(session_manager: SessionManager) -> str:
    """List available templates"""
    templates = get_templates(session_manager)

    if not templates:
        return "No templates available"

    result = "Available templates:\n\n"
    for ext in sorted(templates.keys()):
        items = templates[ext]
        if isinstance(items, list) and items and isinstance(items[0], dict):
            desc = items[0].get("desc", "") or "(no description)"
            result += f"  {ext:<8} → {desc}\n"
        else:
            result += f"  {ext:<8} → (invalid template)\n"

    result += "\nUse /newfile <file> --template <ext> to use a template"
    return result


def handle_set_template(session_manager: SessionManager, ext: str, content: str) -> str:
    """Set template for extension"""
    # Normalize extension
    if not ext.startswith("."):
        ext = f".{ext}"

    templates = get_templates(session_manager)
    templates[ext.lower()] = [{"desc": f"Custom template for {ext}", "body": content}]

    # Save to session
    config = session_manager.get_config()
    config["newfile_templates"] = templates
    session_manager._save_config()

    return f"Template set for {ext}"


def handle_create_file(session_manager: SessionManager, filename: str,
                      template: Optional[str], content: Optional[str],
                      force: bool) -> str:
    """Create a new file"""
    try:
        # Strip surrounding quotes if present (PowerShell/Windows may include them)
        filename = filename.strip('"').strip("'")

        # Expand path properly for Windows
        filepath = Path(filename).expanduser().resolve()

        # Create parent directories if needed
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists
        if filepath.exists() and not force:
            return f"File {filepath} exists. Use --force to overwrite."

        # Get content
        file_content = ""
        if content:
            # Inline content provided
            file_content = content
        elif template:
            # Use template
            templates = get_templates(session_manager)
            template_content = get_template_content(templates, template, filepath.suffix)
            if template_content:
                file_content = template_content
        else:
            # Use default template for extension
            templates = get_templates(session_manager)
            template_content = get_template_content(templates, filepath.suffix, filepath.suffix)
            if template_content:
                file_content = template_content

        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(file_content)

        return f"File created: {filepath}"

    except Exception as e:
        return f"Error creating file: {e}"


def get_templates(session_manager: SessionManager) -> Dict[str, Any]:
    """Get templates from session config"""
    config = session_manager.get_config()
    templates = config.get("newfile_templates", get_default_templates())
    # Validate that templates is a dict with proper structure
    if not isinstance(templates, dict):
        return get_default_templates()
    # Clean invalid entries
    cleaned = {}
    for ext, items in templates.items():
        if isinstance(items, list) and items and isinstance(items[0], dict):
            cleaned[ext] = items
    # Merge with defaults for missing extensions
    defaults = get_default_templates()
    for ext, items in defaults.items():
        if ext not in cleaned:
            cleaned[ext] = items
    return cleaned


def get_default_templates() -> Dict[str, Any]:
    """Get default templates"""
    return {
        ".py": [{"desc": "Python starter", "body": "#!/usr/bin/env python\nif __name__=='__main__':\n    print('hello')\n"}],
        ".txt": [{"desc": "Plain notes", "body": "# Notes\n"}],
        ".md": [{"desc": "Markdown doc", "body": "# Markdown Document\n"}],
        ".json": [{"desc": "Basic JSON", "body": "{\n  \"name\": \"new_project\"\n}\n"}],
        ".html": [{"desc": "HTML skeleton", "body": "<!DOCTYPE html>\n<html>\n<head>\n  <meta charset=\"utf-8\" />\n  <title>New File</title>\n</head>\n<body>\n</body>\n</html>\n"}]
    }


def get_template_content(templates: Dict[str, Any], template_spec: str, file_ext: str) -> Optional[str]:
    """Get template content for given spec"""
    # Try exact extension match first
    ext_key = template_spec.lower()
    if not ext_key.startswith("."):
        ext_key = f".{ext_key}"

    if ext_key in templates:
        items = templates[ext_key]
        if isinstance(items, list) and items and isinstance(items[0], dict):
            return items[0].get("body", "")

    # Try file extension match
    file_ext_key = file_ext.lower()
    if file_ext_key in templates:
        items = templates[file_ext_key]
        if isinstance(items, list) and items and isinstance(items[0], dict):
            return items[0].get("body", "")

    return None


def handle_help() -> str:
    """Show help for newfile command"""
    return """
Newfile Command - Create files with templates

USAGE:
  /newfile <file>                    - Create file with automatic template
  /newfile <file> --template <ext>   - Create with specific template
  /newfile <file> --content <text>   - Create with inline content
  /newfile <file> --force            - Overwrite existing files
  /newfile --list-templates          - Show available templates
  /newfile --set-template <ext> <content> - Set template for extension
  /newfile --help                    - Show this help

EXAMPLES:
  /newfile script.py                - Create Python file with starter code
  /newfile notes.txt --content "My notes" - Create with custom content
  /newfile report.md --template .md - Use Markdown template

For detailed help, use: /help /newfile
""".strip()


if __name__ == "__main__":
    main()
