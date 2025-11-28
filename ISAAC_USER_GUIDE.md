# Isaac User Guide - Complete Command Reference

## Overview

Isaac is a **high-performance AI shell assistant** with C++/Python hybrid architecture, featuring:

- **C++ Core**: Ultra-fast command routing and validation (< 10ms latency)
- **5-Adjust Safety**: Never accidentally destroy your system
- **Multi-Provider AI**: Grok (xAI), Claude (Anthropic), OpenAI with intelligent fallback
- **Strategy Pattern Router**: 15+ routing strategies for optimal command handling
- **Memory Optimized**: < 20 MB startup with lazy loading and memory pooling

Isaac supports THREE ways to interact:

1. **Meta Commands** - Start with `/` (e.g., `/status`, `/config`, `/help`)
2. **Natural Language** - Start with `isaac` (e.g., `isaac show me all python files`)
3. **Regular Shell Commands** - Just type them (e.g., `ls`, `git status`)

---

## 🚀 Quick Start Examples

### Basic Usage
```bash
# Start Isaac (C++ optimized)
isaac --start

# Check system status
/status

# Configure AI providers
/config set api_key xai your-xai-key
/config set api_key anthropic your-claude-key

# Natural language queries
isaac show me all python files in this directory
isaac what is the current git status
isaac help me debug this error

# Safe shell commands with AI assistance
ls -la
git status
mkdir new-project
```

### Advanced Examples
```bash
# AI-powered file operations
isaac read the main.py file and summarize it
isaac find all TODO comments in the codebase
isaac create a new function for user authentication

# Workspace management
isaac switch to the web-frontend workspace
isaac show me the current workspace status
isaac backup this workspace

# Team collaboration
isaac share this workspace with the team
isaac show me team collections
isaac add this knowledge to team memory

# Device routing (multi-device support)
/route !laptop ls -la
/route !server:load_balancer /status
```

---

## 🏗️ Architecture Overview

### C++/Python Hybrid Design

**C++ Core (Performance):**
- CommandRouter with 15+ routing strategies
- TierValidator with optimized regex validation
- ShellAdapter with direct system calls
- Memory pooling for frequent allocations
- Zero-copy string operations

**Python Layer (Flexibility):**
- AI Router with multi-provider orchestration
- Plugin system with security sandboxing
- UI components with ANSI terminal control
- Team collaboration and workspace management

### Safety System (5 Tiers)

1. **Tier 1**: Instant execution (safe commands like `ls`, `pwd`)
2. **Tier 2**: Auto-correct typos (`gti status` → `git status`)
3. **Tier 2.5**: Correct + confirm (shows correction, asks for approval)
4. **Tier 3**: AI validation required (potentially dangerous commands)
5. **Tier 4**: Lockdown (never execute, like `rm -rf /`)

---

## 📚 Command Categories

### Meta Commands (`/` prefix)

#### System Management
```bash
/status              # System status and diagnostics
/config             # Configuration management
/help               # Show all available commands
/exit               # Exit Isaac
/clear              # Clear terminal screen
```

#### Configuration
```bash
/config                     # Show configuration overview
/config set key value       # Set configuration value
/config get key            # Get configuration value
/config list               # List all configuration keys
/config status             # Show configuration status
```

#### AI & Analysis
```bash
/ask "question"            # Ask AI a question
/ambient                   # Ambient AI monitoring
/debug                     # Debug mode
/script                    # Script analysis
```

#### File Operations
```bash
/read file.txt             # Read file contents
/write file.txt "content"  # Write to file
/edit file.txt             # Edit file with AI assistance
/search "pattern"          # Search for text patterns
/grep "regex"              # Advanced regex search
```

#### Workspace Management
```bash
/workspace                 # Workspace operations
/bubble                    # Bubble (context) management
/timemachine              # Time-based workspace snapshots
```

#### Communication
```bash
/msg "message"            # Send message
/mine                     # Personal notes
/tasks                    # Task management
```

### Natural Language (`isaac` prefix)

```bash
isaac show me all python files
isaac what is the current directory structure
isaac help me understand this error message
isaac create a function to validate email addresses
isaac refactor this code for better performance
isaac explain how this algorithm works
```

### Regular Shell Commands

All standard shell commands work with AI assistance:

```bash
ls -la                    # List files (with AI context)
git status               # Git operations
mkdir new-project        # Directory operations
ps aux | grep python     # Piping support
find . -name "*.py"      # Find operations
```

---

## 🔧 Advanced Features

### Strategy-Based Routing

Isaac uses 15+ routing strategies for optimal command handling:

- **PipeStrategy**: Handles `|` piping operations
- **CdStrategy**: Directory change commands
- **ForceExecutionStrategy**: `/f` and `/force` commands
- **ConfigStrategy**: `/config` meta-commands
- **DeviceRoutingStrategy**: `!device` multi-device routing
- **TaskModeStrategy**: `isaac task:` multi-step tasks
- **AgenticModeStrategy**: `isaac agent:` autonomous workflows
- **NaturalLanguageStrategy**: AI query processing
- **TierExecutionStrategy**: Default safety validation

### Memory Optimization

- **Lazy Loading**: Components loaded on-demand (45% memory reduction)
- **Memory Pooling**: Object reuse for CommandResult allocations
- **Zero-Copy Strings**: `string_view` in C++ routing components
- **Target**: < 20 MB startup memory

### Plugin Security

- **Sandboxing**: Isolated execution environment
- **Permission System**: Granular access controls
- **API Key Management**: Secure key storage and validation
- **Resource Limits**: CPU time, memory, and file access controls

### Team Collaboration

- **Workspace Sharing**: Share complete development contexts
- **Team Collections**: Shared knowledge base
- **Team Memory**: Collaborative AI memory
- **Permission Management**: Role-based access control

---

## 🎯 Best Practices

### Performance Tips
- Use C++ optimized commands for speed-critical operations
- Leverage lazy loading by accessing features on-demand
- Configure only needed AI providers to reduce memory usage

### Safety Guidelines
- Trust the 5-tier safety system - it prevents accidents
- Use `/force` only when you know what you're doing
- Natural language queries are safe (no execution)

### AI Usage
- Set at least one AI provider (XAI recommended for speed)
- Use specific, clear queries for best results
- Leverage context awareness for coding assistance

---

## 🔍 Troubleshooting

### Common Issues

**High Memory Usage:**
- Check lazy loading: `isaac --start --no-boot`
- Monitor with `/status` command
- Reduce configured AI providers

**Command Not Found:**
- Use `/help` to see available commands
- Check command syntax (meta commands start with `/`)
- Natural language queries start with `isaac`

**AI Not Responding:**
- Verify API keys: `/config status`
- Check network connectivity
- Try different AI provider

**Performance Issues:**
- Ensure C++ core is built: `make -j$(nproc)`
- Check memory usage: `/status`
- Restart Isaac to clear memory

---

## 📈 Development Status

- ✅ **C++ Core**: Command routing, validation, shell adapters
- ✅ **Strategy Pattern**: 15+ routing strategies implemented
- ✅ **Memory Optimization**: Pooling, lazy loading, zero-copy
- ✅ **Plugin Security**: Sandboxing, permissions, API keys
- ✅ **Team Collaboration**: Workspace sharing, collections, memory
- ✅ **UI Components**: Terminal control, ANSI handling, size detection

**Next Priorities:**
- CI/CD pipeline setup
- Type hints and linting
- Documentation completion
- Performance benchmarking

---

**Isaac: Your AI-powered shell for the modern developer.** 🚀
