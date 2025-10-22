# Track 1: Local Environment Quality-of-Life

## Overview
**Goal:** Transform Isaac from hardcoded commands to a fully extensible, resilient plugin system with offline capabilities.

**Status:** ✅ **COMPLETE** (October 21, 2025)  
**Total Estimated Time:** 7-10 hours  
**Actual Implementation Time:** ~7 hours  
**Priority:** HIGH (foundation for all future enhancements)

**Completion Report:** `.claude/status/TRACK1_COMPLETE.md`

---

## Two-Phase Approach

### Phase 1: **Unified Dispatcher** (Track 1.1)
**What:** Plugin-based command system with YAML manifests  
**Why:** Makes adding new commands trivial, eliminates hardcoded logic  
**Time:** 4-6 hours  
**Spec:** `.claude/mail/to_implement/unified_dispatcher_spec.md`

### Phase 2: **Command Queue Overlay** (Track 1.2)
**What:** Local SQLite queue for offline command resilience  
**Why:** Never lose commands when cloud connection drops  
**Time:** 3-4 hours  
**Spec:** `.claude/mail/to_implement/command_queue_overlay_spec.md`

---

## Why This Order Matters

```
Track 1.1 (Dispatcher) → Track 1.2 (Queue) → Track 3 (Advanced Features)
         ↓                      ↓                    ↓
   Foundation            Resilience           Intelligence
```

**Track 1.1 must come first** because:
1. Queue needs `/queue` and `/sync` commands → requires dispatcher
2. Advanced features (Track 3) need plugin system
3. Hot-reload (Track 3.2) depends on manifest architecture

---

## Track 1.1: Unified Dispatcher

### What Changes

**Before:**
```python
# Hardcoded in command_router.py
if cmd == "config":
    import config
    config.run()
if cmd == "status":
    import status
    status.run()
```

**After:**
```
isaac/commands/config/
  ├─ command.yaml    # Declarative manifest
  └─ run.py          # Handler script
  
Dispatcher auto-loads and validates all manifests
```

### Key Benefits
- ✅ **Extensibility:** Add commands by dropping YAML + script
- ✅ **Validation:** Automatic argument type checking and constraints
- ✅ **Security:** Timeouts, output caps, binary allowlists
- ✅ **Composability:** Pipe semantics (`/history | /grep docker`)
- ✅ **Documentation:** Manifests self-document with examples

### Files to Create
1. `isaac/runtime/dispatcher.py` - Core engine
2. `isaac/runtime/manifest_loader.py` - YAML parser + validation
3. `isaac/runtime/security_enforcer.py` - Safety boundaries
4. Convert 5 commands to manifests: `/help`, `/status`, `/config`, `/list`, `/backup`

### Success Criteria
- All existing meta-commands work identically through dispatcher
- New command can be added without touching core code
- Pipe semantics work (`cmdA | cmdB`)
- All tests pass (no regressions)

**Full Spec:** `.claude/mail/to_implement/unified_dispatcher_spec.md`

---

## Track 1.2: Command Queue Overlay

### What Changes

**Before:**
```
User: !laptop2 /status
       ↓
Cloud unavailable → ERROR ❌
Command lost forever
```

**After:**
```
User: !laptop2 /status
       ↓
Cloud unavailable → Queue locally ✅
       ↓
Prompt: isaac [OFFLINE: 1 queued]>
       ↓
Background: Connection restored → Auto-sync
       ↓
Notification: "1 queued command synced"
```

### Key Benefits
- ✅ **Resilience:** Commands never lost (SQLite persistence)
- ✅ **Transparency:** Offline indicator in prompt
- ✅ **Automatic:** Background sync with exponential backoff
- ✅ **Graceful:** Survives process restarts and crashes

### Files to Create
1. `isaac/queue/command_queue.py` - SQLite queue manager
2. `isaac/queue/sync_worker.py` - Background sync thread
3. Integration with `SessionManager` and `CommandRouter`
4. New meta-commands: `/queue` (view), `/sync` (force sync)

### Success Criteria
- Commands queued when cloud unavailable
- Auto-sync when connection returns
- Prompt shows offline indicator + queued count
- Queue persists across restarts

**Full Spec:** `.claude/mail/to_implement/command_queue_overlay_spec.md`

---

## Implementation Roadmap

