#!/usr/bin/env python3
"""
Help Command Handler - Plugin format
"""

import sys
import json


def main():
    """Main entry point for help command"""
    # Read payload from stdin
    payload = json.loads(sys.stdin.read())
    args = payload.get("args", {})
    session = payload.get("session", {})

    # Get the requested command for detailed help
    command_name = args.get("command")

    if command_name:
        # Show detailed help for specific command
        output = get_detailed_help(command_name)
    else:
        # Show overview of all commands
        output = get_overview_help(session)

    # Return envelope
    print(json.dumps({
        "ok": True,
        "kind": "text",
        "stdout": output,
        "meta": {}
    }))


def get_overview_help(session):
    """Show overview of available commands"""
    return """
Available Commands:
  /help              - Show this help
  /status            - Quick system status
  /status -v         - Detailed status
  /config            - Configuration overview
  /config status     - System status check
  /config ai         - AI provider details
  /config cloud      - Cloud sync status
  /config plugins    - List plugins
  /config set <k> <v> - Change setting
  /clear             - Clear screen
  /exit, /quit       - Exit ISAAC

Collections (xAI):
  /mine list         - List all collections
  /mine use <name>   - Switch active collection
  /mine cast <file>  - Upload file to collection
  /mine dig <query>  - Search active collection
  /mine create <name> - Create new collection
  /mine delete <name> - Delete collection
  /mine info         - Show collection details

AI Interaction:
  /ask <question>    - Direct AI chat
  isaac <query>      - AI query or command translation

Piping (Experimental):
  <cmd> | <cmd>      - Chain commands together
  /mine dig "query" | /ask "analyze this"
  ls | /save files.txt

Examples:
  /help /config      - Detailed help for config command
  /status -v         - Verbose system status
  /mine use cnc-info - Switch to CNC manuals collection
  /mine dig "g01" | /ask "explain this"
""".strip()


def get_detailed_help(command_name):
    """Show detailed help for a specific command"""
    help_map = {
        "/config": """
Config Command - Detailed Help

USAGE:
  /config                    - Show configuration overview
  /config status            - Detailed system status
  /config ai                - AI provider configuration
  /config cloud             - Cloud sync status
  /config plugins           - List available plugins
  /config set <key> <value> - Change configuration setting

EXAMPLES:
  /config                    - Show version, session, history
  /config status            - Show cloud, AI, network status
  /config ai                - Show AI provider and connection
  /config set default_tier 3 - Change safety tier

SETTINGS:
  default_tier: Command safety level (1-4)
  sync_enabled: Enable cloud sync (true/false)
  ai_provider: AI service (xai, claude, etc.)
  ai_model: Specific AI model to use
""".strip(),

        "/status": """
Status Command - Detailed Help

USAGE:
  /status       - One-line system summary
  /status -v    - Detailed status (same as /config status)

EXAMPLES:
  /status       - Shows: Session ID, Cloud/AI status, History count
  /status -v    - Full system diagnostics

DISPLAY:
  Session: Machine identifier
  Cloud: ✓ Connected / ✗ Disabled / ✗ Unreachable
  AI: ✓ Available / ✗ No key / ✗ Unreachable
  History: Command count today
""".strip(),

        "/help": """
Help Command - Detailed Help

USAGE:
  /help              - Show command overview
  /help <command>    - Detailed help for specific command

EXAMPLES:
  /help              - List all available commands
  /help /config      - Show config command details
  /help /status      - Show status command details

ALIASES:
  /h, /?             - Same as /help
""".strip()
    }

    return help_map.get(command_name, f"No detailed help available for: {command_name}")


if __name__ == "__main__":
    main()