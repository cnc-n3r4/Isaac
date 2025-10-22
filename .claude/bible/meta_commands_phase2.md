# Meta-Commands Implementation - Phase 2

## Objective
Build fully functional `/config`, `/status`, and `/help` meta-commands with working subcommands and settings persistence.

## Files to Create/Modify

### 1. Create `isaac/commands/config.py`
Full implementation from `ui_simplification.md` Phase 2.1 with:
- Working `_show_overview()`, `_show_status()`, `_show_ai_details()`, `_show_cloud_details()`, `_show_plugins()`
- Functional `_set_config()` that persists to SessionManager
- Health checks for AI and Cloud connections

### 2. Create `isaac/commands/status.py`
Full implementation from `ui_simplification.md` Phase 2.2 with:
- One-line status summary
- `-v` flag delegation to ConfigCommand

### 3. Update `isaac/core/command_router.py`
Add `_handle_meta_command()` method from `ui_simplification.md` Phase 2.3 with routing for:
- `/config` → ConfigCommand
- `/status` → StatusCommand
- `/help` → HelpCommand (update existing)
- `/exit`, `/quit` → Handled in main loop
- `/clear` → OS clear command

### 4. Update `isaac/commands/help.py`
Expand to show all meta-commands:
```
Available Commands:
  /help              - Show this help
  /status            - Quick system status
  /status -v         - Detailed status
  /config            - Configuration overview
  /config status     - System status check
  /config ai         - AI provider details
  /config cloud      - Cloud sync status
  /config plugins    - List plugins
  /config set <k> <v> - Change setting
  /clear             - Clear screen
  /exit, /quit       - Exit ISAAC

Natural Language:
  isaac <query>      - AI query or command translation
```

## Testing Checklist
- [ ] `/config` shows overview with session ID, history count, tier
- [ ] `/config status` shows cloud, AI, network, session details
- [ ] `/config ai` shows provider, model, connection status
- [ ] `/config cloud` shows sync status, last sync time
- [ ] `/config plugins` lists togrok, backup, task_planner
- [ ] `/config set default_tier 3` changes and persists setting
- [ ] `/status` shows one-line summary
- [ ] `/status -v` delegates to `/config status`
- [ ] `/help` shows updated command list
- [ ] `/clear` clears screen
- [ ] Unknown `/command` shows error with help suggestion

## Dependencies
- `SessionManager.preferences` must support get/set/save
- `CloudClient.health_check()` method (add if missing)
- `XaiClient` connection test method (add if missing)

## Complexity: Medium
Estimated time: 2-3 hours
