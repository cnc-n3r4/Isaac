# Isaac User Guide - Complete Command Reference

## Overview

Isaac is an AI-enhanced shell assistant with THREE ways to interact:

1. **Meta Commands** - Start with `/` (e.g., `/status`, `/ask`, `/help`)
2. **Natural Language** - Start with `isaac` (e.g., `isaac show me all python files`)
3. **Regular Shell Commands** - Just type them (e.g., `ls`, `git status`)

---

## Vision & Design Goals

### Command Syntax Philosophy

**Native Isaac Commands:**
- ALL built-in Isaac commands use `/slash --flag` structure
- Examples: `/status`, `/ask --model grok`, `/write --overwrite`
- Consistent, discoverable, never conflicts with shell commands

**User Aliases:**
- User-created aliases work WITHOUT the `/slash` prefix
- Natural Unix/shell feel: `ls`, `man`, `apropos`, `ll`, `grep`
- Created via `/alias` command, used naturally in shell
- No forcing users to type `/man` or `/ls` - keep it natural

**Design Principle:** 
> Isaac's native commands are namespaced with `/`. User's world stays natural and unobtrusive.

### Piping Vision

**Everything Must Pipe:**
All commands (Isaac and shell) should support piping as first-class feature.

**Background Job System:**
Long-running pipe chains should automatically or explicitly run as background jobs.

```bash
# Automatic background for long chains
/ask analyze this codebase | /write analysis.md | /msg @team
# System detects this will take time, backgrounds it
# User gets: "Job #1234 started in background"
# Later: "!bang Job #1234 complete: analysis.md created, message sent"

# Explicit background mode
/bg /ask complex query | /process | /validate | /write output.txt
# Returns immediately with job ID
# Alerts with !bang when complete
```

**Bang Notification System:**
- `!bang` notifications when background jobs complete
- Non-intrusive - doesn't interrupt current command
- Shows job ID, status, results location

**Current Status:**
- ⚠️ Basic piping works (`/ask | /write`)
- ❌ Background job system not implemented
- ❌ Bang notifications not implemented
- ❌ Auto-detection of long-running chains not implemented
- ❌ `/bg` prefix command not implemented

This is the **VISION** - test cases will be written against this model, many will fail initially.

---

## Core Concepts

### The Three Command Types

#### 1. Meta Commands (`/command`)
Built-in Isaac functionality - file operations, AI chat, workspace management, etc.
```bash
/status              # System status
/ask what is Docker? # AI chat (no execution)
/help                # Show all commands
```

#### 2. Natural Language (`isaac <query>`)
AI translates your request into shell commands and **executes them**
```bash
isaac show me all python files
# AI translates to: find . -name "*.py"
# Then EXECUTES the command
```

#### 3. Shell Commands (raw commands)
Regular terminal commands with safety validation
```bash
ls                   # Tier 1: instant execution
git status           # Tier 2: auto-correction enabled
rm -rf /             # Tier 4: BLOCKED for safety
```

---

## Meta Commands Reference

### AI & Chat

**`/ask <question>`** - Chat with AI (NO command execution)
```bash
/ask what is Docker?
/ask explain async/await in Python
/ask where is Alaska?  # Geographic question
```
- Pure conversational mode
- NO commands are executed
- Use for explanations, learning, questions

**`/ambient <subcommand>`** - AI learning and pattern analysis
```bash
/ambient stats       # Show what Isaac has learned
/ambient patterns    # Show detected workflow patterns
/ambient suggestions # Get proactive suggestions
/ambient analyze     # Analyze recent commands
```
- Learns from your command patterns
- Suggests next steps in workflows
- NOT for executing code queries

### File Operations

**`/read <file>`** - Read file contents
```bash
/read myfile.txt
/read src/app.py --lines 10-50
```

**`/write <file> <content>`** - Write to file
```bash
/write notes.txt "my content"
echo "content" | /write output.txt  # From pipe
```

**`/edit <file>`** - Interactive file editing
```bash
/edit config.json
```

**`/newfile <filename>`** - Create new file
```bash
/newfile script.py
/newfile notes.txt --content "Hello"
/ask where is Alaska? | /newfile geography.txt  # From pipe
```
- Creates file in **current working directory**
- Use absolute paths to specify location: `/newfile C:\Users\me\file.txt`

**`/search <pattern>`** - Search for text in files
```bash
/search "TODO"
/search "function.*async" --regex
```

