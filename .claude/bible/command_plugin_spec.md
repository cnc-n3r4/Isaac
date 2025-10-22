# Isaac Modular Command Definition Spec

This document defines a lightweight, file-based plugin system for Isaac's `/commands`. Each command is described by a **YAML manifest** and (optionally) a script/binary. Commands can be dispatched locally or routed to a target via `!alias`.

---

## 0. Directory Layout

```
isaac/
├─ commands/                 # userland commands
│  ├─ add/
│  │  ├─ command.yaml        # manifest
│  │  └─ run.py              # handler (optional)
│  ├─ list/
│  │  ├─ command.yaml
│  │  └─ run.py
│  ├─ grep/
│  │  ├─ command.yaml
│  │  └─ run.sh
│  └─ ask/
│     ├─ command.yaml
│     └─ run.py
├─ runtime/
│  └─ dispatcher.py          # loads manifests, routes, piping
└─ shared/
   └─ lib.py                 # helpers (io, validation, security)
```

---

## 1. Manifest Schema (YAML)

Each command declares metadata, arguments, I/O contracts, and security policy.

```yaml
# commands/<name>/command.yaml
name: add
version: 1.0.0
summary: "Add an item to a list"
description: |
  Adds an item to a named list (e.g., grocery). Items are stored centrally
  and available across machines.

triggers: ["/add"]           # words Isaac recognizes for this command
aliases: ["/a"]              # optional shorthand

args:
  - name: list
    type: string
    required: true
    pattern: "^[A-Za-z0-9._-]{1,32}$"
    help: "Name of the list, e.g., grocery"
  - name: item
    type: string
    required: true
    min_length: 1
    max_length: 256
    help: "Item to add"

stdin: false                 # does this command read from stdin (pipe)?
stdout:
  type: text                 # text | json | table | file
  schema: null               # optional JSON Schema for json output

security:
  scope: "user"              # user | worker | root
  allow_remote: true         # permitted to run when routed via !alias
  allowlist:
    linux: []                # if wrapper executes OS binaries, list them
    windows: []
  resources:
    timeout_ms: 5000
    max_stdout_kib: 64

runtime:
  entry: "run.py"            # optional; if absent, this is a pure builtin
  interpreter: "python"      # python | shell | powershell | node | native
  env:                       # optional environment variables
    - key: "LIST_DB_PATH"
      value: "${ISAAC_DATA}/lists.db"

telemetry:
  log_invocation: true
  log_output: true
  redact_patterns:           # regexes to redact from logs/output
    - "(?i)apikey=[A-Za-z0-9_-]+"

examples:
  - "/add grocery apples"
  - "/add grocery \"coffee beans\""
```

> **Note**: If `runtime.entry` is omitted, Isaac can implement the command internally (e.g., a built-in).

---

## 2. JSON Schema for Manifests

Use this to validate `command.yaml` on load.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["name", "version", "summary", "triggers", "args", "security", "stdout"],
  "properties": {
    "name": {"type":"string", "pattern":"^[a-z][a-z0-9_-]*$"},
    "version": {"type":"string"},
    "summary": {"type":"string"},
    "description": {"type":"string"},
    "triggers": {"type":"array", "items":{"type":"string"}},
    "aliases": {"type":"array", "items":{"type":"string"}},
    "args": {
      "type":"array",
      "items": {
        "type":"object",
        "required":["name","type","required"],
        "properties": {
          "name":{"type":"string"},
          "type":{"type":"string","enum":["string","int","float","bool","path","enum"]},
          "required":{"type":"boolean"},
          "pattern":{"type":"string"},
          "enum":{"type":"array","items":{"type":["string","number","boolean"]}},
          "min_length":{"type":"integer","minimum":0},
          "max_length":{"type":"integer","minimum":0},
          "help":{"type":"string"}
        }
      }
    },
    "stdin":{"type":"boolean"},
    "stdout":{
      "type":"object",
      "required":["type"],
      "properties":{
        "type":{"type":"string","enum":["text","json","table","file"]},
        "schema":{}
      }
    },
    "security":{
      "type":"object",
      "required":["scope","allow_remote","resources"],
      "properties":{
        "scope":{"type":"string","enum":["user","worker","root"]},
        "allow_remote":{"type":"boolean"},
        "allowlist":{
          "type":"object",
          "properties":{
            "linux":{"type":"array","items":{"type":"string"}},
            "windows":{"type":"array","items":{"type":"string"}}
          }
        },
        "resources":{
          "type":"object",
          "properties":{
            "timeout_ms":{"type":"integer","minimum":100},
            "max_stdout_kib":{"type":"integer","minimum":1}
          }
        }
      }
    },
    "runtime":{
      "type":"object",
      "properties":{
        "entry":{"type":"string"},
        "interpreter":{"type":"string","enum":["python","shell","powershell","node","native"]},
        "env":{
          "type":"array",
          "items":{
            "type":"object",
            "required":["key","value"],
            "properties":{"key":{"type":"string"},"value":{"type":"string"}}
          }
        }
      }
    },
    "telemetry":{
      "type":"object",
      "properties":{
        "log_invocation":{"type":"boolean"},
        "log_output":{"type":"boolean"},
        "redact_patterns":{"type":"array","items":{"type":"string"}}
      }
    },
    "examples":{"type":"array","items":{"type":"string"}}
  }
}
```

---

## 3. Dispatcher Contract

- **Resolve trigger**: first token starting with `/` selects command.
- **Parse args**: map positional args to `args[]` in manifest, then validate.
- **Piping**: if `cmdA | cmdB`, feed `cmdA` stdout to `cmdB` stdin when `stdin: true`.
- **Routing**: leading `!alias` routes the composed command to target agent.
- **Timeouts**: enforce `security.resources.timeout_ms` per command.
- **Stdout cap**: truncate or spill to artifact when output exceeds `max_stdout_kib`.

---

## 4. Return Envelope

All commands return a normalized envelope (to terminal and history DB).

```json
{
  "ok": true,
  "kind": "text",
  "stdout": "added 'apples' to grocery",
  "meta": {
    "command": "/add",
    "args": {"list":"grocery","item":"apples"},
    "duration_ms": 42,
    "truncated": false,
    "artifact": null
  }
}
```

For `file` outputs:
```json
{
  "ok": true,
  "kind": "file",
  "stdout": null,
  "meta": {"artifact":"presigned://…/montage.jpg"}
}
```

---

## 5. Examples

### 5.1 `/add` (builtin Python handler)

`commands/add/command.yaml`
```yaml
name: add
version: 1.0.0
summary: "Add an item to a list"
triggers: ["/add"]
args:
  - { name: list, type: string, required: true, pattern: "^[A-Za-z0-9._-]{1,32}$" }
  - { name: item, type: string, required: true, min_length: 1, max_length: 256 }
