
# Isaac - AI-Enhanced Multi-Platform Shell Assistant

## Quick Start for AI Agents

### Essential Commands
```powershell
# Development setup
pip install -e .              # Install with entry point 'isaac'
isaac --start --no-boot       # ✅ WORKING: Launch permanent shell assistant
isaac --oneshot /help         # Test single command without interactive mode

# Testing (run after tier/config changes)
pytest tests/test_tier_validator.py -v           # Tier safety tests
pytest tests/test_cloud_client.py -v             # Cloud sync tests
pytest tests/ --cov=isaac --cov-report=term-missing  # Full coverage report
```

### First Time Setup
```powershell
# Set API keys for AI functionality (at least one required)
$env:XAI_API_KEY = "your-xai-key"           # Grok (primary)
$env:ANTHROPIC_API_KEY = "your-claude-key"  # Claude (fallback)
$env:OPENAI_API_KEY = "your-openai-key"     # OpenAI (backup)

# Set master key for authentication (optional, creates ~/.isaac/.master_key)
$env:ISAAC_MASTER_KEY = "your-master-key"

# Launch Isaac
isaac --start
```

### What You'll See on Startup
Isaac displays a comprehensive boot sequence showing:
- **Core System Status**: Session manager, config, message queue, task manager, performance monitoring
- **AI Providers**: Shows which AI services are configured (Grok primary, Claude/OpenAI as fallbacks)
- **Commands Loaded**: Lists all 40+ available commands with versions
- **Phase Status**: Current development phase and unified command interfaces

### Basic Usage
```powershell
# Meta-commands (start with /)
isaac --start
/help                    # Show all available commands
/status                  # System status and diagnostics
/config                  # View/modify settings

# AI queries (start with 'isaac')
isaac show me all python files
isaac what is Docker?
isaac help me debug this error

# Regular shell commands (tier-validated)
ls -la
git status
```

### Authentication System
Isaac uses a key-based authentication system:
- **Master Key**: Set `ISAAC_MASTER_KEY` environment variable or create `~/.isaac/.master_key` file
- **User Keys**: Create with `/config keys create` command
- **Interactive Mode**: Currently allows unauthenticated access for development
- **Direct Commands**: Require authentication when using `-key` parameter

### How to Use Your Master Key
```powershell
# Set your master key (you already did this)
$env:ISAAC_MASTER_KEY = "ET0B7OrBkdF9HeMo8WpdvA"

# Start Isaac with authentication
isaac -key ET0B7OrBkdF9HeMo8WpdvA --start --no-boot

# Or run direct commands with authentication
isaac -key ET0B7OrBkdF9HeMo8WpdvA --oneshot /status
```

### Testing Key Authentication
Your master key is **active and working**! When you start Isaac with `-key`, it authenticates you with full admin permissions including:
- ✅ Read/write/execute access
- ✅ AI functionality
- ✅ Cloud sync
- ✅ Admin privileges

### What You Can Do With Authentication
Once authenticated, you can:
- **Run any command** without restrictions
- **Access AI features** (when API keys are configured)
- **Use cloud sync** for session persistence
- **Execute privileged operations** that require authentication

### Logout/Login Process
Currently, Isaac doesn't have explicit logout/login commands. Authentication works as follows:
- **Interactive Mode**: No authentication required (development mode)
- **Direct Commands**: Use `-key` parameter for authentication
- **Session Persistence**: Your authentication state persists during the session

### Command Categories
- **AI & Analysis**: `/ask`, `/ambient`, `/debug`, `/script`
- **File Operations**: `/read`, `/write`, `/edit`, `/search`, `/grep`
- **System Management**: `/status`, `/config`, `/backup`, `/update`
- **Workspace**: `/workspace`, `/bubble`, `/timemachine`
- **Communication**: `/msg`, `/mine`, `/tasks`

### Execution Modes
- **Interactive Mode**: `isaac --start` - Full shell replacement with AI assistance
- **One-shot Mode**: `isaac --oneshot /command` - Execute single command and exit
- **Direct Mode**: `isaac /command` - Execute command with authentication required

