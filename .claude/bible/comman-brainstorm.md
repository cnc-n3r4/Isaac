# Isaac CLI Command Brainstorm
Custom `/` commands that behave like scripts or pipes, designed for internal Isaac shells.

---

## 1. Core Utility Commands

| Command | Purpose | Example |
|----------|----------|----------|
| `/echo` | test or return a literal string | `/echo system online` |
| `/time` | display time and date across hosts | `/time !labpc` |
| `/status` | show active agents and heartbeat states | `/status all` |
| `/log` | tail recent system logs | `/log --lines 50` |
| `/exec` | run raw command on target | `/exec !labpc "df -h"` |

---

## 2. History & Search

| Command | Purpose | Example |
|----------|----------|----------|
| `/history` | show merged command + AI query history | `/history --today` |
| `/search` | fuzzy or regex search through all logs | `/search "apt install"` |
| `/summary` | summarize today’s interactions | `/summary --since 9am` |

---

## 3. Task & Note Management

| Command | Purpose | Example |
|----------|----------|----------|
| `/add` | add note or task | `/add grocery bread` |
| `/list` | list tasks or notes | `/list grocery` |
| `/done` | mark task complete | `/done grocery bread` |
| `/note` | add tagged persistent note | `/note @projectX "client meeting scheduled"` |

---

## 4. Communication / Messaging

| Command | Purpose | Example |
|----------|----------|----------|
| `/msg` | send message to another machine | `/msg !labpc "run diagnostics"` |
| `/inbox` | view received messages | `/inbox --unread` |
| `/broadcast` | send message to all agents | `/broadcast "backup starting"` |

---

## 5. Files & Data

| Command | Purpose | Example |
|----------|----------|----------|
| `/push` | upload or sync file to hub | `/push report.log` |
| `/pull` | fetch from hub | `/pull latest_config.yaml` |
| `/grep` | pipe-style search across local files | `/grep TODO *.py` |
| `/cat` | read short file contents | `/cat /etc/hostname` |

---

## 6. System Control

| Command | Purpose | Example |
|----------|----------|----------|
| `/reboot` | restart agent | `/reboot !labpc` |
| `/shutdown` | shutdown agent | `/shutdown !studio` |
| `/update` | pull latest scripts/configs | `/update !all` |
| `/sync` | force db + index sync | `/sync --now` |

---

## 7. Monitoring & Automation

| Command | Purpose | Example |
|----------|----------|----------|
| `/watch` | periodically rerun command | `/watch /status --interval 10s` |
| `/schedule` | queue job for later | `/schedule !labpc backup at 02:00` |
| `/alert` | set conditional notification | `/alert if cpu>90 send "CPU high"` |

---

## 8. AI and Knowledge

| Command | Purpose | Example |
|----------|----------|----------|
| `/ask` | query AI engine with context | `/ask "summarize build logs"` |
| `/analyze` | process file or data block | `/analyze build_output.log` |
| `/explain` | explain command or config | `/explain systemd service` |
| `/learn` | ingest new knowledge into memory | `/learn /notes/setup.md` |

---

## 9. Developer Utilities

| Command | Purpose | Example |
|----------|----------|----------|
| `/git` | run git shorthand | `/git status` |
| `/test` | run test harness on code | `/test sandbox` |
| `/lint` | static check code | `/lint *.py` |
| `/deploy` | package + send code to agent | `/deploy !labpc projectX` |

---

## 10. Fun / Misc

| Command | Purpose | Example |
|----------|----------|----------|
| `/joke` | fetch random dev humor | `/joke` |
| `/quote` | inspirational quote | `/quote` |
| `/fortune` | random UNIX-style fortune | `/fortune` |
| `/sound` | play system sound or alert | `/sound "ding"` |

---

## Pipe Semantics
Commands can chain locally:
/grep "error" /log | /analyze

Isaac detects the pipe, streams output from the first command as input to the next handler.

---

## Notes
- Each `/` command resolves to a script in `/commands` or `/scripts` dir.
- Output gets fed back into the **Isaac dispatcher**, optionally into AI context.
- Command results also append to `cmd_history_db` for later `/search`.

---

## Future Command Ideas
- `/map` — visualize host layout graph.
- `/trace` — trace message route between agents.
- `/train` — retrain embeddings on new history slices.
- `/review` — auto-summary of code changes across nodes.