### Week 1: Track 1.1 (Dispatcher)
**Day 1-2:** Foundation (4 hours)
- Create `isaac/runtime/` directory
- Implement `manifest_loader.py` with JSON Schema validation
- Implement `security_enforcer.py` with timeout/output cap
- Write unit tests

**Day 3:** Core Dispatcher (2 hours)
- Implement `dispatcher.py` main class
- Add command loading, trigger resolution, arg parsing
- Write unit tests for dispatcher methods

**Day 4:** Migration (2 hours)
- Convert 5 commands to YAML manifests
- Update `command_router.py` integration
- Run full test suite, fix regressions

### Week 2: Track 1.2 (Queue)
**Day 1:** Database (2 hours)
- Create `isaac/queue/` directory
- Implement `command_queue.py` with SQLite schema
- Write unit tests for queue operations

**Day 2:** Sync Worker (2 hours)
- Implement `sync_worker.py` background thread
- Add exponential backoff logic
- Test offline/online cycles

**Day 3:** Integration (1 hour)
- Update `SessionManager` to initialize queue
- Update `CommandRouter` to queue on cloud failure
- Update prompt for offline indicator

**Day 4:** Polish (1 hour)
- Add `/queue` and `/sync` meta-commands
- Add sync notifications
- Test graceful shutdown

---

## Testing Strategy

### Track 1.1 Tests
**Unit Tests:**
- `test_manifest_loader.py` - YAML validation
- `test_security_enforcer.py` - Timeouts, caps, allowlists
- `test_dispatcher.py` - Trigger resolution, arg parsing, execution

**Integration Tests:**
- `test_dispatcher_integration.py` - All 5 commands work
- `test_pipe_semantics.py` - Command chaining
- `test_device_routing.py` - `!alias` queuing

**Regression Tests:**
- All existing tests must pass (no behavior changes)

### Track 1.2 Tests
**Unit Tests:**
- `test_command_queue.py` - Enqueue, dequeue, status
- `test_sync_worker.py` - Background thread, backoff

**Integration Tests:**
- `test_queue_integration.py` - End-to-end offline → online flow
- `test_queue_persistence.py` - Restart survival

**Stress Tests:**
- 100+ commands queued while offline
- Memory usage stable over long runs

---

## Dependencies

### Track 1.1 Dependencies
**Required:**
- `.claude/bible/COMMAND_PLUGIN_SPEC.md` - Implementation spec
- `.claude/bible/COMMAND_BRAINSTORM.md` - Command catalog
- `SessionManager` - For preferences and cloud access
- `CloudClient` - For `!alias` routing

**Blocks:**
- Track 1.2 (needs `/queue` and `/sync` commands)
- Track 3.2 (hot-reload needs dispatcher)

### Track 1.2 Dependencies
**Required:**
- Track 1.1 (Dispatcher) - For `/queue` and `/sync` commands
- `CloudClient` - For `is_available()` check
- `SessionManager` - For lifecycle management

**Enables:**
- Track 2.1 (Job Lifecycle) - Enhanced queue with cloud state tracking

---

## Configuration

### Track 1.1 Config
No new config needed - uses existing `SessionManager`.

### Track 1.2 Config
Add to `~/.isaac/config.json`:
```json
{
  "queue": {
    "enabled": true,
    "sync_interval_seconds": 30,
    "max_retry_count": 10,
    "cleanup_after_days": 7,
    "batch_size": 10
  }
}
```

---

## Success Metrics

### Track 1.1 Success
- ✅ All 5 meta-commands work through dispatcher
- ✅ New command added without touching core code
- ✅ Pipe semantics functional
- ✅ Zero test regressions
- ✅ <100ms command dispatch overhead

### Track 1.2 Success
- ✅ Zero commands lost during offline periods
- ✅ Auto-sync within 30s of connection restore
- ✅ Prompt clearly shows offline state
- ✅ Queue survives crashes/restarts
- ✅ <10MB database for 1000+ queued commands

---

## What Comes After Track 1

### Track 2: Cloud Hub Refinements
Once local resilience is solid, enhance the cloud backend:
- **Track 2.1:** Job lifecycle state machine (queued → running → done)
- **Track 2.2:** Search API upgrade (full-text history search)
- **Track 2.3:** Event bus layer (pub/sub for notifications)

