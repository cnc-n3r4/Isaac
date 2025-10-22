# Isaac Extended Command Catalog

This document defines Isaac's **complete command vocabulary** across 10 categories. All internal commands use the `/` prefix; device routing uses `!alias`. Natural language queries use `isaac <query>`.

---

## 1. Core Utility Commands

### `/help [cmd]`
Display command reference or detailed help for a specific command.
```
/help
/help /ask
```

### `/status`
Show system status: cloud connection, AI availability, session info.
```
/status
```

### `/config [section] [key] [value]`
View or update configuration settings.
```
/config                       # show all
/config ai provider openai    # set AI provider
/config cloud enable false    # disable cloud sync
```

### `/clear`
Clear terminal output area (preserves header).
```
/clear
```

### `/exit`
Exit Isaac shell and return to native shell.
```
/exit
```

---

## 2. History & Search

### `/history [filter]`
Display command history with optional filtering.
```
/history
/history git
```

### `/search <query>`
Search across command history, AI queries, and session data.
```
/search "docker ps"
/search task:deployment
```

### `/recall [n]`
Re-execute command from history by index.
```
/recall 42
```

---

## 3. Task & Note Management

### `/task <description>`
Plan and execute multi-step tasks with interactive approval.
```
/task backup all configs to ~/backups
```

### `/note <text>`
Add a quick note to session journal.
```
/note "remember to review PR #47"
```

### `/journal [date]`
View session journal entries.
```
/journal
/journal 2025-01-20
```

---

## 4. Communication & Device Routing

### `/msg !<device> <message>`
Send message to another Isaac instance.
```
/msg !laptop2 "deployment ready"
```

### `/show-cmd !<device>`
Show command running on remote device.
```
/show-cmd !desktop3
```

### `/sync [target]`
Manually trigger cloud sync or sync to specific device.
```
/sync
/sync !laptop2
```

---

## 5. Files & Data

### `/add <list> <item>`
Add item to named list (shopping, todos, etc.).
```
/add grocery "coffee beans"
```

### `/list <name>`
Display items in a list.
```
/list grocery
```

### `/grep <pattern> [files]`
Search for pattern in files or piped input.
```
/grep "ERROR" *.log
/history | /grep docker
```

### `/backup [target]`
Backup configuration or session data.
```
/backup
/backup configs
```

### `/restore <snapshot>`
Restore from backup snapshot.
```
/restore 2025-01-20_14:30
```

---

## 6. System Control

### `/f <command>`
**Force execution** - bypasses tier validation (internal mode only).
```
/f rm -rf temp/
```

### `/tier <command>`
Check tier classification for a command.
```
/tier "git push origin main"
```

### `/validate <command>`
Preview AI validation decision without executing.
```
/validate "sudo systemctl restart nginx"
```

---

## 7. Monitoring & Automation

### `/watch <cmd> [interval]`
Repeatedly execute command at interval (default 5s).
```
/watch "df -h" 10
```

### `/collect <data-type>`
Gather system data (logs, metrics, diagnostics).
```
/collect logs
/collect cpu-metrics
```

### `/alert <condition> <message>`
Set up condition-based notifications.
```
/alert "disk > 90%" "Disk space critical"
```

---

## 8. AI and Knowledge

### `/ask <query>`
Query AI with session context (standard internal command).
```
/ask "how do I set up docker networking?"
```

### `/explain <command>`
Get AI explanation of what a command does.
```
/explain "rsync -avz --delete src/ dest/"
```

### `/fix <error>`
Ask AI to suggest fix for error output.
```
/fix "connection refused on port 8080"
```

### `/collect grok <topic>`
Create or update x.ai vector search collection.
```
/collect grok kubernetes-docs https://k8s.io/docs
```

---

## 9. Developer Utilities

### `/debug [component]`
Toggle debug output for system components.
```
/debug
/debug command-router on
```

### `/trace <command>`
Execute command with detailed tracing.
```
/trace "git status"
```

### `/test <suite>`
Run test suite or specific test.
```
/test tier-validator
```

### `/reload`
Reload configuration and command plugins without restart.
```
/reload
```

---

## 10. Fun/Misc

### `/fortune`
Display random tech wisdom or tip.
```
/fortune
```

### `/joke`
Get a programming joke from AI.
```
/joke
```

### `/sass <context>`
Get sassy Isaac personality response (for invalid queries).
```
# Happens automatically when user forgets "isaac" prefix
# Response: "I have a name, use it."
```

---

## Pipe Semantics

Commands can be chained with `|` when they support stdin:

```
/history | /grep docker | /export results.txt
```

**Pipe-compatible commands:**
- `/grep` (stdin: true)
- `/export` (stdin: true)
- `/format` (stdin: true)

---

## Device Routing (`!alias`)

Prepend `!<device>` to route entire command sequence to target:

```
/msg !laptop2 "status check"
/show-cmd !desktop3
!laptop2 /history | /grep deploy
```

---

## Natural Language Shortcut

While `/ask` is the internal standard, `isaac <query>` works in both modes for convenience:

```
isaac what's my current directory?
isaac explain git rebase
```

---

## Future Command Ideas

### Advanced Task Management
- `/workflow <name>` - Execute saved multi-command workflows
- `/schedule <time> <command>` - Schedule command execution
- `/depends <cmd1> on <cmd2>` - Define command dependencies

### Team Collaboration
- `/share <item>` - Share file/output with team
- `/broadcast <message>` - Send to all devices
- `/collab <session-id>` - Join collaborative session

### Learning & Insights
- `/learn <pattern>` - Teach Isaac a new auto-fix pattern
- `/insights` - AI-generated usage insights
- `/recommend` - Get command recommendations based on context

### Advanced Monitoring
- `/dashboard` - Display live system dashboard
- `/trend <metric>` - Show metric trends over time
- `/anomaly` - Detect anomalous system behavior

---

## Command Discovery

### Built-in Commands
Commands implemented directly in Isaac core (e.g., `/help`, `/config`, `/status`).

### Plugin Commands
Commands loaded from `isaac/commands/<name>/command.yaml` manifests.

### User Commands
Custom commands in `~/.isaac/commands/` directory.

To list all available commands:
```
/help --list
```

To check command source:
```
/help /add --verbose
# Shows: Plugin command from isaac/commands/add/command.yaml
```

---

## Command Metadata

All commands support these flags:

- `--help` - Show detailed usage
- `--dry-run` - Preview action without executing
- `--verbose` - Enable detailed output
- `--json` - Output in JSON format (when applicable)

Example:
```
/backup --dry-run --verbose
```

---

## Security Notes

- **Tier 4 commands** always require explicit confirmation
- **/f (force)** is internal-mode only - never available externally
- **Device routing** requires authenticated connection
- **AI queries** are privacy-protected (not in command history recall)

---

**See also:**
- `COMMAND_PLUGIN_SPEC.md` - Plugin architecture details
- `COMMAND_PATTERNS.md` - Real interaction examples
- `ISAAC_FINAL_DESIGN.md` - Overall system architecture
