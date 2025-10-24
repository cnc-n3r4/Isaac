# /newfile Command Implementation Guide

## Overview
Implement a new meta-command `/newfile` for creating and managing text files within Isaac. This replaces the problematic `/save` command with proper path handling, templates, and safety features.

## Requirements

### Core Functionality
- **Command Syntax**: `/newfile <file> [options]`
- **Path Handling**: Support `~` expansion, relative paths, Windows compatibility
- **Safety**: Tier 3 classification with confirmation for overwrites
- **Output**: JSON envelope responses for Isaac integration
- **Templates**: Built-in templates for common file types

### Command Options
- `file` (string) - Target filename to create
- `template` (string) - Template extension to use (e.g., ".py")
- `content` (string) - Inline content for file creation
- `force` (boolean) - Overwrite existing files without confirmation
- `list_templates` (boolean) - Display available templates
- `set_template_ext` (string) - Extension for custom template
- `set_template_content` (string) - Content for custom template
- `help` (boolean) - Show command help

## Implementation Structure

### File Locations
```
isaac/commands/newfile/
├── command.yaml    # Command definition for dispatcher
└── run.py         # Main implementation
```

### command.yaml Structure
```yaml
name: newfile
version: 1.0.0
summary: "Create files with templates and proper path handling"

triggers: ["/newfile"]

args:
  - name: file
    type: string
    required: false
    help: "File to create"
  - name: template
    type: string
    required: false
    help: "Template extension to use"
  - name: content
    type: string
    required: false
    help: "Inline content for the file"
  - name: force
    type: boolean
    required: false
    help: "Overwrite existing files"
  - name: list_templates
    type: boolean
    required: false
    help: "List available templates"
  - name: set_template_ext
    type: string
    required: false
    help: "Extension for set-template"
  - name: set_template_content
    type: string
    required: false
    help: "Content for set-template"
  - name: help
    type: boolean
    required: false
    help: "Show help"
```

## Code Implementation

### run.py Structure

#### Main Entry Point
```python
#!/usr/bin/env python3
"""
Newfile Command Handler - Create and manage files with templates
"""

import os
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.core.session_manager import SessionManager

def main():
    """Main entry point for newfile command"""
    try:
        # Read payload from stdin (Isaac dispatcher format)
        payload = json.loads(sys.stdin.read())
        args = payload.get("args", {})
        session = payload.get("session", {})

        # Get session manager
        session_manager = SessionManager()

        # Route to appropriate handler
        if args.get("help"):
            result = handle_help()
        elif args.get("list_templates"):
            result = handle_list_templates(session_manager)
        elif args.get("set_template_ext") and args.get("set_template_content"):
            result = handle_set_template(session_manager,
                                       args.get("set_template_ext"),
                                       args.get("set_template_content"))
        else:
            # Create file operation
            filename = args.get("file")
            if not filename:
                return {
                    "ok": False,
                    "error": {
                        "code": "MISSING_FILE",
                        "message": "File name required. Usage: /newfile <filename> [options]"
                    }
                }
            result = handle_create_file(session_manager, filename,
                                      args.get("template"),
                                      args.get("content"),
                                      args.get("force", False))

        # Return Isaac envelope
        return {
            "ok": True,
            "stdout": result,
            "meta": {"command": "/newfile"}
        }

    except Exception as e:
        return {
            "ok": False,
            "error": {
                "code": "NEWFILE_ERROR",
                "message": str(e)
            }
        }
```

#### Core Functions

### handle_create_file()
```python
def handle_create_file(session_manager: SessionManager, filename: str,
                      template: Optional[str], content: Optional[str],
                      force: bool) -> str:
    """Create a new file with optional template or content"""
    try:
        # Expand path properly for Windows
        filepath = Path(filename).expanduser().resolve()

        # Create parent directories if needed
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists
        if filepath.exists() and not force:
            return f"File {filepath} exists. Use --force to overwrite."

        # Determine file content
        file_content = ""
        if content:
            # Inline content provided
            file_content = content
        elif template:
            # Use specified template
            templates = get_templates(session_manager)
            file_content = get_template_content(templates, template, filepath.suffix)
        else:
            # Use default template for extension
            templates = get_templates(session_manager)
            file_content = get_template_content(templates, filepath.suffix, filepath.suffix)

        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(file_content)

        return f"File created: {filepath}"

    except Exception as e:
        return f"Error creating file: {e}"
```

### Template System

