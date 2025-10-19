# Feature Brief: Isaac 2.0 MVP

## Objective
Build a multi-platform shell assistant with cloud-synced sessions that validates commands through a 5-tier safety system and provides natural language query support.

## Problem Statement

**Current State:**
- Terminal commands execute without validation
- No command history across machines
- Risky commands (rm -rf) can execute accidentally
- Natural language requires external tools

**Issues:**
- User has 5-6 machines (Windows + Linux VMs)
- Command history doesn't roam between machines
- No safety layer for destructive commands
- Shell experience not unified across platforms

## Solution

Isaac 2.0 wraps the shell with:
1. **Multi-platform support** - Works on PowerShell (Windows) and bash (Linux)
2. **5-tier command system** - Instant execution (Tier 1) to lockdown warnings (Tier 4)
3. **Cloud session sync** - GoDaddy-hosted PHP API for roaming sessions
4. **Permanent shell layer** - Launch once with `isaac --start`, stays active
5. **Safety validation** - Prevents accidental destructive commands
6. **Natural language** - "isaac <query>" for AI assistance (Phase 2)

## Requirements

### Functional Requirements
- [ ] Detect shell automatically (PowerShell 7+ > 5.1 on Windows, bash on Linux)
- [ ] Display splash screen on startup (5.5 seconds, WarGames theme)
- [ ] Lock top 3 header lines (shell + machine, session info, status)
- [ ] Route commands through tier validator
- [ ] Execute Tier 1 commands instantly (ls, cd, pwd)
- [ ] Prompt confirmation for Tier 3 commands (git, cp, mv)
- [ ] Show lockdown warning for Tier 4 commands (rm -rf, format)
- [ ] Sync command history to cloud after each command
- [ ] Support `exit` to quit
- [ ] Load session from cloud on startup
- [ ] Create default config on first run (~/.isaac/config.json)

### Visual Requirements
- [ ] 5.5 second splash screen (non-skippable)
  - Line 1: "would you like to play... a game?"
  - Line 2: "nah!!"
  - ASCII art "Isaac" + acronym
- [ ] Locked header (top 3 lines):
  - Line 1: Shell version | Machine name
  - Line 2: Session info (command count)
  - Line 3: Status indicator [✓✓ ONLINE | SYNCED]
- [ ] Separator line (━━━━━━━━)
- [ ] Scroll region below header (all interaction)
- [ ] Prompt: `isaac> Ready.` then `user> _`

## Technical Details

**Files to Create:**
- Python modules: ~22 files
  - Core: session_manager.py, command_router.py, tier_validator.py
  - Adapters: base_adapter.py, powershell_adapter.py, bash_adapter.py, shell_detector.py
  - API: cloud_client.py, session_sync.py
  - UI: splash_screen.py, header_display.py, prompt_handler.py, terminal_control.py
  - Models: preferences.py, command_history.py
  - Utils: config_loader.py, logger.py, validators.py, platform_utils.py
  - Entry: __main__.py + __init__.py files
- PHP API: 5 files (config.php, save_session.php, get_session.php, health_check.php, .htaccess)
- Data: 3 files (tier_defaults.json, splash_art.txt, help_text.txt)
- Config: 2 files (setup.py, requirements.txt)
- Tests: 3 files (test_tier_validator.py, conftest.py, pytest.ini)

**Files to Modify:** None (greenfield project)

## Architecture Context

### Shell Abstraction Pattern
```python
# Base interface all shells implement
class BaseShellAdapter:
    def execute(command: str) -> CommandResult:
        """Execute command, return (success, output, exit_code)"""
        
# Platform-specific implementations
PowerShellAdapter.execute() → subprocess.run(['pwsh', ...])
BashAdapter.execute() → subprocess.run(['bash', '-c', ...])

# Auto-detection on startup
detect_shell() → PowerShellAdapter (Windows) or BashAdapter (Linux)
```

### Tier System Flow
```
User Input → TierValidator.get_tier(command)
  ↓
Tier 1 → Execute immediately (ls, cd, pwd)
Tier 2 → Auto-correct typo (future: AI)
Tier 3 → Confirm first (git, cp, mv)
Tier 4 → Lockdown warning + exact "yes" required (rm -rf, format)
  ↓
CommandRouter.route_command()
  ↓
ShellAdapter.execute()
  ↓
Log to SessionManager → Sync to cloud
```

### Session Sync Pattern
```
Startup:
  SessionManager.sync_from_cloud()
    → CloudClient.get_session_file('preferences.json')
    → CloudClient.get_session_file('command_history.json')
    → Load into memory

After Each Command:
  SessionManager.add_command(cmd, result)
    → Append to command_history
    → CloudClient.save_session_file('command_history.json')
    → Returns immediately (sync happens in background)
```

### Terminal UI Pattern
```
Startup Sequence:
  1. show_splash() - 5.5 seconds forced
  2. TerminalControl.clear_screen()
  3. HeaderDisplay.render_locked_header()
     - Print lines 1-3
     - Print separator
     - TerminalControl.set_scroll_region(5, terminal_height)
  4. PromptHandler.run_interactive_loop()
     - input() from scroll region
     - Commands execute
     - Output appears in scroll region
     - Header NEVER scrolls (lines 1-4 frozen)
```

