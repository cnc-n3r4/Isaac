# Next-Phase Design Ideas for Isaac Distributed System

---

## 1. Local Environment Quality-of-Life
### 🔹 Unified Shell Interface
- Merge `/` and `!` handlers into a single lightweight dispatcher.
- Keep a small plugin registry so new verbs (`/add`, `/list`, `/search`, `/task`) auto-register from a `plugins/` directory.
- Add per-terminal color themes or prompts that display `[isaac@desktop] >` for quick context.

### 🔹 Command Queue Overlay
- Maintain a small local queue (`~/.isaac/queue.db`) that buffers outgoing jobs if the cloud hub is unreachable.
- Background thread syncs when connection returns — ensures nothing is lost if you drop Wi-Fi.

---

## 2. Cloud Hub Refinements
### 🔹 Job Lifecycle State Machine
- queued → picked_up → running → done|failed
- Each state change triggers a webhook or event; supports live dashboards later.
- Add a `job_retries` field with exponential backoff and jitter.

### 🔹 Search API Upgrade
- Expose `/search?kind=(chat|cmd|both)&q=term&terminal_id=...`
- Integrate SQLite FTS5 or Postgres `tsvector` for case-insensitive full-text queries.
- Add filters for:
  - time range
  - terminal
  - return type (`summary` vs `raw`)

### 🔹 Event Bus Layer
- Lightweight pub/sub inside the hub for:
  - job status updates
  - notifications
  - system metrics
- Could use Redis Streams or a simple in-process queue for now.

---

## 3. Agent Enhancements
### 🔹 Configurable Modules
- Agents read a manifest:
  ```yaml
  modules:
    - exec
    - monitor
    - aiquery
