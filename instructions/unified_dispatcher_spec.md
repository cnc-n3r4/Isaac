# Unified Dispatcher Implementation - Track 1.1

## Objective
Build the plugin-based command dispatcher from COMMAND_PLUGIN_SPEC.md, replacing the current simple script-based meta-commands with a modular YAML manifest system.

## Vision
Transform Isaac from hardcoded meta-commands to a **fully extensible plugin architecture** where new commands are added by simply dropping a YAML manifest + handler script into `isaac/commands/<name>/`.

## Scope
Implement the full dispatcher architecture that enables:
- Auto-discovery of commands via `command.yaml` manifests
- Argument parsing and validation per manifest schema
- Pipe semantics (`cmdA | cmdB`)
- Device routing (`!alias`)
- Security enforcement (timeouts, allowlists, sandboxing)
- Hot-reload capability (future: Track 3.2)

---

## Architecture Overview

### Before (Current State)
```
User: /config
  ↓
command_router.py → _handle_meta_command()
  ↓
if cmd == "config": import config.py
if cmd == "status": import status.py
if cmd == "help": import help.py
  ↓
Hardcoded function call
```

### After (Plugin System)
```
User: /config
  ↓
command_router.py → dispatcher.execute()
  ↓
dispatcher.resolve_trigger("/config")
  ↓
Load manifest: commands/config/command.yaml
  ↓
Parse args: {"subcommand": "status"}
  ↓
Validate: args match manifest schema
  ↓
Execute: run commands/config/run.py with envelope
  ↓
Return normalized result envelope
```

---

## Files to Create

### 1. `isaac/runtime/dispatcher.py` (Core Engine)
**Main dispatcher class** implementing:

```python
class CommandDispatcher:
    def __init__(self, session_manager):
        self.commands = {}  # trigger → manifest mapping
        self.session = session_manager
        self.security = SecurityEnforcer()
        self.loader = ManifestLoader()
        
    def load_commands(self, directories: list[Path]):
        """Scan directories for command.yaml manifests"""
        # Implements Section 0 (Directory Layout)
        
    def resolve_trigger(self, input_text: str) -> Optional[dict]:
        """Match /command to loaded manifest"""
        # Returns: {"manifest": {...}, "args_raw": "..."}
        
    def parse_args(self, manifest: dict, args_raw: str) -> dict:
        """Extract and validate arguments per manifest"""
        # Implements Section 1 (Manifest Schema) validation
        
    def execute(self, command: str, args: dict, stdin: Optional[str] = None) -> dict:
        """Run handler and return normalized envelope"""
        # Implements Section 4 (Return Envelope)
        
    def chain_pipe(self, cmd1: str, cmd2: str) -> dict:
        """Connect stdout of cmd1 to stdin of cmd2"""
        # Implements Section 8 (Pipe Semantics)
        
    def route_remote(self, alias: str, command: str) -> dict:
        """Send command to device via cloud client"""
        # Implements Section 3 (Routing)
```

**Key Methods:**
- `load_commands()` - Scan `isaac/commands/*/command.yaml` and `~/.isaac/commands/`
- `resolve_trigger(input)` - Match `/command` to manifest (handle aliases)
- `parse_args(manifest, input)` - Extract positional/named args, validate types
- `execute(command, args, stdin)` - Run handler with timeout/security enforcement
- `chain_pipe(cmd1, cmd2)` - Connect stdout → stdin when `stdin: true`
- `route_remote(alias, command)` - Send to device via CloudClient

**From:** `.claude/bible/COMMAND_PLUGIN_SPEC.md` Section 3 (Dispatcher Contract)

---

### 2. `isaac/runtime/manifest_loader.py` (YAML Parser)
**Manifest validation and caching:**

```python
class ManifestLoader:
    def __init__(self):
        self.schema = self._load_json_schema()
        self.cache = {}  # path → parsed manifest
        
    def load_manifest(self, yaml_path: Path) -> dict:
        """Load and validate command.yaml"""
        # Implements Section 2 (JSON Schema validation)
        
    def validate_manifest(self, manifest: dict) -> tuple[bool, list[str]]:
        """Validate against JSON Schema, return errors"""
        
    def hot_reload(self, yaml_path: Path):
        """Reload changed manifest (future: Track 3.2)"""
```

**Key Features:**
- JSON Schema validation (Section 2 of spec)
- Manifest caching with file modification time tracking
- Clear error messages for invalid manifests
- Support for hot-reload (stub for Track 3.2)

**From:** `.claude/bible/COMMAND_PLUGIN_SPEC.md` Section 2 (JSON Schema for Manifests)

---

