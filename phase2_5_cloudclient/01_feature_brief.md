# Feature Brief: CloudClient Integration

## Objective
Enable Isaac to sync command history and preferences across multiple machines via GoDaddy cloud API.

## Problem Statement

**Current State:**
- Isaac stores data locally (~/.isaac/)
- Each machine has isolated command history
- No way to access history from other machines
- GoDaddy API deployed and tested (Phase 2)

**Issues:**
- User switches between machines → loses context
- Commands executed on Machine A not visible on Machine B
- No backup of session data
- Manual config replication required

## Solution

Integrate CloudClient HTTP wrapper to sync data to GoDaddy API:
- SessionManager initializes CloudClient on startup
- Commands auto-sync after execution (optional, won't block)
- Preferences sync after updates
- Health check disables cloud if API unreachable
- Graceful fallback to local-only mode

## Requirements

### Functional Requirements
- [ ] Create CloudClient class with HTTP methods
- [ ] Initialize CloudClient in SessionManager if sync_enabled
- [ ] Sync commands to cloud after execution
- [ ] Sync preferences to cloud after updates
- [ ] Load from cloud on startup
- [ ] Health check to validate API connectivity
- [ ] Graceful degradation if cloud unavailable

### Configuration Requirements
- [ ] User config: sync_enabled, api_url, api_key, user_id
- [ ] Validate config before enabling cloud sync
- [ ] Disable cloud if credentials missing

## Technical Details

**Files to Create:**
- `isaac/api/cloud_client.py` (~120 lines)

**Files to Modify:**
- `isaac/core/session_manager.py` (~20 lines added)
- `isaac/__main__.py` (~1 line added)

**API Endpoints (GoDaddy):**
- Health: `GET {api_url}/health_check.php`
- Save: `POST {api_url}/save_session.php`
- Get: `GET {api_url}/get_session.php?user_id={user_id}&filename={filename}`

**Authentication:**
- Header: `Authorization: Bearer {api_key}`

## Architecture Context

**CloudClient Class Structure:**
```python
class CloudClient:
    def __init__(self, api_url: str, api_key: str, user_id: str):
        self.api_url = api_url
        self.api_key = api_key
        self.user_id = user_id
        self.timeout = 5
    
    def health_check(self) -> bool:
        # GET health_check.php
        # Return True if 200 OK, False otherwise
    
    def save_session_file(self, filename: str, data: dict) -> bool:
        # POST save_session.php with JSON payload
        # Return True if saved, False on error
    
    def get_session_file(self, filename: str) -> Optional[dict]:
        # GET get_session.php?user_id=X&filename=Y
        # Return dict if found, None otherwise
    
    def is_available(self) -> bool:
        # Check if cloud sync is working
        # Wrapper around health_check()
```

**SessionManager Integration Points:**
1. `__init__()` - Initialize CloudClient if sync_enabled
2. `_log_command()` - Sync to cloud after local save
3. `_save_preferences()` - Sync to cloud after local save
4. `load_from_cloud()` (NEW) - Load session data from cloud

**Entry Point Addition:**
```python
# isaac/__main__.py
session.load_from_local()
session.load_from_cloud()  # ADD THIS LINE
```

## Variables/Data Structures

**Config Format (~/.isaac/config.json):**
```json
{
  "api_url": "https://n3r4.xyz/isaac/api",
  "api_key": "isaac_demo_key_2024",
  "user_id": "ndemi",
  "sync_enabled": true
}
```

**Save Request Payload:**
```json
{
  "user_id": "ndemi",
  "filename": "preferences.json",
  "data": {
    "auto_run": true,
    "theme": "dark"
  }
}
```

**Save Response:**
```json
{
  "success": true,
  "message": "Session saved",
  "timestamp": "2025-10-19T12:34:56+00:00"
}
```

**Get Response:**
```json
{
  "success": true,
  "data": {
    "auto_run": true,
    "theme": "dark"
  }
}
```

## Out of Scope
❌ Conflict resolution (MVP uses last-write-wins)
❌ Encryption (future enhancement)
❌ Delta sync (always uploads full file)
❌ Offline queue (failed syncs are dropped)

## Success Criteria
✅ CloudClient class created with 4 methods
✅ SessionManager initializes CloudClient if sync_enabled
✅ Commands sync to GoDaddy after execution
✅ Preferences sync to GoDaddy after updates
✅ Multi-machine sync works (Machine A → Machine B)
✅ Offline mode works (local-only when sync_enabled: false)
✅ Graceful degradation (no crashes if API unreachable)

## Risk Assessment
**Risk:** LOW (cloud operations are optional, local saves always succeed)  
**Mitigation:**
- All cloud calls wrapped in try/except
- Timeout: 5 seconds max
- Health check on startup disables cloud if unreachable
- Local saves happen regardless of cloud status

---

**Status:** READY FOR IMPLEMENTATION  
**Priority:** HIGH (enables multi-machine workflow)  
**Expected Duration:** 1-2 hours

**END OF FEATURE BRIEF**