stdin: false
stdout: { type: text }
security:
  scope: user
  allow_remote: true
  resources: { timeout_ms: 5000, max_stdout_kib: 64 }
runtime:
  entry: "run.py"
  interpreter: "python"
```

`commands/add/run.py` (pseudo):
```python
import sys, json, os
from pathlib import Path

def main():
    payload = json.loads(sys.stdin.read())  # Isaac passes args & context via stdin
    lst = payload["args"]["list"]
    item = payload["args"]["item"]
    db = os.environ.get("LIST_DB_PATH", os.path.expanduser("~/.isaac/lists.db"))
    # ... insert row (list, item) ...
    print(json.dumps({"ok": True, "kind":"text", "stdout": f"added '{item}' to {lst}", "meta":{}}))

if __name__ == "__main__":
    main()
```

### 5.2 `/grep` (shell wrapper with pipe)

`commands/grep/command.yaml`
```yaml
name: grep
version: 1.0.0
summary: "Search text via regex or fixed string"
triggers: ["/grep"]
args:
  - { name: pattern, type: string, required: true, min_length: 1, max_length: 128 }
  - { name: files, type: path, required: false }
stdin: true
stdout: { type: text }
security:
  scope: user
  allow_remote: true
  allowlist:
    linux: ["/bin/grep"]
    windows: ["C:\\Windows\\System32\\findstr.exe"]
  resources: { timeout_ms: 15000, max_stdout_kib: 256 }
runtime:
  entry: "run.sh"
  interpreter: "shell"
```

`commands/grep/run.sh` (pseudo):
```sh
#!/usr/bin/env bash
# Isaac passes JSON on stdin: {"args":{"pattern":"ERROR","files":"*.log"}, "stdin":"...optional data..."}
# Implement with grep/findstr based on platform
```

### 5.3 `/ask` (AI query)

`commands/ask/command.yaml`
```yaml
name: ask
version: 1.0.0
summary: "Query AI with merged history context"
triggers: ["/ask"]
args:
  - { name: prompt, type: string, required: true, min_length: 1 }
stdin: true
stdout: { type: text }
security:
  scope: user
  allow_remote: true
  resources: { timeout_ms: 30000, max_stdout_kib: 512 }
runtime:
  entry: "run.py"
  interpreter: "python"
```

---

## 6. Validation & Safety

- Validate manifests at load against the JSON Schema; reject invalid commands.
- Enforce **platform allowlists** before executing any external binary.
- Sanitize environment (`PATH`, `HOME`) and run handlers under a restricted user.
- Redact sensitive patterns in logs as per `telemetry.redact_patterns`.

---

## 7. Testing Template

Each command folder may include `test.yaml`:

```yaml
cases:
  - name: add-basic
    input: "/add grocery apples"
    expect:
      ok: true
      contains: "apples"
  - name: add-inject
    input: "/add grocery 'foo; rm -rf /'"
    expect:
      ok: false
```

A tiny runner can execute these against a sandbox dispatcher.

---

## 8. Pipe Semantics

- If `A | B`, Isaac constructs two subprocesses:
  - Feed `A`’s normalized `stdout` as `stdin` to `B` **only if** `B.stdin: true`.
- For `json` pipe targets, convert text to NDJSON lines unless `B` declares `stdin:json` (future extension).

---

## 9. Versioning & Capabilities

- Commands declare `version`. Dispatcher can refuse incompatible versions.
- Agents advertise capabilities (e.g., `grep`, `montage`) so hub can route or degrade gracefully.

---

## 10. Error Envelope

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "invalid list name",
    "hint": "Allowed: letters, digits, ., _, -"
  },
  "meta": { "duration_ms": 2 }
}
```

---

## 11. Security Notes

- Never allow `sh -c` with untrusted text.
- Prefer parameterized execution (argv arrays).
- Apply per-command **rate limits** and **quotas** (CPU time, stdout size).
- Route `!alias` only to known agents; log origin, signature, and ttl.
