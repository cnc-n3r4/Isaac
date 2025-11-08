# Isaac 2.0 - Quick Start Guide

Get up and running with Isaac in under 5 minutes!

## What is Isaac?

Isaac is an intelligent shell wrapper that enhances your command-line experience with:
- **AI-powered command assistance** (Grok, Claude, OpenAI)
- **5-tier safety system** to prevent dangerous commands
- **Natural language queries** ("isaac show me all python files")
- **Cross-platform support** (Windows PowerShell + Linux bash)
- **Workspace management** for project isolation
- **Unix aliases on Windows** (use `ls`, `grep`, etc. in PowerShell)

---

## Prerequisites

- **Python 3.8+**
- **PowerShell 7+** (Windows) OR **bash** (Linux/macOS)
- **API Keys** (at least one):
  - xAI (Grok) - https://x.ai/api
  - Anthropic (Claude) - https://console.anthropic.com
  - OpenAI - https://platform.openai.com

---

## Installation

### Step 1: Install Isaac

```bash
cd z:\
pip install -e .
```

### Step 2: Configure API Keys

Create or edit `~/.isaac/config.json`:

```json
{
  "default_tier": 2.5,
  "ai": {
    "providers": {
      "grok": {
        "enabled": true,
        "api_key": "YOUR_XAI_API_KEY",
        "model": "grok-beta"
      },
      "claude": {
        "enabled": true,
        "api_key": "YOUR_ANTHROPIC_API_KEY",
        "model": "claude-3-5-sonnet-20241022"
      },
      "openai": {
        "enabled": true,
        "api_key": "YOUR_OPENAI_API_KEY",
        "model": "gpt-4o-mini"
      }
    },
    "routing": {
      "strategy": "fallback",
      "prefer_provider": "grok",
      "cost_limit_daily": 10.0
    }
  },
  "workspace": {
    "enabled": true,
    "root_dir": "~/.isaac/workspaces"
  }
}
```

**Or use environment variables:**

```bash
# Windows PowerShell
$env:XAI_API_KEY = "your-key-here"
$env:ANTHROPIC_API_KEY = "your-key-here"
$env:OPENAI_API_KEY = "your-key-here"

# Linux/macOS
export XAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
```

### Step 3: Launch Isaac

```bash
isaac --start
```

You should see the Isaac splash screen and prompt!

---

## First Commands

### 1. Check Status

```bash
/status
```

Shows system status, AI provider availability, and configuration.

### 2. Ask the AI

```bash
/ask what is Docker?
```

Get conversational AI responses without executing commands.

### 3. Natural Language Commands

```bash
isaac show me all python files
```

Isaac translates this to the appropriate shell command and executes it.

### 4. Regular Shell Commands

```bash
ls
cd /path/to/dir
git status
```

All your normal commands work as expected, with safety validation.

### 5. File Operations

```bash
/read README.md
/grep "TODO" **/*.py
/newfile script.py
```

Built-in file operations with AI integration.

---

## Essential Commands Cheat Sheet

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show all commands | `/help` |
| `/status` | System status | `/status` |
| `/config` | View configuration | `/config` |
| `/ask` | Ask AI questions | `/ask what is kubernetes?` |
| `/read` | Read files | `/read file.txt` |
| `/write` | Write files | `/write output.txt "content"` |
| `/grep` | Search in files | `/grep "error" *.log` |
| `/workspace` | Manage workspaces | `/workspace create myproject` |
| `/alias` | Unix aliases | `/alias --enable` |
| `/newfile` | Create files | `/newfile script.py` |

---

## Safety Tiers Explained

Isaac validates every command through a 5-tier safety system:

- **Tier 1**: ✅ Instant execution (ls, cd, pwd)
- **Tier 2**: ⚡ Auto-correct typos (git stats → git status)
- **Tier 2.5**: ⚠️ Correct + confirm
- **Tier 3**: 🛡️ AI validation required (rm, chmod)
- **Tier 4**: ⛔ Lockdown - never execute (format, dd)

