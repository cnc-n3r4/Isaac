# Isaac Command System - Complete Documentation Index

This document serves as the **authoritative index** for Isaac's command system documentation. All command-related specifications, patterns, and implementation details are linked here.

---

## Documentation Structure

Isaac's command system is documented across five interconnected files in the bible:

### 1. **COMMAND_PATTERNS.md** (Authoritative Reference)
**Purpose:** Real-world interaction examples showing correct command usage  
**When to use:** When you need to see how commands actually work in practice  
**Key Content:**
- External mode examples (`isaac /command`)
- Internal mode examples (`/command`)
- Device routing examples (`/msg !device`, `/show-cmd !device`)
- Natural language patterns (`isaac <query>`)
- Personality responses ("I have a name, use it.")
- Edge cases and error handling

**Navigation:** Start here for understanding **how users interact with Isaac**.

---

### 2. **COMMAND_BRAINSTORM.md** (Command Catalog)
**Purpose:** Complete inventory of all planned commands across 10 categories  
**When to use:** When planning new features or checking if a command exists  
**Key Content:**
- **10 Command Categories:**
  1. Core Utility (`/help`, `/status`, `/config`, `/clear`, `/exit`)
  2. History & Search (`/history`, `/search`, `/recall`)
  3. Task & Note Management (`/task`, `/note`, `/journal`)
  4. Communication & Device Routing (`/msg`, `/show-cmd`, `/sync`)
  5. Files & Data (`/add`, `/list`, `/grep`, `/backup`, `/restore`)
  6. System Control (`/f`, `/tier`, `/validate`)
  7. Monitoring & Automation (`/watch`, `/collect`, `/alert`)
  8. AI and Knowledge (`/ask`, `/explain`, `/fix`, `/collect grok`)
  9. Developer Utilities (`/debug`, `/trace`, `/test`, `/reload`)
  10. Fun/Misc (`/fortune`, `/joke`, `/sass`)
- Pipe semantics (`/history | /grep docker`)
- Device routing patterns (`!laptop2 /history | /grep deploy`)
- Future command ideas (workflow, scheduling, collaboration)
- Command metadata and flags (`--help`, `--dry-run`, `--verbose`, `--json`)

**Navigation:** Use this for **feature planning and command discovery**.

---

### 3. **COMMAND_PLUGIN_SPEC.md** (Implementation Architecture)
**Purpose:** Technical specification for the YAML-based plugin system  
**When to use:** When implementing new commands or building the dispatcher  
**Key Content:**
- **Directory Layout:**
  ```
  isaac/commands/<name>/
    ├─ command.yaml    # Manifest
    └─ run.py          # Handler
  ```
- **YAML Manifest Schema:**
  - `name`, `version`, `summary`, `description`
  - `triggers` (command words), `aliases` (shortcuts)
  - `args` (validation with types, patterns, constraints)
  - `stdin`/`stdout` (pipe contracts)
  - `security` (scope, remote execution, allowlists, timeouts)
  - `runtime` (entry point, interpreter, environment)
  - `telemetry` (logging, redaction)
- **Dispatcher Contract:**
  - Trigger resolution (`/` prefix detection)
  - Argument parsing and validation
  - Pipe chaining (`cmdA | cmdB`)
  - Device routing (`!alias`)
  - Timeout enforcement
  - Output size limits
- **Return Envelopes:** Normalized JSON responses
- **Security Model:** Validation, allowlists, sandboxing, redaction
- **Testing Templates:** `test.yaml` format
- **Examples:** `/add`, `/grep`, `/ask` manifests

**Navigation:** Use this for **building the command execution engine**.

---

### 4. **ISAAC_FINAL_DESIGN.md** (Overall Architecture)
**Purpose:** High-level system design with command flow integration  
**When to use:** When understanding how commands fit into the larger system  
**Key Content:**
- Command classification (meta/natural/shell)
- Tier-based validation (1-4)
- AI integration for Tier ≥3 commands
- Dual-mode system (external/internal)
- Session management
- Cloud sync architecture
- Agent ecosystem (Isaac as gatekeeper)

**Navigation:** Use this for **architectural context**.

---

