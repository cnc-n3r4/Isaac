# Test Instructions: Task Mode

## Goal
Verify task mode works correctly with multi-step execution and failure recovery.

**Time Estimate:** 30 minutes

---

## Prerequisites

**Requirements:**
- Phase 3.1 complete (ClaudeClient working)
- Phase 3.5 complete (task_planner.py and task_history.py)
- Claude API key configured
- Task mode enabled in config

**Config check** (`~/.isaac/config.json`):
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-YOUR_KEY_HERE",
  "task_mode_enabled": true
}
```

---

## Manual Test 1: Simple Task (Autonomous Mode)

**Test:** Simple 3-step backup task

```bash
isaac task: create a test backup of my current folder
```

**Expected Flow:**
1. Isaac shows task plan (3-4 steps)
2. Ask for execution mode
3. Select: 1 (Autonomous)
4. All steps execute without confirmation
5. Task completes successfully

**Expected Output:**
```
Isaac > Planning task: create a test backup of my current folder
Isaac > Analyzing steps...

============================================================
📋 TASK PLAN
============================================================
Task: create a test backup of my current folder
Steps: 3
Estimated Duration: 1 minute

📝 Steps:
  1. [Tier 1] ls -la
     List current folder contents
  2. [Tier 2] tar -czf backup_test.tar.gz .
     Create compressed backup
  3. [Tier 1] ls -lh backup_test.tar.gz
     Verify backup created
============================================================

Execution modes:
  1. Autonomous - Execute all steps without confirmation
  2. Approve-once - Show plan, execute if approved
  3. Step-by-step - Confirm each step individually
  4. Abort - Cancel task

Select mode [1-4]: 1

🚀 Executing task (mode: autonomous)...

Step 1/3: List current folder contents
Command: ls -la
✅ Step 1 complete

Step 2/3: Create compressed backup
Command: tar -czf backup_test.tar.gz .
✅ Step 2 complete

Step 3/3: Verify backup created
Command: ls -lh backup_test.tar.gz
-rw-r--r-- 1 user user 1.2M Oct 19 12:34 backup_test.tar.gz
✅ Step 3 complete

Isaac > Task complete: 3 steps executed
```

**Verify:**
- [ ] Task plan shown with all steps
- [ ] Autonomous mode executes without prompts
- [ ] All 3 steps complete
- [ ] backup_test.tar.gz file created
- [ ] Task logged to task_history.json

---

## Manual Test 2: Approve-Once Mode

**Test:** Task with confirmation before execution

```bash
isaac task: show system information
```

**Expected Flow:**
1. Isaac shows task plan
2. Select: 2 (Approve-once)
3. Prompt: "Execute all steps? [y/N]"
4. Type: y
5. All steps execute
6. Task completes

**Expected Output:**
```
...
Select mode [1-4]: 2

Execute all steps? [y/N]: y

🚀 Executing task (mode: approve-once)...

Step 1/2: Show OS information
Command: uname -a
✅ Step 1 complete

Step 2/2: Show disk usage
Command: df -h
✅ Step 2 complete

Isaac > Task complete: 2 steps executed
```

**Verify:**
- [ ] Approve-once asks for confirmation
- [ ] Typing 'y' proceeds with execution
- [ ] Typing 'N' aborts (test separately)
- [ ] All steps execute after approval

---

## Manual Test 3: Step-by-Step Mode

**Test:** Manual confirmation for each step

```bash
isaac task: clean up temporary files
```

**Expected Flow:**
1. Isaac shows task plan
2. Select: 3 (Step-by-step)
3. For each step:
   - Shows command
   - Prompts: "Execute step X? [y/N/abort]"
   - Type: y (or N to skip, or abort to stop)
4. Task completes

**Expected Output:**
```
...
Select mode [1-4]: 3

🚀 Executing task (mode: step-by-step)...

Step 1/3: List temp files
Command: find /tmp -name "*.tmp" -type f
Execute step 1? [y/N/abort]: y
✅ Step 1 complete

Step 2/3: Count temp files
Command: find /tmp -name "*.tmp" -type f | wc -l
Execute step 2? [y/N/abort]: y
✅ Step 2 complete

Step 3/3: Remove temp files
Command: find /tmp -name "*.tmp" -type f -delete
Execute step 3? [y/N/abort]: N
Skipped.

