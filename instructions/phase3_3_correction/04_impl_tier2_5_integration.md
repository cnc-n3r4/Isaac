# Implementation: Tier 2.5 Correction + Confirmation

## Goal
Modify command_router.py Tier 2.5 section to correct and confirm before executing.

**Time Estimate:** 15 minutes

---

## File to Modify

**Path:** `isaac/core/command_router.py`

**Lines to change:** 70-81 (Tier 2.5 section)

---

## Current Code (Lines 70-81)

**FIND THIS:**
```python
# Tier 2.5: Correct + confirm (MVP: just confirm, AI in Phase 2)
elif tier == 2.5:
    # Future: AI correction, then confirm
    # For MVP: just confirm
    confirmed = self._confirm(f"Execute: {input_text}?")
    if confirmed:
        return self.shell.execute(input_text)
    else:
        return CommandResult(
            success=False,
            output="Isaac > Aborted.",
            exit_code=-1
        )
```

---

## New Code

**REPLACE WITH:**
```python
# Tier 2.5: Correct + confirm
elif tier == 2.5:
    from isaac.ai.corrector import correct_command
    
    # Try correction
    correction = correct_command(input_text, self.shell.name, self.session.config)
    
    if correction['corrected'] and correction['confidence'] > 0.7:
        # Show correction, ask for confirmation
        print("\n" + "=" * 60)
        print(f"Corrected: {correction['corrected']}")
        print(f"Original: {correction['original']}")
        print(f"Confidence: {correction['confidence']:.0%}")
        print("=" * 60 + "\n")
        
        confirmed = self._confirm("Execute corrected version?")
        if confirmed:
            return self.shell.execute(correction['corrected'])
    else:
        # No correction needed or low confidence - just confirm original
        confirmed = self._confirm(f"Execute: {input_text}?")
        if confirmed:
            return self.shell.execute(input_text)
    
    # User aborted
    return CommandResult(
        success=False,
        output="Isaac > Aborted.",
        exit_code=-1
    )
```

---

## Key Differences from Tier 2

**Confidence Threshold:** 0.7 (lower than Tier 2)
- Tier 2: 0.8 (auto-executes, needs high confidence)
- Tier 2.5: 0.7 (user confirms, can be more lenient)

**User Interaction:**
- Always shows correction details
- User decides whether to use corrected version
- Can abort if correction looks wrong

**Display Format:**
```
============================================================
Corrected: find -name test.txt
Original: find -nam test.txt
Confidence: 90%
============================================================

Execute corrected version? (y/n):
```

---

## Verification Steps

After modifying:

```bash
# Check syntax
python -m py_compile isaac/core/command_router.py
```

---

## Testing

**Test 1: Correction accepted**
```bash
python -m isaac

> find -nam test.txt
```

**Expected Output:**
```
============================================================
Corrected: find -name test.txt
Original: find -nam test.txt
Confidence: 95%
============================================================

Execute corrected version? (y/n): y
[... find output ...]
```

**Test 2: Correction rejected**
```bash
> find -nam test.txt
```

**Input:** n (reject)

**Expected Output:**
```
Isaac > Aborted.
```

**Test 3: No correction**
```bash
> rm temp.txt
```

**Expected Output:**
```
Execute: rm temp.txt? (y/n): y
[... rm output ...]
```

---

## Common Pitfalls

⚠️ **Pitfall 1: Not showing correction details**
- Symptom: User doesn't understand what changed
- Fix: Always print correction box

⚠️ **Pitfall 2: Wrong confidence threshold**
- Symptom: Too many or too few corrections
- Fix: Use 0.7 (70%) for Tier 2.5

⚠️ **Pitfall 3: Executing wrong command**
- Symptom: Original executed when corrected chosen
- Fix: Check which branch executed: corrected vs original

---

**END OF IMPLEMENTATION**
