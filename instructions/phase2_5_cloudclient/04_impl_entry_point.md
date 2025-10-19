# Implementation: Update Entry Point for Cloud Load

## Goal
Add cloud load call to Isaac's entry point to sync data on startup.

**Time Estimate:** 5 minutes

---

## File to Modify

**Path:** `C:\Projects\isaac\isaac\__main__.py`

**Lines to Add:** 1 (after local load)

---

## Architecture Reminder

**Startup Sequence:**
1. SessionManager created
2. `load_from_local()` - Load local files
3. **NEW:** `load_from_cloud()` - Overwrite with cloud data
4. Start REPL loop

**Why after local load:**
- Local data is fallback (always available)
- Cloud data overwrites local (if available)
- Last-write-wins strategy for MVP

---

## Modification: Add Cloud Load Call

### Find (lines after SessionManager initialization):

```python
# Load session data
session.load_from_local()
```

### Add immediately after:

```python
session.load_from_cloud()
```

**Complete section becomes:**
```python
# Initialize session manager
session = SessionManager()

# Load session data
session.load_from_local()
session.load_from_cloud()

# Start REPL
while True:
    # ... rest of REPL loop
```

**What this does:**
- Loads local data first (always available)
- Loads cloud data second (overwrites local if available)
- If cloud unavailable, local data used
- If cloud has newer data, local data overwritten

---

## Verification Steps

After modifying the file:

### Check Syntax
```bash
cd C:\Projects\isaac
python -m py_compile isaac/__main__.py
```

**Expected:** No syntax errors

### Test Startup
```bash
python -m isaac
```

**Expected Output (cloud enabled):**
```
Isaac > Loaded from local storage.
Isaac > Loaded preferences from cloud.
Isaac > Loaded command history from cloud.
Isaac > Ready.
```

**Expected Output (cloud disabled):**
```
Isaac > Loaded from local storage.
Isaac > Ready.
```

---

## Test Manually

### Test 1: Local-Only Mode

**Config:**
```json
{
  "sync_enabled": false
}
```

**Run:**
```bash
python -m isaac
```

**Expected:**
- Only "Loaded from local storage" message
- No cloud load attempt

### Test 2: Cloud Sync Mode

**Config:**
```json
{
  "sync_enabled": true,
  "api_url": "https://n3r4.xyz/isaac/api",
  "api_key": "isaac_demo_key_2024",
  "user_id": "ndemi"
}
```

**Run:**
```bash
python -m isaac
```

**Expected:**
- "Loaded from local storage"
- "Loaded preferences from cloud" (if cloud has data)
- "Loaded command history from cloud" (if cloud has data)

### Test 3: Multi-Machine Sync

**Machine A:**
1. Execute command: `Isaac > echo "test from machine A"`
2. Verify synced to cloud

**Machine B:**
1. Start Isaac
2. Check command history: `Isaac > --show-history`

**Expected:**
- Machine B sees "test from machine A" in history
- Multi-machine sync working

---

## Common Pitfalls

⚠️ **Called before load_from_local()**
- Problem: Cloud data loaded, then overwritten by local
- Solution: ALWAYS call after `load_from_local()` (already correct above)

⚠️ **Missing session.cloud check**
- Problem: Tries to load cloud when cloud=None
- Solution: `load_from_cloud()` already checks `if not self.cloud: return`

⚠️ **No user feedback**
- Problem: User doesn't know if cloud sync worked
- Solution: `load_from_cloud()` already prints messages

---

## Success Signals

✅ **Cloud load called on startup** (if sync_enabled)

✅ **Data synced from cloud** (overwrites local)

✅ **Multi-machine sync works** (Machine A → Machine B)

✅ **Graceful fallback** (if cloud unavailable, uses local)

---

**END OF IMPLEMENTATION**
