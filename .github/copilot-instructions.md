
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
pytest tests/ --cov=isaac --cov-report=term      # Full coverage (≥85% required)
```

## Big Picture Architecture

- **Permanent Shell Layer**: Isaac wraps the shell after `isaac /start`, routing all commands through its engine. Natural language requires "isaac" prefix (e.g., `isaac what is the capital of France?`).
- **Session Roaming**: Cloud-based persistence via GoDaddy PHP API; machine-aware command history, private AI query history.
- **Tier System**: 5 tiers (1: instant, 2: auto-correct, 3: AI validation, 4: lockdown). Customizable via `isaac/data/tier_defaults.json` (e.g., `find` defaults to 2.5, requires confirmation).
- **Task Mode**: Multi-step planning with safety approval; failure recovery (auto-fix, retry, skip, abort, suggest).
- **Auto-Fix Learning**: Learns from corrections, syncs patterns with machine compatibility and confidence scores.
- **Dual History**: Command history (arrow keys) and AI query history (private, machine-agnostic).
- **Session Data**: Six cloud JSON files (preferences, command_history, aiquery_history, task_history, learned_autofixes, learned_patterns); versioning with rollback.
- **UI Simplification**: Simple prompt/output loop; meta-commands (`/help`, `/status`, `/config`); no locked header.
- **Offline Mode**: Local queueing, auto-reconnect, batch sync; prompt shows `isaac [OFFLINE]>`.
- **Agent Ecosystem**: Isaac as gatekeeper; other agents (Sarah, Daniel) have restricted access.

## Developer Workflows

- **Build & Setup**: `pip install -e .` (editable); entry points: `isaac`, `ask`, `mine`.
- **Testing**: `pytest tests/` with coverage; integration tests in `tests/` with completion templates.
- **Meta-Commands**: `/help`, `/status`, `/config` (subcommands: status, AI, cloud, plugins, settings), `/clear` (see `isaac/commands/`).
- **Task Mode**: `isaac /task <goal>` for multi-step execution; recovery: f/r/s/a/?.
- **Session Management**: Cloud-synced; rollback via snapshots (last 3 auto + manual; triggers: time, command count, manual, machine switch).
- **API Timeouts**: Configure xAI in `~/.isaac/config.json`: `xai.collections.timeout_seconds` (default: 3600), `xai.chat.timeout_seconds` (default: 30); xAI SDK has hardcoded 10s gRPC timeout.
- **File Search**: `/config console` to add file_ids (e.g., 'file_01852dbb-3f44-45fc-8cf8-699610d17501') for targeted queries.
- **Random Replies**: Generator for failed commands/missing prefix; configure `random_replies_file` in `~/.isaac/config.json` (see `docs/reference/random_replies.md`).

## Project-Specific Conventions

- **Tier Classification**: Commands tiered by safety; Tier 2.5 (find/sed/awk) confirms after typo correction.
- **Error Handling**: Shell adapters return `CommandResult` (never raise exceptions); cloud client returns False/None on errors.
- **Config Management**: Path-based loading; user prefs in `~/.isaac/config.json`.
- **Privacy**: AI query history private to user/Isaac; other agents restricted.
- **Auto-Fix Patterns**: Stored in `learned_autofixes.json` with machine compatibility and cross-platform translation.
- **Versioning**: Last 3 auto-snapshots + manual; rollback triggers as above.

## Integration Points & Key Files

- `isaac/core/command_router.py`: Routing, tier logic, meta-commands.
- `isaac/core/session_manager.py`: Session, config, cloud sync.
- `isaac/adapters/`: Shell abstraction (PowerShell, bash); return `CommandResult`.
- `isaac/commands/`: Meta-commands (e.g., `/help` in `help/run.py`).
- `isaac/ui/permanent_shell.py`: Main loop (prompt_toolkit-based).
- `isaac/ai/`: AI validation, translation, task planning (xAI SDK).
- `isaac/api/cloud_client.py`: GoDaddy API sync (requests-based, no exceptions).
- Session files: preferences.json, command_history.json, aiquery_history.json, task_history.json, learned_autofixes.json, learned_patterns.json.</content>
<parameter name="filePath">c:\Projects\Isaac\.github\copilot-instructions.md