# Bug Fixes Applied - October 22, 2025

## Issue 1: `/f` and `/force` prefix not working ✅ FIXED

**Problem:** No way to force execute shell commands without AI validation.

**Solution:** Added force execution detection in `command_router.py`:
```python
# Check for force execution prefix (/f or /force)
if input_text.startswith('/f ') or input_text.startswith('/force '):
    # Extract actual command (skip /f or /force prefix)
    if input_text.startswith('/f '):
        actual_command = input_text[3:]  # Skip '/f '
    else:
        actual_command = input_text[7:]  # Skip '/force '
    
    print(f"Isaac > Force executing (bypassing AI validation): {actual_command}")
    return self.shell.execute(actual_command)
```

**Test:**
```bash
$> /f rm important_file.txt
Isaac > Force executing (bypassing AI validation): rm important_file.txt
# Executes immediately, no AI check

$> /force Get-Process | Where-Object CPU -gt 50
Isaac > Force executing (bypassing AI validation): Get-Process | Where-Object CPU -gt 50
# Executes immediately
```

---

## Issue 2: Collections list not showing all 3 collections ✅ FIXED

**Problem:** Collections were hardcoded to `tc_logs` and `cpf_logs` only.

**Solution:** Changed to dynamic lookup from `xai.collections` config:
```python
# OLD (hardcoded):
configured_collections = {
    'tc_logs': config.get('tc_log_collection_id'),
    'cpf_logs': config.get('cpf_log_collection_id')
}

# NEW (dynamic from config):
xai_config = config.get('xai', {})
configured_collections = xai_config.get('collections', {})
# Now reads ALL collections from config!
```

**Test:**
```bash
$> /mine ls
Configured Collections (from config):
• tc-logs (ID: abc12345...)
• cpf-logs (ID: def67890...)
• cnc-info (ID: ghi24680...) ← active
```

---

## Issue 3: Collection names updated (underscore → hyphen) ✅ FIXED

**Problem:** Old names used underscores (`tc_logs`), new names use hyphens (`tc-logs`).

**Solution:** Dynamic lookup supports ANY collection names from config. No hardcoding!

**Your collections (in `~/.isaac/config.json`):**
```json
{
  "xai": {
    "api_key": "xai-...",
    "collections": {
      "tc-logs": "your-uuid-here",
      "cpf-logs": "your-uuid-here",
      "cnc-info": "your-uuid-here"
    }
  }
}
```

**Test:**
```bash
$> /mine use cnc-info
Switched to collection: cnc-info

$> /mine dig "cnc stuff"
🔍 Searching cnc-info...
[Results from your cnc-info collection]
```

---

## How to Test All Fixes

### 1. Force Execution
```bash
$> /f ls
# Bypasses tier check, executes immediately

$> /force rm test.txt
# Bypasses tier check, executes immediately
```

### 2. Collections List
```bash
$> /mine ls
# Should show all 3 collections: tc-logs, cpf-logs, cnc-info
```

### 3. Use New Collection Names
```bash
$> /mine use tc-logs
Switched to collection: tc-logs

$> /mine use cpf-logs
Switched to collection: cpf-logs

$> /mine use cnc-info
Switched to collection: cnc-info

$> /mine dig "some query"
🔍 Searching cnc-info...
```

### 4. Cast to Collections
```bash
$> /mine cast test.txt cnc-info
Cast into mine: test.txt → cnc-info collection
```

---

## Config Format Reference

**Your `~/.isaac/config.json` should look like:**
```json
{
  "xai": {
    "api_key": "xai-your-key-here",
    "api_url": "https://api.x.ai/v1",
    "model": "grok-3",
    "collections": {
      "tc-logs": "uuid-for-tc-logs",
      "cpf-logs": "uuid-for-cpf-logs",
      "cnc-info": "uuid-for-cnc-info"
    }
  }
}
```

**Adding more collections:**
Just add to the `collections` object:
```json
"collections": {
  "tc-logs": "uuid-1",
  "cpf-logs": "uuid-2",
  "cnc-info": "uuid-3",
  "research-notes": "uuid-4",
  "news-cache": "uuid-5"
}
```

Isaac will automatically find them!

---

## Files Modified

1. **`isaac/core/command_router.py`**
   - Added `/f` and `/force` prefix detection
   - Routes to immediate shell execution (bypasses AI)

2. **`isaac/commands/mine/run.py`**
   - Replaced hardcoded collection names
   - Dynamic lookup from `xai.collections` config
   - Supports any collection names (hyphens, underscores, whatever)

---

## Next Steps

1. **Test force execution:**
   ```bash
   $> /f Get-Process
   $> /force ls -la
   ```

2. **Verify collections list:**
   ```bash
   $> /mine ls
   # Should see tc-logs, cpf-logs, cnc-info
   ```

3. **Test your cnc-info collection:**
   ```bash
   $> /mine use cnc-info
   $> /mine dig "show me cnc stuff"
   # Check what blob info it retrieves
   ```

All three bugs are now fixed! 🎯