**`/grep <pattern>`** - Grep for patterns
```bash
/grep "import.*os"
/glob "**/*.py" | /grep "def main"
```

**`/glob <pattern>`** - Find files by pattern
```bash
/glob "**/*.py"
/glob "src/**/*.js"
```

### Piping Commands

You can pipe Isaac commands together:
```bash
/glob "**/*.py" | /grep "def main" | /read
/ask where is Alaska? | /newfile geography.txt
echo "data" | /write output.txt
```

**How pipes work:**
1. First command outputs data in "blob" format (kind + content)
2. Second command receives it as `piped_input` in context
3. Continues down the chain

### Workspace Management

**`/workspace create <name>`** - Create isolated workspace
```bash
/workspace create myproject
/workspace create myproject --venv  # With Python venv
/workspace create myproject --collection  # With xAI RAG
/workspace create myproject --venv --collection  # Both
```

**`/workspace list`** - Show all workspaces

**`/workspace switch <name>`** - Switch to workspace (changes directory)

**`/workspace delete <name>`** - Delete workspace

### System & Status

**`/status`** - Show Isaac system status
```bash
/status      # Quick summary
/status -v   # Detailed status
```

**`/config`** - View/modify configuration
```bash
/config                    # Show all config
/config ai                 # Show AI config
/config set key value      # Set config value
```

**`/msg`** - View queued messages
```bash
/msg                 # Show all messages
/msg --type code     # Code-related messages only
/msg --type system   # System messages only
```

**`/tasks`** - View background tasks
```bash
/tasks                    # List all tasks
/tasks --show <task_id>   # Show specific task
```

### Help & Documentation

**`/help`** - Show command help
```bash
/help              # List all commands
/help ask          # Help for specific command
```

---

## Natural Language Commands

Start any query with `isaac` to have AI translate and **execute**:

```bash
# File operations
isaac show me all python files
isaac find files larger than 100MB
isaac count lines in JavaScript files

# Git operations
isaac show git commits from last week
isaac what branch am I on?

# System information
isaac how much disk space is free?
isaac show running processes

# NOT for Python code execution
isaac what is Path.cwd()?
# This will explain what Path.cwd() is
# It will NOT execute the Python code
```

**Important:** Natural language is for **shell commands**, not Python code execution.

---

## What `/ask` vs `isaac` vs `/ambient`

### `/ask` - Pure Chat (NO Execution)
```bash
/ask what is Docker?           # ✓ Explains Docker
/ask where is Alaska?          # ✓ Geographic info
/ask what is Path.cwd()?       # ✓ Explains the method
/ask where is alaska.exe?      # ✓ Suggests: where.exe alaska.exe
```
- Conversational AI
- NO command execution
- For learning, explanations, questions

### `isaac` - Natural Language → Shell Execution
```bash
isaac show me all python files        # ✓ Finds and lists .py files
isaac find alaska.exe                 # ✓ Searches for the file
isaac what is my current directory?   # ✓ Runs pwd/Get-Location
```
- Translates to shell commands
- **EXECUTES** the command
- For actions, not questions

### `/ambient` - Pattern Learning (NO Execution)
```bash
/ambient patterns    # ✓ Shows learned workflow patterns
/ambient stats       # ✓ Statistics about command usage
/ambient analyze     # ✓ Analyzes recent command patterns
```
- Learns from your behavior
- Suggests next steps
- NO code execution

---

## Current Issues & Limitations

### Issue #1: File Creation Directory
**Problem:** `/newfile` creates files where Isaac's Python process started, not where your shell is.

**Current Behavior:**
```bash
cd ~
/newfile test.txt
# Creates in: C:\Projects\ProMan\ProMan-Tinktr\test.txt (wrong!)
```

**Workaround:** Use absolute paths
```bash
/newfile C:\Users\ndemi\test.txt
```

**Status:** Under investigation - process CWD vs shell CWD mismatch

### Issue #2: Wildcard Expansion in Unix Alias Translation
**Problem:** When Isaac translates Unix commands to PowerShell, wildcards lose their filtering behavior.

**Expected (native PowerShell):**
```powershell
PS C:\Users\ndemi> ls *rive
# Shows only: My Drive, OneDrive, Proton Drive
```

