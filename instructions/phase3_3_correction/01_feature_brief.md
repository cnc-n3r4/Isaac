# Feature Brief: Auto-Correction

## Objective
Enable AI-powered typo correction for Tier 2 and 2.5 commands to improve user experience.

---

## Problem Statement

**Current State:**
- Tier 2: Commands execute as-is (no correction)
- Tier 2.5: Commands show confirmation but no correction
- Users waste time fixing typos manually

**Issues:**
- "grp file.txt" → command not found error
- "cd /tm" → directory doesn't exist
- User must retype entire command

---

## Solution

Add AI correction that:
1. **Tier 2:** Auto-correct + execute (seamless)
2. **Tier 2.5:** Correct + confirm (show before executing)
3. Only correct with high confidence (>0.8)
4. Fall back to original if low confidence

---

## Requirements

### Functional Requirements
- [ ] Tier 2: Auto-correct typos and execute silently
- [ ] Tier 2.5: Show correction, ask confirmation
- [ ] High confidence threshold: 0.8
- [ ] Preserve original command in logs
- [ ] Graceful degradation if AI disabled

### Visual Requirements

**Tier 2 (Auto-correct):**
```
User Input:
> grp pattern file.txt

Isaac Output:
Isaac > Auto-correcting: grp → grep
[... grep output ...]
```

**Tier 2.5 (Correct + Confirm):**
```
User Input:
> find -nam test.txt

Isaac Output:
Corrected: find -name test.txt
Original: find -nam test.txt
Execute corrected version? (y/n): y
[... find output ...]
```

---

## Technical Details

**Files to Create:**
- `isaac/ai/corrector.py` - Correction logic

**Files to Modify:**
- `isaac/core/command_router.py` - Tier 2 section (lines 64-68)
- `isaac/core/command_router.py` - Tier 2.5 section (lines 70-81)

---

## Architecture Context

**Current Tier 2 Flow:**
```
User Command → Tier 2 → Execute
```

**New Tier 2 Flow:**
```
User Command → Tier 2 → correct_command() → 
If confidence > 0.8: Execute corrected
Else: Execute original
```

**Current Tier 2.5 Flow:**
```
User Command → Tier 2.5 → Confirm → Execute
```

**New Tier 2.5 Flow:**
```
User Command → Tier 2.5 → correct_command() → 
Show correction → Confirm → Execute corrected
```

---

## Data Structures

### Correction Result
```python
{
    'corrected': 'grep pattern file.txt',  # or None if no typo
    'original': 'grp pattern file.txt',
    'confidence': 0.95
}
```

---

## Out of Scope

❌ Not changing:
- Tier 1, 3, 4 behavior (no correction)
- Command execution logic
- Tier validation

❌ Not adding:
- Learning from corrections (Phase 3.6 feature)
- Multi-typo detection (one pass only)
- User-specific correction preferences

---

## Success Criteria

✅ **Must Pass:**
- `grp file` → auto-corrects to `grep file` (Tier 2)
- `find -nam test` → suggests `find -name test`, confirms (Tier 2.5)
- Low confidence → executes original
- AI disabled → executes without correction
- Original command logged (audit trail)

---

## Risk Assessment

**Risk:** Incorrect correction executed  
**Level:** LOW  
**Mitigation:** High confidence threshold (0.8). Tier 2.5 shows correction.

**Risk:** AI unavailable  
**Level:** LOW  
**Mitigation:** Falls back to executing original command.

---

**END OF FEATURE BRIEF**
