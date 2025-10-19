# Testing: CloudClient Integration

## Goal
Verify CloudClient works correctly with SessionManager.

**Time Estimate:** 15 minutes

---

## Manual Testing

### Test 1: Local-Only Mode
**Purpose:** Verify Isaac works without cloud sync

**Steps:**
1. Edit `~/.isaac/config.json`:
```json
{
  "sync_enabled": false
}
```

2. Start Isaac:
```bash
python -m isaac
```

3. Run a command:
```
isaac> ls
```

4. Exit and restart Isaac

**Expected Result:**
- ✅ Isaac starts without errors
- ✅ Commands execute normally
- ✅ No cloud API calls made
- ✅ Command history persists locally

---

### Test 2: Cloud Sync Enabled
**Purpose:** Verify cloud sync works

**Steps:**
1. Edit `~/.isaac/config.json`:
```json
{
  "sync_enabled": true,
  "api_url": "https://n3r4.xyz/isaac/api",
  "api_key": "your-api-key-here",
  "user_id": "ndemi"
}
```

2. Start Isaac:
```bash
python -m isaac
```

3. Run a command:
```
isaac> pwd
```

4. Check GoDaddy files:
```bash
# SSH to GoDaddy or use FTP
ls public_html/isaac/api/data/ndemi/
# Expected files:
# - command_history.json
# - preferences.json
```

5. Verify file contents:
```bash
cat public_html/isaac/api/data/ndemi/command_history.json
# Should contain pwd command
```

**Expected Result:**
- ✅ Isaac starts and loads from cloud
- ✅ Command syncs to GoDaddy after execution
- ✅ Files exist in GoDaddy data directory
- ✅ JSON data is valid

---

### Test 3: Multi-Machine Sync
**Purpose:** Verify commands sync between machines

**Steps:**
1. On Machine A:
```bash
python -m isaac
isaac> echo "test from machine A"
isaac> exit
```

2. On Machine B (with same user_id in config):
```bash
python -m isaac
isaac> --show-history
```

**Expected Result:**
- ✅ Machine B sees "echo test from machine A" in history
- ✅ Timestamps are correct
- ✅ Machine ID shows "Machine A"

---

### Test 4: Offline Mode (Graceful Degradation)
**Purpose:** Verify Isaac doesn't crash if API is unreachable

**Steps:**
1. Disconnect from network OR set wrong API URL:
```json
{
  "sync_enabled": true,
  "api_url": "https://fake-url-that-does-not-exist.com",
  "api_key": "test",
  "user_id": "ndemi"
}
```

2. Start Isaac:
```bash
python -m isaac
```

3. Run a command:
```
isaac> ls
```

**Expected Result:**
- ✅ Isaac starts (health check fails, disables cloud)
- ✅ Commands execute normally (local-only mode)
- ✅ No crashes or exceptions
- ✅ User sees no errors (silent fallback)

---

### Test 5: Preference Sync
**Purpose:** Verify preferences sync to cloud

**Steps:**
1. Start Isaac with cloud enabled:
```bash
python -m isaac
```

2. Change a preference:
```
isaac> --set auto-run on
```

3. Check GoDaddy:
```bash
cat public_html/isaac/api/data/ndemi/preferences.json
# Should show: "auto_run": true
```

4. On different machine, start Isaac:
```bash
python -m isaac
isaac> --show-preferences
```

**Expected Result:**
- ✅ Preferences sync to GoDaddy
- ✅ Second machine loads synced preferences
- ✅ auto_run is enabled on second machine

---

## Automated Testing (Phase 2.5 Test Suite)

**Run test suite created by Test workspace:**

```bash
pytest tests/test_cloud_client.py -v
```

**Expected Output:**
```
tests/test_cloud_client.py::test_cloudclient_init PASSED
tests/test_cloud_client.py::test_health_check_success PASSED
tests/test_cloud_client.py::test_health_check_failure PASSED
tests/test_cloud_client.py::test_save_session_file_success PASSED
tests/test_cloud_client.py::test_save_session_file_network_error PASSED
tests/test_cloud_client.py::test_get_session_file_success PASSED
tests/test_cloud_client.py::test_get_session_file_not_found PASSED
tests/test_cloud_client.py::test_get_session_file_network_error PASSED
tests/test_cloud_client.py::test_is_available_true PASSED
tests/test_cloud_client.py::test_is_available_no_api_key PASSED
tests/test_cloud_client.py::test_session_manager_cloud_init PASSED
tests/test_cloud_client.py::test_session_manager_cloud_disabled PASSED
tests/test_cloud_client.py::test_save_and_get_roundtrip PASSED
tests/test_cloud_client.py::test_cloud_unreachable_fallback PASSED
tests/test_cloud_client.py::test_network_timeout_graceful PASSED

============================== 15 passed in 0.20s ===============================
```

**If any test fails:**
- Review error message
- Check CloudClient implementation
- Verify SessionManager integration
- Check network connectivity

---

## Success Criteria Checklist

**Phase 2.5 Complete When:**

- [x] CloudClient class created with 4 methods
- [x] SessionManager initializes CloudClient if sync_enabled
- [x] Commands sync to GoDaddy after execution
- [x] Preferences sync to GoDaddy when saved
- [x] Isaac loads from cloud on startup
- [x] Multi-machine sync works (tested with 2 machines)
- [x] Offline mode works (no crashes when API unreachable)
- [x] All 15 automated tests passing

---

## Troubleshooting

### Issue: "Module not found: requests"
**Solution:**
```bash
pip install requests
```

### Issue: "401 Unauthorized" from API
**Solution:**
- Check API key in `~/.isaac/config.json`
- Verify key matches GoDaddy configuration
- Test with curl:
```bash
curl -H "Authorization: Bearer your-key" https://n3r4.xyz/isaac/api/health_check.php
```

### Issue: "Connection timeout"
**Solution:**
- Check network connectivity
- Verify API URL is correct
- Try health check manually:
```bash
curl https://n3r4.xyz/isaac/api/health_check.php
```

### Issue: "CloudClient not syncing"
**Solution:**
- Check `sync_enabled: true` in config
- Verify SessionManager.cloud is not None
- Add debug print in _log_command():
```python
if self.cloud:
    print(f"DEBUG: Syncing to cloud...")  # Add this line
    try:
        self.cloud.save_session_file(...)
```

### Issue: "Data not loading from cloud"
**Solution:**
- Check GoDaddy files exist
- Verify load_from_cloud() is called in __main__.py
- Check file permissions on GoDaddy

---

## Next Steps

After Phase 2.5 testing complete:

1. ✅ Phase 2.5 CloudClient implemented and tested
2. ⏳ Phase 3: AI Integration (natural language, task mode)
3. ⏳ Phase 3.1: Claude API Client
4. ⏳ Phase 3.2: Translation
5. ⏳ Phase 3.3: Auto-correction
6. ⏳ Phase 3.4: AI Validation
7. ⏳ Phase 3.5: Task Mode

---

**END OF TESTING**