### 3. `isaac/runtime/security_enforcer.py` (Safety Layer)
**Security boundaries and resource limits:**

```python
class SecurityEnforcer:
    def enforce_timeout(self, handler, timeout_ms: int):
        """Kill handler if exceeds timeout"""
        
    def cap_stdout(self, output: str, max_kib: int) -> tuple[str, bool]:
        """Truncate output if exceeds limit, return (output, truncated)"""
        
    def check_allowlist(self, manifest: dict, platform: str) -> bool:
        """Verify binary is in platform allowlist"""
        
    def sanitize_env(self, env: dict) -> dict:
        """Clean environment variables"""
        
    def redact_patterns(self, text: str, patterns: list[str]) -> str:
        """Apply telemetry redaction patterns"""
```

**Key Features:**
- Timeout enforcement with subprocess termination
- Output size caps (prevent memory exhaustion)
- Platform-specific binary allowlists (Section 6)
- Environment sanitization
- Pattern-based output redaction (Section 1, telemetry)

**From:** `.claude/bible/COMMAND_PLUGIN_SPEC.md` Section 6 (Validation & Safety) + Section 11 (Security Notes)

---

### 4. `isaac/runtime/__init__.py`
Export public API:
```python
from .dispatcher import CommandDispatcher
from .manifest_loader import ManifestLoader
from .security_enforcer import SecurityEnforcer

__all__ = ['CommandDispatcher', 'ManifestLoader', 'SecurityEnforcer']
```

---

## Convert Existing Commands to Plugins

Migrate these 5 commands to YAML manifest format:

### 4.1 `/help` Command
**Files:**
- `isaac/commands/help/command.yaml` (new)
- `isaac/commands/help/run.py` (migrate from `isaac/commands/help.py`)

**Manifest:**
```yaml
name: help
version: 1.0.0
summary: "Display command reference or detailed help for specific command"
description: |
  Shows available commands and usage. Can provide detailed help for specific commands.

triggers: ["/help"]
aliases: ["/h", "/?"]

args:
  - name: command
    type: string
    required: false
    help: "Command name for detailed help"

stdin: false
stdout:
  type: text

security:
  scope: user
  allow_remote: true
  resources:
    timeout_ms: 1000
    max_stdout_kib: 16

runtime:
  entry: "run.py"
  interpreter: "python"

telemetry:
  log_invocation: true
  log_output: false

examples:
  - "/help"
  - "/help /config"
```

**Handler (`run.py`):**
```python
import sys, json

def main():
    payload = json.loads(sys.stdin.read())
    args = payload["args"]
    
    # Use dispatcher's loaded commands for dynamic help
    if args.get("command"):
        # Show detailed help for specific command
        output = get_command_help(args["command"])
    else:
        # Show all commands
        output = list_all_commands()
    
    print(json.dumps({
        "ok": True,
        "kind": "text",
        "stdout": output,
        "meta": {}
    }))

if __name__ == "__main__":
    main()
```

---

### 4.2 `/status` Command
**Files:**
- `isaac/commands/status/command.yaml` (new)
- `isaac/commands/status/run.py` (migrate from `isaac/commands/status.py`)

**Manifest:**
```yaml
name: status
version: 1.0.0
summary: "Quick system status or detailed diagnostics"

triggers: ["/status"]
aliases: ["/s"]

args:
  - name: verbose
    type: bool
    required: false
    help: "Show detailed status (-v flag)"

stdin: false
stdout:
  type: text

security:
  scope: user
  allow_remote: true
  resources:
    timeout_ms: 3000
    max_stdout_kib: 32

runtime:
  entry: "run.py"
  interpreter: "python"

telemetry:
  log_invocation: true
  log_output: false

examples:
  - "/status"
  - "/status -v"
```

---

### 4.3 `/config` Command
**Files:**
- `isaac/commands/config/command.yaml` (new)
- `isaac/commands/config/run.py` (migrate from `isaac/commands/config.py`)

**Manifest:**
```yaml
name: config
version: 1.0.0
summary: "View or modify configuration settings"

triggers: ["/config"]

args:
  - name: subcommand
    type: enum
    enum: ["status", "ai", "cloud", "plugins", "set"]
    required: false
    help: "Configuration section or action"
  - name: key
    type: string
    required: false
    help: "Setting key (for 'set' subcommand)"
  - name: value
    type: string
    required: false
    help: "Setting value (for 'set' subcommand)"

stdin: false
stdout:
  type: text

security:
  scope: user
  allow_remote: false  # Config changes are local-only
  resources:
    timeout_ms: 5000
    max_stdout_kib: 64

runtime:
  entry: "run.py"
  interpreter: "python"

telemetry:
  log_invocation: true
  log_output: true
  redact_patterns:
    - "(?i)(api[_-]?key|token|password)\\s*[=:]\\s*[A-Za-z0-9_-]+"

examples:
  - "/config"
  - "/config status"
  - "/config ai"
  - "/config set default_tier 3"
```

