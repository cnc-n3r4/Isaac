# Implementation: Modify SessionManager for Cloud Sync

## Goal
Integrate CloudClient into SessionManager to enable automatic cloud sync.

**Time Estimate:** 30 minutes

---

## File to Modify

**Path:** `C:\Projects\isaac\isaac\core\session_manager.py`

**Lines to Add:** ~20 (across 4 sections)

---

## Architecture Reminder

**SessionManager Structure:**
- `__init__()` - Load config, init local storage, NOW: init CloudClient
- `_log_command()` - Save command locally, NOW: sync to cloud
- `_save_preferences()` - Save prefs locally, NOW: sync to cloud
- `load_from_cloud()` (NEW METHOD) - Load session data from cloud

**Integration Strategy:**
- Cloud operations are OPTIONAL (local saves always happen first)
- All cloud calls wrapped in try/except (no crashes)
- Health check on startup disables cloud if unreachable

---

## Modification 1: Initialize CloudClient

### Find (lines ~40-43):

```python
# Initialize cloud sync (future enhancement)
self.cloud = None
```

### Replace with:

```python
# Initialize cloud sync if enabled
self.cloud = None
if self.config.get('sync_enabled', False):
    try:
        from isaac.api.cloud_client import CloudClient
        
        self.cloud = CloudClient(
            api_url=self.config.get('api_url', ''),
            api_key=self.config.get('api_key', ''),
            user_id=self.config.get('user_id', self.machine_id)
        )
        
        # Verify API is reachable
        if not self.cloud.health_check():
            print("Isaac > Cloud sync unavailable (API unreachable). Using local-only mode.")
            self.cloud = None
            
    except Exception as e:
        print(f"Isaac > Cloud sync initialization failed: {e}. Using local-only mode.")
        self.cloud = None
```

**What this does:**
- Checks config for `sync_enabled: true`
- Initializes CloudClient with credentials from config
- Runs health check to verify API connectivity
- Disables cloud if API unreachable (falls back to local-only)
- Catches any errors (missing imports, bad config, etc.)

---

## Modification 2: Enable Cloud Sync in _log_command()

### Find (lines ~88-93):

```python
# Cloud sync (future enhancement)
# if self.cloud:
#     self.cloud.save_session_file('command_history.json', self.command_history.to_dict())
```

### Replace with:

```python
# Cloud sync (async-style error handling)
if self.cloud:
    try:
        self.cloud.save_session_file('command_history.json', self.command_history.to_dict())
    except Exception:
        pass  # Don't block command execution if cloud fails
```

