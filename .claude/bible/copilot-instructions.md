
# Isaac - AI-Enhanced Multi-Platform Shell Assistant

## Quick Start for AI Agents

### Essential Commands
```powershell
# Development setup
pip install -e .              # Install with entry point 'isaac'
isaac /start                 # Launch permanent shell assistant

# Testing (run after tier/config changes)
pytest tests/test_tier_validator.py -v           # Tier safety tests
pytest tests/test_cloud_client.py -v             # Cloud sync tests
pytest tests/ --cov=isaac --cov-report=term      # Full coverage
```

### Command Structure (Crystal Clear!)

**External Mode (before `isaac /start`):**
- `isaac /ask <query>` - AI query
- `isaac /move <files>` - File operations  
- `isaac /task <description>` - Multi-step tasks
- `isaac /start` - Enter internal mode
- Restriction: Internal-only commands like `/f`, `/msg`, `/collect` NOT available externally

**Internal Mode (after `isaac /start`):**
- **All Isaac commands use `/` prefix:** `/help`, `/config`, `/status`, `/ask`, `/task`, `/collect`, `/debug`, `/msg`, `/f`, `/exit`
- **Device routing uses `!` prefix:** `/msg !laptop2 "text"`, `/show-cmd !desktop3`
- **Natural language:** `isaac <query>` works same as `/ask <query>`
- **Shell commands:** No prefix (e.g., `ls`, `cd`, `rm`) go through tier validation
- **Invalid queries without 'isaac':** Get sass response "I have a name, use it."

### Big Picture Architecture

- **Permanent Shell Layer**: Isaac wraps the shell after launch (`isaac /start`), routing all commands through its engine.
- **Session Roaming**: Cloud-based session persistence (GoDaddy PHP API), machine-aware command history, and privacy boundaries for AI queries.
- **Tier System**: 4+ tiers (1: instant, 2: auto-correct, 2.5: confirm typo, 3: AI validation, 4: lockdown). User-customizable via config.
- **Task Mode**: Multi-step command planning, safety-based approval, interactive failure recovery (auto-fix, retry, skip, abort, suggest).
- **Auto-Fix Learning**: Isaac learns from user corrections, syncs patterns, tracks machine compatibility, and confidence scores.
- **Dual History**: Command history (machine-aware, arrow keys) and AI query history (private, machine-agnostic).
- **Session Data Structure**: Six cloud JSON files (preferences, command_history, aiquery_history, task_history, learned_autofixes, learned_patterns), versioning, and rollback system.
- **UI Simplification**: Simple prompt/output loop, meta-commands for config/status/help, no locked header or complex screen management.
- **Offline Mode**: Local queueing, auto-reconnect, batch sync, prompt indicator.
- **Agent Ecosystem**: Isaac is the gatekeeper; other agents (Sarah, Daniel) have defined access boundaries.

### Developer Workflows

- **Build & Setup**: `pip install -e .` (editable), `isaac /start` to launch.
- **Testing**: `pytest tests/` (≥85% coverage required), integration tests in `instructions/test_integration/`.
- **Meta-Commands**: ALL start with `/` - `/help`, `/status`, `/config`, `/ask`, `/task`, `/clear` (see `isaac/commands/`). Device routing uses `!` - e.g., `/msg !laptop2`, `/show-cmd !desktop3`. `/config` supports subcommands for status, AI, cloud, plugins, and settings.
- **Task Mode**: Use `/task <goal>` for multi-step planning and execution. Failure recovery options: f/r/s/a/? (auto-fix, retry, skip, abort, suggest).
- **Session Management**: All session data is cloud-synced; rollback via snapshots (manual or auto-triggered).

### Project-Specific Conventions

- **Tier Classification**: See `isaac/data/tier_defaults.json` for command tiers. Tier 2.5 (find/sed/awk) requires confirmation after typo correction.
- **Error Handling**: All shell adapters return `CommandResult` (never raise exceptions).
- **Config Management**: Path-based config loading, user preferences in `~/.isaac/config.json`.
- **Privacy**: AI query history is private to user/Isaac; other agents have restricted access.
- **Auto-Fix Patterns**: Learned fixes stored in `learned_autofixes.json`, with machine-specific compatibility and cross-platform translation.
- **Versioning**: Last 3 auto-snapshots + manual, rollback triggers (time, command count, manual, machine switch).

### Integration Points & Key Files

- `isaac/core/command_router.py`: Command routing, meta-command handling, tier logic
- `isaac/core/session_manager.py`: Session, config, cloud sync
- `isaac/adapters/`: Shell abstraction (PowerShell, bash)
- `isaac/commands/`: Meta-commands (`/help`, `/config`, `/status`, `/ask`, etc.)
- `isaac/ui/permanent_shell.py`: Main shell loop (prompt/output)
- `isaac/ai/`: AI validation, translation, task planning
- `isaac/api/cloud_client.py`: Cloud sync (GoDaddy PHP API)
- Session files: preferences.json, command_history.json, aiquery_history.json, task_history.json, learned_autofixes.json, learned_patterns.json

### UI & User Experience

**External Mode:**
- Standard shell prompt: `C:\ >`
- Commands prefixed with `isaac /command`
- Limited command set for safety

**Internal Mode:**
- Isaac prompt: `$>`
- All `/commands` available
- Natural language with `isaac <query>` or sass response for invalid queries
- Personality: "I have a name, use it." for unrecognized queries
- Offline indicator: `isaac [OFFLINE]>` when cloud unavailable

### Agent Ecosystem & Privacy

- Isaac is the root key/gatekeeper for all agents
- AI query history is private (not in arrow-key recall)