### Track 3: Agent Enhancements
With plugin foundation in place, add intelligence:
- **Track 3.1:** Configurable modules (agent capabilities)
- **Track 3.2:** Plugin hot-reloading (watch `command.yaml`)
- **Track 3.3:** Resource monitoring (CPU, memory, network tracking)

---

## Risk Mitigation

### Track 1.1 Risks
**Risk:** Dispatcher adds latency to commands  
**Mitigation:** Cache loaded manifests, benchmark <100ms overhead

**Risk:** Breaking existing functionality  
**Mitigation:** Comprehensive regression test suite, parallel implementation

**Risk:** Complex manifest syntax confuses users  
**Mitigation:** Clear examples in COMMAND_BRAINSTORM.md, validation errors with hints

### Track 1.2 Risks
**Risk:** Queue grows unbounded during long offline periods  
**Mitigation:** Config-based size limits, warning at >100 pending

**Risk:** Sync worker consumes too much CPU/network  
**Mitigation:** Exponential backoff, batch size limits, configurable intervals

**Risk:** Database corruption loses queued commands  
**Mitigation:** SQLite WAL mode, automatic corruption detection + rebuild

---

## Documentation Updates Needed

### After Track 1.1
- Update `COMMAND_PATTERNS.md` with pipe examples
- Update `copilot-instructions.md` with plugin architecture
- Create `docs/ADDING_COMMANDS.md` developer guide

### After Track 1.2
- Update `ISAAC_FINAL_DESIGN.md` with queue architecture
- Update `ISAAC_UI_SPECIFICATION.md` with offline indicators
- Create `docs/OFFLINE_MODE.md` user guide

---

## Handoff Notes

### For Implementation Agents
Both specs are ready for implementation:
- **Dispatcher Spec:** `.claude/mail/to_implement/unified_dispatcher_spec.md`
- **Queue Spec:** `.claude/mail/to_implement/command_queue_overlay_spec.md`

Each spec includes:
- Architecture overview
- File-by-file implementation details
- Complete code examples
- Testing checklists
- Success criteria
- Step-by-step implementation order

### For Testing Agents
Test suites should be written in parallel with implementation:
- Unit tests validate individual components
- Integration tests validate end-to-end flows
- Regression tests ensure no breaking changes

### For Documentation Agents
Update bible and user docs after each phase completes:
- Track 1.1 → Plugin architecture documented
- Track 1.2 → Offline mode documented

---

## Quick Start

### To Implement Track 1.1 (Dispatcher)
```bash
# Read the spec
cat .claude/mail/to_implement/unified_dispatcher_spec.md

# Create runtime directory
mkdir -p isaac/runtime

# Follow implementation order in spec
# Step 1: manifest_loader.py (2 hours)
# Step 2: security_enforcer.py (2 hours)
# Step 3: dispatcher.py (2 hours)
# Step 4: Migrate commands (2 hours)
```

### To Implement Track 1.2 (Queue)
```bash
# Read the spec
cat .claude/mail/to_implement/command_queue_overlay_spec.md

# Create queue directory
mkdir -p isaac/queue

# Follow implementation order in spec
# Step 1: command_queue.py (2 hours)
# Step 2: sync_worker.py (2 hours)
# Step 3: Integration (2 hours)
```

---

## Questions for Design Review

Before starting implementation, consider:

1. **Manifest Schema:** Is the YAML format intuitive enough? Should we add more validation?
2. **Security Model:** Are timeouts/caps sufficient? Need sandboxing (chroot/containers)?
3. **Queue Behavior:** Should users see notifications for each synced command, or batch summary?
4. **Error Handling:** How should dispatcher report manifest validation errors to users?
5. **Performance:** Is SQLite adequate for queue, or should we consider in-memory queue with periodic flush?

---

**Status:** ✅ Fully specified, ready for implementation  
**Next Action:** Hand off to YAML Maker or Implement persona  
**Expected Completion:** 2 weeks (with testing and polish)

---

**See Also:**
- `.claude/bible/COMMAND_PLUGIN_SPEC.md` - Plugin architecture specification
- `.claude/bible/COMMAND_BRAINSTORM.md` - Full command catalog
- `.claude/bible/COMMAND_SYSTEM_OVERVIEW.md` - Command system navigation
- `.github/copilot-instructions.md` - Next-Phase Design Roadmap (source material)
