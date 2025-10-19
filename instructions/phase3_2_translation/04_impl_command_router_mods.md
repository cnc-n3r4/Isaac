# Implementation: Command Router Integration

## Goal
Modify command_router.py to wire AI translation into "isaac [query]" detection.

**Time Estimate:** 15 minutes

---

## File to Modify

**Path:** `isaac/core/command_router.py`

**Lines to change:** 46-53 (placeholder section)

---

## Current Code (Lines 46-53)

**FIND THIS:**
```python
# Natural language check (MVP: reject without 'isaac' prefix)
if self._is_natural_language(input_text):
    if not input_text.lower().startswith('isaac '):
        return CommandResult(
            success=False,
            output="Isaac > I have a name, use it.",
            exit_code=-1
        )
    # AI integration in Phase 2
    return CommandResult(
        success=False,
        output="Isaac > AI integration coming in Phase 2.",
        exit_code=-1
    )
```

---

## New Code

**REPLACE WITH:**
```python
# Natural language check - AI translation
if self._is_natural_language(input_text):
    if not input_text.lower().startswith('isaac '):
        return CommandResult(
            success=False,
            output="Isaac > I have a name, use it.",
            exit_code=-1
        )
    
    # AI translation (Phase 3.2)
    query = input_text[6:].strip()  # Remove "isaac " prefix
    
    from isaac.ai.translator import translate_query
    result = translate_query(query, self.shell.name, self.session)
    
    if result['success']:
        # Log AI query separately (privacy)
        self.session.log_ai_query(
            query=query,
            translated_command=result['command'],
            explanation=result.get('explanation', ''),
            executed=True
        )
        
        # Execute translated command through tier system (CRITICAL)
        print(f"Isaac > Executing: {result['command']}")
        return self.route_command(result['command'])
    else:
        # Translation failed
        return CommandResult(
            success=False,
            output=f"Isaac > {result['error']}",
            exit_code=-1
        )
```

---

## Critical Safety Note

**MUST USE:** `return self.route_command(result['command'])`

**DO NOT USE:** `return self.shell.execute(result['command'])`

**Why:** Translated command must go through tier validation. Using `shell.execute()` directly bypasses safety checks and can lead to data loss.

**Example:**
- User: "isaac delete all log files"
- Translation: `rm -rf *.log` (Tier 3 or 4)
- Without tier check: Executes immediately → data loss
- With tier check: Prompts user → safe

---

## Verification Steps

After modifying:

```bash
# 1. Check syntax
python -m py_compile isaac/core/command_router.py

# 2. Test import
python -c "from isaac.core.command_router import CommandRouter; print('✅ Import successful')"
```

**Expected Output:**
```
✅ Import successful
```

---

## Testing Integration

**Test 1: Simple query**
```bash
# Start Isaac
python -m isaac

# Run query
> isaac list files

# Expected output:
Isaac > Translating...
Isaac > Command: ls
Isaac > Explanation: Lists files in current directory
Isaac > Confidence: 95%
Isaac > Executing: ls
[... ls output ...]
```

**Test 2: Query without "isaac" prefix**
```bash
> list files

# Expected:
Isaac > I have a name, use it.
```

**Test 3: AI disabled**
```bash
# Edit ~/.isaac/config.json - set ai_enabled: false

> isaac list files

# Expected:
Isaac > AI integration disabled. Enable in ~/.isaac/config.json
```

---

## Common Pitfalls

⚠️ **Pitfall 1: Bypassing tier system**
- Symptom: AI commands execute without confirmation
- Fix: Use `self.route_command()`, NOT `self.shell.execute()`

⚠️ **Pitfall 2: Not logging AI query**
- Symptom: AI queries don't appear in history
- Fix: Call `self.session.log_ai_query()` before execution

⚠️ **Pitfall 3: Import error**
- Symptom: ModuleNotFoundError for translator
- Fix: Ensure isaac/ai/ folder has __init__.py

⚠️ **Pitfall 4: Query prefix not removed**
- Symptom: AI gets "isaac find files" instead of "find files"
- Fix: Strip "isaac " prefix with `input_text[6:].strip()`

---

**END OF IMPLEMENTATION**