### 5. **ISAAC_UI_SPECIFICATION.md** (Terminal Interface)
**Purpose:** UI/UX design including command input and display  
**When to use:** When implementing terminal UI or command feedback  
**Key Content:**
- Prompt design (external vs internal modes)
- Command output formatting
- Status indicators during command execution
- Error display patterns
- Offline mode indicators

**Navigation:** Use this for **UI implementation**.

---

## Command System Design Principles

### 1. Prefix Discipline (CRITICAL)
- **Internal commands:** ALL use `/` prefix (`/help`, `/ask`, `/task`, `/f`)
- **Device routing:** ALL use `!` prefix (`/msg !laptop2`, `/show-cmd !desktop3`)
- **Natural language:** Use `isaac` prefix (`isaac what's my IP?`)
- **Shell commands:** No prefix (goes through tier validation)

**Why this matters:** Clear prefix separation prevents ambiguity and ensures safety. `/f` (force) being internal-only protects against external abuse.

### 2. Dual-Mode Safety
- **External Mode (`isaac /command`):**
  - Limited command set for safety
  - No access to `/f` (force execution)
  - Restricted to safe meta-commands
  - Standard shell prompt: `C:\ >`

- **Internal Mode (`isaac /start` → `$>`):**
  - Full command access
  - `/f` available for power users
  - Enhanced personality (sass responses)
  - Isaac prompt: `$>` or `isaac [OFFLINE]>`

**Why this matters:** Prevents accidental damage before entering permanent shell mode.

### 3. Modular Plugin Architecture
Commands are **YAML-defined plugins** with:
- Declarative validation (no code needed for simple commands)
- Security constraints (timeouts, output limits, allowlists)
- Composability (pipe support via `stdin: true`)
- Platform awareness (Linux/Windows allowlists)

**Why this matters:** New commands can be added without touching core code.

### 4. Device Routing (`!alias`)
Isaac can route commands to other machines:
```
/msg !laptop2 "deployment ready"
!desktop3 /history | /grep docker
```

**Why this matters:** Multi-machine workflow without SSH complexity.

### 5. Personality Integration
Isaac has context-aware personality:
- Valid commands: Professional, helpful responses
- Invalid queries: "I have a name, use it."
- Force command saves: "saved your dumbass" (after `/f` execution)

**Why this matters:** Makes the tool memorable and reinforces correct usage patterns.

---

## Quick Reference: Where to Find What