---

### 4.4 `/list` Command
**Files:**
- `isaac/commands/list/command.yaml` (new)
- `isaac/commands/list/run.py` (migrate from `isaac/commands/list.py`)

**Manifest:**
```yaml
name: list
version: 1.0.0
summary: "Manage named lists (shopping, todos, etc.)"

triggers: ["/list"]
aliases: ["/ls"]

args:
  - name: list_name
    type: string
    required: true
    pattern: "^[A-Za-z0-9._-]{1,32}$"
    help: "Name of the list (e.g., grocery, todos)"

stdin: false
stdout:
  type: text

security:
  scope: user
  allow_remote: true
  resources:
    timeout_ms: 3000
    max_stdout_kib: 128

runtime:
  entry: "run.py"
  interpreter: "python"

telemetry:
  log_invocation: true
  log_output: true

examples:
  - "/list grocery"
  - "/list todos"
```

---

### 4.5 `/backup` Command
**Files:**
- `isaac/commands/backup/command.yaml` (new)
- `isaac/commands/backup/run.py` (migrate from `isaac/commands/backup.py`)

**Manifest:**
```yaml
name: backup
version: 1.0.0
summary: "Backup configuration and session data"

triggers: ["/backup"]

args:
  - name: target
    type: enum
    enum: ["config", "session", "all"]
    required: false
    help: "What to backup (default: all)"

stdin: false
stdout:
  type: text

security:
  scope: user
  allow_remote: false
  resources:
    timeout_ms: 10000
    max_stdout_kib: 16

runtime:
  entry: "run.py"
  interpreter: "python"

telemetry:
  log_invocation: true
  log_output: false

examples:
  - "/backup"
  - "/backup config"
```

---

## Update Integration Point

### 5. Update `isaac/core/command_router.py`
**Replace meta-command handling with dispatcher:**

```python
from isaac.runtime import CommandDispatcher

class CommandRouter:
    def __init__(self, session_manager, shell):
        self.session = session_manager
        self.shell = shell
        self.dispatcher = CommandDispatcher(session_manager)
        
        # Load commands from isaac/commands/ and ~/.isaac/commands/
        self.dispatcher.load_commands([
            Path(__file__).parent.parent / 'commands',
            Path.home() / '.isaac' / 'commands'
        ])
    
    def route_command(self, input_text: str):
        """Main routing logic"""
        
        # 1. Check for meta-commands (/)
        if input_text.startswith('/'):
            # Special cases handled by shell loop
            if input_text in ['/exit', '/quit']:
                return {'action': 'exit'}
            if input_text == '/clear':
                return {'action': 'clear'}
            
            # All other / commands go through dispatcher
            return self._dispatch_command(input_text)
        
        # 2. Check for device routing (!)
        if input_text.startswith('!'):
            return self._route_device(input_text)
        
        # 3. Check for natural language (isaac)
        if input_text.lower().startswith('isaac '):
            return self._handle_natural_language(input_text[6:])
        
        # 4. Regular shell command
        return self._execute_shell_command(input_text)
    
    def _dispatch_command(self, input_text: str):
        """Route / command through dispatcher"""
        try:
            # Check for pipes
            if '|' in input_text:
                parts = input_text.split('|')
                return self.dispatcher.chain_pipe(parts[0].strip(), parts[1].strip())
            
            # Single command
            result = self.dispatcher.execute(input_text)
            return result
            
        except Exception as e:
            return {
                "ok": False,
                "error": {
                    "code": "DISPATCH_ERROR",
                    "message": str(e),
                    "hint": "Try /help for available commands"
                },
                "meta": {}
            }
    
    def _route_device(self, input_text: str):
        """Handle !alias routing"""
        # Extract alias and command
        parts = input_text[1:].split(None, 1)
        if len(parts) != 2:
            return {"ok": False, "error": {"message": "Usage: !alias /command"}}
        
        alias, command = parts
        return self.dispatcher.route_remote(alias, command)
```

**Key Changes:**
- Remove `_handle_meta_command()` method (replaced by dispatcher)
- Add `CommandDispatcher` initialization in `__init__`
- Update `route_command()` to use `dispatcher.execute()`
- Keep special cases (`/exit`, `/quit`, `/clear`) in router
- Add pipe detection and `dispatcher.chain_pipe()` support
- Add `!alias` routing via `dispatcher.route_remote()`

