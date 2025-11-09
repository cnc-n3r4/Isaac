
# Isaac - AI-Enhanced Multi-Platform Shell Assistant

## Quick Start for AI Agents

### Essential Commands
```powershell
# Development setup
pip install -e .              # Install with entry point 'isaac'
isaac --start                 # Launch permanent shell assistant

# Testing (run after tier/config changes)
pytest tests/test_tier_validator.py -v           # Tier safety tests
pytest tests/test_cloud_client.py -v             # Cloud sync tests
pytest tests/ --cov=isaac --cov-report=term-missing  # Full coverage report
```

### Big Picture Architecture

- **Permanent Shell Layer**: Isaac wraps the shell after launch (`isaac --start`), routing all commands through its engine. Natural language requires explicit "isaac" prefix.
- **Multi-Provider AI Router**: Intelligent fallback chain: Grok (xAI) → Claude (Anthropic) → OpenAI. Cost optimization via `TaskAnalyzer` and `CostOptimizer` in `isaac/ai/`.
- **Tier System**: 5-tier command safety (1: instant, 2: auto-correct, 2.5: confirm, 3: AI validate, 4: lockdown). Configured in `isaac/data/tier_defaults.json`.
- **Tool-Enabled Agent**: `IsaacAgent` class combines AI router with file tools (read/write/edit/grep/glob) for autonomous coding assistance.
- **Plugin-Based Commands**: `CommandDispatcher` loads commands from `command.yaml` manifests in `isaac/commands/*/`. Each command can define triggers, args, security limits.
- **Cross-Platform Shell Adapters**: `PowerShellAdapter` and `BashAdapter` provide unified `CommandResult` interface, never raise exceptions.
- **Command Queue**: Offline-capable queue in `isaac/queue/command_queue.py` with background sync worker.
- **Workspace Management**: Isolated project environments with optional venv and xAI Collections (RAG) support.
- **Session Persistence**: Cloud sync via GoDaddy PHP API, machine-aware history, config in `~/.isaac/`.

### Developer Workflows

- **Build & Setup**: `pip install -e .` creates `isaac`, `ask`, and `mine` entry points. Config in `~/.isaac/`.
- **Testing**: `pytest tests/` (≥85% coverage required). Use fixtures from `tests/conftest.py`: `temp_isaac_dir`, `mock_api_client`, `sample_preferences`.
- **Meta-Commands**: 21+ built-in commands in `isaac/commands/*/`. Each directory has `command.yaml` manifest and `run.py` implementation. New: `/update` command for intelligent package management.
- **AI Providers**: Set `XAI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`. Router auto-selects based on task complexity via `TaskAnalyzer`.
- **Tool Development**: Extend `BaseTool` from `isaac/tools/base.py`. See `ReadTool`, `WriteTool`, `EditTool`, `ShellTool` for patterns.
- **Command Routing**: All input flows through `CommandRouter` → `TierValidator` → `CommandDispatcher` or shell adapter.

### Project-Specific Conventions

- **Tier Classification**: Commands in `isaac/data/tier_defaults.json` by tier. Override via user preferences. Tier 2.5 requires post-correction confirmation.
- **Error Handling**: Shell adapters return `CommandResult(success, output, exit_code)` - never raise exceptions. Validates in `BaseShellAdapter.execute()`.
- **Config Management**: Use `Path(__file__).parent.parent / 'data'` for package data. User config in `Path.home() / '.isaac'`.
- **AI Tool Schemas**: Tools define JSON Schema via `get_parameters_schema()`. Agent formats as function calls for provider APIs.
- **Cross-Platform Paths**: Always use `pathlib.Path`, never string concatenation. Adapters handle shell-specific syntax.
- **Provider Fallback**: `AIRouter.chat()` tries providers in order, preserves context on fallback. Tracks costs in `cost_tracking.json`.
- **Command Manifests**: YAML format with `triggers`, `args`, `security.resources` (timeout_ms, max_stdout_kib). See `docs/command_plugin_spec.md`.

### Integration Points & Key Files