### Troubleshooting Common Issues

**"Invalid key: c-tab" Error (FIXED):**
- This was caused by unsupported key bindings in prompt_toolkit
- **SOLUTION**: Use `isaac --start --no-boot` (now working!)
- The Ctrl+Tab key binding has been made optional to prevent this error
- Alternative: Use `isaac --oneshot /command` for single commands

**"you think I work for free? cute." Error:**
- Isaac requires authentication for direct command execution
- Set master key: `$env:ISAAC_MASTER_KEY = "your-key"`
- Or create master key file: `echo "your-key" > ~/.isaac/.master_key`
- Interactive mode currently allows unauthenticated access

**API Key Warnings:**
- Set environment variables: `$env:XAI_API_KEY`, `$env:ANTHROPIC_API_KEY`, `$env:OPENAI_API_KEY`
- At minimum, configure XAI (Grok) for basic AI functionality
- Claude and OpenAI provide fallback for complex queries

**Command Loading Issues:**
- Ensure all `command.yaml` manifests have required fields: `name`, `version`, `summary`
- Check that aliases start with `/` (e.g., `/fix` not `fix`)
- Use `int` not `integer` for argument types

### Troubleshooting Common Issues

**"Invalid key: c-tab" Error:**
- This occurs when Isaac receives unexpected keyboard input during startup
- Try running with: `isaac --start --no-boot` to skip advanced input handling
- Or use: `isaac --oneshot /help` for single commands without interactive mode
- Avoid piping input to interactive mode - use oneshot mode instead

**"you think I work for free? cute." Error:**
- Isaac requires authentication for direct command execution
- Set master key: `$env:ISAAC_MASTER_KEY = "your-key"`
- Or create master key file: `echo "your-key" > ~/.isaac/.master_key`
- Interactive mode currently allows unauthenticated access

**API Key Warnings:**
- Set environment variables: `$env:XAI_API_KEY`, `$env:ANTHROPIC_API_KEY`, `$env:OPENAI_API_KEY`
- At minimum, configure XAI (Grok) for basic AI functionality
- Claude and OpenAI provide fallback for complex queries

**Command Loading Issues:**
- Ensure all `command.yaml` manifests have required fields: `name`, `version`, `summary`
- Check that aliases start with `/` (e.g., `/fix` not `fix`)
- Use `int` not `integer` for argument types

## Big Picture Architecture

- **Permanent Shell Layer**: Isaac wraps the shell after launch (`isaac --start`), routing all commands through its engine. Natural language requires explicit "isaac" prefix.
- **Strategy Pattern Router**: `CommandRouter` uses 15+ strategies (MetaCommandStrategy, NaturalLanguageStrategy, TierExecutionStrategy, etc.) for modular command processing.
- **Multi-Provider AI Router**: Intelligent fallback chain: Grok (xAI) → Claude (Anthropic) → OpenAI. Cost optimization via `TaskAnalyzer` and `CostOptimizer` in `isaac/ai/`.
- **Tier System**: 5-tier command safety (1: instant, 2: auto-correct, 2.5: confirm, 3: AI validate, 4: lockdown). Configured in `isaac/data/tier_defaults.json`.
- **Tool-Enabled Agent**: `IsaacAgent` class combines AI router with file tools (read/write/edit/grep/glob) for autonomous coding assistance.
- **Plugin-Based Commands**: `CommandDispatcher` loads commands from `command.yaml` manifests in `isaac/commands/*/`. Each command can define triggers, args, security limits.
- **Cross-Platform Shell Adapters**: `PowerShellAdapter` and `BashAdapter` provide unified `CommandResult` interface, never raise exceptions.
- **Command Queue**: Offline-capable queue in `isaac/queue/command_queue.py` with background sync worker.
- **Workspace Management**: Isolated project environments with optional venv and xAI Collections (RAG) support.
- **Session Persistence**: Cloud sync via GoDaddy PHP API, machine-aware history, config in `~/.isaac/`.

## Critical Developer Workflows

