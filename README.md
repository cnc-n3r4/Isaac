# Isaac 2.0 🚀

**An Intelligent Shell Assistant with AI Superpowers**

Isaac transforms your command-line experience by combining multi-tier safety validation, AI-powered assistance from multiple providers, natural language processing, and cross-platform support into one powerful tool.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

---

## ✨ Key Features

- 🛡️ **5-Tier Safety System** - Never accidentally destroy your system
- 🤖 **Multi-Provider AI** - Grok (xAI), Claude (Anthropic), and OpenAI with intelligent fallback
- 💬 **Natural Language Interface** - Just say what you want: `isaac show me all python files`
- ⚡ **Auto-Correct Typos** - `gti status` → `git status` automatically
- 🔄 **Cross-Platform** - Use Unix commands on Windows PowerShell
- 📁 **Workspace Management** - Isolated environments for each project
- 🔍 **Advanced File Operations** - Claude Code-style file manipulation
- 🧠 **Knowledge Management** - xAI Collections for context-aware AI (RAG)

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
cd /path/to/isaac

# Install Isaac
pip install -e .

# Configure API keys (at least one required)
export XAI_API_KEY="your-xai-key"           # Grok
export ANTHROPIC_API_KEY="your-claude-key"  # Claude
export OPENAI_API_KEY="your-openai-key"     # OpenAI

# Launch Isaac
isaac --start
```

### First Commands

```bash
# Check system status
/status

# Ask the AI anything
/ask what is Docker?

# Natural language commands
isaac show me all files larger than 100MB

# Create a workspace
/workspace create myproject --venv --collection

# Regular shell commands work too (with safety validation)
ls
git status
npm install
```

---

## 💡 Why Isaac?

### The Problem
Modern development involves complex commands, cryptic syntax, potential for dangerous mistakes, and juggling multiple projects with different environments.

### The Solution
Isaac acts as your intelligent shell companion that:

1. **Understands What You Want**
   ```bash
   isaac show me all python files
   # Instead of: find . -name "*.py"
   ```

2. **Prevents Disasters**
   ```bash
   rm -rf /
   # Isaac: ⛔ Command too dangerous. Aborted.
   ```

3. **Auto-Corrects Mistakes**
   ```bash
   gti stats
   # Isaac: ✓ Auto-correcting: git stats → git status
   ```

4. **Manages Projects Efficiently**
   ```bash
   /workspace create webapp --venv --collection
   # Complete isolated environment with AI context
   ```

---

## 📚 Core Concepts

### Safety Tiers

Isaac validates every command through a 5-tier safety system:

| Tier | Type | Description | Examples |
|------|------|-------------|----------|
| **1** | ✅ Instant | Execute immediately, no delay | `ls`, `cd`, `pwd` |
| **2** | ⚡ Auto-Correct | Fix typos automatically | `gti` → `git` |
| **2.5** | ⚠️ Confirm | Auto-correct + confirmation | `git push`, `find` |
| **3** | 🛡️ Validate | AI analysis required | `rm -rf`, `chmod` |
| **4** | ⛔ Lockdown | Never execute (use `/force` to override) | `format`, `dd` |

### Multi-Provider AI

Isaac uses intelligent fallback across providers:

```
Grok (Primary) → Claude (Fallback) → OpenAI (Backup)
  Fast & cheap     Superior reasoning    High reliability
  $5-15/1M tokens  $3-15/1M tokens      $0.15-0.60/1M tokens
```

**Result:** Optimized costs with automatic failover

---

## 🎯 Use Cases

### Software Development
```bash
# Create project workspace with virtual environment and AI context
/workspace create webapp --venv --collection

# Upload project documentation for context-aware AI
/mine upload workspace-webapp README.md docs/*.md

# Ask AI questions with project context
/ask how should I structure the authentication module?

# Search your codebase
/grep "TODO" src/**/*.py

