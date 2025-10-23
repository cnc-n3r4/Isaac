#!/usr/bin/env python3
"""
Alias Command Handler - Manage Unix-to-PowerShell command aliases
"""

import sys
import json
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.core.unix_aliases import UnixAliasTranslator


def main():
    """Main entry point for alias command"""
    try:
        # Read payload from stdin
        payload = json.loads(sys.stdin.read())
        args = payload.get("args", {})
        session = payload.get("session", {})

        subcommand = args.get("subcommand", "list")
        command = args.get("command")
        unix_cmd = args.get("unix_cmd")
        powershell_cmd = args.get("powershell_cmd")

        # Initialize translator
        translator = UnixAliasTranslator()

        if subcommand == "list":
            result = handle_list(translator)
        elif subcommand == "show":
            if not command:
                result = "Usage: /alias show <command>"
            else:
                result = handle_show(translator, command)
        elif subcommand == "enable":
            result = handle_enable(session)
        elif subcommand == "disable":
            result = handle_disable(session)
        elif subcommand == "add":
            if not unix_cmd or not powershell_cmd:
                result = "Usage: /alias add <unix_cmd> <powershell_cmd>"
            else:
                result = handle_add(session, unix_cmd, powershell_cmd)
        elif subcommand == "remove":
            if not unix_cmd:
                result = "Usage: /alias remove <unix_cmd>"
            else:
                result = handle_remove(session, unix_cmd)
        elif subcommand == "help":
            result = handle_help()
        else:
            result = f"Unknown subcommand: {subcommand}\n\n{handle_help()}"

        # Return envelope
        print(json.dumps({
            "ok": True,
            "stdout": result,
            "meta": {"command": "/alias", "subcommand": subcommand}
        }))

    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": {
                "code": "ALIAS_ERROR",
                "message": str(e)
            }
        }))


def handle_list(translator: UnixAliasTranslator) -> str:
    """Show all available aliases"""
    aliases = translator.list_aliases()

    if not aliases:
        return "No aliases available"

    result = "Available Unix aliases:\n\n"
    for cmd, desc in sorted(aliases.items()):
        result += f"  {cmd:<10} → {desc}\n"

    result += "\nUse '/alias show <command>' for details and examples"
    return result


def handle_show(translator: UnixAliasTranslator, command: str) -> str:
    """Show translation for specific command"""
    description = translator.get_description(command)
    if not description:
        return f"No alias found for: {command}"

    examples = translator.get_examples(command)

    result = f"{command}: {description}\n\n"

    if examples:
        result += "Examples:\n"
        for example in examples:
            unix = example.get('unix', '')
            powershell = example.get('powershell', '')
            result += f"  Unix:    {unix}\n"
            result += f"  PowerShell: {powershell}\n\n"

    return result.strip()


def handle_enable(session) -> str:
    """Enable Unix alias translation"""
    # Update session config
    session['enable_unix_aliases'] = True
    session['show_translated_command'] = True

    return "Unix alias translation enabled. Commands like 'ls' will be translated to PowerShell equivalents."


def handle_disable(session) -> str:
    """Disable Unix alias translation"""
    session['enable_unix_aliases'] = False

    return "Unix alias translation disabled. Unix commands will fail normally."


def handle_add(session, unix_cmd: str, powershell_cmd: str) -> str:
    """Add custom alias"""
    overrides = session.get('alias_overrides', {})
    overrides[unix_cmd] = powershell_cmd
    session['alias_overrides'] = overrides

    return f"Added alias: {unix_cmd} → {powershell_cmd}"


def handle_remove(session, unix_cmd: str) -> str:
    """Remove custom alias"""
    overrides = session.get('alias_overrides', {})
    if unix_cmd in overrides:
        del overrides[unix_cmd]
        session['alias_overrides'] = overrides
        return f"Removed alias: {unix_cmd}"
    else:
        return f"No custom alias found for: {unix_cmd}"


def handle_help() -> str:
    """Show help for alias command"""
    return """
Alias Command - Unix-to-PowerShell Translation

USAGE:
  /alias                    - List all available aliases
  /alias list              - Show all Unix-to-PowerShell aliases
  /alias show <command>    - Show details for specific Unix command
  /alias enable            - Enable Unix alias translation
  /alias disable           - Disable Unix alias translation
  /alias add <unix> <ps>   - Add custom alias mapping
  /alias remove <unix>     - Remove custom alias
  /alias help              - Show this help

EXAMPLES:
  /alias                   - Show ls → Get-ChildItem, cd → Set-Location, etc.
  /alias show ls          - Show PowerShell equivalent and examples
  /alias enable           - Enable automatic Unix→PowerShell translation
  /alias add ll "ls -la"  - Add custom alias for detailed listing

For detailed help, use: /help /alias
""".strip()


if __name__ == "__main__":
    main()