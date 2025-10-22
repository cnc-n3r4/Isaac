# Track 1: Quick Start Guide

**Status:** ✅ Fully specified, ready for implementation  
**Time:** 7-10 hours total (Track 1.1: 4-6h, Track 1.2: 3-4h)

---

## What Is Track 1?

**Transform Isaac from hardcoded commands → fully extensible plugin system with offline resilience**

### Track 1.1: Unified Dispatcher (Plugin System)
- Add commands by dropping YAML manifest + script
- Automatic validation, security, pipe semantics
- Device routing (`!alias`)

### Track 1.2: Command Queue Overlay (Offline Resilience)
- Commands never lost when cloud unavailable
- Auto-sync when connection returns
- SQLite persistence, background worker

---

## Documentation Structure

```
.claude/bible/
├── TRACK1_LOCAL_QOL.md              # Master document (read this first)
│
.claude/mail/to_implement/
├── unified_dispatcher_spec.md        # Track 1.1 implementation spec
└── command_queue_overlay_spec.md     # Track 1.2 implementation spec
│
.claude/status/
└── TRACK1_SPECIFICATION_COMPLETE.md  # Completion report
```

---

## Quick Links

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **TRACK1_LOCAL_QOL.md** | High-level vision, roadmap, timeline | Planning phase |
| **unified_dispatcher_spec.md** | Step-by-step Track 1.1 implementation | Building dispatcher |
| **command_queue_overlay_spec.md** | Step-by-step Track 1.2 implementation | Building queue |
| **TRACK1_SPECIFICATION_COMPLETE.md** | Summary, decisions, risks | Status check |

---

## Implementation Order (MUST FOLLOW)

### ✅ Prerequisites (COMPLETE)
- Meta-commands Phase 2 implemented
- `/help`, `/status`, `/config` working
- SessionManager, CloudClient functional

### 🎯 Track 1.1: Unified Dispatcher (4-6 hours)
**Spec:** `.claude/mail/to_implement/unified_dispatcher_spec.md`

**Step 1:** Foundation (2 hours)
```bash
mkdir -p isaac/runtime
# Create manifest_loader.py with JSON Schema validation
# Create security_enforcer.py with timeouts + caps
# Write unit tests
```

**Step 2:** Core Dispatcher (2 hours)
```bash
# Create dispatcher.py main class
# Add command loading, trigger resolution, arg parsing
# Write unit tests
```

**Step 3:** Migration (1 hour)
```bash
# Convert 5 commands to YAML manifests
# /help, /status, /config, /list, /backup
```

**Step 4:** Integration (1 hour)
```bash
# Update command_router.py to use dispatcher
# Run full test suite
# Fix any regressions
```

### 🎯 Track 1.2: Command Queue Overlay (3-4 hours)
**Spec:** `.claude/mail/to_implement/command_queue_overlay_spec.md`

**Step 1:** Database (2 hours)
```bash
mkdir -p isaac/queue
# Create command_queue.py with SQLite schema
# Write unit tests
```

**Step 2:** Sync Worker (2 hours)
```bash
# Create sync_worker.py background thread
# Add exponential backoff logic
# Test offline/online cycles
```

**Step 3:** Integration (1 hour)
```bash
# Update SessionManager to initialize queue
# Update CommandRouter to queue on cloud failure
# Update prompt for offline indicator
```

**Step 4:** Polish (30 min)
```bash
# Add /queue and /sync meta-commands
# Test graceful shutdown
```

---

## Success Criteria

### Track 1.1 Success Checklist
- [ ] All 5 meta-commands work through dispatcher (no behavior changes)
- [ ] New command can be added without editing core code
- [ ] Pipe works: `/history | /grep docker`
- [ ] All existing tests pass (zero regressions)
- [ ] Command dispatch overhead <100ms

### Track 1.2 Success Checklist
- [ ] Commands queued when cloud unavailable
- [ ] Auto-sync within 30s of connection restore
- [ ] Prompt shows: `isaac [OFFLINE: 2 queued]>`
- [ ] Queue survives process restarts
- [ ] Database <10MB for 1000+ queued commands

---

## Testing Strategy

### Track 1.1 Tests
```bash
# Unit tests
pytest tests/test_manifest_loader.py -v
pytest tests/test_security_enforcer.py -v
pytest tests/test_dispatcher.py -v

# Integration tests
pytest tests/test_dispatcher_integration.py -v

# Regression tests (all existing tests must pass)
pytest tests/ --cov=isaac --cov-report=term
```