- `isaac/core/command_router.py`: Routes input → tier validator → AI/dispatcher/shell. Handles `/`, `isaac`, `!device` prefixes.
- `isaac/core/tier_validator.py`: Loads `tier_defaults.json`, applies user overrides, returns tier (1-4) for commands.
- `isaac/core/session_manager.py`: Manages config, preferences, cloud sync. Central state hub.
- `isaac/ai/router.py`: Multi-provider routing with `TaskAnalyzer` (complexity), `CostOptimizer` (budget), performance tracking.
- `isaac/ai/agent.py`: `IsaacAgent` class - chat with tool execution. System prompts for code assistance.
- `isaac/tools/`: `ReadTool`, `WriteTool`, `EditTool`, `GrepTool`, `GlobTool`, `ShellTool` - file ops with pathlib, cross-platform. ShellTool executes safe commands with tier validation.
- `isaac/runtime/dispatcher.py`: `CommandDispatcher` loads `command.yaml` manifests, parses args, enforces security limits.
- `isaac/adapters/`: `PowerShellAdapter`, `BashAdapter` extend `BaseShellAdapter`. Platform-specific `execute()` methods.
- `isaac/commands/*/`: Plugin commands (ask, mine, workspace, status, config, update, etc). Each has `command.yaml` + `run.py`.
- `isaac/queue/command_queue.py`: SQLite-based offline queue. `sync_worker.py` syncs when cloud available.
- `tests/conftest.py`: Pytest fixtures - `temp_isaac_dir`, `mock_api_client`, `sample_preferences`, `tier_defaults_json`.

### UI & User Experience

- Simple prompt → output → prompt flow (no locked header)
- Meta-commands for configuration and status
- Natural language requires "isaac" prefix
- Offline mode indicator: `isaac [OFFLINE]>`

### Agent Ecosystem & Privacy

- Isaac is the root key/gatekeeper for all agents
- AI query history is private (not in arrow-key recall)

### Roadmap & Open Design Questions

- Shell abstraction: PowerShell vs bash detection, translation, tier lists
- Startup sequence: splash screen, header locking, warm/cold start
- Offline mode: queue management, reconnection logic, conflict resolution

---
For more details, see:
- `README.md` - User-facing quick start and feature overview
- `QUICK_START_AI.md` - AI system setup and usage guide
- `HOW_TO_GUIDE.md` - Detailed workflow examples (workspace, AI, tools)
- `AI_ROUTING_BUILD_SUMMARY.md` - Multi-provider routing architecture

---
**If unclear or incomplete, ask for feedback on specific sections to iterate.**

## Meta-Commands System

### Current Implementation (`isaac/commands/`)
Isaac uses a **plugin-based command system** with `command.yaml` manifests:
- Each command directory contains `command.yaml` (metadata) and implementation files
- `CommandDispatcher` in `isaac/runtime/dispatcher.py` loads all manifests at startup
- Commands are registered by `triggers` and `aliases` from manifests
- 21+ built-in commands: help, ask, mine, workspace, status, config, backup, restore, etc.

### Command Types by Prefix

**1. Local Meta-Commands** (`/command`):
```python
# Handled in command_router.py → CommandDispatcher
if input_text.startswith('/'):
    command_info = dispatcher.resolve_trigger(input_text)
    # Execute via manifest specification (Python, shell, etc.)
```

**2. Natural Language** (`isaac <query>`):
```python
# Requires "isaac" prefix to trigger AI translation
if input_text.lower().startswith('isaac '):
    query = input_text[6:].strip()
    result = translator.translate(query, shell_name, session)
    # Translated command goes through normal tier validation
```

**3. Device Routing** (`!device <cmd>`):
```python
# Route commands to other machines in Isaac network
if input_text.startswith('!'):
    parts = input_text[1:].split(None, 1)  # !alias /command
    queue_id = session.queue.enqueue(cmd, target_device=alias)
```

**4. Regular Shell Commands** (no prefix):
```python
# Standard shell commands go through tier validation
tier = validator.get_tier(command)  # From tier_defaults.json
if tier <= 2:
    result = shell.execute(command)
elif tier >= 3:
    decision = ai_validator.validate(command)
```

