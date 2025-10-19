# Testing Instructions: CloudClient Integration

## Goal
Verify CloudClient integration works correctly in all scenarios.

**Time Estimate:** 20 minutes

---

## Test Suite

### Test 1: Local-Only Mode

**Purpose:** Verify Isaac works without cloud sync.

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

3. Execute command:
   ```bash
   Isaac > echo "test local only"
   ```

4. Check local file:
   ```bash
   type %USERPROFILE%\.isaac\command_history.json
   ```

**Expected Results:**
- ✅ Isaac starts without cloud messages
- ✅ Command saved locally
- ✅ NO GoDaddy API calls made
- ✅ No crashes or errors

---

### Test 2: Cloud Sync Enabled

**Purpose:** Verify cloud sync works when enabled.

**Steps:**
1. Edit `~/.isaac/config.json`:
   ```json
   {
     "sync_enabled": true,
     "api_url": "https://n3r4.xyz/isaac/api",
     "api_key": "isaac_demo_key_2024",
     "user_id": "ndemi"
   }
   ```

2. Start Isaac:
   ```bash
   python -m isaac
   ```

3. Execute command:
   ```bash
   Isaac > echo "test cloud sync"
   ```

4. Verify on GoDaddy:
   - Check `public_html/isaac/api/data/ndemi/command_history.json`
   - Should contain "test cloud sync"

**Expected Results:**
- ✅ Cloud sync initialized on startup
- ✅ Health check passed
- ✅ Command synced to GoDaddy
- ✅ File exists on server

---

### Test 3: Multi-Machine Sync

**Purpose:** Verify commands sync across machines.

**Machine A Steps:**
1. Enable cloud sync (config from Test 2)
2. Execute command:
   ```bash
   Isaac > echo "from machine A"
   ```
3. Exit Isaac

**Machine B Steps:**
1. Enable cloud sync (same user_id: "ndemi")
2. Start Isaac
3. Check history:
   ```bash
   Isaac > --show-history
   ```

**Expected Results:**
- ✅ Machine B sees "from machine A" in history
- ✅ Cloud data loaded on startup
- ✅ Multi-machine sync working

---

### Test 4: API Unreachable (Graceful Degradation)

**Purpose:** Verify Isaac doesn't crash if API unreachable.

**Steps:**
1. Edit config with invalid URL:
   ```json
   {
     "sync_enabled": true,
     "api_url": "https://invalid-url-12345.com/api",
     "api_key": "bad_key",
     "user_id": "ndemi"
   }
   ```

2. Start Isaac:
   ```bash
   python -m isaac
   ```

3. Execute command:
   ```bash
   Isaac > echo "test offline"
   ```

**Expected Results:**
- ✅ Health check fails gracefully
- ✅ Message: "Cloud sync unavailable. Using local-only mode."
- ✅ Isaac continues in local-only mode
- ✅ NO crashes or exceptions
- ✅ Command saved locally

---

### Test 5: Network Timeout

**Purpose:** Verify timeout handling.

**Steps:**
1. Enable cloud sync with real API
2. Simulate slow network (optional: use firewall rule to delay)
3. Execute command:
   ```bash
   Isaac > echo "timeout test"
   ```

**Expected Results:**
- ✅ Request times out after 5 seconds
- ✅ NO crash (try/except catches timeout)
- ✅ Command saved locally regardless

**Note:** Timeout test is optional (hard to simulate). Verify timeout=5 in code.

---

### Test 6: Preferences Sync

**Purpose:** Verify preferences sync to cloud.

**Steps:**
1. Enable cloud sync
2. Update preference:
   ```bash
   Isaac > --set auto-run true
   ```

3. Verify on GoDaddy:
   - Check `public_html/isaac/api/data/ndemi/preferences.json`
   - Should contain `{"auto_run": true, ...}`

**Expected Results:**
- ✅ Preference saved locally
- ✅ Preference synced to cloud
- ✅ File exists on server with correct data

---

### Test 7: Load from Cloud on Startup

**Purpose:** Verify cloud data loaded on startup.

**Setup:**
1. Manually upload test data to GoDaddy:
   - File: `public_html/isaac/api/data/ndemi/preferences.json`
   - Content: `{"data": {"test_key": "cloud_value"}}`

**Steps:**
1. Delete local preferences:
   ```bash
   del %USERPROFILE%\.isaac\preferences.json
   ```

2. Start Isaac (cloud sync enabled)

**Expected Results:**
- ✅ Message: "Loaded preferences from cloud"
- ✅ Local file recreated with cloud data
- ✅ Contains test_key: "cloud_value"

---

### Test 8: Bad API Key (Authorization Failure)

**Purpose:** Verify authentication errors handled gracefully.

**Steps:**
1. Edit config with wrong API key:
   ```json
   {
     "sync_enabled": true,
     "api_url": "https://n3r4.xyz/isaac/api",
     "api_key": "WRONG_KEY_12345",
     "user_id": "ndemi"
   }
   ```

2. Start Isaac

**Expected Results:**
- ✅ Health check fails (401 Unauthorized)
- ✅ Message: "Cloud sync unavailable"
- ✅ Falls back to local-only mode
- ✅ NO crash

---

## Automated Test (Optional)

**If Phase 2.5 tests created by TEST workspace:**

```bash
pytest tests/test_cloud_client.py -v
```

**Expected:**
- All 15 tests PASS
- Coverage: 90%+

---

## Success Criteria

**Before marking CloudClient integration complete:**

- [ ] Test 1 passed (local-only mode)
- [ ] Test 2 passed (cloud sync enabled)
- [ ] Test 3 passed (multi-machine sync)
- [ ] Test 4 passed (API unreachable graceful)
- [ ] Test 5 passed (timeout handling) OR verified timeout=5 in code
- [ ] Test 6 passed (preferences sync)
- [ ] Test 7 passed (load from cloud on startup)
- [ ] Test 8 passed (bad API key handled)

**Optional:**
- [ ] Automated tests passing (if created)

---

## Troubleshooting

### Issue: Cloud sync not working

**Check:**
- Config has `sync_enabled: true`
- API URL correct (https://n3r4.xyz/isaac/api)
- API key correct (isaac_demo_key_2024)
- Network connectivity (ping n3r4.xyz)
- GoDaddy API deployed (Phase 2 complete)

### Issue: Commands not syncing

**Check:**
- `self.cloud` initialized (health check passed)
- Try/except not silently failing (add debug prints)
- GoDaddy API save_session.php working (test with curl)

### Issue: Multi-machine sync not working

**Check:**
- Both machines use same user_id
- Both machines have sync_enabled: true
- Cloud data exists on GoDaddy
- Load from cloud called on startup

---

**END OF TESTING INSTRUCTIONS**