### Roadmap & Open Design Questions

- Shell abstraction: PowerShell vs bash detection, translation, tier lists
- Startup sequence: splash screen, warm/cold start optimization
- Offline mode: queue management, reconnection logic, conflict resolution

---
For more details, see:
- `VISUAL_20251018_isaac_design_session.md` (design session log)
- `ui_simplification.md` (UI simplification instructions)
- `decision flow chart.md` (command classification and execution swimlane)
- `PORTING_NOTES.md` (platform notes)

---
**If unclear or incomplete, ask for feedback on specific sections to iterate.**

## Meta-Commands System

### Current Implementation (`isaac/commands/`)
Isaac currently has **simple Python scripts** for meta-commands, not the full YAML plugin system:
- `help.py`: Display available commands and usage
- `list.py`: List management functions
- `backup.py` / `restore.py`: Configuration backup/restore
- `togrok_handler.py`: x.ai API integration for vector search collections

### Command Types by Prefix

**1. Meta-Commands** (`/command`):
```python
# Handled in command_router.py before shell execution
if input_text.startswith('/'):
    # Built-in Isaac commands like /help, /status, /config
    # See isaac/commands/ directory for implementations
```

**2. Natural Language** (`isaac <query>` or `/ask <query>`):
```python
# Two ways to trigger AI:
# 1. With 'isaac' prefix (works in both modes)
if input_text.lower().startswith('isaac '):
    query = input_text[6:].strip()
# 2. With /ask command (internal mode standard)
elif input_text.startswith('/ask'):
    query = input_text[4:].strip()
    result = translate_query(query, shell_name, session)
    # Translated command goes through normal tier validation
```

**3. Task Mode** (`/task <description>`):
```python
# Multi-step task planning and execution
if input_text.startswith('/task'):
    from isaac.ai.task_planner import execute_task
    task_desc = input_text[5:].strip()  # Remove '/task' prefix
    return execute_task(task_desc, shell, session)
```

**4. Regular Shell Commands** (no prefix):
```python
# Standard shell commands go through tier validation
tier = validator.get_tier(command)  # Returns 1-4 based on tier_defaults.json
if tier <= 2:
    execute_immediately()
else:
    route_to_ai_validation()
```

### Future Plugin Architecture
The full YAML-based plugin system is documented in `docs/command_plugin_spec.md` but not yet implemented. When building this:
- Place manifests in `isaac/commands/<name>/command.yaml`
- Implement dispatcher in `isaac/runtime/dispatcher.py`
- Support piping with `stdin: true` flag
- Enforce `security.resources` limits (timeout_ms, max_stdout_kib)

## Command Orchestration Flow
```
USER → ORCHESTRATOR → VALIDATOR → EXECUTOR → CHRONO-LOG → UI
```

### Command Classification
Commands are classified into three types:

- **Meta-Commands** (ALL use `/` prefix): `/help`, `/config`, `/status`, `/ask`, `/task`, `/msg`, `/collect`, `/debug`
  - Device routing uses `!` bang: `/msg !laptop2 "text"`, `/show-cmd !desktop3`
  - Executed immediately, no tier validation

- **Natural Language** (`isaac <query>` or `/ask <query>`): AI-powered queries and command translation
  - `/ask` is the internal mode standard
  - `isaac <query>` works in both modes for convenience

- **Regular Shell Commands** (no prefix): Standard shell commands with tier-based safety validation

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
pytest tests/ --cov=isaac --cov-report=term      # Full test suite with coverage
```

### Testing Patterns
- **Test Discovery**: `pytest tests/` with `test_*.py` pattern
- **Mock Fixtures**: Use `temp_isaac_dir` and `mock_api_client` from `tests/conftest.py`
- **Coverage Target**: ≥85% coverage required
- **Integration Tests**: Located in `instructions/test_integration/` with completion templates

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

### Debugging Terminal UI
- **Screen Updates**: `TerminalControl` uses dirty flags (`header_dirty`, `body_dirty`)
- **Terminal Size**: Dynamically calculated via `_update_terminal_size()`, not hardcoded
- **Header Layout**: Fixed 5 lines (3 content + 2 borders) with column-aligned cells
- **Output Area**: Scrollable region with `output_scroll_offset` for history navigation
- **Config Mode**: Toggle with special key, uses `config_items` array with cursor navigation
- **Status Thread**: Background `_update_status_thread()` refreshes indicators every 10 seconds

## Project Conventions

### Safety-Critical Patterns
**Tier Classification** (`isaac/data/tier_defaults.json`):
```json
{
  "1": ["ls", "cd", "pwd"],           // Instant execution
  "2": ["grep", "head", "tail"],      // Standard commands
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
# From isaac/ai/xai_client.py
class XaiClient:
    def __init__(self, api_key, api_url, model='grok-beta'):
        # Provider abstraction with fallback handling
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
- `isaac/ai/validator.py`: Command validation and correction
- `isaac/ai/translator.py`: Natural language to shell command conversion
- `isaac/ai/task_planner.py`: Multi-step task decomposition

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
- **AI Providers**: xAI (primary), Claude (fallback) via REST APIs
- **Shell Environments**: PowerShell (Windows), bash (Unix-like)

### Cross-Component Communication
- **Session Manager**: Central hub for config, preferences, and cloud sync
- **Command Router**: Orchestrates tier validation, AI processing, and execution
- **Terminal Control**: Manages UI state and updates status indicators
- **Shell Adapters**: Platform-specific command execution with unified interface

### Development Environment Setup
- **Python 3.8+** required with `requirements.txt` dependencies
- **Editable Install**: `pip install -e .` creates `isaac` command
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