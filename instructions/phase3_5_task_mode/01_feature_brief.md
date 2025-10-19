# Feature Brief: Task Mode

## Objective
Enable multi-step task automation via "isaac task: [description]" with AI planning, execution modes, and failure recovery.

---

## Problem Statement

**Current State:**
- Users execute commands one at a time
- Complex tasks require multiple manual steps
- No automation for workflows

**Issues:**
- Time-consuming repetitive tasks
- Easy to miss steps in complex workflows
- No recovery mechanism for failures

---

## Solution

Add task mode that:
1. Detects "isaac task:" prefix
2. AI plans multi-step execution
3. Shows plan to user
4. Offers 3 execution modes
5. Executes with tier validation per step
6. Handles failures with 5 recovery options
7. Logs immutable task history

---

## Requirements

### Functional Requirements
- [ ] Parse "isaac task: [description]"
- [ ] AI generates step-by-step plan
- [ ] Display plan with estimated duration and risks
- [ ] Offer 3 execution modes:
  - Autonomous (run all)
  - Approve-once (confirm plan, then run)
  - Step-by-step (confirm each step)
- [ ] Execute steps through tier system
- [ ] Handle failures with 5 recovery options
- [ ] Log task history immutably

### Visual Requirements

**Task Plan Display:**
```
============================================================
🤖 TASK PLAN
============================================================
Task: backup my home folder

Steps:
  1. [Tier 1] cd ~
  2. [Tier 2] tar -czf backup_$(date +%Y%m%d).tar.gz .
  3. [Tier 1] ls -lh backup_*.tar.gz

Estimated Duration: 5-10 minutes
Risks: Large file transfer, disk space needed

Execution Modes:
  1. Autonomous - Run all steps automatically
  2. Approve-once - Confirm plan, then run
  3. Step-by-step - Confirm each step
  
Choose mode (1/2/3):
============================================================
```

**Failure Recovery:**
```
Step 2 FAILED: tar command error

Recovery Options:
  1. Auto-fix - Let AI suggest and apply fix
  2. Retry - Run same command again
  3. Skip - Continue to next step
  4. Abort - Stop task execution
  5. Suggest - AI suggests alternatives, you choose
  
Choose recovery (1/2/3/4/5):
```

---

## Technical Details

**Files to Create:**
- `isaac/models/task_history.py` - Immutable task logging
- `isaac/ai/task_planner.py` - Planning + execution

**Files to Modify:**
- `isaac/core/command_router.py` - Detect "isaac task:"

---

## Architecture Context

**Task Flow:**
```
"isaac task: [desc]" → plan_task() → AI generates steps →
Show plan → User chooses mode → Execute steps (with tier checks) →
On failure: Recovery options → Continue or abort →
Log to TaskHistory (immutable)
```

**CRITICAL:** Each step goes through `route_command()` for tier validation.

---

## Data Structures

### Task Plan
```python
{
    'task_id': 'task_20251019_123456',
    'description': 'backup my home folder',
    'steps': [
        {'command': 'cd ~', 'tier': 1, 'description': 'Navigate to home'},
        {'command': 'tar -czf ...', 'tier': 2, 'description': 'Create archive'},
        {'command': 'ls -lh ...', 'tier': 1, 'description': 'Verify backup'}
    ],
    'estimated_duration': '5-10 minutes',
    'risks': ['Large file transfer', 'Disk space needed']
}
```

### Task History Entry
```python
{
    'task_id': 'task_20251019_123456',
    'timestamp': 1697654321.0,
    'description': 'backup my home folder',
    'mode': 'approve-once',
    'steps': [
        {'step': 1, 'command': 'cd ~', 'status': 'success', 'output': '...'},
        {'step': 2, 'command': 'tar ...', 'status': 'failed', 'error': '...'},
        {'step': 2, 'command': 'tar ...', 'status': 'success', 'output': '...', 'recovery': 'retry'}
    ],
    'status': 'completed',
    'machine_id': 'machine-abc123'
}
```

---

## Out of Scope

❌ Not changing:
- Tier validation rules
- Shell execution
- Command history (separate from task history)

❌ Not adding (Phase 3.6):
- Learning from task failures
- Cross-platform task translation
- Rollback/undo functionality

---

## Success Criteria

✅ **Must Pass:**
- `isaac task: backup /home` → shows multi-step plan
- User selects autonomous mode → executes all steps
- Step fails → shows 5 recovery options
- Retry recovery → re-runs failed step
- Abort recovery → stops task, logs partial completion
- Task history logged immutably (append-only)
- AI disabled → shows error, no crash

---

## Risk Assessment

**Risk:** Task leaves system in inconsistent state  
**Level:** MEDIUM  
**Mitigation:** Immutable task history for audit. Recovery options for failures. Each step validates through tiers.

**Risk:** AI plans incorrect steps  
**Level:** MEDIUM  
**Mitigation:** User reviews plan before execution. Can choose step-by-step mode.

**Risk:** Runaway automation  
**Level:** LOW  
**Mitigation:** User controls mode. Can abort at any time. Tier validation per step.

---

**END OF FEATURE BRIEF**