### Command Manifest Format
Each `command.yaml` defines:
- `triggers`: Primary command names (e.g., `/ask`, `/help`)
- `aliases`: Alternative names
- `args`: Array of argument specs (name, type, required, default)
- `security.resources`: Runtime limits (timeout_ms, max_stdout_kib)
- `execution`: How to run (python_module, shell_script, etc.)

Example from a manifest:
```yaml
triggers: ["/workspace"]
args:
  - name: action
    type: enum
    enum: [create, list, switch, delete]
    required: true
security:
  resources:
    timeout_ms: 30000
    max_stdout_kib: 100
```

## Command Orchestration Flow
```
USER → ORCHESTRATOR → VALIDATOR → EXECUTOR → CHRONO-LOG → UI
```

### Command Classification
Commands are classified into three types:
- **Local** (`/ask`, `/help`): Meta-commands executed immediately
- **Direct** (`isaac /f <cmd>`): Bypass validation, execute immediately
- **Regular** (no prefix): Shell commands with tier-based safety validation

### Tier-Based Execution
- **Tier ≤2**: Auto-execute (safe commands like `ls`, `cd`, `pwd`)
- **Tier ≥3**: Route to AI validation before execution

### AI Validation Decisions
- **SAFE**: Execute immediately
- **NEEDS_CONFIRM**: Prompt user for explicit Yes/No
- **DENY**: Block execution with logged reason

### Chronological Logging
Append-only audit trail capturing:
- `exec_start/result`: Command execution lifecycle
- `validation_start/decision`: AI analysis events
- `user_confirmation`: User Yes/No choices
- `cancel_reason`: Blocked/denied operations

## Detailed Command Flow

### High-Level Swimlane
```
USER → ORCHESTRATOR → VALIDATOR → EXECUTOR → CHRONO-LOG → UI
```

**Flow Table:**
| USER | ORCHESTRATOR | VALIDATOR | EXECUTOR | CHRONO-LOG | UI |
|------|-------------|-----------|----------|------------|----|
| type command | classify(local/direct/regular) | | | | |
| | | | | | H0: update Mode/Tier/Last |
| Local (/ask,help) | → execute | | → exec | append(local_exec) | |
| Direct (`isaac`) | execute now | | → exec | append(exec_start/result) | |
| Regular Tier≤2 | execute now | | → exec | append(exec_start/result) | |
| Regular Tier≥3 | ask AI validator | ← analyze | | | H1: AI busy |
| | ← decision | SAFE/CONFIRM/DENY | | append(validation_decision) | |
| | SAFE→execute | | → exec | append(exec_start/result) | H2/H3: exec updates |
| confirm? | CONFIRM→ask user | | | | H4: flash Yes/No |
| | Yes→execute | | → exec | append(user_confirmation) | |
| | No→cancel | | | append(cancel_reason) | H5: show reason |

### Classification Flow
**Input:** raw_user_input  
**Output:** classification {kind: local|direct|regular, tier: null|int, normalized_command: string}

```
User input
    ↓
Parse + Classify: local? direct? tier?
    ↓
Local (/ask…) → Local Route
    ↓
Direct (`isaac <cmd>`) → Direct Route  
    ↓
Regular (no prefix) → Tier 1..N
```

### Execution & Logging Flow
**Routes based on classification:**
- **Local:** execute → LOG(local_exec)
- **Direct:** execute → LOG(exec_start/result)  
- **Regular Tier ≤2:** execute → LOG(exec_start/result)
- **Regular Tier ≥3:** → Validation path → LOG(validation_start)

### AI Validation Flow
**For Tier ≥3 only:**
```
Inputs: cmd, history, policy
    ↓
Risk Checks → Decision + Rationale (JSON)
    ↓
SAFE | NEEDS_CONFIRM | DENY
```
**Outputs:** status, rationale, flags, suggested_remediations

### User Confirmation Flow
**For NEEDS_CONFIRM decisions:**
```
Validation Decision
    ↓
SAFE → Execute → LOG(exec_start/result) → Done
DENY → LOG(deny_reason) → Done
NEEDS_CONFIRM → Prompt user (Yes/No)
    ↓
Yes → Execute → LOG(exec_*) → Done
No → Cancel → LOG(cancel_reason) → Done
```