**What this does:**
- Syncs command history to cloud after local save
- Wrapped in try/except (cloud failures won't crash Isaac)
- Silent failure (user already has local copy)

---

## Modification 3: Add Cloud Sync to _save_preferences()

### Find (method `_save_preferences()`, after local save):

```python
def _save_preferences(self):
    """Save user preferences to disk."""
    prefs_file = os.path.join(self.isaac_dir, 'preferences.json')
    with open(prefs_file, 'w') as f:
        json.dump(self.preferences.to_dict(), f, indent=2)
```

### Add after local save (before method ends):

```python
    # Sync to cloud if available
    if self.cloud:
        try:
            self.cloud.save_session_file('preferences.json', self.preferences.to_dict())
        except Exception:
            pass  # Local save succeeded, cloud optional
```

**Complete method becomes:**
```python
def _save_preferences(self):
    """Save user preferences to disk."""
    prefs_file = os.path.join(self.isaac_dir, 'preferences.json')
    with open(prefs_file, 'w') as f:
        json.dump(self.preferences.to_dict(), f, indent=2)
    
    # Sync to cloud if available
    if self.cloud:
        try:
            self.cloud.save_session_file('preferences.json', self.preferences.to_dict())
        except Exception:
            pass  # Local save succeeded, cloud optional
```

**What this does:**
- Syncs preferences to cloud after local save
- Cloud failure doesn't affect local save
- Silent error handling

---

## Modification 4: Add load_from_cloud() Method

### Add new method (after `load_from_local()` method):

```python
def load_from_cloud(self):
    """Load session data from cloud if available.
    
    For MVP: Overwrites local data with cloud data (last-write-wins).
    Future: Merge strategies, conflict resolution.
    """
    if not self.cloud:
        return  # Cloud sync disabled
    
    try:
        # Load preferences from cloud (overwrite local)
        cloud_prefs = self.cloud.get_session_file('preferences.json')
        if cloud_prefs:
            self.preferences = Preferences.from_dict(cloud_prefs)
            print("Isaac > Loaded preferences from cloud.")
        
        # Load command history from cloud (overwrite local)
        cloud_history = self.cloud.get_session_file('command_history.json')
        if cloud_history:
            self.command_history = CommandHistory.from_dict(cloud_history)
            print("Isaac > Loaded command history from cloud.")
            
    except Exception as e:
        # Cloud load failed, use local data
        print(f"Isaac > Cloud load failed: {e}. Using local data.")
```

**What this does:**
- Loads preferences and history from cloud (if available)
- Overwrites local data with cloud data (last-write-wins for MVP)
- Silent failure (keeps local data if cloud fails)
- User feedback messages

---

## Verification Steps

After modifying the file:

### Check Syntax
```bash
cd C:\Projects\isaac
python -m py_compile isaac/core/session_manager.py
```

**Expected:** No syntax errors

### Import Test
```bash
python -c "from isaac.core.session_manager import SessionManager; print('Import successful')"
```

**Expected:** "Import successful"

---

## Test Manually

### Test 1: Cloud Sync Disabled

**Edit config:**
```json
{
  "sync_enabled": false
}
```

**Run Isaac:**
```bash
python -m isaac
```

**Expected Output:**
```
Isaac > Loaded from local storage.
Isaac > Ready.
```

**Verify:**
- No cloud initialization messages
- Isaac works normally (local-only)

### Test 2: Cloud Sync Enabled

**Edit config:**
```json
{
  "sync_enabled": true,
  "api_url": "https://n3r4.xyz/isaac/api",
  "api_key": "isaac_demo_key_2024",
  "user_id": "ndemi"
}
```

**Run Isaac:**
```bash
python -m isaac
```

**Expected Output:**
```
Isaac > Loaded from local storage.
Isaac > Loaded preferences from cloud.
Isaac > Loaded command history from cloud.
Isaac > Ready.
```

**Verify:**
- Cloud sync initialized
- Data loaded from cloud

### Test 3: API Unreachable

**Edit config with bad URL:**
```json
{
  "sync_enabled": true,
  "api_url": "https://invalid-url.com/api",
  "api_key": "bad_key",
  "user_id": "ndemi"
}
```

**Run Isaac:**
```bash
python -m isaac
```

**Expected Output:**
```
Isaac > Cloud sync unavailable (API unreachable). Using local-only mode.
Isaac > Loaded from local storage.
Isaac > Ready.
```

**Verify:**
- No crash (graceful fallback)
- Local mode works

### Test 4: Command Sync

**With cloud enabled, execute command:**
```bash
Isaac > ls
```

**Check GoDaddy:**
- File: `public_html/isaac/api/data/ndemi/command_history.json`
- Contains: Latest `ls` command

### Test 5: Preferences Sync

**Update preference:**
```bash
Isaac > --set auto-run true
```

**Check GoDaddy:**
- File: `public_html/isaac/api/data/ndemi/preferences.json`
- Contains: `{"auto_run": true, ...}`

---

## Common Pitfalls

⚠️ **ImportError: CloudClient not found**
- Problem: `from isaac.api.cloud_client import CloudClient` fails
- Solution: Ensure `isaac/api/cloud_client.py` created first (Step 02)

⚠️ **Missing config fields**
- Problem: `self.config.get('api_url', '')` returns empty string
- Solution: Add all required fields to `~/.isaac/config.json`

⚠️ **Cloud failures crash Isaac**
- Problem: Forgot try/except around cloud calls
- Solution: All cloud operations wrapped (already in code above)

⚠️ **Infinite loop on cloud load**
- Problem: `load_from_cloud()` triggers save, which triggers load...
- Solution: Only load on startup (called from `__main__.py`, not in save methods)

⚠️ **Overwriting local with older cloud data**
- Problem: Cloud has old data, overwrites newer local data
- Solution: For MVP, this is expected (last-write-wins). Future: timestamps/conflict resolution

---

## Success Signals

✅ **Cloud sync initializes** (if sync_enabled: true)

✅ **Health check runs** on startup

✅ **Commands auto-sync** to GoDaddy after execution

✅ **Preferences auto-sync** after updates

✅ **Graceful fallback** if API unreachable (no crash)

✅ **Local-only mode works** (if sync_enabled: false)

---

**END OF IMPLEMENTATION**