- **Build & Setup**: `pip install -e .` creates `isaac`, `ask`, and `mine` entry points. Config in `~/.isaac/`.
- **Testing**: `pytest tests/` (≥85% coverage required). Use fixtures from `tests/conftest.py`: `temp_isaac_dir`, `mock_api_client`, `sample_preferences`. ⚠️ **Import errors in test suite** due to incomplete command implementations.
- **Meta-Commands**: 40+ built-in commands in `isaac/commands/*/`. Each directory has `command.yaml` manifest and `run.py` implementation.
- **AI Providers**: Set `XAI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`. Router auto-selects based on task complexity via `TaskAnalyzer`.
- **Tool Development**: Extend `BaseTool` from `isaac/tools/base.py`. See `ReadTool`, `WriteTool`, `EditTool`, `ShellTool` for patterns.
- **Command Routing**: All input flows through `CommandRouter` → `TierValidator` → `CommandDispatcher` or shell adapter.

## Project-Specific Conventions

- **Tier Classification**: Commands in `isaac/data/tier_defaults.json` by tier. Override via user preferences. Tier 2.5 requires post-correction confirmation.
- **Error Handling**: Shell adapters return `CommandResult(success, output, exit_code)` - never raise exceptions. Validates in `BaseShellAdapter.execute()`.
- **Config Management**: Use `Path(__file__).parent.parent / 'data'` for package data. User config in `Path.home() / '.isaac'`.
- **AI Tool Schemas**: Tools define JSON Schema via `get_parameters_schema()`. Agent formats as function calls for provider APIs.
- **Cross-Platform Paths**: Always use `pathlib.Path`, never string concatenation. Adapters handle shell-specific syntax.
- **Provider Fallback**: `AIRouter.chat()` tries providers in order, preserves context on fallback. Tracks costs in `cost_tracking.json`.
- **Command Manifests**: YAML format with `triggers`, `args`, `security.resources` (timeout_ms, max_stdout_kib). See `docs/command_plugin_spec.md`.

## Integration Points & Key Files

- `isaac/core/command_router.py`: Strategy pattern routing with 15+ command strategies
- `isaac/core/tier_validator.py`: Safety classification using JSON tier definitions
- `isaac/core/session_manager.py`: Configuration and cloud sync management
- `isaac/ai/router.py`: Multi-provider routing with task analysis and cost optimization
- `isaac/ai/agent.py`: `IsaacAgent` - chat interface with automatic tool execution
- `isaac/tools/`: `ReadTool`, `WriteTool`, `EditTool`, `GrepTool`, `GlobTool`, `ShellTool` - file ops with pathlib, cross-platform
- `isaac/runtime/dispatcher.py`: `CommandDispatcher` loads `command.yaml` manifests, parses args, enforces security limits
- `isaac/adapters/`: `PowerShellAdapter`, `BashAdapter` extend `BaseShellAdapter`. Platform-specific `execute()` methods
- `isaac/commands/*/`: Plugin commands (ask, mine, workspace, status, config, update, etc). Each has `command.yaml` + `run.py`
- `tests/conftest.py`: Pytest fixtures - `temp_isaac_dir`, `mock_api_client`, `sample_preferences`, `tier_defaults_json`

## UI & User Experience

- Simple prompt → output → prompt flow (no locked header)
- Meta-commands for configuration and status
- Natural language requires "isaac" prefix
- Offline mode indicator: `isaac [OFFLINE]>`

## Agent Ecosystem & Privacy

- Isaac is the root key/gatekeeper for all agents
- AI query history is private (not in arrow-key recall)

---
For more details, see:
- `README.md` - User-facing quick start and feature overview
- `QUICK_START_AI.md` - AI system setup and usage guide
- `HOW_TO_GUIDE.md` - Detailed workflow examples (workspace, AI, tools)
- `AI_ROUTING_BUILD_SUMMARY.md` - Multi-provider routing architecture

---
**If unclear or incomplete, ask for feedback on specific sections to iterate.**</content>
<parameter name="filePath">c:\Projects\Isaac\.github\copilot-instructions.md