# Analyze code quality
/analyze src/auth.py
```

### System Administration
```bash
# Find large files
isaac find files larger than 1GB

# Safe command execution with AI validation
sudo systemctl restart nginx
# (Isaac analyzes impact before execution)

# Search logs with built-in grep
/grep -i "error" /var/log/*.log
```

### Learning & Documentation
```bash
# Ask questions
/ask explain Kubernetes pods

# Create learning workspace
/workspace create learn-python --collection

# Upload tutorials for context
/mine upload workspace-learn-python *.md
```

---

## 🏗️ Architecture

```
Isaac 2.0
│
├── Core Layer
│   ├── Command Router (Route all commands)
│   ├── Tier Validator (Safety validation)
│   ├── Session Manager (State management)
│   └── Unix Alias Translator (Cross-platform)
│
├── AI Layer
│   ├── Multi-Provider Router (Grok/Claude/OpenAI)
│   ├── IsaacAgent (Tool-enabled AI)
│   ├── Query Classifier (Intent detection)
│   └── Translator (Natural language → commands)
│
├── Tool Layer
│   ├── ReadTool, WriteTool, EditTool
│   ├── GrepTool, GlobTool
│   └── File operations
│
└── Command Layer (21+ Built-in Commands)
    ├── /workspace (Manage workspaces)
    ├── /ask (AI questions)
    ├── /analyze (Code analysis)
    ├── /mine (xAI Collections/RAG)
    └── ... and more
```

---

## 📖 Documentation

Isaac comes with comprehensive documentation:

| Document | Purpose | Reading Time |
|----------|---------|--------------|
| **[OVERVIEW.md](OVERVIEW.md)** | System overview and architecture | 15 min |
| **[QUICK_START.md](QUICK_START.md)** | Get up and running fast | 10 min |
| **[HOW_TO_GUIDE.md](HOW_TO_GUIDE.md)** | Practical workflows and tasks | 30 min |
| **[COMPLETE_REFERENCE.md](COMPLETE_REFERENCE.md)** | Detailed command reference | 60 min |
| **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** | Navigate all documentation | 5 min |

### Quick Links
- **New users:** Start with [QUICK_START.md](QUICK_START.md)
- **Learn workflows:** See [HOW_TO_GUIDE.md](HOW_TO_GUIDE.md)
- **Command reference:** Check [COMPLETE_REFERENCE.md](COMPLETE_REFERENCE.md)
- **AI features:** Read [QUICK_START_AI.md](QUICK_START_AI.md)

---

## 🔧 Built-in Commands

Essential commands to get you started:

```bash
/help              # Show all commands
/status            # System status
/config            # View/edit configuration
/ask <question>    # Ask AI anything
/workspace create  # Create isolated workspace
/alias --enable    # Enable Unix commands on Windows
isaac <query>      # Natural language commands

# File Operations
/read file.txt               # Read with line numbers
/write file.txt "content"    # Create/overwrite
/edit file.txt "old" "new"   # String replacement
/grep "pattern" **/*.py      # Regex search
/glob "**/*.md"              # Pattern matching
/newfile app.py              # Create with templates

# AI & Analysis
/ask what is Docker?         # Information queries
/analyze code.py             # Code analysis
/summarize README.md         # Content summary
/mine create docs            # xAI Collections (RAG)
```

---

## 🌟 Examples

### Natural Language Translation
```bash
# Natural language
isaac show me all files modified today
→ Translates to: find . -type f -mtime -1

isaac count lines in all JavaScript files
→ Translates to: find . -name "*.js" -exec wc -l {} +

isaac show git commits from last week
→ Translates to: git log --since="1 week ago"
```

### Unix Commands on Windows
```bash
# Enable Unix aliases in PowerShell
/alias --enable

