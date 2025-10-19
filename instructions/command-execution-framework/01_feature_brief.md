# Feature Brief: Command Execution Framework

## Objective
Build complete command execution system enabling Isaac to parse, route, and execute user commands in both CLI and interactive REPL modes with AI-powered natural language translation.

## Problem Statement

**Current State:**
- `isaac/__main__.py` initializes SessionManager
- Prints "Ready." and exits
- Basic `sys.argv` parsing added (acknowledges args but doesn't execute)

**Issues:**
- User types `isaac backup my documents` - nothing happens
- No command routing mechanism
- No command handlers
- No REPL loop for interactive mode
- No AI translation for natural language commands

**User Expectation:**
```bash
# CLI mode
isaac backup my-folder to /mnt/external
# Should: Translate paths, confirm, execute backup

# Interactive mode  
isaac
isaac> backup my documents
AI: Translating... cp -r ~/Documents /backup/
Execute? (y/n) y
isaac> Backup complete.
```

## Solution

Implement modular command execution framework with four layers:

1. **Entry Layer** (`__main__.py`)
   - Parse CLI arguments vs interactive mode
   - Initialize REPL loop if no args
   - Pass commands to router

2. **Routing Layer** (`core/command_router.py`)
   - Parse command strings
   - Identify command type (internal vs shell vs natural language)
   - Route to appropriate handler
   - Integrate AI translator for path resolution

3. **Handler Layer** (`commands/` package)
   - Individual handlers for each command type
   - Integration with SessionManager
   - Status tracking and logging

4. **AI Translation Layer** (`core/ai_translator.py`)
   - Translate natural language → executable commands
   - Path resolution ("my documents" → `~/Documents`)
   - Suggestion generation for errors

## Requirements

### Functional Requirements
- [ ] CLI mode: `isaac <command> [args]` executes immediately
- [ ] Interactive mode: `isaac` enters REPL with `isaac>` prompt
- [ ] Natural language translation with confirmation prompt
- [ ] Explicit backup targets (user specifies destination)
- [ ] Helpful error messages with suggestions
- [ ] Complete command logging (success/fail/cancelled)
- [ ] Scannable help system with category drill-down

### Visual Requirements (CLI Output)
- [ ] Simple `isaac>` prompt in REPL
- [ ] AI translation preview before execution
- [ ] Status symbols: ✓ (success) / ✗ (failed) / ⊘ (cancelled)
- [ ] Error messages in terminal with suggestions
- [ ] Help output scannable (≤30 lines for overview)

## Technical Details

**Files to Create:**
- `isaac/core/command_router.py` - Command parsing and routing
- `isaac/core/ai_translator.py` - Natural language translation
- `isaac/commands/__init__.py` - Handler package
- `isaac/commands/backup.py` - Backup handler
- `isaac/commands/restore.py` - Restore handler
- `isaac/commands/list.py` - List backups/history
- `isaac/commands/help.py` - Help system

**Files to Modify:**
- `isaac/__main__.py` - Add REPL loop and router integration

## Architecture Context

### Existing Components

**SessionManager** (`isaac/core/session_manager.py`):
```python
class SessionManager:
    def __init__(self):
        self.local_storage = LocalStorage()
        self.cloud_client = CloudClient()
        
    def load_from_local(self):
        """Load session from local storage"""
        pass
        
    def load_from_cloud(self):
        """Sync with cloud storage"""
        pass
        
    def _log_command(self, command: str):
        """Log command to session history"""
        pass
```

**Current __main__.py** (after DEBUG patch):
```python
import sys
from isaac.core.session_manager import SessionManager

def main():
    """Main entry point."""
    session = SessionManager()
    session.load_from_local()
    session.load_from_cloud()
    print("Isaac > Ready.")
    
    if len(sys.argv) > 1:
        command = ' '.join(sys.argv[1:])
        print(f"Isaac > Executing: {command}")
        session._log_command(command)
        # TODO: Add actual command execution logic here
    else:
        # TODO: Implement REPL loop
        pass

if __name__ == "__main__":
    main()
```

### New Architecture Pattern

```
User Input
    ↓
__main__.py (Entry Point)
    ↓
CommandRouter (Parse & Route)
    ↓
    ├─→ InternalHandler (--help, --version, etc.)
    ├─→ ShellHandler (cd, ls, cp, etc.)
    ├─→ NaturalLanguageHandler (via AI Translator)
    │       ↓
    │   AI Translator (Resolve paths, generate commands)
    │       ↓
    │   Confirmation Prompt
    │       ↓
    └─→ Command Execution
            ↓
        SessionManager (Logging)
            ↓
        Status Return (✓/✗/⊘)
```

## Variables/Data Structures

### Command Types
```python
from enum import Enum

class CommandType(Enum):
    INTERNAL = "internal"      # --help, --version, etc.
    SHELL = "shell"            # cd, ls, cp, etc.
    NATURAL = "natural"        # AI-translated commands
    TASK = "task"              # isaac task: description
```

### Command Result
```python
from dataclasses import dataclass

@dataclass
class CommandResult:
    success: bool
    message: str
    status_symbol: str  # '✓' / '✗' / '⊘'
    suggestion: str = None  # For failed commands
```

### AI Translation Response
```python
@dataclass
class TranslationResult:
    original: str              # "backup my documents"
    translated: str            # "cp -r ~/Documents /backup/"
    resolved_paths: dict       # {"my documents": "~/Documents"}
    confidence: float          # 0.0 - 1.0
    needs_confirmation: bool
```

## Out of Scope

❌ **Not changing:**
- Existing SessionManager structure (only adding methods)
- Local/cloud storage implementations
- Command logging format (use existing `_log_command()`)

❌ **Not implementing (yet):**
- Predefined aliases/shortcuts
- Filesystem traversal for "smart search"
- Automatic backup storage selection
- Path-aware REPL prompts
- Man-page style help documentation

❌ **Explicitly rejected:**
- Magic backup locations (user must specify destination)
- Complex REPL prompts (keep it simple: `isaac>`)
- Verbose man-page help (keep it scannable)

## Success Criteria

✅ **CLI Mode:**
- `isaac backup folder to /dest` executes backup after confirmation
- `isaac --help` shows scannable command list (≤30 lines)
- Invalid commands show helpful suggestions

✅ **Interactive Mode:**
- `isaac` (no args) enters REPL with `isaac>` prompt
- Natural language commands translated and confirmed before execution
- `exit` or Ctrl+C exits cleanly

✅ **Error Handling:**
- All errors include suggestions: "Try 'isaac backup \"My Documents\"' instead"
- Status symbols visible: ✓ success, ✗ failed, ⊘ cancelled

✅ **Logging:**
- All commands logged regardless of status
- History shows status symbols
- Learning system can access failure patterns

✅ **AI Translation:**
- "my documents" → `~/Documents` (or suggests if ambiguous)
- Shows translation before execution
- Requires confirmation for destructive operations

## Risk Assessment

**Risk Level:** MEDIUM

**Risks:**
1. **AI Translation Accuracy** - May misinterpret ambiguous paths
   - *Mitigation:* Always show preview + require confirmation
   
2. **REPL Blocking** - Input loop may block on errors
   - *Mitigation:* Comprehensive error handling with graceful recovery
   
3. **Command Injection** - User input passed to shell
   - *Mitigation:* Input validation + confirmation prompts

4. **SessionManager Integration** - Existing methods may not support new logging needs
   - *Mitigation:* Add new methods if needed, don't modify existing ones

**Dependencies:**
- Existing SessionManager must remain functional
- Local/cloud storage systems must remain unchanged
- Command logging must use existing infrastructure

---

**Feature Status:** READY_FOR_IMPLEMENTATION

**Estimated Effort:** 6-8 hours

**Priority:** HIGH - Blocks all user workflows
