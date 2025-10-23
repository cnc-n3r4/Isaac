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
  /help [command]     - Show help (overview or detailed for command)
  /status [-v]        - Quick system status (verbose with -v)
  /config <subcmd>    - Configuration management
  /alias <subcmd>     - Unix-to-PowerShell alias management
  /mine <subcmd>      - xAI collection search and management
  /newfile [file]     - Create files with templates
  /clear              - Clear screen
  /exit, /quit        - Exit ISAAC

Collections (xAI Mining):
  /mine --list                  - Quick alias to --deed --all (legacy-friendly)
  /mine --deed [--all]          - Deed the claim: --all lists everything; no arg shows active details
  /mine --stake <name>          - Stake/create new claim (initial plot-out)
  /mine --claim <name>          - Claim/use/switch to a staked claim (enter the territory)
  /mine --drift <name>          - Carve/create drift (collection) within active claim
  /mine --muck <file>           - Muck file into active drift (upload waste rock & ore)
  /mine --dig <question>        - Dig answers from active drift/claim
  /mine --pan <drift>           - Pan file_ids in a specific drift
  /mine --haul <file_id>        - Haul file out of drift (extract by ID)
  /mine --haul <nugget_name>    - Haul file out by saved nugget name
  /mine --abandon <claim>       - Abandon/delete claim (drifts caved in)
  /mine --info                  - Quick alias to --deed (for active only)

Nugget Management:
  /mine --nuggets               - List all saved nuggets (named file_ids)
  /mine --nuggets save <coll>   - Save piped file_ids as named nuggets
  /mine --nuggets search <q>    - Search nuggets by name or filename

AI Interaction:
  /ask <question>    - Direct AI chat
  isaac <query>      - AI query or command translation

File Operations:
  /newfile <file>    - Create file with template
  /save <file>       - Save piped output to file

Piping (Experimental):
  <cmd> | <cmd>      - Chain commands together
  /mine --dig "query" | /ask "analyze this"
  /mine --pan collection | /mine --nuggets save collection
  ls | /save files.txt

Examples:
  /help /alias       - Detailed help for alias command
  /status -v         - Verbose system status
  /alias list        - Show available Unix aliases
  /mine --stake cnc-info       - Stake a new claim for CNC manuals
  /mine --claim cnc-info       - Enter the CNC manuals claim
  /mine --dig "g01 command"    - Dig for G01 command info
  /mine --pan cnc-info | /mine --nuggets save cnc-info  - Save file_ids as nuggets
  /mine --haul favorite_manual - Extract saved manual by nugget name
  /newfile script.py           - Create Python file with template
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

        "/newfile": """
Newfile Command - Detailed Help

USAGE:
  /newfile <file>                    - Create file with automatic template
  /newfile <file> --template <ext>   - Create with specific template
  /newfile <file> --content <text>   - Create with inline content
  /newfile <file> --force            - Overwrite existing files
  /newfile --list-templates          - Show available templates
  /newfile --set-template <ext> <content> - Set template for extension

EXAMPLES:
  /newfile script.py                - Create Python file with starter code
  /newfile notes.txt --content "My notes" - Create with custom content
  /newfile report.md --template .md - Use Markdown template
  /newfile config.json --force      - Overwrite existing config
  /newfile --set-template .sh "#!/bin/bash\\necho hello" - Set shell template

TEMPLATES:
  Automatic templates for: .py, .txt, .md, .json, .html, .css, .js
  Templates include starter code and common patterns
  Custom templates can be set per file extension

PATH HANDLING:
  Supports ~ for home directory (~/file.txt)
  Relative paths work from current directory
  Directories are created automatically
""".strip(),

        "/mine": """
Mine Command - Detailed Help

USAGE:
  /mine list                    - List all collections
  /mine use <name>              - Switch active collection
  /mine use <name> dig <text>   - Switch collection and search
  /mine create <name>           - Create new collection
  /mine cast <file>             - Upload file to active collection
  /mine dig <question>          - Search active collection
  /mine delete <name>           - Delete collection
  /mine info                    - Show active collection details
  /mine pan <collection>        - List file_ids in collection

EXAMPLES:
  /mine list                    - Show all available collections
  /mine use mydocs              - Switch to 'mydocs' collection
  /mine dig "what is CNC?"      - Search for CNC information
  /mine cast manual.pdf         - Upload PDF to active collection
  /mine create tutorials        - Create new 'tutorials' collection
  /mine pan mydocs              - List file IDs in 'mydocs'

COLLECTIONS:
  Collections store your documents for AI search
  Active collection is used for /mine dig searches
  Files are uploaded with /mine cast for later retrieval
  Supports multiple collections for different topics

SEARCH FEATURES:
  Natural language search across all uploaded documents
  Returns relevant excerpts with context
  Can be piped to other commands for analysis
""".strip(),
    }

    return help_map.get(command_name, f"No detailed help available for: {command_name}")


if __name__ == "__main__":
    main()