
# Isaac - AI-Enhanced Multi-Platform Shell Assistant

## Quick Start for AI Agents

### Essential Commands
```powershell
# Development setup
pip install -e .              # Install with entry point 'isaac'
isaac --start -key YOUR_KEY   # Launch permanent shell assistant (requires auth key)

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

# Launch Isaac
isaac --start
```

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
/workspace create myproject --venv
ls -la
git status
```

### Command Categories
- **AI & Analysis**: `/ask`, `/ambient`, `/debug`, `/script`
- **File Operations**: `/read`, `/write`, `/edit`, `/search`, `/grep`
- **System Management**: `/status`, `/config`, `/backup`, `/update`
- **Workspace**: `/workspace`, `/bubble`, `/timemachine`
- **Communication**: `/msg`, `/mine`, `/tasks`

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
**If unclear or incomplete, ask for feedback on specific sections to iterate.**

### Agent Ecosystem & Privacy

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