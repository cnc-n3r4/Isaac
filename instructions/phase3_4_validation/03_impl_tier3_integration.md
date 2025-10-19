# Implementation: Tier 3 Validation Integration

## Goal
Modify command_router.py Tier 3 section to display AI validation before confirmation.

**Time Estimate:** 20 minutes

---

## File to Modify

**Path:** `isaac/core/command_router.py`

**Lines to change:** 83-93 (Tier 3 section)

---

## Current Code (Lines 83-93)

**FIND THIS:**
```python
# Tier 3: Validation required (MVP: simple confirm, AI in Phase 2)
elif tier == 3:
    # Future: AI validation
    # For MVP: simple confirmation
    confirmed = self._confirm(f"Validate this command: {input_text}?")
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
# Tier 3: AI validation required
elif tier == 3:
    from isaac.ai.validator import validate_command
    
    # AI validates command
    validation = validate_command(input_text, self.shell.name, self.session.config)
    
    # Display validation results
    print("\n" + "=" * 60)
    print("🤖 AI VALIDATION")
    print("=" * 60)
    print(f"Command: {input_text}")
    
    if validation['safe']:
        print("Safe: ✅ Yes")
    else:
        print("Safe: ⚠️  Use with caution")
    
    if validation['warnings']:
        print("\n⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    if validation['suggestions']:
        print("\n💡 Suggestions:")
        for suggestion in validation['suggestions']:
            print(f"  - {suggestion}")
    
    print("=" * 60)
    
    # Confirm after showing validation
    confirmed = self._confirm("\nProceed with execution?")
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

## Display Format

**Example Output:**
```
============================================================
🤖 AI VALIDATION
============================================================
Command: git push -f origin main
Safe: ⚠️  Use with caution

⚠️  Warnings:
  - Force push will overwrite remote history
  - Other team members may lose work
  - Can cause merge conflicts

💡 Suggestions:
  - Use git push without -f if possible
  - Communicate with team before force pushing
  - Consider using --force-with-lease for safety
============================================================

Proceed with execution? (y/n):
```

---

## Key Points

**Always Show Validation:**
- Even if safe: True, display the box
- Warnings may be empty for safe commands
- Suggestions always helpful

**User Control:**
- Validation is advisory, not blocking
- User can proceed despite warnings
- Clear yes/no prompt after validation

**Graceful Degradation:**
- If AI unavailable, shows warning about that
- User can still proceed (fallback to MVP behavior)

---

## Verification Steps

After modifying:

```bash
# Check syntax
python -m py_compile isaac/core/command_router.py
```

---

## Testing

**Test 1: Dangerous command**
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
  - Force push will overwrite remote history
  - [... more warnings ...]

💡 Suggestions:
  - Use git push without -f
  - [... more suggestions ...]
============================================================

Proceed with execution? (y/n):
```

**Test 2: Safe command**
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
  - Consider using -i flag for confirmation if file exists
============================================================

Proceed with execution? (y/n):
```

**Test 3: AI unavailable**
```bash
# Set ai_enabled: false in config

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

---

## Common Pitfalls

⚠️ **Pitfall 1: Not showing validation box**
- Symptom: User doesn't see analysis
- Fix: Always print the box, even for safe commands

⚠️ **Pitfall 2: Blocking execution**
- Symptom: Commands don't execute even when confirmed
- Fix: User confirmation is final decision, not AI

⚠️ **Pitfall 3: Poor formatting**
- Symptom: Validation hard to read
- Fix: Use separators (=== lines), clear labels

⚠️ **Pitfall 4: Crash on API error**
- Symptom: Isaac crashes if network down
- Fix: validate_command() handles errors, returns safe defaults

---

**END OF IMPLEMENTATION**
