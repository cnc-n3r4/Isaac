# Next-Phase Design Ideas for Isaac Distributed System

## 1) Local Environment Quality-of-Life
### Unified Shell Interface
- Merge `/` and `!` handlers into a single lightweight dispatcher.
- Keep a small plugin registry so new verbs (`/add`, `/list`, `/search`, `/task`) auto-register from a `plugins/` directory.
- Add per-terminal color themes or prompts that display `[isaac@desktop] >` for quick context.

### Command Queue Overlay
- Maintain a small local queue (`~/.isaac/queue.db`) that buffers outgoing jobs if the cloud hub is unreachable.
- Background thread syncs when connection returns — ensures nothing is lost if you drop Wi‑Fi.

---

## 2) Cloud Hub Refinements
### Job Lifecycle State Machine
```
queued → picked_up → running → done | failed
```
- Each state change triggers a webhook or event; supports live dashboards later.
- Add a `job_retries` field with exponential backoff and jitter.

### Search API Upgrade
- Expose `/search?kind=(chat|cmd|both)&q=term&terminal_id=...`
- Integrate SQLite FTS5 or Postgres `tsvector` for case-insensitive full-text queries.
- Add filters for:
  - time range
  - terminal
  - return type (`summary` vs `raw`)

### Event Bus Layer
- Lightweight pub/sub inside the hub for:
  - job status updates
  - notifications
  - system metrics
- Could use Redis Streams or a simple in-process queue for now.

---

## 3) Agent Enhancements
### Configurable Modules
- Agents read a manifest:
  ```yaml
  modules:
    - exec
    - monitor
    - aiquery
  ```
- Each module has independent polling intervals and privileges.

### Health + Metrics
- Agents push heartbeats:
  ```json
  { "agent_id":"labpc", "uptime":13452, "cpu":12.1, "mem":42.3 }
  ```
- Hub stores this in `agent_status` for `/status` or `/fleet` commands.

---

## 4) Data & Storage
### Partitioned but Queryable History
- Keep `cmd_history_<terminal>.db` local for speed.
- Hub periodically merges indexes into the global FTS layer.
- Add `replica_ts` columns to resolve sync conflicts.

### Snapshot Summaries
- Periodically summarize long AI conversations into short embeddings.
- Store `summary_vector` for semantic search later (keeps token counts down).

---

## 5) Security & Auth Improvements
### Session Tokens
- Agents authenticate with short-lived JWTs signed by the hub.
- Each job envelope carries `sig`, `nonce`, and `exp`.

### RBAC
- Role tiers: `root` (Isaac), `worker` (Coder), `user` (Nick)
- Each role maps to an allowlist subset.

---

## 6) UX & Tools
### `/status` Command
- Shows job queue, agent uptime, and last heartbeat for each node.
- `/status !labpc` → show details for one agent.

### `/inspect <job_id>`
- Pulls full log and result for debugging.

### `/search` Improvements
- Allow fuzzy search (`--fuzzy`) or regex search (`--regex`).

---

## 7) Future Optional Layers
### Telegram / Web Frontend
- Once the local system is solid, wrap the same API in a Telegram bot or web dashboard.
- Only route `/` and `!` commands, no secrets.

### Automation Engine
- Add a simple scheduler that can trigger stored commands by cron or condition:
  ```
  /schedule !labpc backup at 02:00
  ```

---

## 8) Stretch Goals
- Voice input (“Isaac, add coffee beans to grocery”)
- Natural language aliasing (“tell labpc to deploy projectX” → auto‑parse to `!labpc deploy projectX`)
- Machine‑to‑machine “inbox/outbox” graph UI to visualize message flow.

---

## Summary
These additions don’t break your current design; they deepen reliability, search, and modularity.
They make Isaac the backbone of your distributed personal network — everything else (Telegram, web UI, automation) can layer on top later without changing the core message bus.