## UI Integration Hooks
The terminal header updates in real-time synchronized with command flow:

- **H0**: Classification → Update "Mode", "Tier", "Last: '<cmd>'"
- **H1**: Validation start/decision → Update AI status + decision badge
- **H2**: Exec start → Pulse Mode:EXEC, bump history count
- **H3**: Exec result → Update CPU/Net, Mode:IDLE, refresh Last command
- **H4**: User confirmation → Flash Yes/No in status cells
- **H5**: Cancel/deny → Show reason tag in status cluster
- **H6**: Prompt focus → Draw white/blocked prompt line

### Header Layout (Fixed 3-line format)
```
Line 1: ISAAC vX.Y.Z | SID:xxxx     | [cloud] [AI] [VPN]
Line 2: <user>@<machine> | Last:'x' | Hist:### [log] [Tier]
Line 3: PWD:<cwd> | IP:<ip>         | [CPU] [Net] Wrap:80
```
Column widths: ~34 | ~28 | ~18 (fixed-fit to frame)  
Prompt line: White background + block cursor (always current)  
Output area: Scroll region beneath header + prompt line

## Developer Workflows

### Build & Setup
```bash
pip install -e .  # Install in development mode with entry point 'isaac'
pytest tests/ --cov=isaac --cov-report=term-missing  # Run full test suite with coverage
```

### Testing Patterns
- **Test Discovery**: `pytest tests/` with `test_*.py` pattern
- **Mock Fixtures**: Use `temp_isaac_dir` and `mock_api_client` from `tests/conftest.py`
- **Coverage Target**: ≥85% coverage required
- **Integration Tests**: Located in `instructions/test_integration/` with completion templates

### Debugging AI Router
- **Provider Selection**: Check `TaskAnalyzer` output to see complexity scoring
- **Cost Tracking**: `cost_tracking.json` in `~/.isaac/` has detailed usage by provider
- **Fallback Logic**: `AIRouter.chat()` preserves conversation context across provider switches
- **Tool Execution**: `IsaacAgent.chat()` returns `tool_executions` list showing all file ops performed
- **Shell Commands**: `ShellTool` validates commands through tier system before execution

## Project Conventions

### Safety-Critical Patterns
**Tier Classification** (`isaac/data/tier_defaults.json`):
```json
{
  "1": ["ls", "cd", "pwd"],           // Instant execution
  "2": ["grep", "head", "tail"],      // Standard commands
  "2.5": ["find", "sed", "awk"],      // Moderate - requires confirmation
  "3": ["cp", "mv", "git"],           // Moderate risk
  "4": ["rm", "format", "dd"]         // Dangerous - requires confirmation
}
```

**Structured Error Handling**:
```python
# From isaac/adapters/base_adapter.py
@dataclass
class CommandResult:
    success: bool
    output: str
    exit_code: int
# Never raise exceptions - always return structured results
```

### Configuration Management
**Path-Based Config Loading**:
```python
# From isaac/core/tier_validator.py
data_dir = Path(__file__).parent.parent / 'data'
config = json.load((data_dir / 'tier_defaults.json').open())
```

**Session Persistence** (`~/.isaac/config.json`):
- User preferences, API keys, cloud sync settings
- Command history partitioned by terminal_id
- AI chat history merged across machines

### AI Integration Patterns
**Multi-Provider Support**:
```python
# From isaac/ai/router.py
class AIRouter:
    def __init__(self, config_path=None, session_mgr=None):
        # Provider abstraction with fallback handling
        self.task_analyzer = TaskAnalyzer(config_manager=routing_config)
        self.cost_optimizer = CostOptimizer(routing_config, cost_storage_path)
```

**Command Enhancement Pipeline**:
1. Natural language detection
2. AI validation/correction
3. Tier classification
4. Safe execution with rollback

### Cross-Platform Shell Abstraction
**Adapter Pattern** (`isaac/adapters/`):
```python
# From isaac/adapters/base_adapter.py
class BaseShellAdapter(ABC):
    @abstractmethod
    def execute(self, command: str) -> CommandResult:
        pass
# PowerShellAdapter, BashAdapter implement platform-specific execution
```