### Track 1.2 Tests
```bash
# Unit tests
pytest tests/test_command_queue.py -v
pytest tests/test_sync_worker.py -v

# Integration tests
pytest tests/test_queue_integration.py -v

# Stress tests
pytest tests/test_queue_stress.py -v
```

---

## Example: Adding New Command (After Track 1.1)

### 1. Create manifest (`isaac/commands/grep/command.yaml`)
```yaml
name: grep
version: 1.0.0
summary: "Search text via regex"
triggers: ["/grep"]
args:
  - { name: pattern, type: string, required: true }
stdin: true
stdout: { type: text }
security:
  scope: user
  allow_remote: true
  resources: { timeout_ms: 15000, max_stdout_kib: 256 }
runtime:
  entry: "run.py"
  interpreter: "python"
```

### 2. Create handler (`isaac/commands/grep/run.py`)
```python
import sys, json, re

def main():
    payload = json.loads(sys.stdin.read())
    pattern = payload["args"]["pattern"]
    stdin_data = payload.get("stdin", "")
    
    matches = [line for line in stdin_data.split('\n') 
               if re.search(pattern, line)]
    
    print(json.dumps({
        "ok": True,
        "kind": "text",
        "stdout": '\n'.join(matches),
        "meta": {}
    }))

if __name__ == "__main__":
    main()
```

### 3. Test
```bash
# Restart Isaac (or use hot-reload in Track 3.2)
isaac /start

# Test standalone
/grep "ERROR" 

# Test with pipe
/history | /grep "docker"
```

**That's it! No core code changes needed.**

---

## Common Issues & Solutions

### Issue 1: "Command not found after adding manifest"
**Solution:** Restart Isaac or implement hot-reload (Track 3.2)

### Issue 2: "Timeout too short for command"
**Solution:** Increase `security.resources.timeout_ms` in manifest

### Issue 3: "Queue not syncing"
**Solution:** Check CloudClient.is_available(), verify sync_worker running

### Issue 4: "Pipe not working"
**Solution:** Ensure target command has `stdin: true` in manifest

---

## Timeline Estimates

### Optimistic (Solo, No Blocks)
- Week 1: Track 1.1 (6 hours)
- Week 2: Track 1.2 (4 hours)
- **Total:** 10 hours

### Realistic (With Reviews)
- Week 1: Track 1.1 (8 hours)
- Week 2: Track 1.2 (6 hours)
- Week 3: Polish + docs (4 hours)
- **Total:** 18 hours

### Conservative (With Issues)
- Week 1-2: Track 1.1 (12 hours)
- Week 3-4: Track 1.2 (8 hours)
- Week 5: Polish (4 hours)
- **Total:** 24 hours

**Plan for realistic: 3 weeks, 18 hours**

---

## What Comes After Track 1?

### Track 2: Cloud Hub Refinements
- Job lifecycle state machine
- Search API upgrade (full-text history)
- Event bus layer (pub/sub)

### Track 3: Agent Enhancements
- Configurable modules
- Plugin hot-reloading
- Resource monitoring

### Extended Commands
Implement commands from COMMAND_BRAINSTORM.md:
- Task & Note Management
- Communication & Device Routing
- AI and Knowledge

---

## Need Help?

### For Architecture Questions
→ Read `.claude/bible/TRACK1_LOCAL_QOL.md` (master document)

### For Implementation Details
→ Read spec in `.claude/mail/to_implement/`

### For Command Examples
→ Read `.claude/bible/COMMAND_PLUGIN_SPEC.md` Section 5

### For Testing Guidance
→ Read spec section "Testing Checklist"

---

## Ready to Start?

### Step 1: Read the Master Plan
```bash
cat .claude/bible/TRACK1_LOCAL_QOL.md
```

### Step 2: Read Track 1.1 Spec
```bash
cat .claude/mail/to_implement/unified_dispatcher_spec.md
```

### Step 3: Create Runtime Directory
```bash
mkdir -p isaac/runtime
```

### Step 4: Follow Implementation Order
See unified_dispatcher_spec.md for step-by-step instructions.

---

## Key Reminders

1. ✅ **Track 1.1 MUST come before Track 1.2** (queue needs dispatcher)
2. ✅ **Test after each step** (unit → integration → regression)
3. ✅ **No regressions allowed** (all existing tests must pass)
4. ✅ **Follow specs exactly** (they're battle-tested)
5. ✅ **Update docs after completion** (keep bible current)

---

**Last Updated:** 2025-10-21  
**Status:** Ready for handoff to implementation agents  
**Next Action:** Read unified_dispatcher_spec.md and start coding! 🚀
