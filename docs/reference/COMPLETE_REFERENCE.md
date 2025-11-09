# Isaac 2.0 - Complete Reference

Comprehensive documentation of all Isaac features, commands, and functionality.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Safety & Security](#safety--security)
4. [Command Reference](#command-reference)
5. [AI Integration](#ai-integration)
6. [Configuration Reference](#configuration-reference)
7. [API Reference](#api-reference)
8. [Advanced Topics](#advanced-topics)

---

## System Overview

### What is Isaac?

Isaac is an intelligent shell wrapper that enhances command-line workflows with:

- **Multi-tier safety validation** (5 tiers of command safety)
- **AI-powered assistance** (Grok, Claude, OpenAI)
- **Natural language processing** (translate English to shell commands)
- **Workspace isolation** (project-specific environments)
- **Cross-platform support** (Windows PowerShell, Linux bash, macOS)
- **Tool integration** (Claude Code-style file operations)
- **RAG with xAI Collections** (context-aware AI)

### Core Concepts

#### 1. Command Types

Isaac recognizes three command types:

**Regular Commands** (no prefix)
```bash
ls
cd /path
git status
```
- Executed through shell adapter (PowerShell or bash)
- Subject to tier validation
- Can use Unix aliases on Windows

**Meta Commands** (/ prefix)
```bash
/help
/config
/workspace create myproject
```
- Built-in Isaac commands
- Executed via plugin dispatcher
- Can be piped together

**Device Routing** (! prefix)
```bash
!laptop /status
!server git pull
```
- Route commands to other machines
- Requires cloud sync setup
- Queued when offline

#### 2. Safety Tiers

| Tier | Name | Behavior | Examples |
|------|------|----------|----------|
| 1 | Instant | Execute immediately | ls, cd, pwd, git status |
| 2 | Auto-correct | Fix typos, execute | git stats → git status |
| 2.5 | Confirm | Auto-correct + confirm | git push origin master |
| 3 | Validate | AI validation required | rm -rf, chmod 777 |
| 4 | Lockdown | Never execute | format, dd, rm -rf / |

#### 3. AI Providers

Isaac supports multiple AI providers with automatic fallback:

**Primary: Grok (xAI)**
- Model: grok-beta
- Cost: $5 input, $15 output per 1M tokens
- Speed: Fast
- Best for: General queries, quick responses

**Fallback: Claude (Anthropic)**
- Model: claude-3-5-sonnet-20241022
- Cost: $3 input, $15 output per 1M tokens
- Speed: Medium
- Best for: Complex reasoning, code analysis

**Backup: OpenAI**
- Model: gpt-4o-mini
- Cost: $0.15 input, $0.60 output per 1M tokens
- Speed: Fast
- Best for: Reliable fallback, cost optimization

---

## Architecture

### Directory Structure

```
isaac/
├── core/              # Core functionality
│   ├── command_router.py          # Main command routing
│   ├── tier_validator.py          # Safety tier validation
│   ├── session_manager.py         # Session state
│   ├── pipe_engine.py             # Command piping
│   ├── sandbox_enforcer.py        # Workspace security
│   └── unix_aliases.py            # Unix translation
│
├── ai/                # AI integration
│   ├── base.py                    # Base AI client
│   ├── router.py                  # Multi-provider routing
│   ├── grok_client.py             # Grok integration
│   ├── claude_client.py           # Claude integration
│   ├── openai_client.py           # OpenAI integration
│   ├── agent.py                   # Tool-enabled agent
│   ├── translator.py              # NL → command
│   ├── corrector.py               # Typo correction
│   ├── validator.py               # Command validation
│   └── config_manager.py          # AI configuration
│
├── tools/             # File operation tools
│   ├── base.py                    # Tool base class
│   ├── file_ops.py                # Read/Write/Edit
│   └── code_search.py             # Grep/Glob
│
├── adapters/          # Shell adapters
│   ├── base_adapter.py            # Abstract shell
│   ├── powershell_adapter.py     # PowerShell
│   ├── bash_adapter.py            # Bash
│   └── shell_detector.py         # Auto-detect
│
├── commands/          # Built-in commands (21)
│   ├── alias/                     # Unix aliases
│   ├── analyze/                   # Code analysis
│   ├── ask/                       # AI questions
│   ├── backup/                    # Backup
│   ├── config/                    # Configuration
│   ├── edit/                      # Edit files
│   ├── glob/                      # Find files
│   ├── grep/                      # Search files
│   ├── help/                      # Help system
│   ├── list/                      # List items
│   ├── mine/                      # xAI Collections
│   ├── newfile/                   # Create files
│   ├── queue/                     # Command queue
│   ├── read/                      # Read files
│   ├── restore/                   # Restore backups
│   ├── save/                      # Save output
│   ├── status/                    # System status
│   ├── summarize/                 # Summarize content
│   ├── sync/                      # Cloud sync
│   ├── workspace/                 # Workspaces
│   └── write/                     # Write files
│
├── runtime/           # Runtime environment
│   ├── dispatcher.py              # Plugin dispatcher
│   ├── manifest_loader.py         # Load manifests
│   └── security_enforcer.py       # Security
│
├── ui/                # User interface
│   ├── terminal_control.py        # Terminal UI
│   ├── splash_screen.py           # Splash screen
│   └── config_console.py          # Config TUI
│
├── models/            # Data models
├── api/               # Cloud API
├── queue/             # Command queue
├── scheduler/         # Task scheduler
├── integrations/      # External services
└── data/              # Static data
    └── unix_aliases.json          # Unix mappings
```

### Data Flow

```
User Input
    ↓
Command Router
    ↓
├─→ Meta Command? (/command)
│   ├─→ Pipe Engine (if |)
│   └─→ Command Dispatcher
│       └─→ Plugin (run.py)
│
├─→ Device Route? (!device)
│   └─→ Cloud Client / Queue
│
├─→ Natural Language? (isaac ...)
│   ├─→ Query Classifier
│   ├─→ Chat Mode → xAI Client
│   └─→ Command Mode → Translator → Execute
│
└─→ Regular Command
    ├─→ Unix Alias? (if Windows)
    ├─→ Tier Validator
    │   ├─→ Tier 1: Execute
    │   ├─→ Tier 2: Corrector → Execute
    │   ├─→ Tier 2.5: Corrector → Confirm → Execute
    │   ├─→ Tier 3: Validator → Confirm → Execute
    │   └─→ Tier 4: Block
    └─→ Shell Adapter (PowerShell/Bash)
```

---

## Safety & Security

### Tier System Details

#### Tier 1: Instant Execution

**Purpose**: Allow safe, read-only commands without delay

**Examples**:
- `ls`, `dir` - List files
- `cd` - Change directory
- `pwd` - Print working directory
- `cat` - Read files
- `git status` - Check git status
- `git log` - View git history
- `echo` - Print text

**Criteria**:
- Read-only operations
- No system modification
- No network operations
- Cannot delete data

#### Tier 2: Auto-Correct

**Purpose**: Fix typos, execute immediately

**Examples**:
- `git stats` → `git status`
- `gti commit` → `git commit`
- `pyton` → `python`
- `npm isntall` → `npm install`

**Features**:
- Levenshtein distance calculation
- Command history analysis
- Common typo database
- Confidence threshold (>80%)

#### Tier 2.5: Confirm

**Purpose**: Auto-correct with user confirmation

**Examples**:
- `git push origin master`
- `npm publish`
- `git merge`

**Behavior**:
1. Attempt auto-correction
2. Display correction + confidence
3. Request confirmation
4. Execute if approved

#### Tier 3: AI Validation

**Purpose**: Analyze potentially dangerous commands

**Examples**:
- `rm -rf directory/`
- `chmod 777 file`
- `sudo systemctl restart`
- `DROP TABLE users`

**AI Analysis**:
- Safety warnings
- Impact assessment
- Suggested alternatives
- Confirmation required

#### Tier 4: Lockdown

**Purpose**: Block extremely dangerous commands

**Examples**:
- `rm -rf /`
- `dd if=/dev/zero of=/dev/sda`
- `mkfs.ext4 /dev/sda1`
- `format C:`

**Behavior**:
- Always blocked
- No execution allowed
- Use `/force` to override (use carefully!)

### Sandbox Enforcement

Isaac's `SandboxEnforcer` provides:

**Path Validation**:
- Blocks system directories (`/etc`, `/sys`, `C:\Windows`)
- Allows user home directory
- Workspace isolation
- Sensitive directory protection

**Command Validation**:
- Whitelist of allowed commands
- Full path validation
- Resource limits

**File Size Limits**:
- Default: 100MB maximum
- Configurable per operation
- Prevents resource exhaustion

**Workspace Isolation**:
- Each workspace is isolated
- Metadata tracking
- Collection association
- Virtual environment support

---

## Command Reference

### File Operations

#### /read - Read Files

**Syntax**:
```bash
/read <file_path> [--lines <start>-<end>]
```

**Description**: Read file contents with line numbers

**Options**:
- `--lines N-M` - Read lines N through M

**Examples**:
```bash
/read README.md
/read script.py --lines 10-20
/read config.json
```

**Features**:
- Displays line numbers
- Handles large files
- UTF-8 encoding
- Path expansion (~/, ./)

**Output Format**:
```
     1→ # Heading
     2→ Content here
     3→ More content
```

---

#### /write - Write Files

**Syntax**:
```bash
/write <file_path> <content>
```

**Description**: Create or overwrite file with content

**Examples**:
```bash
/write output.txt "Hello World"
/write config.json '{"key": "value"}'
/write script.sh "#!/bin/bash\necho 'test'"
```

**Features**:
- Creates parent directories
- UTF-8 encoding
- Overwrites existing files
- Handles multiline content

---

#### /edit - Edit Files

**Syntax**:
```bash
/edit <file_path> <old_string> <new_string> [--all]
```

**Description**: Replace exact string in file

**Options**:
- `--all` - Replace all occurrences (default: first only)

**Examples**:
```bash
/edit config.py "DEBUG = False" "DEBUG = True"
/edit app.js "const port = 3000" "const port = 8080"
/edit utils.py "old_function" "new_function" --all
```

**Features**:
- Exact string matching
- Preserves formatting
- Line number tracking
- Safe replacement

**Important**: Must use exact string match, including whitespace

---

#### /grep - Search Files

**Syntax**:
```bash
/grep [options] <pattern> <path>
```

**Description**: Search for regex pattern in files

**Options**:
- `-i` - Case insensitive
- `-n` - Show line numbers (default: true)
- `-C N` - Show N lines of context
- `-A N` - Show N lines after match
- `-B N` - Show N lines before match
- `--count` - Count matches only

**Examples**:
```bash
/grep "TODO" **/*.py
/grep -i "error" *.log
/grep -C 3 "function main" src/*.js
/grep --count "import" *.py
```

**Features**:
- Full regex support
- Recursive search
- Multiple file patterns
- Context display

---

#### /glob - Find Files

**Syntax**:
```bash
/glob <pattern> [path]
```

**Description**: Find files matching glob pattern

**Examples**:
```bash
/glob "**/*.py"
/glob "*.md"
/glob "src/**/*.test.js"
/glob "**/package.json"
```

**Patterns**:
- `*` - Match any characters in filename
- `**` - Match any directories (recursive)
- `?` - Match single character
- `[abc]` - Match a, b, or c

**Features**:
- Fast pattern matching
- Recursive traversal
- Sorted by modification time
- Handles large directories

---

#### /newfile - Create Files with Templates

**Syntax**:
```bash
/newfile <filename> [options]
```

**Description**: Create files with automatic templates

**Options**:
- `--template <ext>` - Use specific template
- `--content <text>` - Inline content
- `--force` - Overwrite existing
- `--list-templates` - Show available templates
- `--set-template <ext> <content>` - Add custom template

**Examples**:
```bash
# Create with auto template
/newfile app.py

# Create with custom content
/newfile notes.txt --content "Project notes"

# Use specific template
/newfile index.html --template .html

# Create from pipe
echo "test" | /newfile output.txt

# List templates
/newfile --list-templates

# Add custom template
/newfile --set-template .go "package main\n\nfunc main() {}\n"

# Force overwrite
/newfile existing.py --force
```

**Default Templates**:
- `.py` - Python starter with main block
- `.txt` - Plain text with header
- `.md` - Markdown document
- `.json` - Basic JSON structure
- `.html` - HTML5 skeleton

**Features**:
- Automatic extension detection
- Pipe support (stdin)
- Custom template management
- Parent directory creation

---

### Workspace Management

#### /workspace - Manage Workspaces

**Syntax**:
```bash
/workspace <--subcommand> [options]
```

**Subcommands**:

**--create** - Create new workspace
```bash
/workspace --create <name> [--venv] [--collection]
```
- `--venv` - Create Python virtual environment
- `--collection` - Create xAI collection

**--list** - List all workspaces
```bash
/workspace --list
```

**--switch** - Switch to workspace
```bash
/workspace --switch <name>
```
- Changes current directory
- Updates session state

**--add-collection** - Add collection to existing workspace
```bash
/workspace --add-collection <name>
```
- Adds xAI collection to workspace created without `--collection`

**--delete** - Delete workspace
```bash
/workspace --delete <name> [--preserve-collection]
```
- `--preserve-collection` - Keep xAI collection

**Examples**:
```bash
# Create basic workspace
/workspace --create myproject

# Create with venv
/workspace --create api-server --venv

# Create with everything
/workspace --create webapp --venv --collection

# Add collection to existing workspace
/workspace --add-collection myproject

# List workspaces
/workspace --list

# Switch workspace
/workspace --switch webapp

# Delete workspace
/workspace --delete old-project
```

**Workspace Structure**:
```
~/.isaac/workspaces/myproject/
├── .workspace.json          # Metadata
├── .venv/                   # Virtual environment (if --venv)
├── activate_venv.bat        # Activation script (Windows)
└── [your project files]
```

**Metadata** (`.workspace.json`):
```json
{
  "name": "myproject",
  "created_at": "2024-11-08T12:00:00",
  "collection_id": "coll_abc123",
  "has_venv": true
}
```

---

### AI & Intelligence

#### /ask - Ask AI Questions

**Syntax**:
```bash
/ask <question>
```

**Description**: Get AI responses without command execution

**Examples**:
```bash
/ask what is Docker?
/ask explain async/await in Python
/ask what are REST API best practices?
/ask how do I use git rebase?
```

**Features**:
- Conversational responses
- No command execution
- Multi-provider support
- Context-aware (knows your shell, OS, directory)

**Use Cases**:
- Learning new concepts
- Getting explanations
- Best practices
- Technical questions

**vs Natural Language**:
- `/ask` = Information only
- `isaac <query>` = Command execution

---

#### Natural Language Commands

**Syntax**:
```bash
isaac <natural language query>
```

**Description**: Translate English to shell commands and execute

**Examples**:
```bash
isaac show me all python files
isaac find files larger than 100MB
isaac count lines in JavaScript files
isaac show git commits from last week
```

**Features**:
- AI translation to shell commands
- Automatic execution (after safety validation)
- Explanation provided
- Multi-platform aware

**Important**: Must start with "isaac"

**Query Classification**:
```bash
# Geographic/General → /ask (no execution)
isaac where is Alaska?

# File/Command → Execution
isaac where is alaska.exe?
```

---

#### /analyze - Code Analysis

**Syntax**:
```bash
/analyze <file_path>
```

**Description**: AI-powered code analysis

**Examples**:
```bash
/analyze src/main.py
/analyze app.js
/analyze utils.go
```

**Analysis Includes**:
- Code quality assessment
- Potential bugs
- Security vulnerabilities
- Performance issues
- Best practices violations
- Suggested improvements

---

#### /summarize - Summarize Content

**Syntax**:
```bash
/summarize <file_path>
```

**Description**: Generate summary of file content

**Examples**:
```bash
/summarize README.md
/summarize docs/api.md
/summarize CHANGELOG.md
```

**Features**:
- Concise summaries
- Key points extraction
- Handles long documents
- Markdown formatting

---

### xAI Collections (RAG)

#### /mine - Collection Management

**Syntax**:
```bash
/mine --<command> [value]
```

**Commands**:

**--create** - Create collection
```bash
/mine --create <name>
```

**--upload** - Upload file to active collection
```bash
/mine --upload <file_path>
```

**--search** - Search active collection
```bash
/mine --search <query>
```

**--list** - List all collections
```bash
/mine --list
```

**--info** - Show active collection details
```bash
/mine --info
```

**--use** - Switch to collection
```bash
/mine --use <collection_name>
```

**--delete** - Delete collection
```bash
/mine --delete <collection_name>
```

**--status** - Show system status
```bash
/mine --status
```

**--help** - Show help
```bash
/mine --help
```

**Examples**:
```bash
# Create collection
/mine --create project_docs

# Switch to collection
/mine --use project_docs

# Upload files
/mine --upload README.md
/mine --upload docs/guide.md

# Search active collection
/mine --search "how to authenticate"

# List all collections
/mine --list

# Show active collection info
/mine --info

# Delete collection
/mine --delete old_docs
```

**Features**:
- Vector-based search using xAI Collections
- Context-aware AI responses
- Multiple file formats supported
- Automatic indexing and retrieval
- Personal file history management

---

### System Commands

#### /config - Configuration

**Syntax**:
```bash
/config [section]
/config set <key> <value>
/config console
```

**Subcommands**:
- No args - Show all config
- `status` - System status
- `ai` - AI configuration
- `cloud` - Cloud settings
- `plugins` - Plugin settings
- `collections` - xAI collections config
- `console` - Interactive TUI
- `set <key> <value>` - Set value

**Examples**:
```bash
# View all config
/config

# View AI config
/config ai

# Set value
/config set default_tier 2
/config set ai.routing.prefer_provider claude

# Interactive editor
/config console
```

---

#### /status - System Status

**Syntax**:
```bash
/status
```

**Description**: Display system status

**Shows**:
- AI provider status
- API key validation
- Workspace count
- Current tier
- Session info
- Cloud sync status

**Example Output**:
```
Isaac Status:
✓ AI Provider: Grok (primary)
✓ Workspaces: 5 available
✓ Current tier: 2.5
✓ Session: active
✓ Cloud: connected
```

---

#### /help - Help System

**Syntax**:
```bash
/help [command]
```

**Description**: Show help information

**Examples**:
```bash
# All commands
/help

# Specific command
/help /workspace
/help /grep
/help /newfile
```

---

#### /alias - Unix Aliases

**Syntax**:
```bash
/alias [options]
```

**Options**:
- No args - List all aliases
- `--list` - List aliases
- `--show <cmd>` - Show details
- `--enable` - Enable auto-translation
- `--disable` - Disable auto-translation
- `--add <unix> <ps>` - Add custom alias
- `--remove <unix>` - Remove custom alias

**Examples**:
```bash
# List aliases
/alias

# Show details
/alias --show ls

# Enable translation
/alias --enable

# Now use Unix commands in PowerShell
ls -la
grep "pattern" file.txt

# Add custom alias
/alias --add ll "ls -la"

# Remove alias
/alias --remove ll

# Disable translation
/alias --disable
```

**Supported Commands**:
See [Unix Aliases on Windows](#unix-aliases-on-windows) section

---

### Backup & Restore

#### /backup - Create Backups

**Syntax**:
```bash
/backup [target]
```

**Targets**:
- No args - Backup everything
- `config` - Config only
- `session` - Session data only
- `all` - Everything (default)

**Examples**:
```bash
/backup
/backup config
/backup session
```

**Backup Location**: `~/.isaac/backups/backup_YYYY-MM-DD.zip`

---

#### /restore - Restore Backups

**Syntax**:
```bash
/restore [--file <backup_file>]
```

**Description**: Restore from backup

**Examples**:
```bash
# List backups
/restore

# Restore specific backup
/restore --file backup_2024-11-08.zip
```

---

### Utility Commands

#### /save - Save Output

**Syntax**:
```bash
command | /save <file_path>
```

**Description**: Save command output to file

**Examples**:
```bash
/grep "TODO" **/*.py | /save todos.txt
/status | /save system_status.txt
```

---

#### /list - List Items

**Syntax**:
```bash
/list [type]
```

**Types**:
- `backups` - List backups
- `history` - Command history
- `workspaces` - Workspaces

**Examples**:
```bash
/list backups
/list history
/list workspaces
```

---

#### /queue - Command Queue

**Syntax**:
```bash
/queue <subcommand>
```

**Subcommands**:
- `list` - Show queued commands
- `clear` - Clear queue
- `run` - Run queued commands

**Examples**:
```bash
/queue list
/queue run
/queue clear
```

**Use Case**: Offline command queuing for cloud sync

---

#### /sync - Cloud Sync

**Syntax**:
```bash
/sync
```

**Description**: Sync session to cloud

**Features**:
- Preference sync
- Command queue upload
- Device registration
- Session roaming

---

## AI Integration

### Multi-Provider Architecture

#### Provider Configuration

**config.json**:
```json
{
  "ai": {
    "providers": {
      "grok": {
        "enabled": true,
        "api_key": "xai-...",
        "model": "grok-beta",
        "api_url": "https://api.x.ai/v1/chat/completions"
      },
      "claude": {
        "enabled": true,
        "api_key": "sk-ant-...",
        "model": "claude-3-5-sonnet-20241022",
        "api_url": "https://api.anthropic.com/v1/messages"
      },
      "openai": {
        "enabled": true,
        "api_key": "sk-...",
        "model": "gpt-4o-mini",
        "api_url": "https://api.openai.com/v1/chat/completions"
      }
    },
    "routing": {
      "strategy": "fallback",
      "prefer_provider": "grok",
      "cost_limit_daily": 10.0,
      "max_retries": 3
    },
    "defaults": {
      "temperature": 0.7,
      "max_tokens": 4096
    }
  }
}
```

#### Fallback Logic

```
1. Try Primary (Grok)
   ├─ Success → Return
   └─ Failure → Try Fallback

2. Try Fallback (Claude)
   ├─ Success → Return
   └─ Failure → Try Backup

3. Try Backup (OpenAI)
   ├─ Success → Return
   └─ Failure → Error

All failures tracked for monitoring
```

#### Cost Tracking

**Features**:
- Per-provider cost tracking
- Token usage monitoring
- Daily cost limits
- Usage statistics
- Cost optimization

**View Costs**:
```bash
/config ai

# Shows:
# Provider Usage:
# - Grok: 1.2M tokens, $0.12
# - Claude: 500K tokens, $0.05
# - OpenAI: 200K tokens, $0.01
# Total: $0.18 / $10.00 daily limit
```

### Tool System

Isaac's tool system enables AI agents to perform file operations:

#### Available Tools

**ReadTool** - Read files
```python
{
  "name": "read_file",
  "parameters": {
    "file_path": "path/to/file.txt",
    "start_line": 10,  # optional
    "end_line": 20     # optional
  }
}
```

**WriteTool** - Create files
```python
{
  "name": "write_file",
  "parameters": {
    "file_path": "path/to/file.txt",
    "content": "File content here"
  }
}
```

**EditTool** - Edit files
```python
{
  "name": "edit_file",
  "parameters": {
    "file_path": "path/to/file.txt",
    "old_string": "old text",
    "new_string": "new text"
  }
}
```

**GrepTool** - Search files
```python
{
  "name": "grep_search",
  "parameters": {
    "pattern": "TODO",
    "path": "**/*.py",
    "case_insensitive": true
  }
}
```

**GlobTool** - Find files
```python
{
  "name": "glob_search",
  "parameters": {
    "pattern": "**/*.md"
  }
}
```

#### IsaacAgent

The `IsaacAgent` class provides AI with tool execution:

**Usage**:
```python
from isaac.ai import IsaacAgent

agent = IsaacAgent()
result = agent.chat("Read README.md and summarize it")

# Agent automatically:
# 1. Calls read_file tool
# 2. Reads README.md
# 3. Generates summary
```

**Features**:
- Automatic tool selection
- Iterative tool calling
- Context management
- Error handling
- Token usage tracking

---

## Configuration Reference

### Complete Configuration Schema

```json
{
  "default_tier": 2.5,
  "machine_id": "auto-generated-uuid",

  "ai": {
    "providers": {
      "grok": {
        "enabled": true,
        "api_key": "xai-...",
        "model": "grok-beta",
        "api_url": "https://api.x.ai/v1/chat/completions",
        "timeout": 30
      },
      "claude": {
        "enabled": true,
        "api_key": "sk-ant-...",
        "model": "claude-3-5-sonnet-20241022",
        "api_url": "https://api.anthropic.com/v1/messages",
        "timeout": 30
      },
      "openai": {
        "enabled": true,
        "api_key": "sk-...",
        "model": "gpt-4o-mini",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "timeout": 30
      }
    },
    "routing": {
      "strategy": "fallback",
      "prefer_provider": "grok",
      "cost_limit_daily": 10.0,
      "max_retries": 3,
      "retry_delay": 1
    },
    "defaults": {
      "temperature": 0.7,
      "max_tokens": 4096,
      "top_p": 1.0
    }
  },

  "workspace": {
    "enabled": true,
    "root_dir": "~/.isaac/workspaces"
  },

  "sandbox": {
    "enabled": false,
    "root_dir": "~/.isaac/sandboxes",
    "block_system_paths": true,
    "max_file_size_mb": 100,
    "allowed_commands": ["pip", "npm", "git", "python", "node"]
  },

  "xai": {
    "collections": {
      "api_key": "xai-...",
      "management_api_key": "xai-...",
      "api_host": "api.x.ai",
      "management_api_host": "management-api.x.ai",
      "timeout_seconds": 3600
    },
    "chat": {
      "api_key": "xai-...",
      "model": "grok-3"
    }
  },

  "cloud": {
    "enabled": false,
    "api_url": "https://your-server.com/api",
    "api_key": "your-api-key",
    "sync_interval": 300
  },

  "ui": {
    "show_splash": true,
    "show_header": true,
    "color_scheme": "default"
  },

  "logging": {
    "level": "INFO",
    "file": "~/.isaac/isaac.log",
    "max_size_mb": 10
  },

  "unix_aliases": {
    "enabled": false,
    "show_translation": true
  }
}
```

### Environment Variables

```bash
# API Keys
XAI_API_KEY              # xAI (Grok)
ANTHROPIC_API_KEY        # Claude
OPENAI_API_KEY           # OpenAI

# Configuration
ISAAC_CONFIG_PATH        # Custom config location
ISAAC_HOME               # Custom Isaac home directory

# Logging
ISAAC_LOG_LEVEL          # DEBUG, INFO, WARNING, ERROR
ISAAC_LOG_FILE           # Log file path
```

---

## API Reference

### Python API

#### Session Manager

```python
from isaac.core.session_manager import SessionManager

# Initialize
session = SessionManager()

# Get config
config = session.get_config()

# Update config
session.update_config("default_tier", 2)
session.save_config()

# Preferences
prefs = session.preferences
```

#### AI Router

```python
from isaac.ai import AIRouter

# Initialize
router = AIRouter()

# Chat
response = router.chat(messages=[
    {"role": "user", "content": "Hello"}
])

print(response.content)

# Statistics
stats = router.get_stats()
print(f"Total cost: ${stats['total_cost']:.4f}")
```

#### IsaacAgent

```python
from isaac.ai import IsaacAgent

# Initialize
agent = IsaacAgent()

# Chat with tools
result = agent.chat("Read file.txt and find all TODOs")

# Returns:
# {
#   'response': "Found 5 TODOs...",
#   'tool_calls': [...],
#   'usage': {...}
# }
```

#### Tools

```python
from isaac.tools import ReadTool, WriteTool, EditTool

# Read file
read_tool = ReadTool()
content = read_tool.execute(file_path="README.md")

# Write file
write_tool = WriteTool()
write_tool.execute(file_path="output.txt", content="Hello")

# Edit file
edit_tool = EditTool()
edit_tool.execute(
    file_path="config.py",
    old_string="DEBUG = False",
    new_string="DEBUG = True"
)
```

---

## Advanced Topics

### Custom Command Development

Create custom Isaac commands using the plugin system.

#### Directory Structure

```
~/.isaac/commands/mycommand/
├── command.yaml          # Manifest
└── run.py                # Handler
```

#### Manifest (command.yaml)

```yaml
name: mycommand
version: 1.0.0
summary: "My custom command"

triggers: ["/mycommand"]

args:
  - name: input
    type: string
    required: true
    help: "Input parameter"

stdin: false
stdout:
  type: text

security:
  scope: user
  allow_remote: false
  resources:
    timeout_ms: 5000
    max_stdout_kib: 64

runtime:
  entry: "run.py"
  interpreter: "python"

telemetry:
  log_invocation: true
  log_output: false

examples:
  - "/mycommand test"
```

#### Handler (run.py)

```python
#!/usr/bin/env python3
import sys
import json

def main():
    # Read payload from stdin
    payload = json.loads(sys.stdin.read())
    args = payload.get("args", {})

    # Process
    result = f"Processed: {args.get('input')}"

    # Return envelope
    print(json.dumps({
        "ok": True,
        "stdout": result,
        "meta": {"command": "/mycommand"}
    }))

if __name__ == "__main__":
    main()
```

### Shell Adapter Development

Create adapters for new shells.

```python
from isaac.adapters.base_adapter import BaseShellAdapter, CommandResult

class MyShellAdapter(BaseShellAdapter):
    def __init__(self):
        super().__init__()
        self.name = "myshell"

    def execute(self, command: str) -> CommandResult:
        # Execute command in your shell
        # Return CommandResult
        pass

    def is_available(self) -> bool:
        # Check if shell is available
        return True
```

### AI Provider Integration

Add new AI providers.

```python
from isaac.ai.base import BaseAIClient, AIResponse

class MyAIClient(BaseAIClient):
    def __init__(self, api_key: str, model: str = "default"):
        super().__init__(api_key, model)

    def chat(self, messages: list, **kwargs) -> AIResponse:
        # Implement chat logic
        # Return AIResponse
        pass

    def _calculate_cost(self, input_tokens: int,
                       output_tokens: int) -> float:
        # Calculate cost
        return 0.0
```

### Pipe Engine Development

Create custom pipe operators.

```python
from isaac.core.pipe_engine import PipeEngine

class MyPipeOperator:
    def execute(self, input_blob: dict) -> dict:
        # Process blob
        # Return output blob
        return {
            "kind": "text",
            "content": "processed output"
        }
```

---

## Appendices

### A. Tier Classification Rules

**Tier 1 Patterns**:
- `ls`, `dir`, `pwd`, `cd`
- `cat`, `head`, `tail`, `less`, `more`
- `git status`, `git log`, `git diff`
- `echo`, `printf`
- Read-only operations

**Tier 2 Patterns**:
- Common typos with high confidence
- Safe operations with auto-correct

**Tier 2.5 Patterns**:
- `git push`
- `npm publish`
- `git merge`
- Operations with confirmation

**Tier 3 Patterns**:
- `rm -rf`
- `chmod`
- `sudo`
- Database operations
- System modifications

**Tier 4 Patterns**:
- `rm -rf /`
- `dd if=/dev/zero`
- `format`
- `mkfs`
- Destructive operations

### B. Error Codes

| Code | Description |
|------|-------------|
| `UNKNOWN_COMMAND` | Command not found |
| `INVALID_MANIFEST` | Bad command.yaml |
| `MISSING_HANDLER` | run.py not found |
| `EXECUTION_ERROR` | Handler crashed |
| `TIMEOUT` | Command exceeded timeout |
| `PIPE_ERROR` | Pipe operation failed |
| `UNSUPPORTED_BLOB` | Unknown blob type |
| `ALIAS_ERROR` | Alias operation failed |
| `NEWFILE_ERROR` | File creation failed |

### C. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Cancel command |
| `Ctrl+D` | Exit Isaac |
| `Ctrl+L` | Clear screen |
| `Up/Down` | Command history |
| `Tab` | Auto-complete (if available) |

### D. File Paths

| Path | Description |
|------|-------------|
| `~/.isaac/` | Isaac home directory |
| `~/.isaac/config.json` | Configuration |
| `~/.isaac/workspaces/` | Workspaces |
| `~/.isaac/backups/` | Backups |
| `~/.isaac/commands/` | Custom commands |
| `~/.isaac/isaac.log` | Log file |
| `~/.isaac/.session` | Session data |

---

## Glossary

**Tier** - Safety level for command validation (1-4)

**Meta Command** - Isaac built-in command (starts with /)

**Device Routing** - Execute command on remote machine (starts with !)

**Blob** - Data passed between piped commands

**Workspace** - Isolated project environment

**Collection** - xAI RAG knowledge base

**Provider** - AI service (Grok, Claude, OpenAI)

**Fallback** - Alternative provider when primary fails

**Tool** - File operation available to AI (read, write, edit, grep, glob)

**Manifest** - command.yaml file defining plugin

**Dispatcher** - System that executes plugin commands

**Session** - Current Isaac instance state

**Adapter** - Shell-specific implementation (PowerShell, bash)

---

**End of Complete Reference** 📚

For quick start: See **QUICK_START.md**
For how-tos: See **HOW_TO_GUIDE.md**