## Key Files & Integration Points

### Core Components
- `isaac/core/command_router.py`: Command prefix routing and AI processing pipeline
- `isaac/core/tier_validator.py`: Safety classification using JSON tier definitions
- `isaac/core/session_manager.py`: Configuration and cloud sync management

### UI Architecture
- `isaac/ui/terminal_control.py`: Terminal display management with status header
- `isaac/ui/permanent_shell.py`: Main shell loop with command processing
- `isaac/ui/advanced_input.py`: Keyboard handling for config mode navigation

### AI Components
- `isaac/ai/router.py`: Multi-provider routing with task analysis and cost optimization
- `isaac/ai/agent.py`: `IsaacAgent` - chat interface with automatic tool execution
- `isaac/ai/task_analyzer.py`: Complexity scoring for provider selection
- `isaac/ai/cost_optimizer.py`: Budget tracking and cost-aware routing

### Cloud Integration
- `isaac/api/cloud_client.py`: HTTP client for PHP API communication
- `php_api/`: GoDaddy-hosted backend with Bearer token authentication
- Session files: `command_history.json`, `preferences.json`, `task_history.json`

### Data Models
- `isaac/models/preferences.py`: User configuration storage
- `isaac/models/aiquery_history.py`: AI interaction logging
- `isaac/models/task_history.py`: Task execution tracking

## Integration Points

### External Dependencies
- **PHP API**: `https://n3r4.xyz/isaac/api/` with Bearer token auth
- **AI Providers**: xAI (primary), Claude (fallback), OpenAI (backup) via REST APIs
- **Shell Environments**: PowerShell (Windows), bash (Unix-like)

### Cross-Component Communication
- **Session Manager**: Central hub for config, preferences, and cloud sync
- **Command Router**: Orchestrates tier validation, AI processing, and execution
- **Terminal Control**: Manages UI state and updates status indicators
- **Shell Adapters**: Platform-specific command execution with unified interface

### Development Environment Setup
- **Python 3.8+** required with `requirements.txt` dependencies
- **Editable Install**: `pip install -e .` creates `isaac`, `ask`, `mine` commands
- **Test Environment**: `pytest` with coverage reporting and mock fixtures
- **Configuration**: `~/.isaac/` directory for user data and settings

## Next-Phase Design Roadmap

### Local Environment Quality-of-Life
#### Unified Shell Interface
- Merge `/` and `!` handlers into a single lightweight dispatcher
- Keep a small plugin registry so new verbs (`/add`, `/list`, `/search`, `/task`) auto-register from a `plugins/` directory
- Add per-terminal color themes or prompts that display `[isaac@desktop] >` for quick context

#### Command Queue Overlay
- Maintain a small local queue (`~/.isaac/queue.db`) that buffers outgoing jobs if the cloud hub is unreachable
- Background thread syncs when connection returns — ensures nothing is lost if you drop Wi-Fi

### Cloud Hub Refinements
#### Job Lifecycle State Machine
- queued → picked_up → running → done|failed
- Each state change triggers a webhook or event; supports live dashboards later
- Add a `job_retries` field with exponential backoff and jitter

#### Search API Upgrade
- Expose `/search?kind=(chat|cmd|both)&q=term&terminal_id=...`
- Integrate SQLite FTS5 or Postgres `tsvector` for case-insensitive full-text queries
- Add filters for time range, terminal, and return type (`summary` vs `raw`)

#### Event Bus Layer
- Lightweight pub/sub inside the hub for job status updates, notifications, and system metrics
- Could use Redis Streams or a simple in-process queue for now

### Agent Enhancements
#### Configurable Modules
- Agents read a manifest to enable/disable capabilities:
  ```yaml
  modules:
    - exec
    - monitor
    - aiquery
    - fileops
  ```

#### Plugin Hot-Reloading
- Watch `commands/` directory for changes and reload manifests without restart
- Support for development mode with auto-restart on plugin changes

#### Resource Monitoring
- Track CPU, memory, and network usage per command execution
- Implement per-agent resource quotas and throttling</content>
<parameter name="filePath">c:\Projects\Isaac\.github\copilot-instructions.md