---

## Testing Checklist

### Unit Tests (`tests/test_dispatcher.py`)
- [ ] Manifest loader validates against JSON Schema
- [ ] Invalid manifests rejected with clear errors
- [ ] Trigger resolution handles aliases correctly
- [ ] Argument parsing extracts positional args
- [ ] Argument validation enforces types and patterns
- [ ] Timeout enforcement kills slow handlers
- [ ] Output cap truncates large stdout
- [ ] Platform allowlist blocks unauthorized binaries
- [ ] Redaction patterns mask sensitive data

### Integration Tests (`tests/test_dispatcher_integration.py`)
- [ ] All 5 migrated commands work identically
- [ ] `/help` shows dynamically loaded commands
- [ ] `/config set default_tier 3` persists to SessionManager
- [ ] Pipe works: `/history | /grep docker` (future commands)
- [ ] Device routing queues `!laptop2 /status`
- [ ] Unknown command shows helpful error + suggestion
- [ ] Return envelope matches spec format

### Regression Tests
- [ ] All existing `test_tier_validator.py` tests pass
- [ ] All existing `test_cloud_client.py` tests pass
- [ ] All existing `test_ai_integration.py` tests pass
- [ ] No behavioral changes for shell commands

---

## Dependencies

### Required
- **COMMAND_PLUGIN_SPEC.md** (Section 0-11) - Full implementation spec
- **COMMAND_BRAINSTORM.md** - Command catalog for future migration
- **SessionManager** - For preferences and cloud client access
- **CloudClient** - For `!alias` routing

### Optional (Future Enhancements)
- **Track 3.2: Plugin Hot-Reloading** - File watcher for auto-reload
- **Track 2.1: Job Lifecycle** - State tracking for routed commands

---

## Success Criteria

### Must Have (Phase 1)
1. ✅ Dispatcher loads manifests from `isaac/commands/*/command.yaml`
2. ✅ All 5 existing meta-commands migrated to plugin format
3. ✅ Commands execute with timeout and output cap enforcement
4. ✅ Return envelope matches spec format (Section 4)
5. ✅ All existing tests pass (no regressions)

### Should Have (Phase 2)
6. ✅ Pipe semantics work (`cmdA | cmdB` when `stdin: true`)
7. ✅ Device routing queues commands via CloudClient
8. ✅ Invalid manifests show clear error messages
9. ✅ User commands loaded from `~/.isaac/commands/`

### Nice to Have (Phase 3 - Future)
10. Hot-reload detects new/changed manifests (Track 3.2)
11. Manifest validation errors shown in `/status -v`
12. Command performance metrics logged

---

## Implementation Order

### Step 1: Foundation (2 hours)
1. Create `isaac/runtime/` directory
2. Implement `manifest_loader.py` with JSON Schema validation
3. Implement `security_enforcer.py` with timeout/cap logic
4. Write unit tests for loader and enforcer

### Step 2: Core Dispatcher (2 hours)
1. Implement `dispatcher.py` core class
2. Add `load_commands()` and `resolve_trigger()`
3. Add `parse_args()` and `execute()`
4. Write unit tests for dispatcher methods

### Step 3: Migration (1 hour)
1. Create manifest for `/help` command
2. Migrate `/help` handler to envelope format
3. Test `/help` works through dispatcher
4. Repeat for `/status`, `/config`, `/list`, `/backup`

### Step 4: Integration (1 hour)
1. Update `command_router.py` to use dispatcher
2. Handle pipe detection (`|` in input)
3. Handle device routing (`!alias`)
4. Run full test suite, fix regressions

---

## Complexity: Medium-High
**Estimated time:** 4-6 hours  
**Priority:** HIGH (foundation for all Track 3 enhancements)

---

## References
- `.claude/bible/COMMAND_PLUGIN_SPEC.md` - Implementation spec (Sections 0-11)
- `.claude/bible/COMMAND_BRAINSTORM.md` - Full command catalog
- `.claude/bible/COMMAND_SYSTEM_OVERVIEW.md` - Navigation guide
- `.claude/bible/COMMAND_PATTERNS.md` - Real interaction examples

---

## Next Steps After Completion
Once dispatcher is working:
1. **Track 1.2:** Command Queue Overlay (offline resilience)
2. **Track 3.2:** Plugin Hot-Reloading (watch `command.yaml` files)
3. **Track 3.1:** Configurable Modules (agent capabilities)
4. Migrate commands from COMMAND_BRAINSTORM.md categories incrementally

---

**Ready for handoff to implementation agent (YAML Maker or Implement persona)**
