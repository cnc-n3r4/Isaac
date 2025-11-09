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
  /config --status     - System status check
  /config --ai         - AI provider details
  /config --ai-routing - AI routing configuration
  /config --cloud      - Cloud sync status
  /config --plugins    - List plugins
  /config --set <k> <v> - Change setting
  /config --apikey <service> <key> - Set API key
  /clear             - Clear screen
  /exit, /quit       - Exit ISAAC

Collections (xAI):
  /mine --list              - List all collections
  /mine --create <name>     - Create new collection
  /mine --use <name>        - Switch active collection
  /mine --delete <name>     - Delete collection
  /mine --upload <file>     - Upload file to collection
  /mine --search <query>    - Search active collection
  /mine --info              - Show collection details

AI Interaction:
  /ask <question>    - Direct AI chat (no execution)
  /a <question>      - Short alias for /ask
  isaac <query>      - AI query or command translation

File Operations:
  /read <file>       - Read file contents
  /write <file>      - Write/create file
  /edit <file>       - Edit existing file
  /newfile <name>    - Create new file
  /backup            - Backup config/session data
  /restore           - Restore from backup

Search & Navigation:
  /grep <pattern>    - Search files with regex
  /glob <pattern>    - Find files by pattern
  /list <name>       - Manage named lists
  /workspace         - Show workspace info

System Management:
  /alias             - Manage command aliases
  /sync              - Sync data with cloud
  /queue             - Show command queue
  <cmd> | <cmd>      - Chain commands together
  /mine --search "query" | /ask "analyze this"
  ls | /save files.txt

Examples:
  /help /config      - Detailed help for config command
  /status -v         - Verbose system status
  /mine --use cnc-info - Switch to CNC manuals collection
  /mine --search "g01" | /ask "explain this"
""".strip()


def get_detailed_help(command_name):
    """Show detailed help for a specific command"""
    help_map = {
        "/config": """
Config Command - Detailed Help

USAGE:
  /config                    - Show configuration overview
  /config --status           - Detailed system status
  /config --ai               - AI provider configuration
  /config --ai-routing       - AI routing configuration
  /config --cloud            - Cloud sync status
  /config --plugins          - List available plugins
  /config --collections      - xAI Collections status
  /config --set <key> <value> - Change configuration setting
  /config --apikey <service> <key> - Set API key for AI service

AI ROUTING CONFIGURATION:
  /config --ai-routing                         - View current routing settings
  /config --ai-routing-set <level> <provider>  - Set provider for complexity
  /config --ai-routing-model <prov> <model>    - Set model for provider
  /config --ai-routing-limits <period> <amt>   - Set cost limits
  /config --ai-routing-reset                   - Reset to defaults

EXAMPLES:
  /config                    - Show version, session, history
  /config --status          - Show cloud, AI, network status
  /config --ai              - Show AI provider and connection
  /config --ai-routing      - View routing configuration
  /config --set default_tier 3 - Change safety tier
  /config --apikey xai-chat YOUR_API_KEY - Set xAI chat API key
  /config --apikey claude YOUR_API_KEY - Set Claude API key

AI ROUTING EXAMPLES:
  /config --ai-routing-set simple grok - Use Grok for simple tasks
  /config --ai-routing-set complex claude - Use Claude for complex tasks
  /config --ai-routing-set code_write claude - Always use Claude for code
  /config --ai-routing-model claude claude-opus - Change Claude model
  /config --ai-routing-limits daily 10.0 - Set $10 daily limit
  /config --ai-routing-limits monthly 100.0 - Set $100 monthly limit

API KEY SERVICES:
  xai-chat        - xAI API key for chat completion
  xai-collections - xAI API key for collections
  claude          - Anthropic Claude API key
  openai          - OpenAI API key

ROUTING COMPLEXITY LEVELS:
  simple   - Quick answers, basic queries (default: openai)
  medium   - Standard questions, explanations (default: grok)
  complex  - Multi-step reasoning, code review (default: claude)
  expert   - Architecture, system design (default: claude)

ROUTING TASK TYPES:
  code_write  - Code generation (default: claude)
  code_debug  - Debugging and fixes (default: claude)
  tool_use    - Tool/function calling (default: claude)

SETTINGS:
  default_tier: Command safety level (1-4)
  sync_enabled: Enable cloud sync (true/false)
  ai_provider: AI service (xai, claude, etc.)
  ai_model: Specific AI model to use
""".strip(),

        "/mine": """
Mine Command - xAI Collections Manager

COLLECTION MANAGEMENT:
  /mine --create <name>     - Create new collection
  /mine --use <name>        - Switch to collection
  /mine --delete <name>     - Delete collection

FILE OPERATIONS:
  /mine --upload <file>     - Upload file to active collection
  /mine --search <query>    - Search active collection

