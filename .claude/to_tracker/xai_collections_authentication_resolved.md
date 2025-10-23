# xAI Collections API Authentication - RESOLVED ✅

**Date:** October 22, 2025  
**Status:** WORKING  
**Blocker Duration:** ~3 hours  

---

## Problem Summary

xAI Collections API authentication was failing with multiple errors:
1. `"Incorrect API key provided: xa***GB"` - Key truncation
2. `"No API key configured"` - Key not loading
3. `"DNS resolution failed"` - Wrong hostname format
4. `"Received http2 header with status: 404"` - Wrong endpoint

---

## Root Cause

**Config structure was incomplete/incorrect:**
- Missing `api_key` (had only `management_api_key`)
- Wrong `management_api_host` format (had full URL path instead of hostname)
- Confused `api_host` vs `management_api_host` roles

**xAI SDK uses TWO separate endpoints:**
- `api.x.ai` - gRPC endpoint for search, upload, document operations
- `management-api.x.ai` - REST endpoint for list, create, delete operations

---

## Working Configuration

**File:** `C:\Users\ndemi\.isaac\config.json`

```json
{
  "sync_enabled": true,
  "api_url": "https://n3r4.xyz/isaac/api",
  "api_key": "isaac_prod_123vEG",
  "user_id": "ndemi",
  "machine_id": "57f154b0",
  "ai_enabled": true,
  "task_mode_enabled": true,
  "auto_correct_tier2": true,
  "ai_min_confidence": 0.7,
  "xai": {
    "chat": {
      "api_key": "xai-123eXV",
      "api_url": "https://api.x.ai/v1/chat/completions",
      "model": "grok-3"
    },
    "collections": {
      "api_key": "xai-123eXV",
      "management_api_key": "xai-token-123OGB",
      "management_api_host": "management-api.x.ai",
      "enabled": true,
      "default_collection": "tc-log",
      "tc-log": "collection_ea35fd69-106d-4ded-9359-e31248430774",
      "cnc-info": "collection_bbccc2e5-1934-465a-b782-d12f1e3b1393",
      "cpf-log": "collection_ec1409e2-1071-4731-a3bc-af35fe59fbc6"
    }
  },
  "active_collection_id": "collection_bbccc2e5-1934-465a-b782-d12f1e3b1393",
  "active_collection_name": "cnc-info"
}
```

**KEY DISCOVERY:** The Chat API key (`xai-123eXV`) works for Collections gRPC operations! You only need the Collections-specific key (`xai-token-...`) for management operations.

---

## Key Requirements

### Required Config Keys (Collections)

```json
"collections": {
  "api_key": "xai-...",                    // REQUIRED - Chat OR Collections key works
  "management_api_key": "xai-token-...",   // REQUIRED - Collections key for management
  "management_api_host": "management-api.x.ai"  // REQUIRED - Just hostname, no paths
}
```

**Note:** `api_host` defaults to `api.x.ai` and can be omitted.

### Common Mistakes

❌ **WRONG:**
```json
"collections": {
  "management_api_key": "xai-token-...",  // Missing api_key
  "management_api_host": "management-api.x.ai/auth/teams/c13e6a5c-.../api-keys"  // Has URL path
}
```

❌ **WRONG:**
```json
"collections": {
  "api_key": "xai-token-...",
  "api_host": "management-api.x.ai"  // Wrong endpoint for search/upload
}
```

✅ **CORRECT (Minimal):**
```json
"collections": {
  "api_key": "xai-123eXV",               // Chat key works!
  "management_api_key": "xai-token-...",
  "management_api_host": "management-api.x.ai"
}
```

✅ **CORRECT (Explicit):**
```json
"collections": {
  "api_key": "xai-token-...",
  "management_api_key": "xai-token-...",
  "api_host": "api.x.ai",
  "management_api_host": "management-api.x.ai"
}
```

---

## SDK Architecture

**xAI Collections uses dual-endpoint architecture:**

| Operation | Endpoint | Protocol | Uses |
|-----------|----------|----------|------|
| `/mine list` | `management-api.x.ai` | REST | `management_api_key` |
| `/mine create` | `management-api.x.ai` | REST | `management_api_key` |
| `/mine delete` | `management-api.x.ai` | REST | `management_api_key` |
| `/mine dig` | `api.x.ai` | gRPC | `api_key` |
| `/mine cast` | `api.x.ai` | gRPC | `api_key` |
| `/mine info` | `management-api.x.ai` | REST | `management_api_key` |

**Both keys must be the same Collections API key** - the distinction is operational, not authentication.

---

## Code Implementation

**File:** `isaac/commands/mine/run.py` (lines 59-72)

```python
self.client = Client(
    api_key=api_key,                              # For gRPC (search, upload)
    management_api_key=management_api_key or api_key,  # For REST (list, create, delete)
    api_host=api_host,                            # "api.x.ai"
    management_api_host=management_api_host,      # "management-api.x.ai"
    timeout=3600
)
```

**Key loading logic** (lines 37-56):
```python
# Try nested structure first
xai_config = self.session_manager.config.get('xai', {})
collections_config = xai_config.get('collections', {})

api_key = collections_config.get('api_key')
management_api_key = collections_config.get('management_api_key')

# Fallback to flat structure for backward compatibility
if not api_key:
    api_key = self.session_manager.config.get('xai_api_key')
if not management_api_key:
    management_api_key = self.session_manager.config.get('xai_management_api_key')

# Strip whitespace from API keys
if api_key:
    api_key = api_key.strip()
if management_api_key:
    management_api_key = management_api_key.strip()
```

---

## Verified Working Commands

```powershell
isaac
$> /mine list
Available Collections (API):
• tc-logs (1 docs, created: 2025-10-21)
• cpf-logs (9 docs, created: 2025-10-21)
• cnc-info (1 docs, created: 2025-10-22) [ACTIVE]

$> /mine dig "m09"
Answer: [Search results returned successfully]
```

---

## Debugging Tools Created

1. **`show_raw_config.py`** - Shows config with line numbers and repr() to catch hidden chars
2. **`debug_config_loading.py`** - Validates config parsing and key structure
3. **`.claude/mail/to_debug/xai_collections_api_key_issue.md`** - Comprehensive issue documentation

---

## Lessons Learned

1. **xAI SDK documentation incomplete** - Collections API not documented in main README
2. **Two-endpoint architecture** - Must provide both `api_host` and `management_api_host`
3. **Hostname only** - No URL paths in host config (just `api.x.ai`, not `api.x.ai/v1/...`)
4. **Both keys required** - Even if same value, SDK expects both parameters
5. **Config restart required** - Isaac loads config once on startup, requires restart for changes

---

## Next Steps

- [x] Collections search working (`/mine dig`)
- [x] Collections list working (`/mine list`)
- [ ] Test upload (`/mine cast file.txt`)
- [ ] Test collection switching (`/mine use tc-log`)
- [ ] Document Collections API in Isaac user guide
- [ ] Add config validation on Isaac startup to catch missing keys early

---

## References

- xAI SDK GitHub: https://github.com/xai-org/xai-sdk-python
- xAI Console: https://console.x.ai (where API keys are generated)
- Collections API keys: Separate from Chat API keys
- Isaac config location: `~/.isaac/config.json` (Windows: `C:\Users\<user>\.isaac\config.json`)