# ISAAC COMMAND REFERENCE v2.0
**Comprehensive Command Documentation**
**Date:** 2025-11-09
**Total Commands:** 50+

---

## HOW TO USE THIS REFERENCE

**Quick Navigation:**
- [File Operations](#file-operations) - read, write, edit, file, glob, grep, search
- [System & Configuration](#system--configuration) - config, status, help, debug, update
- [AI & Analysis](#ai--analysis) - ask, analyze, mine, summarize
- [Workspace & Projects](#workspace--projects) - workspace, backup, restore, sync
- [Collaboration & Tasks](#collaboration--tasks) - tasks, msg, team, pair, learn
- [Advanced Features](#advanced-features) - machine, bubble, pipeline, alias, script

**Conventions:**
- 🟢 **Fully Functional** - Ready to use
- 🟡 **Partially Functional** - Works but needs improvement
- 🔴 **Placeholder/Stub** - Not implemented
- ⭐ **Recommended** - Best practice command

---

## QUICK REFERENCE TABLE

| Command | Category | Status | One-Line Description |
|---------|----------|--------|---------------------|
| `/ask` | AI | 🟢 | Direct AI chat without command execution |
| `/alias` | System | 🟢 | Manage Unix-to-PowerShell command aliases |
| `/analyze` | AI | 🟢 | AI analysis of piped data |
| `/backup` | System | 🔴 | Backup configuration (placeholder) |
| `/bubble` | Advanced | 🟡 | Workspace state management |
| `/config` | System | 🟢⭐ | Configuration management |
| `/debug` | System | 🟡 | Debug analysis and diagnostics |
| `/edit` | Files | 🟢⭐ | Edit files with exact string replacement |
| `/file` | Files | 🟢⭐ | Unified file operations (read/write/edit/append) |
| `/glob` | Files | 🟢⭐ | Find files by pattern matching |
| `/grep` | Files | 🟢⭐ | Search files with regex |
| `/help` | System | 🟢⭐ | Command help system |
| `/images` | Cloud | 🟡 | Cloud image storage |
| `/learn` | Collab | 🟡 | Self-improving learning system |
| `/list` | System | 🔴 | Named list management (placeholder) |
| `/machine` | Advanced | 🟢 | Machine registry (single) |
| `/machines` | Advanced | 🟢 | Machine orchestration status |
| `/man` | System | 🟢 | Manual pages |
| `/mine` | AI | 🟢⭐ | xAI Collections manager |
| `/msg` | Collab | 🟢 | Message queue management |
| `/newfile` | Files | 🟢⭐ | Create files with templates |
| `/pair` | Collab | 🟡 | Collaborative pair programming |
| `/pipeline` | Advanced | 🔴 | Pipeline execution (stub) |
| `/read` | Files | 🟢⭐ | Read files with line numbers |
| `/resources` | Advanced | 🟡 | Resource management |
| `/restore` | System | 🟡 | Restore from backup |
| `/save` | System | 🟡 | Save operations |
| `/script` | Advanced | 🟡 | Scripting support |
| `/search` | Files | 🟢⭐ | Unified search (glob + grep auto-detect) |
| `/share` | Collab | 🟡 | Sharing features |
| `/status` | System | 🟢 | System status dashboard |
| `/summarize` | AI | 🟡 | Text summarization |
| `/sync` | Cloud | 🟡 | Cloud synchronization |
| `/tasks` | Collab | 🟢 | Background task management |
| `/team` | Collab | 🟡 | Team collaboration |
| `/timemachine` | Advanced | 🔴 | Time machine (stub) |
| `/update` | System | 🟡 | System updates |
| `/upload` | Cloud | 🟡 | File uploads |
| `/watch` | Files | 🟡 | File watching |
| `/workspace` | Workspace | 🟡 | Workspace management |
| `/write` | Files | 🟢⭐ | Create new files |

---

## FILE OPERATIONS

### `/read` - Read Files with Line Numbers 🟢⭐

**Purpose**: Display file contents with line numbers and optional range filtering.

**Syntax**:
```bash
/read <file_path>
/read <file_path> --offset <n>
/read <file_path> --limit <n>
/read <file_path> --offset <n> --limit <n>
```

**Arguments**:
- `file_path` (required): Path to file to read
- `--offset <n>` (optional): Line number to start from (0-indexed, default: 0)
- `--limit <n>` (optional): Maximum number of lines to read (default: all)
- `--help-cmd`: Show help message

**Default Values**:
- `offset`: 0 (start from beginning)
- `limit`: None (read entire file)

**Examples**:
```bash
# Read entire file
/read myfile.py

# Read from line 100 onwards
/read myfile.py --offset 100

# Read first 50 lines
/read myfile.py --limit 50

# Read 50 lines starting from line 100
/read myfile.py --offset 100 --limit 50
```

**Output**:
- Human-readable: File contents with line numbers
- Summary to stderr: Line count and range
- JSON envelope (non-TTY): `{"ok": true, "stdout": "..."}`

**Platform Support**: All platforms
**Safety Tier**: 1 (instant execution)
**Related Commands**: `/write`, `/edit`, `/file`, `/grep`

---

### `/write` - Create New Files 🟢⭐

**Purpose**: Create new files with content from argument or stdin.

**Syntax**:
```bash
/write <file_path> <content>
/write <file_path> --overwrite
echo "content" | /write <file_path>
```

**Arguments**:
- `file_path` (required): Path to file to create
- `content` (optional): Content to write (or use stdin if omitted)
- `--overwrite` (optional): Allow overwriting existing files (default: false)
- `--help-cmd`: Show help message

**Default Values**:
- `overwrite`: false (prevent accidental overwrites)
- `content`: Read from stdin if not provided

**Examples**:
```bash
# Write text directly
/write newfile.txt "Hello World"

# Write with overwrite permission
/write file.txt "content" --overwrite

# Write from pipe
echo "test content" | /write output.txt
```

**Output**:
- Human-readable: "File written: <path> (<bytes> bytes)"
- JSON envelope (non-TTY): `{"ok": true, "stdout": "..."}`

**Platform Support**: All platforms
**Safety Tier**: 2 (confirm)
**Related Commands**: `/read`, `/edit`, `/file`, `/newfile`

---

### `/edit` - Edit Files with String Replacement 🟢⭐

**Purpose**: Edit files by finding and replacing exact strings.

**Syntax**:
```bash
/edit <file_path> <old_string> <new_string>
/edit <file_path> <old_string> <new_string> --replace-all
```

**Arguments**:
- `file_path` (required): Path to file to edit
- `old_string` (required): Exact string to find
- `new_string` (required): Replacement string
- `--replace-all` (optional): Replace all occurrences (default: first only)
- `--help-cmd`: Show help message

**Default Values**:
- `replace_all`: false (replace first occurrence only)

**Examples**:
```bash
# Replace first occurrence
/edit app.py "old text" "new text"

# Replace all occurrences
/edit file.txt "bug" "fix" --replace-all

# Edit JSON config
/edit config.json '"debug": false' '"debug": true'
```

**Output**:
- Human-readable: "Edited: <path>\nReplacements: <count>"
- JSON envelope (non-TTY): `{"ok": true, "stdout": "..."}`

**Platform Support**: All platforms
**Safety Tier**: 2 (confirm)
**Related Commands**: `/read`, `/write`, `/file`

---

### `/file` - Unified File Operations 🟢⭐

**Purpose**: Single command for all file operations (read/write/edit/append).

**Syntax**:
```bash
# Explicit operations
/file read <path> [--offset <n>] [--limit <n>]
/file write <path> <content> [--overwrite]
/file edit <path> <old> <new> [--replace-all]
/file append <path> <content>

# Smart mode (auto-detects operation)
/file <path>                # Read if exists
/file <path> <content>      # Write content
```

**Subcommands**:
- `read`: Read file with optional range
- `write`: Create or overwrite file
- `edit`: Replace strings in file
- `append`: Append content to existing file
- Smart mode: Automatically determines operation

**Arguments** (vary by subcommand):
- `read`: `path`, `--offset`, `--limit`
- `write`: `path`, `content`, `--overwrite`
- `edit`: `path`, `old_string`, `new_string`, `--replace-all`
- `append`: `path`, `content`

**Examples**:
```bash
# Read operations
/file read README.md
/file read app.py --offset 50 --limit 100

# Write operations
/file write config.json '{"key": "value"}'
/file write log.txt "Entry" --overwrite

# Edit operations
/file edit script.py "old_function" "new_function"
/file edit config.ini "debug=false" "debug=true" --replace-all

# Append operations
/file append log.txt "New log entry"
echo "data" | /file append output.txt

# Smart mode
/file myfile.txt                # Reads file
/file newfile.txt "content"     # Writes file
```

**Output**:
- Varies by operation (see individual commands)
- JSON envelope (non-TTY): Operation-specific

**Platform Support**: All platforms
**Safety Tier**: Varies (1-2 depending on operation)
**Related Commands**: `/read`, `/write`, `/edit`, `/newfile`
**Note**: **Recommended** unified interface for file operations

---

### `/glob` - Find Files by Pattern 🟢⭐

**Purpose**: Find files and directories using glob patterns (*, ?, **).

**Syntax**:
```bash
/glob <pattern>
/glob <pattern> --path <directory>
```

**Arguments**:
- `pattern` (required): Glob pattern (e.g., `*.py`, `**/*.js`)
- `--path <dir>` (optional): Directory to search in (default: current directory)

**Default Values**:
- `path`: Current working directory

**Glob Pattern Syntax**:
- `*`: Match any sequence of characters
- `?`: Match any single character
- `[abc]`: Match any character in set
- `**`: Match directories recursively

**Examples**:
```bash
# Find all Python files
/glob "*.py"

# Find JS files recursively in src/
/glob "src/**/*.js"

# Find test files only
/glob "test_*.py"

# Search in specific directory
/glob "*.log" --path /var/log

# Find markdown files recursively
/glob "**/*.md"
```

**Output**:
- Human-readable: "Found <n> files:" + list
- JSON envelope (non-TTY): `{"ok": true, "stdout": "[file_paths]"}`

**Platform Support**: All platforms
**Safety Tier**: 1 (instant execution)
**Related Commands**: `/grep`, `/search`, `/watch`

---

### `/grep` - Search Files with Regex 🟢⭐

**Purpose**: Search file contents using regular expressions.

**Syntax**:
```bash
/grep <pattern>
/grep <pattern> --glob <file_pattern>
/grep <pattern> --path <directory>
/grep <pattern> --ignore-case
/grep <pattern> --context <n>
/grep <pattern> --output <mode>
```

**Arguments**:
- `pattern` (required): Regex pattern to search for
- `--path <dir>` (optional): Directory to search (default: '.')
- `--glob <pattern>` (optional): File pattern filter (e.g., `*.py`)
- `--ignore-case` / `-i` (optional): Case-insensitive search
- `--context <n>` / `-C <n>` (optional): Lines of context (default: 0)
- `--output <mode>` (optional): Output mode (default: 'files')
  - `files`: List files with matches
  - `content`: Show matching lines
  - `count`: Show match counts per file
- `--help-cmd`: Show help message

**Default Values**:
- `path`: '.' (current directory)
- `context`: 0 (no context lines)
- `output`: 'files' (list files only)
- `ignore_case`: false

**Examples**:
```bash
# Search for TODO in all files
/grep "TODO"

# Search in Python files only
/grep "error" --glob "*.py"

# Case-insensitive search
/grep "import" --ignore-case

# Show matching lines with context
/grep "function" --glob "*.py" --context 3

# Show match counts
/grep "pattern" --output count

# Complex regex search
/grep "def test_.*:" --glob "test_*.py" --output content
```

**Output**:
- `files` mode: List of file paths
- `content` mode: File:line + matching content + context
- `count` mode: File + match count
- JSON envelope (non-TTY): Structured matches

**Platform Support**: All platforms
**Safety Tier**: 1 (instant execution)
**Related Commands**: `/glob`, `/search`, `/read`

---

### `/search` - Unified Search (Auto-Detect) 🟢⭐

**Purpose**: Smart search that auto-detects whether to find files (glob) or search content (grep).

**Syntax**:
```bash
# Auto-detect mode
/search <query>

# Explicit grep mode with file filter
/search "<pattern>" in "<files>"

# Force mode
/search --mode glob <pattern>
/search --mode grep <pattern>

# With options
/search <pattern> --path <dir>
/search <pattern> --ignore-case
/search <pattern> --context <n>
/search <pattern> --output <mode>
```

**Arguments**:
- `query` (required): Search query (pattern or text)
- `--mode <mode>` (optional): Force mode (auto/glob/grep, default: auto)
- `--path <dir>` (optional): Directory to search
- `--ignore-case` / `-i` (optional): Case-insensitive
- `--context <n>` / `-C <n>` (optional): Context lines (grep only)
- `--output <mode>` (optional): Output format (grep only)

**Auto-Detection Rules**:
- Patterns with `*`, `**`, `?`, `[...]` → Glob mode (find files)
- File extensions like `*.py` → Glob mode
- Plain text patterns → Grep mode (search content)
- `"pattern" in "files"` syntax → Grep with file filter

**Examples**:
```bash
# Auto-detect as glob (find Python files)
/search "*.py"

# Auto-detect as glob (find markdown recursively)
/search "**/*.md"

# Auto-detect as grep (search for TODO)
/search "TODO"

# Auto-detect as grep (search for imports)
/search "import re"

# Explicit "in" syntax (grep with filter)
/search "TODO" in "*.py"

# Search errors in log files
/search "error" in "**/*.log"

# Find test functions
/search "def test_" in "test_*.py"

# Force glob mode (find files named 'test')
/search --mode glob "test"

# Force grep mode (search for literal "*.py")
/search --mode grep "*.py"

# Case-insensitive search
/search "error" --ignore-case

# Search with context
/search "function" in "*.py" --context 3
```

**Output**:
- Glob mode: List of matching file paths
- Grep mode: Matching content (format depends on `--output`)
- JSON envelope (non-TTY): Structured results

**Platform Support**: All platforms
**Safety Tier**: 1 (instant execution)
**Related Commands**: `/glob`, `/grep`, `/read`
**Note**: **Recommended** - Best search interface, replaces `/glob` and `/grep`

**Aliases**: `/find` (same as `/search`)

---

### `/newfile` - Create Files with Templates 🟢⭐

**Purpose**: Create new files with optional templates for common file types.

**Syntax**:
```bash
/newfile <name>
/newfile <name> --template <type>
/newfile <name> --content <text>
/newfile <name> --force
```

**Arguments**:
- `name` (required): File name/path
- `--template` / `-t` (optional): Template type (auto-detect from extension)
- `--content` / `-c` (optional): Direct content
- `--force` / `-f` (optional): Overwrite if exists
- `--list-templates` / `-l`: List available templates
- `--help` / `-h`: Show help

**Available Templates**:
- `python`: Python script with shebang and structure
- `json`: JSON with basic structure
- `markdown`: Markdown with header
- `html`: HTML5 boilerplate
- `css`: CSS with reset
- `javascript`: JS/Node.js module template
- `shell`: Shell script with shebang

**Default Behavior**:
- Auto-detects template from file extension
- Creates empty file if no template specified

**Examples**:
```bash
# Create Python file (auto-detect template)
/newfile script.py

# Create with specific template
/newfile config.json --template json

# Create with direct content
/newfile README.md --content "# My Project"

# Force overwrite existing file
/newfile app.py --template python --force

# List available templates
/newfile --list-templates
```

**Output**:
- Human-readable: "Created: <path> (from <template> template)"
- JSON envelope (non-TTY): `{"ok": true, "stdout": "..."}`

**Platform Support**: All platforms
**Safety Tier**: 2 (confirm if exists)
**Related Commands**: `/write`, `/file`, `/edit`

---

## SYSTEM & CONFIGURATION

### `/config` - Configuration Management 🟢⭐

**Purpose**: Manage ISAAC configuration, API keys, AI routing, and system settings.

**Syntax**:
```bash
# Overview
/config

# Specific sections
/config --status
/config --ai
/config --cloud
/config --plugins
/config --collections
/config --console

# Set values
/config --set <key> <value>
/config --apikey <service> <key>

# AI routing
/config --ai-routing
/config --ai-routing-set <level> <provider>
/config --ai-routing-model <provider> <model>
/config --ai-routing-limits <period> <amount>
/config --ai-routing-reset

# Environment
/config --env
/config --env-validate
/config --env-create
```

**Arguments** (extensive - 20+ flags):
- `--status`: Detailed system status
- `--ai`: AI provider configuration
- `--ai-routing`: AI routing configuration
- `--cloud`: Cloud sync status
- `--plugins`: List available plugins
- `--collections`: xAI Collections status
- `--console`: Console settings
- `--set <key> <value>`: Change setting
- `--apikey <service> <key>`: Set API key
- `--ai-routing-set <level> <provider>`: Set provider for complexity level
- `--ai-routing-model <provider> <model>`: Set model for provider
- `--ai-routing-limits <period> <amount>`: Set cost limits
- `--ai-routing-reset`: Reset to defaults
- `--env`: Show environment variables
- `--env-validate`: Validate environment
- `--env-create`: Create `.env` template

**Default Behavior**:
- No args: Shows configuration overview

**AI Routing Complexity Levels**:
- `simple`: Quick answers, basic queries (default: openai)
- `medium`: Standard questions (default: grok)
- `complex`: Multi-step reasoning (default: claude)
- `expert`: Architecture, system design (default: claude)

**AI Routing Task Types**:
- `code_write`: Code generation (default: claude)
- `code_debug`: Debugging (default: claude)
- `tool_use`: Tool/function calling (default: claude)

**API Key Services**:
- `xai-chat`: xAI API key for chat
- `xai-collections`: xAI API key for collections
- `claude`: Anthropic Claude API key
- `openai`: OpenAI API key

**Examples**:
```bash
# Show configuration overview
/config

# Show detailed status
/config --status

# Show AI configuration
/config --ai

# View routing settings
/config --ai-routing

# Set API keys
/config --apikey xai-chat YOUR_API_KEY
/config --apikey claude YOUR_CLAUDE_KEY

# Configure AI routing
/config --ai-routing-set simple grok
/config --ai-routing-set complex claude
/config --ai-routing-set code_write claude

# Set models
/config --ai-routing-model claude claude-opus
/config --ai-routing-model openai gpt-4

# Set cost limits
/config --ai-routing-limits daily 10.0
/config --ai-routing-limits monthly 100.0

# Change settings
/config --set default_tier 3
/config --set sync_enabled true

# Reset routing to defaults
/config --ai-routing-reset
```

**Output**:
- Configuration overview with sections
- Status information
- Confirmation messages for changes
- JSON envelope (non-TTY): `{"ok": true, "stdout": "..."}`

**Platform Support**: All platforms
**Safety Tier**: 1 (safe to view, 2 for modifications)
**Related Commands**: `/status`, `/help`, `/update`

---

### `/status` - System Status Dashboard 🟢

**Purpose**: Display system status, workspace info, and AI session details.

**Syntax**:
```bash
/status
/status -v
```

**Arguments**:
- `-v` / `--verbose` (optional): Detailed status (same as `/config --status`)

**Default Behavior**:
- No args: One-line summary
- With `-v`: Detailed multi-section status

**Status Information Includes**:
- **Session**: Machine ID
- **Workspace**: Active workspace name and path
- **AI Session**: Session ID, age, remaining capacity, rotations
- **Knowledge Base**: Collection ID, files indexed, chunks, watcher status
- **Background Tasks**: Total tasks, status breakdown
- **Machine Orchestration**: Registered machines, online count, load distribution
- **Network**: Hostname, IP address

**Examples**:
```bash
# Quick one-line status
/status
# Output: Session: abc123 | Workspace: ✓ myproject | AI: ✓

# Detailed status
/status -v
# Output: Multi-section status report
```

**Output**:
- One-line: "Session: <id> | Workspace: <status> | AI: <status>"
- Verbose: Multi-section formatted report
- JSON envelope (non-TTY): `{"ok": true, "stdout": "..."}`

**Platform Support**: All platforms
**Safety Tier**: 1 (read-only)
**Related Commands**: `/config`, `/machines`, `/tasks`, `/workspace`

---

### `/help` - Command Help System 🟢⭐

**Purpose**: Show command overview or detailed help for specific commands.

**Syntax**:
```bash
/help
/help <command>
```

**Arguments**:
- `command` (optional): Specific command to get help for

**Default Behavior**:
- No args: Show command overview

**Commands with Detailed Help**:
- `/config`, `/mine`, `/ask`, `/alias`, `/status`, `/glob`, `/grep`, `/read`, `/write`, `/edit`, `/newfile`, `/backup`, `/restore`, `/list`, `/workspace`, `/sync`, `/queue`, `/search`, `/file`, `/msg`

**Examples**:
```bash
# Show command overview
/help

# Get help for specific command
/help /config
/help /search
/help /status
```

**Output**:
- Overview: List of all commands with categories
- Detailed: Command-specific help with syntax and examples
- JSON envelope (non-TTY): `{"ok": true, "stdout": "..."}`

**Platform Support**: All platforms
**Safety Tier**: 1 (read-only)
**Related Commands**: `/man`, `/apropos`, `/whatis`

**Aliases**: `/h`, `/?`

---

## AI & ANALYSIS

### `/ask` - Direct AI Chat 🟢

**Purpose**: Chat with AI directly without command execution.

**Syntax**:
```bash
/ask <question>
/a <question>
```

**Arguments**:
- `question` (required): Question or query for AI

**Behavior**:
- Sends query to AI (xAI/Claude/OpenAI based on routing)
- Returns text response only
- Does NOT execute commands
- Maintains conversation history for context

**Difference from `isaac <query>`**:
- `/ask`: Conversational, returns text only
- `isaac <query>`: Translates to shell commands for execution

**Examples**:
```bash
# Geographic question
/ask where is alaska?

# Technical explanation
/ask what is docker?

# Detailed information
/ask explain kubernetes networking

# Short alias
/a quick question
```

**Output**:
- Plain text response from AI
- JSON envelope (non-TTY): `{"ok": true, "stdout": "<response>"}`

**Platform Support**: All platforms
**Safety Tier**: 1 (no command execution)
**Related Commands**: `isaac`, `/analyze`, `/mine`, `/summarize`

**Aliases**: `/a`

---

### `/mine` - xAI Collections Manager 🟢⭐

**Purpose**: Manage xAI Collections for searching personal file history.

**Syntax**:
```bash
# Collection management
/mine --create <name>
/mine --use <name>
/mine --delete <name>
/mine --list
/mine --info

# File operations
/mine --upload <file>
/mine --search <query>

# Advanced operations
/mine --nuggets
/mine --skip
/mine --haul
/mine --pan
/mine --drop
/mine --survey
/mine --grokbug
/mine --grokrefactor

# Status
/mine --status
/mine --help
```

**Arguments** (extensive - 20+ operations):
- `--create <name>`: Create new collection
- `--use <name>`: Switch to collection
- `--delete <name>`: Delete collection
- `--list`: List all collections
- `--info`: Show active collection details
- `--upload <file>`: Upload file to active collection
- `--search <query>`: Search active collection
- `--status`: Show system status
- Advanced: `--nuggets`, `--skip`, `--haul`, `--pan`, `--drop`, `--survey`
- Smart ops: `--grokbug`, `--grokrefactor`

**Description**:
Search your personal file history using xAI Collections. This is YOUR stuff, not internet knowledge.

**Examples**:
```bash
# Create and use collection
/mine --create mydocs
/mine --use mydocs

# Upload files
/mine --upload file.txt
/mine --upload **/*.py

# Search collection
/mine --search "function definition"

# List all collections
/mine --list

# Show collection info
/mine --info

# Advanced: Extract code nuggets
/mine --nuggets

# Smart: Find and fix bugs with Grok
/mine --grokbug
```

**Output**:
- Operation-specific output
- Collection information
- Search results
- JSON envelope (non-TTY): Structured data

**Platform Support**: All platforms (requires xAI API key)
**Safety Tier**: 1-2 (depending on operation)
**Related Commands**: `/ask`, `/analyze`, `/search`

---

### `/analyze` - AI Analysis of Piped Data 🟢

**Purpose**: Analyze data piped from previous command using AI.

**Syntax**:
```bash
<command> | /analyze
<command> | /analyze <analysis_type>
```

**Arguments**:
- `analysis_type` (optional): Type of analysis (default: 'general')

**Usage**:
- Receives data from pipe
- Sends to AI for analysis
- Returns analysis results

**Examples**:
```bash
# Analyze command output
/grep "error" *.log | /analyze

# Analyze file contents
/read config.json | /analyze

# Analyze with specific type
/mine --search "bugs" | /analyze code_review
```

**Output**:
- AI analysis of piped data
- JSON blob format: `{"kind": "text", "content": "...", "meta": {}}`

**Platform Support**: All platforms
**Safety Tier**: 1 (analysis only, no execution)
**Related Commands**: `/ask`, `/mine`, `/summarize`

---

## COLLABORATION & TASKS

### `/msg` - Message Queue Management 🟢

**Purpose**: Manage notifications from ISAAC's autonomous AI monitoring.

**Syntax**:
```bash
# View messages
/msg
/msg --sys
/msg --code
/msg --all
/msg --read <id>

# Acknowledge messages
/msg --ack <id>
/msg --ack-all
/msg --ack-all --sys
/msg --ack-all --code

# Delete messages
/msg --delete <id>
/msg --clear
/msg --clear --sys
/msg --clear --code
/msg --clear --ack

# Auto-run
/msg --auto-run
```

**Arguments**:
- `--sys` / `-s`: Filter to system messages only
- `--code` / `-c`: Filter to code messages only
- `--all` / `-a`: Show all messages
- `--read <id>`: Read full message content
- `--ack <id>`: Acknowledge specific message
- `--ack-all`: Acknowledge all pending messages
- `--delete <id>`: Delete specific message
- `--clear`: Clear messages (with optional filters)
- `--auto-run` / `-ar`: Auto-run suggested commands

**Message Types**:
- `!` - System operations (updates, monitoring, alerts)
- `¢` - Code operations (linting, testing, debugging)

**Message Priority**:
- `[URGENT]` - Requires immediate attention
- `[HIGH]` - Important, review soon
- `[NORMAL]` - Standard notification
- `[LOW]` - Informational only

**Prompt Indicator**:
- `[7$]>` means 7 pending messages

**Examples**:
```bash
# View all pending messages
/msg

# View system messages only
/msg --sys

# Read full message
/msg --read 42

# Acknowledge message
/msg --ack 42

# Acknowledge all code messages
/msg --ack-all --code

# Delete message
/msg --delete 42

# Clear acknowledged messages
/msg --clear --ack
```

**Output**:
- Message list with ID, type, priority, summary
- Full message content for `--read`
- Confirmation for actions
- Formatted text with priority/type indicators

**Platform Support**: All platforms
**Safety Tier**: 1 (read), 2 (delete/clear)
**Related Commands**: `/tasks`, `/status`, `/debug`

**Aliases**: `/messages`

---

### `/tasks` - Background Task Management 🟢

**Purpose**: Manage and monitor background tasks.

**Syntax**:
```bash
# View tasks
/tasks
/tasks --list
/tasks --running
/tasks --completed
/tasks --failed

# Manage tasks
/tasks --show <id>
/tasks --cancel <id>
/tasks --clear

# Statistics
/tasks --stats
```

**Arguments**:
- `--list` / `-l`: List all tasks (default)
- `--running` / `-r`: Filter to running tasks only
- `--completed` / `-c`: Filter to completed tasks only
- `--failed` / `-f`: Filter to failed tasks only
- `--show <id>`: Show task details
- `--cancel <id>`: Cancel running task
- `--clear`: Clear completed/failed tasks
- `--stats` / `-s`: Show task statistics

**Task Information**:
- Task ID
- Status (pending/running/completed/failed)
- Type (background/scheduled/pipeline)
- Progress
- Duration
- Result/Error

**Examples**:
```bash
# List all tasks
/tasks

# Show running tasks only
/tasks --running

# Show task details
/tasks --show task_123

# Cancel task
/tasks --cancel task_123

# Show statistics
/tasks --stats

# Clear completed tasks
/tasks --clear
```

**Output**:
- Formatted task list with status indicators
- Task details for `--show`
- Statistics summary for `--stats`

**Platform Support**: All platforms
**Safety Tier**: 1 (view), 2 (cancel/clear)
**Related Commands**: `/msg`, `/status`, `/pipeline`

---

## ADVANCED FEATURES

### `/alias` - Manage Command Aliases 🟢

**Purpose**: Manage Unix-to-PowerShell command aliases for cross-platform compatibility.

**Syntax**:
```bash
/alias
/alias --list
/alias --show <command>
/alias --enable
/alias --disable
/alias --add <alias> <command>
/alias --remove <alias>
/alias --help
```

**Arguments**:
- No args / `--list`: Show all aliases
- `--show <command>`: Show details for specific command
- `--enable`: Enable alias system
- `--disable`: Disable alias system
- `--add <alias> <command>`: Add custom alias
- `--remove <alias>`: Remove custom alias
- `--help`: Show help

**Description**:
Provides Unix command compatibility on Windows PowerShell. Commands like `ls`, `grep`, `cat` are automatically translated to their PowerShell equivalents.

**Examples**:
```bash
# List all aliases
/alias

# Show ls alias details
/alias --show ls

# Enable automatic translation
/alias --enable

# Add custom alias
/alias --add ll "ls -la"

# Remove custom alias
/alias --remove ll

# Disable alias system
/alias --disable
```

**Common Aliases**:
- `ls` → `Get-ChildItem` (Windows) / `ls` (Unix)
- `grep` → `Select-String` (Windows) / `grep` (Unix)
- `cat` → `Get-Content` (Windows) / `cat` (Unix)
- `ps` → `Get-Process` (Windows) / `ps` (Unix)
- `kill` → `Stop-Process` (Windows) / `kill` (Unix)
- `cd` → `Set-Location` (Windows) / `cd` (Unix)

**Output**:
- Alias list with mappings
- Translation details
- Confirmation messages
- JSON envelope (non-TTY): `{"ok": true, "stdout": "..."}`

**Platform Support**: All platforms (primarily for Windows)
**Safety Tier**: 1 (view), 2 (modify)
**Related Commands**: `/config`, `/help`

---

### `/machine` - Machine Registry 🟢

**Purpose**: Register and manage individual machines in the ISAAC network.

**Syntax**:
```bash
/machine register --hostname <host> --ip-address <ip> [options]
/machine unregister --machine-id <id>
/machine list [filters]
/machine show <id>
/machine status <id>
/machine group <action> [options]
/machine groups
/machine discover
/machine find [criteria]
```

**Actions**:
- `register`: Register new machine
- `unregister`: Remove machine from registry
- `list`: List registered machines
- `show`: Show machine details
- `status`: Show machine status
- `group`: Manage machine groups
- `groups`: List all groups
- `discover`: Auto-discover machines on network
- `find`: Find machines by criteria

**Arguments** (extensive):
- `--hostname <host>`: Machine hostname
- `--ip-address <ip>`: Machine IP address
- `--port <port>`: SSH port (default: 22)
- `--tags <tags>`: Comma-separated tags
- `--group-name <name>`: Group name
- `--group-members <ids>`: Group member IDs
- `--filter-tags <tags>`: Filter by tags
- `--min-cpu <n>`: Minimum CPU cores
- `--min-memory <n>`: Minimum memory (GB)
- `--machine-id <id>`: Machine ID

**Examples**:
```bash
# Register machine
/machine register --hostname server1 --ip-address 192.168.1.100

# Register with tags
/machine register --hostname gpu-box --ip-address 192.168.1.50 --tags "gpu,cuda"

# List all machines
/machine list

# Show machine details
/machine show machine_abc123

# Unregister machine
/machine unregister --machine-id machine_abc123

# Create machine group
/machine group create --group-name "production" --group-members "id1,id2"

# List groups
/machine groups

# Find GPU machines
/machine find --filter-tags "gpu"
```

**Output**:
- Machine registration confirmation
- Machine lists with status
- Machine details
- Group information
- Formatted text with emoji indicators

**Platform Support**: All platforms
**Safety Tier**: 2 (registration/modification)
**Related Commands**: `/machines`, `/config`, `/status`

---

### `/machines` - Machine Orchestration Status 🟢

**Purpose**: View machine orchestration status and load balancing.

**Syntax**:
```bash
/machines
/machines --status
/machines --list
/machines --groups
/machines --load
```

**Arguments**:
- No args / `--status`: Show orchestration status (default)
- `--list`: List online machines
- `--groups`: Show machine groups
- `--load`: Show load distribution
- `--verbose` / `-v`: Detailed output

**Status Information**:
- Total registered machines
- Online machines count
- Machine groups
- Load distribution (CPU%, Memory%)
- Recent executions tracked

**Examples**:
```bash
# Show orchestration status
/machines

# List online machines
/machines --list

# Show machine groups
/machines --groups

# Show load distribution
/machines --load
```

**Output**:
- Status summary
- Machine lists
- Load statistics
- JSON envelope (non-TTY): `{"ok": true, "stdout": "..."}`

**Platform Support**: All platforms
**Safety Tier**: 1 (read-only)
**Related Commands**: `/machine`, `/status`, `/tasks`

---

## PLACEHOLDER/STUB COMMANDS 🔴

These commands exist but are not implemented:

### `/backup` - Backup Configuration 🔴
**Status**: Placeholder
**Message**: "Backup feature coming soon"
**Recommendation**: Use OS-level backups until implemented

### `/list` - Named List Management 🔴
**Status**: Placeholder
**Recommendation**: Unclear purpose, may be removed

### `/pipeline` - Pipeline Execution 🔴
**Status**: Stub (minimal implementation)
**Recommendation**: Under development

### `/timemachine` - Time Machine 🔴
**Status**: Stub (minimal implementation)
**Recommendation**: Under development

### `/claude-artifacts` 🔴
**Status**: Empty stub
**Recommendation**: Scheduled for deletion

### `/openai-vision` 🔴
**Status**: Empty stub
**Recommendation**: Scheduled for deletion

---

## COMMANDS REQUIRING FURTHER DOCUMENTATION 🟡

These commands exist and are functional but need more comprehensive documentation:

- `/ambient` - Ambient intelligence
- `/apropos` - Search manual pages
- `/arvr` - AR/VR features
- `/bubble` - Workspace state management
- `/debug` - Debug analysis
- `/images` - Cloud image storage
- `/learn` - Self-improving learning system
- `/man` - Manual pages
- `/pair` - Collaborative pair programming
- `/plugin` - Plugin management
- `/resources` - Resource management
- `/restore` - Restore from backup
- `/save` - Save operations
- `/script` - Scripting support
- `/share` - Sharing features
- `/summarize` - Text summarization
- `/sync` - Cloud synchronization
- `/team` - Team collaboration
- `/update` - System updates
- `/upload` - File uploads
- `/watch` - File watching
- `/whatis` - Command lookup
- `/workspace` - Workspace management

*Comprehensive documentation for these commands will be added in a future update.*

---

## APPENDIX A: COMMAND CATEGORIES

**File Operations** (9 commands):
read, write, edit, file, glob, grep, search, newfile, watch

**System & Configuration** (7 commands):
config, status, help, man, apropos, whatis, debug, update

**AI & Analysis** (4 commands):
ask, analyze, mine, summarize

**Workspace & Projects** (5 commands):
workspace, backup, restore, sync, bubble

**Collaboration & Tasks** (6 commands):
tasks, msg, team, pair, learn, share

**Cloud & Upload** (3 commands):
images, upload, sync

**Advanced Features** (10 commands):
machine, machines, alias, script, plugin, resources, pipeline, arvr, timemachine, save

**Placeholders/Stubs** (6 commands):
backup, list, pipeline, timemachine, claude-artifacts, openai-vision

---

## APPENDIX B: SAFETY TIERS

**Tier 1 (Instant Execution)** - Safe, read-only operations:
- read, glob, grep, search, help, status, ask, analyze, list, apropos, man, whatis

**Tier 2 (Confirm)** - Modifies files or configuration:
- write, edit, file (write/edit modes), newfile, config (modifications), alias (modifications)

**Tier 3 (AI Validation)** - Potentially dangerous operations:
- (Reserved for system-level operations)

**Tier 4 (Lockdown)** - Explicitly dangerous operations:
- (Reserved for critical system modifications)

---

## APPENDIX C: PLATFORM SUPPORT

**All Platforms** (46 commands):
Most commands support Windows, Linux, and macOS

**Platform-Specific Notes**:
- `/alias`: Primarily for Windows PowerShell compatibility
- File path handling automatically adapts to platform

---

## APPENDIX D: COMMON WORKFLOWS

### Workflow 1: Find and Edit Files
```bash
# Find Python files
/glob "**/*.py"

# Search for specific pattern
/grep "def old_function" --glob "*.py"

# Edit found file
/edit src/module.py "def old_function" "def new_function"
```

### Workflow 2: AI-Assisted Analysis
```bash
# Search for bugs
/mine --search "potential bugs"

# Analyze results
/mine --search "error handling" | /analyze

# Ask AI for explanation
/ask "explain the error in this code"
```

### Workflow 3: System Monitoring
```bash
# Check system status
/status -v

# View messages
/msg

# Check running tasks
/tasks --running

# Monitor machine load
/machines --load
```

### Workflow 4: File Operations
```bash
# Read file
/read config.json

# Edit configuration
/edit config.json '"debug": false' '"debug": true'

# Verify changes
/read config.json --offset 10 --limit 5
```

---

**End of Command Reference**

**For additional help**:
- Use `/help <command>` for command-specific help
- Check ISAAC documentation
- Use `/ask` to ask AI about commands

**Report issues**: https://github.com/anthropics/claude-code/issues
