# Feature Brief: AI Validation

## Objective
Provide AI-powered safety analysis for Tier 3 commands before execution.

---

## Problem Statement

**Current State:**
- Tier 3: Simple confirmation prompt
- No analysis of command impact
- User must assess safety manually

**Issues:**
- "rm *.log" → How many files will be deleted?
- "git push -f" → What are the risks?
- User needs context to make informed decision

---

## Solution

Add AI validation that:
1. Analyzes Tier 3 command for safety
2. Identifies potential warnings
3. Suggests safer alternatives
4. Displays results prominently
5. User confirms after seeing analysis

---

## Requirements

### Functional Requirements
- [ ] Validate Tier 3 commands with AI
- [ ] Display warnings prominently
- [ ] Show suggestions for safer alternatives
- [ ] User confirms after validation
- [ ] Graceful degradation if AI unavailable

### Visual Requirements

**Validation Display:**
```
============================================================
🤖 AI VALIDATION
============================================================
Command: rm *.log
Safe: ⚠️  Use with caution

⚠️  Warnings:
  - Will delete all .log files in current directory
  - Action is irreversible
  - Could delete important logs

💡 Suggestions:
  - Use 'rm -i *.log' for interactive confirmation
  - Review files first with 'ls *.log'
  - Consider moving to trash instead of deleting
============================================================

Proceed with execution? (y/n):
```

---

## Technical Details

**Files to Create:**
- `isaac/ai/validator.py` - Validation logic

**Files to Modify:**
- `isaac/core/command_router.py` - Tier 3 section (lines 83-93)

---

## Architecture Context

**Current Tier 3 Flow:**
```
User Command → Tier 3 → Simple Confirm → Execute
```

**New Tier 3 Flow:**
```
User Command → Tier 3 → validate_command() → 
Display Results → Confirm → Execute
```

---

## Data Structures

### Validation Result
```python
{
    'safe': False,  # True/False/Warning
    'warnings': [
        'Will delete all files',
        'Action is irreversible'
    ],
    'suggestions': [
        'Use rm -i for interactive mode',
        'Review files first'
    ]
}
```

---

## Out of Scope

❌ Not changing:
- Tier 1, 2, 2.5, 4 behavior
- Actual command execution
- Tier system rules

❌ Not adding:
- Automatic blocking (user always decides)
- Learning from past validations
- Context-aware validation (file system state)

---

## Success Criteria

✅ **Must Pass:**
- `git push -f` → warns about force push
- `rm -rf /` → critical warnings shown
- `dd if=/dev/zero of=/dev/sda` → warnings about data loss
- AI unavailable → simple confirmation fallback
- User can proceed despite warnings

---

## Risk Assessment

**Risk:** User ignores warnings  
**Level:** LOW (already present in MVP)  
**Mitigation:** Make warnings prominent and clear.

**Risk:** AI gives incorrect advice  
**Level:** MEDIUM  
**Mitigation:** Validation is advisory only. User has final say.

**Risk:** AI unavailable  
**Level:** LOW  
**Mitigation:** Falls back to simple confirmation.

---

**END OF FEATURE BRIEF**
