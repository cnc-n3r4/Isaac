# Implementation: Tier 2 Auto-Correction

## Goal
Modify command_router.py Tier 2 section to auto-correct and execute.

**Time Estimate:** 15 minutes

---

## File to Modify

**Path:** `isaac/core/command_router.py`

**Lines to change:** 64-68 (Tier 2 section)

---

## Current Code (Lines 64-68)

**FIND THIS:**
```python
# Tier 2: Auto-correct typos (MVP: just execute, AI in Phase 2)
elif tier == 2:
    # Future: AI auto-correction
    # For MVP: just execute
    return self.shell.execute(input_text)
```

---

## New Code

**REPLACE WITH:**
```python
# Tier 2: Auto-correct typos and execute
elif tier == 2:
    from isaac.ai.corrector import correct_command
    
    # Try auto-correction
    correction = correct_command(input_text, self.shell.name, self.session.config)
    
    if correction['corrected'] and correction['confidence'] > 0.8:
        # High confidence typo detected - auto-correct
        print(f"Isaac > Auto-correcting: {correction['original']} → {correction['corrected']}")
        return self.shell.execute(correction['corrected'])
    else:
        # No typo or low confidence - execute as-is
        return self.shell.execute(input_text)
```

---

## Key Points

**Confidence Threshold:** 0.8
- Above: Auto-correct and execute
- Below: Execute original (don't risk wrong correction)

**User Feedback:**
- Always show correction message when auto-correcting
- Silent execution if no typo

**Safety:**
- Tier 2 commands are safe (read-only or minor writes)
- Auto-correction acceptable for this tier

---

## Verification Steps

After modifying:

```bash
# Check syntax
python -m py_compile isaac/core/command_router.py
```

---

## Testing

**Test 1: High confidence correction**
```bash
python -m isaac

> grp pattern file.txt
```

**Expected Output:**
```
Isaac > Auto-correcting: grp pattern file.txt → grep pattern file.txt
[... grep output ...]
```

**Test 2: No typo**
```bash
> ls -la
```

**Expected Output:**
```
[... ls output without correction message ...]
```

**Test 3: Low confidence**
```bash
> som ambiguous command
```

**Expected Output:**
```
[... executes as-is, or command not found error ...]
```

---

## Common Pitfalls

⚠️ **Pitfall 1: Not showing correction**
- Symptom: User confused why different command ran
- Fix: Always print correction message

⚠️ **Pitfall 2: Wrong confidence threshold**
- Symptom: Bad corrections executed
- Fix: Use 0.8 (80%) as minimum

⚠️ **Pitfall 3: Crash on API error**
- Symptom: Isaac crashes if network down
- Fix: correct_command() handles errors, returns no-correction

---

**END OF IMPLEMENTATION**