INFORMATION:
  /mine --list              - List all collections
  /mine --info              - Show active collection details
  /mine --status            - Show system status
  /mine --help              - Show this help

DESCRIPTION:
  Search your personal file history using xAI Collections.
  This is YOUR stuff, not internet knowledge.

EXAMPLES:
  /mine --create mydocs     - Create collection
  /mine --use mydocs        - Switch to collection
  /mine --upload file.txt   - Upload file
  /mine --search "query"    - Search collection
  /mine --info              - Show collection info
""".strip(),

        "/ask": """
Ask Command - Direct AI Chat

USAGE:
  /ask <question>    - Query AI without command execution
  /a <question>      - Short alias for /ask

DESCRIPTION:
  Chat with AI directly without command execution.
  Unlike 'isaac <query>', this sends queries to AI
  and returns text responses without executing commands.

EXAMPLES:
  /ask where is alaska? - Geographic question
  /ask what is docker? - Technical explanation
  /ask explain kubernetes networking - Detailed information
  /a quick question - Short alias

DIFFERENCE FROM ISAAC:
  /ask - Conversational, returns text only
  isaac <query> - Translates to shell commands for execution
""".strip(),

        "/alias": """
Alias Command - Manage Command Aliases

USAGE:
  /alias                    - Show current aliases
  /alias --list             - List all aliases
  /alias --show <name>      - Show specific alias
  /alias --enable           - Enable alias system
  /alias --disable          - Disable alias system
  /alias --add <alias> <command> - Add new alias
  /alias --remove <alias>   - Remove alias

DESCRIPTION:
  Manage Unix-to-PowerShell command aliases for
  cross-platform command compatibility.

EXAMPLES:
  /alias --list             - Show all aliases
  /alias --show ls          - Show ls alias
  /alias --add ll "ls -la"  - Add ll alias
  /alias --enable           - Enable aliases
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
""".strip(),

        "/glob": """
Glob Command - Find Files by Pattern

USAGE:
  /glob <pattern>    - Find files matching glob pattern
  /glob <pattern> --type f|d - Filter by file type (files/directories)
  /glob <pattern> --max <n> - Limit results

DESCRIPTION:
  Search for files and directories using glob patterns.
  Supports wildcards: * (any chars), ? (single char), [abc] (character class)

EXAMPLES:
  /glob *.py              - Find all Python files
  /glob src/**/*.js       - Find JS files in src/ recursively
  /glob test_*.py --type f - Find test files only
  /glob *.log --max 10    - Find up to 10 log files

PATTERN SYNTAX:
  *     - Match any sequence of characters
  ?     - Match any single character
  [abc] - Match any character in the set
  **    - Match directories recursively
""".strip(),

        "/grep": """
Grep Command - Search Files with Regex

USAGE:
  /grep <pattern>              - Search all files for regex pattern
  /grep <pattern> <file>       - Search specific file
  /grep <pattern> --include *.py - Search only Python files
  /grep <pattern> --exclude *.log - Exclude log files
  /grep <pattern> -i           - Case insensitive search
  /grep <pattern> -n           - Show line numbers

DESCRIPTION:
  Search file contents using regular expressions.
  Supports full regex syntax with flags and file filtering.

EXAMPLES:
  /grep "def test_" *.py     - Find test functions in Python files
  /grep "TODO|FIXME" --include *.py - Find todos in code
  /grep "error" *.log -i     - Find errors case-insensitively
  /grep "^class " --include *.java - Find Java classes

REGEX FLAGS:
  -i    - Case insensitive
  -n    - Show line numbers
  -v    - Invert match (show non-matching lines)
""".strip(),

        "/read": """
Read Command - Display File Contents

USAGE:
  /read <file>              - Read entire file
  /read <file> --lines 1-10 - Read specific line range
  /read <file> --head 20    - Read first 20 lines
  /read <file> --tail 20    - Read last 20 lines

DESCRIPTION:
  Display the contents of text files with optional line filtering.

EXAMPLES:
  /read config.json         - Show entire config file
  /read script.py --lines 10-20 - Show lines 10-20
  /read log.txt --tail 50   - Show last 50 lines of log
  /read README.md --head 30 - Show first 30 lines

OPTIONS:
  --lines START-END    - Show specific line range
  --head N             - Show first N lines
  --tail N             - Show last N lines
""".strip(),

        "/write": """
Write Command - Create or Overwrite Files

USAGE:
  /write <file>             - Create file with editor
  /write <file> --content "text" - Write text directly
  /write <file> --append      - Append to existing file

DESCRIPTION:
  Create new files or overwrite existing ones with text content.

EXAMPLES:
  /write newfile.txt        - Create file with editor
  /write config.json --content '{"key": "value"}' - Write JSON
  /write log.txt --content "Entry" --append - Append to log