You can override with `/force`:

```bash
/force rm -rf dangerous_folder
```

---

## Common Workflows

### Create a New Workspace

```bash
# Create workspace with virtual environment and xAI collection
/workspace create myproject --venv --collection

# Switch to workspace
/workspace switch myproject

# List all workspaces
/workspace list
```

### Enable Unix Aliases (Windows)

```bash
# Enable automatic Unix-to-PowerShell translation
/alias --enable

# Now you can use Unix commands in PowerShell
ls -la
grep "pattern" file.txt
cat README.md
```

### File Creation with Templates

```bash
# Create Python file with template
/newfile script.py

# Create with custom content
/newfile notes.txt --content "My notes"

# Create from piped content
echo "Hello World" | /newfile output.txt

# List available templates
/newfile --list-templates
```

### AI-Powered Workflows

```bash
# Ask questions
/ask how do I use git rebase?

# Natural language commands (must start with "isaac")
isaac find all files larger than 100MB
isaac show me git commits from last week

# Analyze code
/analyze path/to/code.py
```

---

## Piping Commands

Chain Isaac commands together:

```bash
/read file.txt | /grep "error" | /save errors.txt
```

---

## Configuration Tips

### Set Default AI Provider

Edit `~/.isaac/config.json`:

```json
{
  "ai": {
    "routing": {
      "prefer_provider": "claude"  // or "grok" or "openai"
    }
  }
}
```

### Adjust Safety Tier

```json
{
  "default_tier": 2  // More permissive (1-4)
}
```

### Enable Workspace Features

```json
{
  "workspace": {
    "enabled": true,
    "root_dir": "~/projects"  // Custom workspace location
  }
}
```

---

## Troubleshooting

### "AI provider not available"

1. Check your API keys in `~/.isaac/config.json`
2. Verify API key is valid at provider's website
3. Check internet connection

### "Command not found"

1. Make sure Isaac was installed: `pip install -e .`
2. Restart your shell
3. Check Python is in PATH

### "Permission denied"

1. Check file permissions: `ls -la`
2. Use `/force` to override safety tier (carefully!)
3. Run with elevated privileges if needed

### "Workspace not found"

1. List workspaces: `/workspace list`
2. Check workspace is in `~/.isaac/workspaces/`
3. Create workspace: `/workspace create name`

---

## Next Steps

- Read the **HOW_TO_GUIDE.md** for detailed workflows
- Read the **COMPLETE_REFERENCE.md** for all commands
- Explore AI features: `/ask`, natural language, task mode
- Set up workspaces for your projects
- Configure Unix aliases if on Windows

---

## Getting Help

```bash
# Show all commands
/help

# Get help on specific command
/help /workspace

# Check system status
/status

# View configuration
/config
```

---

## Example Session

```bash
$ isaac --start

╔═══════════════════════════════════════╗
║        ISAAC 2.0 - Shell Assistant        ║
║     AI-Powered • Multi-Platform           ║
╚═══════════════════════════════════════╝

Isaac > /status
✓ AI Provider: Grok (primary)
✓ Workspaces: 3 available
✓ Current tier: 2.5

Isaac > /workspace create demo --venv
✓ Created workspace 'demo'
✓ Created virtual environment in 'demo/.venv'

Isaac > /alias --enable
Unix alias translation enabled.

Isaac > ls -la
# Automatically translated to: Get-ChildItem -Force | Format-List

Isaac > isaac show me all python files
Isaac > Executing: find . -name "*.py"
./script1.py
./script2.py
./lib/utils.py

Isaac > /ask what is Docker?
Isaac > Docker is a containerization platform that...

Isaac > /exit
Goodbye!
```

---

**Welcome to Isaac! You're now ready to supercharge your command-line experience.** 🚀