**Actual (Isaac):**
```bash
[1$]> ls *rive
Isaac > Translating Unix command: ls *rive -> Get-ChildItem
# Shows ALL files/folders in directory (wildcard ignored)
```

**Root Cause:** Unix alias strategy translates `ls *rive` to `Get-ChildItem` but loses the wildcard filter parameter.

**Workaround:** Use native PowerShell syntax
```bash
Get-ChildItem *rive  # Works correctly
```

**Status:** Unix-to-PowerShell wildcard translation not preserving arguments

### Issue #3: Command Redundancy - /newfile vs /write
**Problem:** `/newfile` and `/write` have significant functional overlap, with `/newfile` adding template complexity.

**Comparison:**
- `/newfile`: 282 lines with template system (default templates for .py/.txt/.md/.json/.html, custom template management, auto-selection by extension)
- `/write`: ~150 lines, simpler approach with explicit content and overwrite flag

**Both support:**
- Creating files with content
- Accepting piped input
- Creating parent directories automatically

**Recommendation:** Deprecate `/newfile` in favor of simpler approach:
- Use `/write` for direct file creation
- Use templates folder + standard `cp`/`copy` commands for template-based files
- Follows Unix philosophy: do one thing well

**Status:** Marked for refactoring - prefer simplicity over feature bloat

### Issue #4: Python Code Execution
**Problem:** No command currently executes Python code snippets directly.

**What doesn't work:**
```bash
/ask what is Path.cwd()?  # Just explains it
isaac what is Path.cwd()? # Might explain it
```

**What you need:** A `/exec` or `/py` command that runs Python code and returns results.

**Status:** Not currently implemented

### Issue #4: Empty Piped Files
**Problem:** Sometimes piped content doesn't make it through.

**Workaround:** Test pipe separately first:
```bash
/ask test question
# Verify you get output
/ask test question | /newfile test.txt
```

---

## Safety Tiers

Isaac validates all commands through a 5-tier safety system:

- **Tier 1** (Instant): `ls`, `pwd`, `echo` - Totally safe
- **Tier 2** (Auto-correct): `git status`, `npm install` - Safe with typo fixes
- **Tier 2.5** (Confirm): Modified tier-2 commands need confirmation after auto-correct
- **Tier 3** (AI Validate): `rm`, `mv` - Requires AI review
- **Tier 4** (Lockdown): `rm -rf /`, `dd` - BLOCKED entirely

You can bypass with `/f` (force):
```bash
/f rm -rf dangerous_folder  # Bypasses AI validation
```

---

## Configuration

Config lives in `~/.isaac/config.json`

### API Keys
```json
{
  "xai_api_key": "your-xai-key",
  "claude_api_key": "your-claude-key",
  "openai_api_key": "your-openai-key"
}
```

### AI Provider Priority
1. Grok (xAI) - Primary
2. Claude (Anthropic) - Fallback for complex queries
3. OpenAI - Backup

---

## Common Workflows

### Workflow 1: Project Setup
```bash
# Create workspace with everything
/workspace create myproject --venv --collection

# Switch to it
/workspace switch myproject

# Install dependencies
pip install requests flask

# Create initial files
/newfile app.py --template .py
/newfile README.md --template .md

# Start coding
/edit app.py
```

### Workflow 2: Code Analysis
```bash
# Find all Python files
isaac show me all python files

# Search for TODO comments
/search "TODO"

# Analyze specific file
/read src/main.py | /ask review this code for bugs
```

### Workflow 3: Data Processing
```bash
# Get data
curl https://api.example.com/data > data.json

# Process with AI
/read data.json | /ask summarize this JSON data | /newfile summary.txt
```

---

## Getting Help

- `/help` - List all commands
- `/help <command>` - Help for specific command
- `/ask <question>` - Ask AI for explanations
- `/status` - Check system status
- `/config` - View configuration

---

## Pro Tips

1. **Use tab completion** - Isaac predicts your next command
2. **Check `/msg`** - Background monitors leave notifications there
3. **Force execution** - `/f <command>` bypasses validation
4. **Pipe everything** - Isaac commands can be chained
5. **Use workspaces** - Keep projects isolated

---

## What's NOT Implemented Yet

- Direct Python code execution (no `/py` or `/exec` command)
- Shell CWD tracking for `/newfile` (uses process CWD)
- Interactive prompts in piped commands (y/n questions fail)
- Real-time code execution in `/ask` responses

---

**Last Updated:** 2025-11-10