OPTIONS:
  --content TEXT       - Write text directly (no editor)
  --append             - Append to existing file instead of overwrite
""".strip(),

        "/edit": """
Edit Command - Modify Existing Files

USAGE:
  /edit <file>              - Edit file with editor
  /edit <file> --lines 1-10 - Edit specific line range
  /edit <file> --search "old" --replace "new" - Replace text

DESCRIPTION:
  Modify existing files using your configured editor or direct text replacement.

EXAMPLES:
  /edit script.py           - Edit Python file
  /edit config.json --lines 5-15 - Edit lines 5-15
  /edit README.md --search "old text" --replace "new text" - Replace text

OPTIONS:
  --lines START-END    - Edit specific line range
  --search TEXT        - Text to find
  --replace TEXT       - Replacement text
""".strip(),

        "/newfile": """
Newfile Command - Create New Files

USAGE:
  /newfile <name>           - Create new file with editor
  /newfile <name> --template <type> - Create from template

DESCRIPTION:
  Create new files with optional templates for common file types.

EXAMPLES:
  /newfile script.py        - Create Python file
  /newfile config.json --template json - Create JSON config
  /newfile README.md --template markdown - Create Markdown file

TEMPLATES:
  python, json, markdown, html, css, javascript, shell
""".strip(),

        "/backup": """
Backup Command - Backup Configuration

USAGE:
  /backup                  - Create backup of config and data
  /backup --list           - List available backups
  /backup --restore <name> - Restore from backup

DESCRIPTION:
  Create and manage backups of Isaac configuration and session data.

EXAMPLES:
  /backup                  - Create new backup
  /backup --list           - Show backup history
  /backup --restore 2025-01-01 - Restore specific backup

BACKUP CONTENTS:
  Configuration files, session data, command history, AI queries
""".strip(),

        "/restore": """
Restore Command - Restore from Backup

USAGE:
  /restore <backup>        - Restore from specific backup
  /restore --list          - List available backups
  /restore --latest        - Restore from most recent backup

DESCRIPTION:
  Restore Isaac configuration and data from backup archives.

EXAMPLES:
  /restore 2025-01-01      - Restore January 1st backup
  /restore --latest        - Restore most recent backup
  /restore --list          - Show available backups

RESTORE SCOPE:
  Configuration, preferences, command history, AI query history
""".strip(),

        "/list": """
List Command - Manage Named Lists

USAGE:
  /list                    - Show all lists
  /list <name>             - Show contents of named list
  /list <name> --add <item> - Add item to list
  /list <name> --remove <item> - Remove item from list
  /list <name> --clear     - Clear list

DESCRIPTION:
  Manage persistent named lists for organizing items like files, tasks, or references.

EXAMPLES:
  /list todos --add "Fix bug #123" - Add todo item
  /list files --add "*.py"        - Add file pattern
  /list favorites                 - Show favorite items
  /list temp --clear              - Clear temporary list

LIST TYPES:
  todos, files, favorites, bookmarks, temp, etc.
""".strip(),

        "/workspace": """
Workspace Command - Show Workspace Information

USAGE:
  /workspace               - Show current workspace details
  /workspace --files       - List all files in workspace
  /workspace --stats       - Show workspace statistics

DESCRIPTION:
  Display information about the current workspace and its contents.

EXAMPLES:
  /workspace               - Show workspace path and status
  /workspace --files       - List all files
  /workspace --stats       - Show file counts by type

INFORMATION:
  Workspace root, file count, directory structure, recent changes
""".strip(),

        "/sync": """
Sync Command - Cloud Synchronization

USAGE:
  /sync                    - Sync all data with cloud
  /sync --status           - Show sync status
  /sync --force            - Force full sync
  /sync --reset            - Reset sync state

DESCRIPTION:
  Synchronize Isaac data with cloud storage for cross-device access.

EXAMPLES:
  /sync                    - Normal sync operation
  /sync --status           - Check sync status
  /sync --force            - Force complete resync
  /sync --reset            - Clear sync state (use with caution)

SYNC DATA:
  Command history, AI queries, preferences, configuration
""".strip(),

        "/queue": """
Queue Command - Command Queue Management

USAGE:
  /queue                   - Show queued commands
  /queue --clear           - Clear command queue
  /queue --run             - Execute queued commands
  /queue --status          - Show queue status

DESCRIPTION:
  Manage the command execution queue for batch operations and offline execution.

EXAMPLES:
  /queue                   - Show pending commands
  /queue --run             - Execute all queued commands
  /queue --clear           - Remove all queued commands
  /queue --status          - Show queue statistics

QUEUE FEATURES:
  Batch execution, offline queuing, progress tracking
""".strip(),
    }

    return help_map.get(command_name, f"No detailed help available for: {command_name}")


if __name__ == "__main__":
    main()