#### get_default_templates()
```python
def get_default_templates() -> Dict[str, Any]:
    """Get built-in templates for common file types"""
    return {
        ".py": [{"desc": "Python starter", "body": "#!/usr/bin/env python\nif __name__=='__main__':\n    print('hello')\n"}],
        ".txt": [{"desc": "Plain notes", "body": "# Notes\n"}],
        ".md": [{"desc": "Markdown doc", "body": "# Markdown Document\n"}],
        ".json": [{"desc": "Basic JSON", "body": "{\n  \"name\": \"new_project\"\n}\n"}],
        ".html": [{"desc": "HTML skeleton", "body": "<!DOCTYPE html>\n<html>\n<head>\n  <meta charset=\"utf-8\" />\n  <title>New File</title>\n</head>\n<body>\n</body>\n</html>\n"}]
    }
```

#### get_templates()
```python
def get_templates(session_manager: SessionManager) -> Dict[str, Any]:
    """Get templates from session config, fallback to defaults"""
    config = session_manager.get_config()
    return config.get("newfile_templates", get_default_templates())
```

#### handle_set_template()
```python
def handle_set_template(session_manager: SessionManager, ext: str, content: str) -> str:
    """Set custom template for file extension"""
    # Normalize extension
    if not ext.startswith("."):
        ext = f".{ext}"

    # Get current templates
    templates = get_templates(session_manager)

    # Set new template
    templates[ext.lower()] = [{"desc": f"Custom template for {ext}", "body": content}]

    # Save to session
    session_manager.config["newfile_templates"] = templates
    session_manager._save_config()

    return f"Template set for {ext}"
```

### Helper Functions

#### get_template_content()
```python
def get_template_content(templates: Dict[str, Any], template_spec: str, file_ext: str) -> Optional[str]:
    """Get template content for given specification"""
    # Try exact extension match first
    ext_key = template_spec.lower()
    if not ext_key.startswith("."):
        ext_key = f".{ext_key}"

    if ext_key in templates:
        items = templates[ext_key]
        if isinstance(items, list) and items:
            return items[0].get("body", "")

    # Try file extension match
    file_ext_key = file_ext.lower()
    if file_ext_key in templates:
        items = templates[file_ext_key]
        if isinstance(items, list) and items:
            return items[0].get("body", "")

    return None
```

#### handle_list_templates()
```python
def handle_list_templates(session_manager: SessionManager) -> str:
    """List available templates"""
    templates = get_templates(session_manager)

    if not templates:
        return "No templates available"

    result = "Available templates:\n\n"
    for ext in sorted(templates.keys()):
        items = templates[ext]
        if isinstance(items, list) and items:
            desc = items[0].get("desc", "") or "(no description)"
            result += f"  {ext:<8} → {desc}\n"
        else:
            result += f"  {ext:<8} → (template)\n"

    result += "\nUse /newfile <file> --template <ext> to use a template"
    return result
```

#### handle_help()
```python
def handle_help() -> str:
    """Show command help"""
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
```

## Integration Points

### Session Manager Integration
- Templates stored in `session_manager.config["newfile_templates"]`
- Use `session_manager._save_config()` to persist changes
- Access via `session_manager.get_config()`

### Command Dispatcher
- Command registered via `command.yaml`
- Arguments parsed automatically by dispatcher
- Results returned in JSON envelope format

### Error Handling
- All exceptions caught and returned as JSON error envelopes
- File operation errors handled gracefully
- Path validation and expansion

## Testing Requirements

### Unit Tests (tests/test_special_commands.py)
```python
def test_newfile_basic():
    # Test basic file creation

def test_newfile_with_template():
    # Test template usage

def test_newfile_force_overwrite():
    # Test force overwrite

def test_newfile_path_expansion():
    # Test ~ expansion and Windows paths

def test_newfile_custom_template():
    # Test setting and using custom templates
```

### Integration Tests
- Test with Isaac session manager
- Test command dispatcher integration
- Test JSON envelope responses

## Implementation Steps

1. **Create directory structure**: `isaac/commands/newfile/`
2. **Implement command.yaml**: Define command arguments and metadata
3. **Implement run.py**: Core logic with all handler functions
4. **Add default templates**: Basic templates for common file types
5. **Integrate with session**: Template persistence and config management
6. **Add error handling**: Comprehensive exception handling
7. **Write tests**: Unit and integration tests
8. **Update help system**: Add to `/help` command

## Acceptance Criteria
- [ ] Creates files with proper Windows path handling
- [ ] Supports `~` expansion and relative paths
- [ ] Handles file overwrites safely with --force
- [ ] Provides useful templates for common file types
- [ ] Allows custom template creation and management
- [ ] Returns proper JSON envelopes for Isaac integration
- [ ] Integrates with session manager for persistence
- [ ] Includes comprehensive help and usage examples
- [ ] Passes all unit and integration tests