| **Need** | **Document** | **Section** |
|----------|-------------|------------|
| Real usage examples | COMMAND_PATTERNS.md | All sections |
| Full command list | COMMAND_BRAINSTORM.md | Categories 1-10 |
| Implement new command | COMMAND_PLUGIN_SPEC.md | Section 1-5 |
| Understand validation | COMMAND_PLUGIN_SPEC.md | Section 6 |
| Pipe semantics | COMMAND_PLUGIN_SPEC.md | Section 8 |
| Device routing | COMMAND_BRAINSTORM.md | Section 4 |
| Force execution | COMMAND_PATTERNS.md | "/f (force execution)" |
| Natural language | COMMAND_PATTERNS.md | "Natural Language" |
| UI design | ISAAC_UI_SPECIFICATION.md | "Command Input" |
| Architecture | ISAAC_FINAL_DESIGN.md | "Command Orchestration" |
| Testing | COMMAND_PLUGIN_SPEC.md | Section 7 |
| Security | COMMAND_PLUGIN_SPEC.md | Section 11 |
| **Track 1 Roadmap** | **TRACK1_LOCAL_QOL.md** | **Overview** |
| **Dispatcher spec** | **unified_dispatcher_spec.md** | **.claude/mail/to_implement/** |
| **Queue spec** | **command_queue_overlay_spec.md** | **.claude/mail/to_implement/** |

---

## Documentation Maintenance

### When to Update Each Document

**COMMAND_PATTERNS.md:**
- Add real user interaction examples as they emerge
- Document new personality responses
- Show edge cases discovered in testing

**COMMAND_BRAINSTORM.md:**
- Add new commands to appropriate categories
- Document new command categories if needed
- Update future ideas section with user feedback

**COMMAND_PLUGIN_SPEC.md:**
- Update YAML schema if new fields added
- Document new security patterns
- Add implementation examples for complex commands

**ISAAC_FINAL_DESIGN.md:**
- Update when command flow changes
- Document new integration points
- Reflect architectural decisions

**ISAAC_UI_SPECIFICATION.md:**
- Update when prompt design changes
- Document new output formatting patterns
- Add new status indicators

### Golden Rule
**COMMAND_PATTERNS.md is the source of truth for usage.**  
**COMMAND_PLUGIN_SPEC.md is the source of truth for implementation.**  
If they conflict, COMMAND_PATTERNS.md wins (implementation must match user expectations).

---

## Implementation Roadmap

### Phase 1: Core Commands (✅ COMPLETE)
Implemented as simple Python scripts in `isaac/commands/`:
- `help.py` - Command reference
- `list.py` - List management
- `backup.py` / `restore.py` - Config backup
- `togrok_handler.py` - x.ai integration
- `config.py` - Configuration management
- `status.py` - System status display

**Status:** Meta-commands Phase 2 completed

### Phase 2: Track 1 - Local Environment QoL (🎯 CURRENT)
**See:** `TRACK1_LOCAL_QOL.md` for complete specification

**Track 1.1:** Unified Dispatcher (4-6 hours)
- Plugin-based command system with YAML manifests
- Auto-discovery and validation
- Pipe semantics and device routing
- Security enforcement (timeouts, caps, allowlists)
- **Spec:** `.claude/mail/to_implement/unified_dispatcher_spec.md`

**Track 1.2:** Command Queue Overlay (3-4 hours)
- Local SQLite queue for offline resilience
- Background sync worker with exponential backoff
- Offline indicator in prompt
- Never lose commands
- **Spec:** `.claude/mail/to_implement/command_queue_overlay_spec.md`

**Status:** Fully specified, ready for implementation

### Phase 3: Extended Commands (Future)
Implement commands from COMMAND_BRAINSTORM.md categories:
- Priority: Task & Note Management (high user value)
- Priority: Communication & Device Routing (multi-machine)
- Priority: AI and Knowledge (differentiator)
- Lower priority: Monitoring, Developer Utilities, Fun/Misc

### Phase 4: Advanced Features (Future)
- **Track 2:** Cloud Hub Refinements (job lifecycle, search API, event bus)
- **Track 3:** Agent Enhancements (configurable modules, hot-reload, resource monitoring)
- Workflow system (saved command sequences)
- Scheduling (cron-like command execution)
- Collaboration (shared sessions)
- Learning (AI-powered command recommendations)

---

## Developer Quick Start

### To Add a New Command

1. **Design the interaction** (update COMMAND_PATTERNS.md with examples)
2. **Add to catalog** (update COMMAND_BRAINSTORM.md in appropriate category)
3. **Write the manifest** (create `isaac/commands/<name>/command.yaml` per COMMAND_PLUGIN_SPEC.md)
4. **Implement the handler** (create `run.py` or `run.sh`)
5. **Test** (create `test.yaml` with validation cases)
6. **Document** (ensure all bible docs reflect the new command)

### To Modify Command Flow

1. **Check COMMAND_PATTERNS.md** for user expectations
2. **Update ISAAC_FINAL_DESIGN.md** if architecture changes
3. **Update COMMAND_PLUGIN_SPEC.md** if dispatcher changes
4. **Regenerate examples** in COMMAND_PATTERNS.md to show new behavior

---

## Cross-References

This document links to:
- **COMMAND_PATTERNS.md** - User interaction examples
- **COMMAND_BRAINSTORM.md** - Full command catalog
- **COMMAND_PLUGIN_SPEC.md** - Plugin implementation spec
- **ISAAC_FINAL_DESIGN.md** - Overall architecture
- **ISAAC_UI_SPECIFICATION.md** - Terminal UI design
- **ISAAC_AI_INTERACTION_DESIGN.md** - AI integration patterns

Other bible documents reference this overview for command system navigation.

---

**Last Updated:** 2025-01-21  
**Maintained By:** Sarah (Visual Persona)  
**Status:** Authoritative - Single source of truth for command system documentation