Isaac > Task complete: 2 steps executed, 1 skipped
```

**Verify:**
- [ ] Each step prompts for confirmation
- [ ] 'y' executes step
- [ ] 'N' skips step
- [ ] 'abort' stops task (test separately)

---

## Manual Test 4: Failure Recovery

**Test:** Simulate step failure and recovery

**Setup:** Create task that will fail

```bash
isaac task: read a file that doesn't exist
```

**Expected Flow:**
1. Isaac plans task
2. Execute mode selection
3. Step fails (file not found)
4. Recovery options shown
5. Select recovery action

**Expected Output:**
```
...
Step 1/1: Read non-existent file
Command: cat /nonexistent/file.txt
❌ Step 1 failed: cat: /nonexistent/file.txt: No such file or directory

============================================================
⚠️  STEP FAILURE - RECOVERY OPTIONS
============================================================
Step 1: Read non-existent file
Command: cat /nonexistent/file.txt
Error: cat: /nonexistent/file.txt: No such file or directory

Recovery options:
  1. Auto-fix - AI suggests fix and applies
  2. Retry - Run same command again
  3. Skip - Continue to next step
  4. Abort - Stop task execution
  5. Suggest - AI suggests alternatives (you choose)

Select recovery [1-5]: 4

Isaac > Task aborted at step 1
```

**Test Each Recovery Option:**

**Option 1 (Auto-fix):**
- Select: 1
- Expected: AI suggests fix (not yet implemented, falls back to retry)

**Option 2 (Retry):**
- Select: 2
- Expected: Same command runs again (likely fails again)

**Option 3 (Skip):**
- Select: 3
- Expected: Continues to next step (or completes if last step)

**Option 4 (Abort):**
- Select: 4
- Expected: Task stops, returns failure

**Option 5 (Suggest):**
- Select: 5
- Expected: AI suggestions (not yet implemented, falls back to skip)

**Verify:**
- [ ] Failure detected and recovery shown
- [ ] All 5 options available
- [ ] Selected option executes correctly
- [ ] Task history logs failure and recovery

---

## Manual Test 5: Task History Logging

**Test:** Verify task history saved correctly

**After running tests above, check:**

```bash
cat ~/.isaac/task_history.json
```

**Expected Structure:**
```json
{
  "tasks": [
    {
      "task_id": "task_20251019_123456",
      "description": "create a test backup of my current folder",
      "mode": "autonomous",
      "status": "success",
      "steps": [
        {
          "step_num": 1,
          "command": "ls -la",
          "status": "success",
          "output": "...",
          "timestamp": "2025-10-19T12:34:56"
        }
      ],
      "created": "2025-10-19T12:34:50",
      "completed": "2025-10-19T12:35:00"
    }
  ],
  "metadata": {
    "total_count": 1
  }
}
```

**Verify:**
- [ ] task_history.json file exists
- [ ] All executed tasks logged
- [ ] Steps include status (success/failed/skipped)
- [ ] Timestamps present
- [ ] Failed steps logged with errors

---

## Automated Tests (pytest)

**Reference:** `tests/test_ai_integration.py`

**Run task mode tests:**
```bash
pytest tests/test_ai_integration.py::test_task_mode_execution -v
pytest tests/test_ai_integration.py::test_task_mode_failure_recovery -v
pytest tests/test_ai_integration.py::test_task_history_logging -v
```

**Expected:**
```
tests/test_ai_integration.py::test_task_mode_execution PASSED
tests/test_ai_integration.py::test_task_mode_failure_recovery PASSED
tests/test_ai_integration.py::test_task_history_logging PASSED
```

---

## Success Criteria

✅ **Phase 3.5 Complete When:**
- [ ] Task planner created (~200 lines)
- [ ] TaskHistory model created (~100 lines)
- [ ] All 3 execution modes work (autonomous, approve-once, step-by-step)
- [ ] Failure recovery shows 5 options
- [ ] Task history logs all tasks and steps
- [ ] Tasks go through tier system (Tier 3+ prompts for confirmation)
- [ ] No crashes on task failure
- [ ] Task commands respect tier validation

---

## Troubleshooting

**Issue: "Task mode requires AI"**
- Check: `ai_enabled: true` in config
- Check: `claude_api_key` present

**Issue: "Task mode disabled in config"**
- Add: `"task_mode_enabled": true` to config

**Issue: "No steps generated for task"**
- Task description too vague
- Try more specific: "backup documents folder to /backup"

**Issue: Steps fail with tier confirmation**
- Expected behavior - Tier 3+ commands require validation
- User sees AI validation, must confirm

**Issue: Task history not saving**
- Check: ~/.isaac/ folder writable
- Check: No JSON syntax errors in task_history.json

---

## Next Phase

**After Phase 3.5 passes:**
- ✅ Task mode working with multi-step execution
- ✅ Failure recovery implemented
- ✅ Task history logging complete
- Optional: Phase 3.6 (Auto-fix learning)

---

**END OF TEST INSTRUCTIONS**
