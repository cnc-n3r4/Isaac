
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

### Big Picture Architecture

- **Permanent Shell Layer**: Isaac wraps the shell after launch (`isaac /start`), routing all commands through its engine. Natural language requires explicit "isaac" prefix.
- **Session Roaming**: Cloud-based session persistence (GoDaddy PHP API), machine-aware command history, and privacy boundaries for AI queries.
- **Tier System**: 5 tiers (1: instant, 2: auto-correct, 3: AI validation, 4: lockdown). User-customizable via `isaac/data/tier_defaults.json`.
- **Task Mode**: Multi-step command planning, safety-based approval, interactive failure recovery (auto-fix, retry, skip, abort, suggest).
- **Auto-Fix Learning**: Isaac learns from user corrections, syncs patterns, tracks machine compatibility, and confidence scores.
- **Dual History**: Command history (machine-aware, arrow keys) and AI query history (private, machine-agnostic).
- **Session Data Structure**: Six cloud JSON files (preferences, command_history, aiquery_history, task_history, learned_autofixes, learned_patterns), versioning, and rollback system.
- **UI Simplification**: Simple prompt/output loop, meta-commands for config/status/help, no locked header or complex screen management.
- **Offline Mode**: Local queueing, auto-reconnect, batch sync, prompt indicator.
- **Agent Ecosystem**: Isaac is the gatekeeper; other agents (Sarah, Daniel) have defined access boundaries.

### Developer Workflows

- **Build & Setup**: `pip install -e .` (editable), `isaac /start` to launch.
- **Testing**: `pytest tests/` (≥85% coverage required), integration tests in `instructions/test_integration/` with completion templates.
- **Meta-Commands**: `/help`, `/status`, `/config`, `/clear` (see `isaac/commands/`). `/config` supports subcommands for status, AI, cloud, plugins, and settings.
- **Task Mode**: Use `isaac /task <goal>` for multi-step planning and execution. Failure recovery options: f/r/s/a/? (auto-fix, retry, skip, abort, suggest).
- **Session Management**: All session data is cloud-synced; rollback via snapshots (manual or auto-triggered).
- **API Timeouts**: Configure xAI timeouts in `~/.isaac/config.json`:
  - Collections (mine command): `xai.collections.timeout_seconds` (default: 3600)
  - Chat (ask command): `xai.chat.timeout_seconds` (default: 30)
  - Note: xAI SDK has hardcoded 10s gRPC timeout for search operations despite config
- **File Search Configuration**: Use `/config console` to configure file-specific search:
  - Add file_ids (like 'file_01852dbb-3f44-45fc-8cf8-699610d17501') to search within specific files
  - Enable "search files only" mode for targeted queries within configured files

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
- `isaac/commands/`: Meta-commands (`/help`, `/config`, `/status`, etc.)
- `isaac/ui/permanent_shell.py`: Main shell loop (prompt/output)
- `isaac/ai/`: AI validation, translation, task planning
- `isaac/api/cloud_client.py`: Cloud sync (GoDaddy PHP API)
- Session files: preferences.json, command_history.json, aiquery_history.json, task_history.json, learned_autofixes.json, learned_patterns.json

### UI & User Experience

- Simple prompt → output → prompt flow (no locked header)
- Meta-commands for configuration and status
- Natural language requires "isaac" prefix
- Offline mode indicator: `isaac [OFFLINE]>`
- Command routing: Regular commands execute directly, `/` commands use dispatcher, `!` for device routing, `isaac task:` for multi-step planning
- Tier enforcement: Commands classified by safety level (1-4) with appropriate validation/confirmation
- AI integration: xAI client for natural language translation and chat queries</content>
<parameter name="filePath">c:\Projects\Isaac\.github\copilot-instructions.md