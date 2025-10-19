# Test Instructions: AI Validation

## Goal
Verify Tier 3 AI validation displays warnings and suggestions before execution.

**Time Estimate:** 10 minutes

---

## Prerequisites

**1. Phase 3.1 complete** (ClaudeClient.validate_command() working)
**2. API key set** in `~/.isaac/config.json`

---

## Manual Tests

### Test 1: Force Push (Git)

```bash
python -m isaac

> git push -f origin main
```

**Expected Output:**
```
============================================================
🤖 AI VALIDATION
============================================================
Command: git push -f origin main
Safe: ⚠️  Use with caution

⚠️  Warnings:
  - Force push overwrites remote history
  - [... more warnings ...]

💡 Suggestions:
  - Use git push without -f
  - [... more suggestions ...]
============================================================

Proceed with execution? (y/n):
```

✅ **Pass if:** Validation shows warnings about force push

---

### Test 2: Recursive Delete

```bash
> rm -rf /tmp/test
```

**Expected Output:**
```
============================================================
🤖 AI VALIDATION
============================================================
Command: rm -rf /tmp/test
Safe: ⚠️  Use with caution

⚠️  Warnings:
  - Recursive delete is irreversible
  - Will delete all files in /tmp/test
  - [... more warnings ...]

💡 Suggestions:
  - Review files first with ls -R /tmp/test
  - [... more suggestions ...]
============================================================

Proceed with execution? (y/n):
```

✅ **Pass if:** Shows warnings about recursive delete

---

### Test 3: Safe Command

```bash
> cp file.txt backup.txt
```

**Expected Output:**
```
============================================================
🤖 AI VALIDATION
============================================================
Command: cp file.txt backup.txt
Safe: ✅ Yes

💡 Suggestions:
  - Consider using -i flag for interactive mode
============================================================

Proceed with execution? (y/n):
```

✅ **Pass if:** Marked as safe, minimal warnings

---

### Test 4: User Proceeds

```bash
> rm test.txt
```

**Input:** y (proceed)

**Expected:**
```
[... rm executes ...]
```

✅ **Pass if:** Command executes after confirmation

---

### Test 5: User Aborts

```bash
> rm test.txt
```

**Input:** n (abort)

**Expected Output:**
```
Isaac > Aborted.
```

✅ **Pass if:** No execution, clean abort

---

### Test 6: AI Disabled

Edit `~/.isaac/config.json`:
```json
{
  "ai_enabled": false
}
```

```bash
> rm test.txt
```

**Expected Output:**
```
============================================================
🤖 AI VALIDATION
============================================================
Command: rm test.txt
Safe: ✅ Yes

⚠️  Warnings:
  - AI validation unavailable

============================================================

Proceed with execution? (y/n):
```

✅ **Pass if:** Shows fallback message, still confirms

---

### Test 7: Critical Command

```bash
> dd if=/dev/zero of=/dev/sda
```

**Expected Output:**
```
============================================================
🤖 AI VALIDATION
============================================================
Command: dd if=/dev/zero of=/dev/sda
Safe: ❌ No

⚠️  Warnings:
  - CRITICAL: Will erase entire disk
  - All data will be permanently lost
  - System may become unbootable
  - [... more critical warnings ...]

💡 Suggestions:
  - DO NOT run this command unless you're absolutely sure
  - Verify disk path with lsblk first
  - Use a test disk or VM
============================================================

Proceed with execution? (y/n):
```

✅ **Pass if:** Critical warnings prominently displayed

---

## Success Criteria

**All tests must pass:**
- [ ] Force push shows warnings
- [ ] Recursive delete shows warnings
- [ ] Safe commands marked as safe
- [ ] User can proceed after validation
- [ ] User can abort after validation
- [ ] AI disabled shows fallback message
- [ ] Critical commands have prominent warnings

---

## Troubleshooting

**Issue:** No validation box shown  
**Solution:** Check Tier 3 code in command_router.py, verify validator imported

**Issue:** Empty warnings/suggestions  
**Solution:** Check Claude API response, verify prompt formatting

**Issue:** Crash on API error  
**Solution:** Verify validator.py handles exceptions gracefully

**Issue:** User can't proceed  
**Solution:** Check confirmation prompt logic, ensure it's after validation

---

**END OF TEST INSTRUCTIONS**