## Variables/Data Structures

### Preferences Model
```python
@dataclass
class Preferences:
    machine_id: str              # "DESKTOP-WIN11"
    auto_run_tier2: bool         # False for MVP
    tier_overrides: Dict[str, int]  # {"find": 1} custom tier assignments
    api_url: str                 # "https://yourdomain.com/isaac/api"
    api_key: str                 # "your_secret_key"
```

### Command History Entry
```python
{
    'command': 'ls -la',
    'machine': 'DESKTOP-WIN11',
    'timestamp': '2025-10-18T14:30:00Z',
    'shell': 'PowerShell',
    'exit_code': 0
}
```

### Tier Defaults (tier_defaults.json)
```json
{
  "1": ["ls", "cd", "pwd", "echo", "cat", "type", "Get-ChildItem", "Set-Location"],
  "2": ["grep", "Select-String", "head", "tail"],
  "2.5": ["find", "sed", "awk", "Where-Object"],
  "3": ["cp", "mv", "git", "npm", "pip", "Copy-Item", "Move-Item"],
  "4": ["rm", "del", "format", "dd", "Remove-Item", "Format-Volume"]
}
```

### Config File (~/.isaac/config.json)
```json
{
  "machine_id": "AUTO-DETECTED-HOSTNAME",
  "auto_run_tier2": false,
  "tier_overrides": {},
  "api_url": "https://yourdomain.com/isaac/api",
  "api_key": "your_secret_key_here"
}
```

## Out of Scope (MVP)

❌ **Not implementing tonight:**
- AI integration (OpenAI/Anthropic/Grok)
- Task mode (multi-step automation)
- Learning engine (auto-fix patterns)
- Arrow key history (use basic input() for MVP)
- Offline queue (graceful degradation only)
- Versioning/rollback system
- Natural language translation
- Tier 2 auto-correction
- AIQUERY history separation

✅ **Building tonight:**
- Shell detection + abstraction
- 5-tier command validation
- Cloud sync client (Python code)
- PHP API endpoints
- Splash screen + header lock
- Local session management
- Basic testing (tier validator)

## Success Criteria

### Windows Test
```bash
isaac --start
# [Splash 5.5s]
# PowerShell 7.3.0 | DESKTOP-WIN11
# Session loaded (0 commands)
# [✓✓ ONLINE | SYNCED]
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# isaac> Ready.

user> ls
# [directory listing]

user> git status
# Isaac > Validate this command? [y/N]: y
# [git output]

user> rm -rf test
# Isaac > DESTRUCTIVE COMMAND. Type 'yes' to proceed: no
# Aborted.

user> exit
# Goodbye!
```

### Linux Test (Multi-Machine Roaming)
```bash
# After running commands on Windows, switch to Linux VM
isaac --start
# [Splash 5.5s]
# bash 5.1 | PARROT-VM
# Session loaded (3 commands)  ← Sees Windows commands!
# [✓✓ ONLINE | SYNCED]

user> isaac --show-log --all
# [DESKTOP-WIN11] ls
# [DESKTOP-WIN11] git status
# [DESKTOP-WIN11] rm -rf test (aborted)

user> pwd
# /home/user

user> exit
# Goodbye!
```

### Back to Windows
```bash
isaac --show-log --all
# [DESKTOP-WIN11] ls
# [DESKTOP-WIN11] git status  
# [DESKTOP-WIN11] rm -rf test (aborted)
# [PARROT-VM] pwd

# ✅ Multi-machine roaming confirmed!
```

## Risk Assessment

**Overall Risk:** LOW

**Technical Risks:**
- Shell detection failure (Windows/Linux) → MITIGATED by fallback logic
- Cloud sync timeout → MITIGATED by local cache fallback
- ANSI escape codes not working on Windows → MITIGATED by colorama + Windows 10+ native ANSI
- Tier misclassification → MITIGATED by comprehensive tests

**User Risks:**
- Accidental Tier 4 command execution → MITIGATED by lockdown warnings + exact "yes" required
- Session data loss → MITIGATED by cloud sync after every command

**Deployment Risks:**
- GoDaddy PHP upload issues → LOW (user has experience)
- API authentication failure → MITIGATED by health_check.php endpoint test

## Implementation Timeline

**Total:** 3-4 hours (VSCode agent builds, user uploads PHP)

1. **Bootstrap** (15 min) - setup.py, structure
2. **Data files** (10 min) - tier_defaults.json, splash_art.txt
3. **Shell adapters** (30 min) - base → PowerShell → bash → detector
4. **Models** (20 min) - preferences, command_history
5. **Core logic** (45 min) - tier_validator → router → session_mgr
6. **Terminal UI** (40 min) - terminal_control → splash → header → prompt
7. **Main entry** (30 min) - __main__.py wiring
8. **PHP API** (20 min) - 5 PHP files
9. **Tests** (15 min) - tier_validator tests
10. **User deployment** (30 min) - pip install, PHP upload, test

---

**END OF FEATURE BRIEF**

**Next:** Implementation instructions (02_impl_bootstrap.md → 11_deployment.md)
