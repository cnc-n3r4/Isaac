# Test Instructions: Auto-Correction

## Goal
Verify Tier 2 auto-correction and Tier 2.5 correction + confirmation work correctly.

**Time Estimate:** 10 minutes

---

## Prerequisites

**1. Phase 3.1 complete** (ClaudeClient.correct_typo() working)
**2. API key set** in `~/.isaac/config.json`
**3. Auto-correction enabled:**
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-...",
  "auto_correct_tier2": true
}
```

---

## Manual Tests

### Test 1: Tier 2 Auto-Correction (High Confidence)

```bash
python -m isaac

> grp pattern file.txt
```

**Expected Output:**
```
Isaac > Auto-correcting: grp pattern file.txt → grep pattern file.txt
[... grep output or error if file doesn't exist ...]
```

✅ **Pass if:** Auto-corrects and executes without confirmation

---

### Test 2: Tier 2 No Typo

```bash
> ls -la
```

**Expected Output:**
```
[... ls output without correction message ...]
```

✅ **Pass if:** Executes directly, no correction message

---

### Test 3: Tier 2.5 Correction + Confirm (Accept)

```bash
> find -nam test.txt
```

**Expected Output:**
```
============================================================
Corrected: find -name test.txt
Original: find -nam test.txt
Confidence: 95%
============================================================

Execute corrected version? (y/n): 
```

**Input:** y

**Expected:**
```
[... find output ...]
```

✅ **Pass if:** Shows correction, executes corrected version

---

### Test 4: Tier 2.5 Correction + Confirm (Reject)

```bash
> find -nam test.txt
```

**Input:** n

**Expected Output:**
```
Isaac > Aborted.
```

✅ **Pass if:** Aborts, no execution

---

### Test 5: Tier 2.5 No Correction

```bash
> rm temp.txt
```

**Expected Output:**
```
Execute: rm temp.txt? (y/n): 
```

**Input:** y

**Expected:**
```
[... rm output ...]
```

✅ **Pass if:** Confirms without showing correction (no typo)

---

### Test 6: AI Disabled

Edit `~/.isaac/config.json`:
```json
{
  "ai_enabled": false
}
```

```bash
> grp pattern file.txt
```

**Expected Output:**
```
bash: grp: command not found
```

✅ **Pass if:** Executes without correction (falls back to no AI)

---

### Test 7: Auto-Correction Disabled

Edit `~/.isaac/config.json`:
```json
{
  "ai_enabled": true,
  "auto_correct_tier2": false
}
```

```bash
> grp pattern file.txt
```

**Expected Output:**
```
bash: grp: command not found
```

✅ **Pass if:** No correction when disabled

---

### Test 8: Low Confidence (Tier 2)

```bash
# Try ambiguous typo
> som weird command
```

**Expected Output:**
```
bash: som: command not found
```

✅ **Pass if:** Executes as-is (confidence too low)

---

## Success Criteria

**All tests must pass:**
- [ ] Tier 2 auto-corrects high confidence typos
- [ ] Tier 2 executes no-typo commands directly
- [ ] Tier 2.5 shows correction and confirms
- [ ] Tier 2.5 allows rejecting correction
- [ ] Tier 2.5 confirms original if no typo
- [ ] AI disabled → no correction, no crash
- [ ] auto_correct_tier2 disabled → no correction
- [ ] Low confidence → execute original

---

## Troubleshooting

**Issue:** No auto-correction happening  
**Solution:** Check ai_enabled and auto_correct_tier2 in config

**Issue:** Corrections always rejected  
**Solution:** Check confidence threshold (0.8 for Tier 2, 0.7 for 2.5)

**Issue:** Crash on API error  
**Solution:** Verify corrector.py handles exceptions gracefully

**Issue:** Wrong command executed  
**Solution:** Check which branch (corrected vs original) is executed

---

**END OF TEST INSTRUCTIONS**
