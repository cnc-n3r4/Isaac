# Isaac - AI-Enhanced Multi-Platform Shell Assistant

## Architecture Overview
Isaac is a sophisticated shell wrapper that provides AI-enhanced command execution with cloud-synced sessions across Windows (PowerShell) and Unix-like systems (bash). The system implements a 5-tier command safety classification and features a locked terminal UI with real-time status monitoring.

**Core Architecture:**
- **Safety-Critical Design**: 5-tier command validation (1=instant execution, 4=lockdown requiring confirmation)
- **Cross-Platform Shell Abstraction**: Unified interface over PowerShell/bash via adapter pattern
- **Cloud Session Roaming**: PHP API backend enables seamless session sync across machines
- **AI Command Processing**: Natural language queries, command correction, and task planning
- **Terminal UI**: Locked header with status indicators, command history, and config panel

**Data Flow:** User Input → Command Prefix Detection (`/` local, `!` distributed) → Tier Validation → AI Processing → Shell Execution → Cloud Sync

## Command System Architecture

### Modular Command Plugin System
Isaac implements a file-based plugin system where each `/` command is defined by a YAML manifest and optional handler script. Commands can be dispatched locally or routed to remote agents via `!alias`.

**Directory Structure**:
```
isaac/commands/              # Userland commands
├─ add/command.yaml          # Manifest with metadata, args, security
├─ add/run.py               # Optional handler script
├─ grep/command.yaml        # Pipe-compatible commands
├─ ask/command.yaml         # AI-powered commands
└─ ...
```

**Manifest Schema** (YAML):
```yaml
name: add
version: 1.0.0
summary: "Add an item to a list"
triggers: ["/add"]
args:
  - name: list
    type: string
    required: true
    pattern: "^[A-Za-z0-9._-]{1,32}$"
  - name: item
    type: string
    required: true
    min_length: 1
    max_length: 256
stdin: false
stdout: { type: text }
security:
  scope: user
  allow_remote: true
  resources: { timeout_ms: 5000, max_stdout_kib: 64 }
runtime:
  entry: "run.py"
  interpreter: "python"
```

### Command Categories & Ecosystem

#### Core Utilities
- `/echo`, `/time`, `/status`, `/log`, `/exec`

#### History & Search
- `/history`, `/search`, `/summary`

#### Task & Note Management
- `/add`, `/list`, `/done`, `/note`

#### Communication / Messaging
- `/msg`, `/inbox`, `/broadcast`

#### Files & Data
- `/push`, `/pull`, `/grep`, `/cat`

#### System Control
- `/reboot`, `/shutdown`, `/update`, `/sync`

#### Monitoring & Automation
- `/watch`, `/schedule`, `/alert`

#### AI and Knowledge
- `/ask`, `/analyze`, `/explain`, `/learn`

#### Developer Utilities
- `/git`, `/test`, `/lint`, `/deploy`

### Pipe Semantics & Chaining
Commands support Unix-style piping: `/grep "error" /log | /analyze`
- Isaac detects pipes and streams output from first command to second
- Only commands with `stdin: true` can receive piped input
- Output normalization ensures compatibility across command types

### Return Envelope Contract
All commands return a standardized JSON envelope:
```json
{
  "ok": true,
  "kind": "text",
  "stdout": "command output here",
  "meta": {
    "command": "/add",
    "args": {"list":"grocery","item":"apples"},
    "duration_ms": 42,
    "truncated": false
  }
}
```

### Security & Validation
- **Platform allowlists**: Restrict external binaries by OS
- **Resource limits**: Timeout and output size caps per command
- **Redaction patterns**: Sanitize sensitive data from logs
- **Scope enforcement**: user/worker/root execution contexts
- **Remote routing**: Controlled agent-to-agent command dispatch

### Plugin Specification Details
Commands are validated against a JSON Schema on load. Each command folder may include `test.yaml` for automated testing:

```yaml
cases:
  - name: add-basic
    input: "/add grocery apples"
    expect:
      ok: true
      contains: "apples"
  - name: add-inject
    input: "/add grocery 'foo; rm -rf /'"
    expect:
      ok: false
```

**Error Envelope** (for failed commands):
```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "invalid list name",
    "hint": "Allowed: letters, digits, ., _, -"
  },
  "meta": { "duration_ms": 2 }
}
```

**Testing Template**: Each command includes validation test cases that can be executed against a sandbox dispatcher.

### Dispatcher Contract
- **Resolve trigger**: First token starting with `/` selects command
- **Parse args**: Map positional args to `args[]` in manifest, then validate
- **Piping**: If `cmdA | cmdB`, feed `cmdA` stdout to `cmdB` stdin when `stdin: true`
- **Routing**: Leading `!alias` routes the composed command to target agent
- **Timeouts**: Enforce `security.resources.timeout_ms` per command
- **Stdout cap**: Truncate or spill to artifact when output exceeds `max_stdout_kib`

## Command Orchestration Flow
```
USER → ORCHESTRATOR → VALIDATOR → EXECUTOR → CHRONO-LOG → UI
```

### Command Classification
Commands are classified into three types:
- **Local** (`/ask`, `/help`): Meta-commands executed immediately
- **Direct** (`isaac <cmd>`): Bypass validation, execute immediately
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
- **Screen Updates**: TerminalControl uses dirty flags (`header_dirty`, `body_dirty`) for efficient redraws
- **Cursor Positioning**: Fixed prompt at line 6, output lines 8-17, logs lines 20+
- **Status Monitoring**: Background thread updates cloud/AI/VPN status every 10 seconds

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

### Integration Points

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