# Now these work automatically:
ls -la          → Get-ChildItem -Force | Format-List
grep "text"     → Select-String "text"
cat file.txt    → Get-Content file.txt
tail -f log.txt → Get-Content log.txt -Wait -Tail 10
```

### Workspace Workflow
```bash
# Create workspace with everything
/workspace create myproject --venv --collection

# Creates:
#   ✓ Isolated directory
#   ✓ Python virtual environment
#   ✓ xAI collection for RAG
#   ✓ Activation scripts

# Switch to workspace
/workspace switch myproject

# Upload documentation
/mine upload workspace-myproject docs/*.md

# Ask context-aware questions
/ask how does the authentication flow work?
```

---

## 🔒 Security & Privacy

### Safety Measures
- ✅ Multi-tier validation for every command
- ✅ AI analysis for potentially dangerous operations
- ✅ Sandbox support with resource limits
- ✅ Path validation to block system directories
- ✅ Confirmation required for destructive commands

### Privacy Features
- ✅ Local command execution (not in cloud)
- ✅ Configurable AI providers
- ✅ No telemetry by default
- ✅ All data stays in `~/.isaac/`
- ✅ API keys stored securely

---

## 📊 Performance & Costs

### Speed
- **Tier 1 Commands:** No overhead (<1ms)
- **Tier 2 Commands:** ~10ms (auto-correct check)
- **Tier 3 Commands:** ~500ms-2s (AI validation)
- **Natural Language:** ~1-3s (translation)

### Cost Optimization
With intelligent fallback, Isaac saves ~35% on AI costs compared to single-provider usage:

```
Monthly usage (100 AI requests/day):
- With fallback optimization: ~$44/month
- Single provider (Claude): ~$68/month
- Savings: 35%
```

---

## 🗺️ Roadmap

### ✅ Currently Available
- Multi-provider AI (Grok, Claude, OpenAI)
- 5-tier safety validation
- Natural language processing
- 21+ built-in commands
- Workspace management
- Unix aliases on Windows
- File operation tools
- xAI Collections (RAG)

### 🚧 Planned Features

**Short Term (1-3 months):**
- Streaming AI responses
- Async/await support
- Voice integration
- Enhanced UI/TUI

**Medium Term (3-6 months):**
- Additional AI providers (Gemini, Mistral)
- Advanced task automation
- Web dashboard
- Team collaboration features

**Long Term (6+ months):**
- VS Code extension
- IDE integrations
- Custom model fine-tuning
- Enterprise features

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Test thoroughly** (see existing documentation)
5. **Commit your changes:** `git commit -m 'Add amazing feature'`
6. **Push to the branch:** `git push origin feature/amazing-feature`
7. **Open a Pull Request**

See [CROSS_PLATFORM_DEV_GUIDE.md](CROSS_PLATFORM_DEV_GUIDE.md) for development guidelines.

---

## 🐛 Troubleshooting

### Common Issues

**"AI provider not available"**
```bash
# Check your API keys
/config

# Verify keys in ~/.isaac/config.json or environment variables
```

**"Command not found"**
```bash
# Reinstall Isaac
pip install -e .

# Verify installation
isaac --version
```

**Need more help?**
- Check [QUICK_START.md](QUICK_START.md) → Troubleshooting
- See [HOW_TO_GUIDE.md](HOW_TO_GUIDE.md) → Troubleshooting section
- Open an issue on GitHub

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with Python, leveraging the power of multiple AI providers
- Inspired by modern AI coding assistants like Claude Code
- Thanks to all contributors and the open-source community

---

## 📬 Contact & Support

- **Author:** Nick Demiduk
- **Email:** Nick.Demiduk@protonmail.com
- **GitHub Issues:** For bug reports and feature requests
- **Documentation:** Start with [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)

---

<div align="center">

**Ready to supercharge your command-line experience?**

[Get Started](QUICK_START.md) | [Documentation](DOCUMENTATION_INDEX.md) | [Examples](HOW_TO_GUIDE.md)

**Welcome to Isaac 2.0!** 🚀

</div>
