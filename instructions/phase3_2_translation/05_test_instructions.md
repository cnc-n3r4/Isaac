# Test Instructions: AI Translation

## Goal
Verify "isaac [query]" translates to shell commands and executes safely.

**Time Estimate:** 15 minutes

---

## Prerequisites

**1. Phase 3.1 complete** (ClaudeClient working)
**2. API key set** in `~/.isaac/config.json`:
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-...",
  "ai_model": "claude-sonnet-4-5-20250929"
}
```

---

## Manual Tests

### Test 1: Simple Translation (Tier 1)

```bash
python -m isaac

> isaac list files
```

**Expected Output:**
```
Isaac > Translating...
Isaac > Command: ls
Isaac > Explanation: Lists files in current directory
Isaac > Confidence: 95%
Isaac > Executing: ls
[... ls output shows files ...]
```

✅ **Pass if:** Command translates and executes

---

### Test 2: Tier 2 Translation

```bash
> isaac find files larger than 100MB
```

**Expected Output:**
```
Isaac > Translating...
Isaac > Command: find . -type f -size +100M
Isaac > Explanation: Finds files larger than 100 megabytes
Isaac > Confidence: 92%
Isaac > Executing: find . -type f -size +100M
[... find output ...]
```

✅ **Pass if:** Complex query translates correctly

---

### Test 3: Tier 3 Translation (Requires Confirmation)

```bash
> isaac delete all log files
```

**Expected Output:**
```
Isaac > Translating...
Isaac > Command: rm *.log
Isaac > Explanation: Removes all log files
Isaac > Confidence: 88%
Isaac > Executing: rm *.log
[TIER 3 VALIDATION PROMPT]
Validate this command: rm *.log? (y/n):
```

✅ **Pass if:** User prompted before execution (tier system working)

---

### Test 4: Natural Language Without Prefix

```bash
> find large files
```

**Expected Output:**
```
Isaac > I have a name, use it.
```

✅ **Pass if:** Rejects queries without "isaac " prefix

---

### Test 5: AI Disabled

Edit `~/.isaac/config.json`:
```json
{
  "ai_enabled": false
}
```

```bash
> isaac list files
```

**Expected Output:**
```
Isaac > AI integration disabled. Enable in ~/.isaac/config.json
```

✅ **Pass if:** Graceful error message

---

### Test 6: Invalid API Key

Edit `~/.isaac/config.json`:
```json
{
  "ai_enabled": true,
  "claude_api_key": "invalid-key-123"
}
```

```bash
> isaac list files
```

**Expected Output:**
```
Isaac > Translating...
Isaac > AI translation failed: API error: 401
```

✅ **Pass if:** Error handled gracefully (no crash)

---

### Test 7: Non-Shell Query

```bash
> isaac what's the weather
```

**Expected Output:**
```
Isaac > Query doesn't appear to be shell-related. Isaac only handles shell commands.
```

✅ **Pass if:** Rejects non-shell queries

---

### Test 8: AI Query History

```bash
> isaac list files
> isaac find logs

# Then check history
python -c "
from isaac.core.session_manager import SessionManager
import os
session = SessionManager(os.path.expanduser('~/.isaac'))
session.load_from_local()
queries = session.ai_query_history.get_recent(5)
for q in queries:
    print(f'{q[\"query\"]} -> {q[\"translated_command\"]}')
"
```

**Expected Output:**
```
list files -> ls
find logs -> find . -name "*.log"
```

✅ **Pass if:** AI queries logged separately

---

## Success Criteria

**All tests must pass:**
- [ ] Simple translation works (Tier 1)
- [ ] Complex translation works (Tier 2)
- [ ] Tier 3 commands require confirmation
- [ ] Queries without "isaac" rejected
- [ ] AI disabled → graceful error
- [ ] Invalid API key → graceful error
- [ ] Non-shell queries rejected
- [ ] AI queries logged separately

---

## Troubleshooting

**Issue:** `ModuleNotFoundError: No module named 'isaac.ai.translator'`  
**Solution:** Check isaac/ai/__init__.py exists, run from correct directory

**Issue:** `KeyError: 'ai_enabled'`  
**Solution:** Add ai_enabled to config.json

**Issue:** Translation fails with "Low confidence"  
**Solution:** Rephrase query to be more specific

**Issue:** Tier 3 command executes without confirmation  
**Solution:** Check route_command() is called, not shell.execute()

---

**END OF TEST INSTRUCTIONS**
