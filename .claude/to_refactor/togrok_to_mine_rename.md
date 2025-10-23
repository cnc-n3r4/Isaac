# Refactor: /togrok → /mine + xAI SDK Integration

**Created:** 2025-10-21  
**Priority:** HIGH  
**Complexity:** MEDIUM  
**Estimated Time:** 1-2 hours

---

## Overview

Rename `/togrok` command to `/mine` and update to use official xAI SDK for Collections API instead of raw HTTP client.

**Rationale:**
- `/mine` has dual meaning: possessive (my files) + mining (extracting data)
- xAI SDK provides proper type hints, error handling, authentication
- Collections API is completely separate from Chat Completions API

---

## Phase 1: Command Rename (30 min)

### Directory Structure
```
isaac/commands/togrok/  →  isaac/commands/mine/
├── command.yaml        →  command.yaml (update triggers/name)
└── run.py             →  run.py (update references)
```

### Files to Rename/Update:

**1. Directory:**
```bash
mv isaac/commands/togrok isaac/commands/mine
```

**2. `isaac/commands/mine/command.yaml`:**
```yaml
name: mine
version: 1.0.0
summary: Personal file history and collection search
description: |
  Search your personal file history (Total Commander logs, project snapshots)
  using xAI Collections. This is YOUR stuff, not internet knowledge.

triggers:
  - /mine

aliases:
  - /mine

# ... rest of config
```

**3. Update help text in `isaac/commands/mine/run.py`:**
- Change all "togrok" references to "mine"
- Update command examples
- Update summary text

**4. Search for any hardcoded references:**
```bash
grep -r "togrok" isaac/
grep -r "/togrok" isaac/
```

---

## Phase 2: xAI SDK Integration (45-60 min)

### Problem: Two Different APIs

**Chat Completions API** (existing, working):
- Endpoint: `https://api.x.ai/v1/chat/completions`
- Key: `xai_chat_api_key`
- Purpose: Grok conversations
- Client: `XaiClient` (keep as-is)

**Collections Management API** (needs SDK):
- Endpoint: Different (xAI SDK handles this)
- Key: `xai_management_api_key` 
- Purpose: Vector search, collection management
- Client: Use xAI SDK, not raw HTTP

### Install xAI SDK

**Add to `requirements.txt`:**
```
xai-sdk>=1.0.0
```

**Install:**
```bash
pip install xai-sdk
```

### Replace XaiCollectionsClient with SDK

**Current (raw HTTP in `isaac/ai/xai_collections_client.py`):**
```python
class XaiCollectionsClient:
    def search_collection(self, collection_id, query, top_k=5):
        response = requests.post(
            f"{self.base_url}/collections/{collection_id}/search",
            ...
        )
```

**New (using xAI SDK):**
```python
from xai import XAI

class XaiCollectionsManager:
    def __init__(self, api_key: str):
        """Initialize with management API key (NOT chat key)"""
        self.client = XAI(api_key=api_key)
    
    def search_collection(self, collection_id: str, query: str, top_k: int = 5):
        """Search collection using xAI SDK"""
        try:
            results = self.client.collections.search(
                collection_id=collection_id,
                query=query,
                top_k=top_k
            )
            return self._format_results(results)
        except Exception as e:
            raise Exception(f"Collection search error: {e}")
    
    def list_collections(self):
        """List all collections"""
        return self.client.collections.list()
    
    def get_collection_info(self, collection_id: str):
        """Get collection metadata"""
        return self.client.collections.get(collection_id)
```

---

## Phase 3: Configuration Update (15 min)

### Separate API Keys in Config

**Update `~/.isaac/config.json`:**
```json
{
  "xai": {
    "chat": {
      "api_key": "xai-chat-...",
      "endpoint": "https://api.x.ai/v1/chat/completions",
      "model": "grok-3"
    },
    "collections": {
      "api_key": "xai-management-...",
      "active_collection": "tc_logs"
    }
  },
  
  "collections": {
    "tc_logs": "collection_ea35fd69-106d-4ded-9359-e31248430774",
    "cpf_logs": "collection_ec1409e2-1071-4731-a3bc-af35fe59fbc6"
  }
}
```

**Backward compatibility:**
- Keep old `xai_api_key` for chat (if new structure missing)
- Warn if `xai.collections.api_key` is missing when using `/mine`

---

## Phase 4: Clean Up /ask Handler (20 min)

### Remove Collections Logic from /ask

**Current:** `/ask` tries to route file history queries to Collections (causing 404)

**New:** `/ask` is ONLY for chat completions

**File:** `isaac/commands/ask/run.py`

**Remove:**
- `_classify_query_intent()` function
- `_search_file_history()` function
- Collections routing logic

**Keep:**
- `_handle_chat_query()` → rename to just `main()` flow
- Chat memory (session history)
- XaiClient for chat completions

**Result:**
```python
def main():
    # Extract query
    query = ...
    
    # Get session
    session = SessionManager()
    config = session.get_config()
    
    # Chat only (no routing)
    client = XaiClient(api_key=config['xai']['chat']['api_key'])
    preprompt = _build_chat_preprompt(session, query)
    response = client.chat(prompt=query, system_prompt=preprompt)
    
    # Log and return
    session.log_ai_query(...)
    print(json.dumps({"ok": True, "stdout": response}))
```

---

## Phase 5: Update /mine to Use SDK (30 min)

**File:** `isaac/commands/mine/run.py`

**Update initialization:**
```python
from isaac.ai.xai_collections_manager import XaiCollectionsManager

def main():
    session = SessionManager()
    config = session.get_config()
    
    # Use management API key (NOT chat key)
    mgmt_key = config.get('xai', {}).get('collections', {}).get('api_key')
    
    if not mgmt_key:
        print("Error: Management API key not configured")
        print("Add 'xai.collections.api_key' to ~/.isaac/config.json")
        return
    
    collections = XaiCollectionsManager(api_key=mgmt_key)
    
    # ... rest of /mine logic ...
```

---

## Testing Plan

### Test 1: /ask (Chat Only)
```powershell
isaac /start
/ask what is docker?
# Expected: Chat response (no Collections attempt)

/ask what did I just ask?
# Expected: Remembers previous question (session history)
```

### Test 2: /mine (Collections Search)
```powershell
/mine list
# Expected: Shows tc_logs, cpf_logs using SDK

/mine use tc_logs
/mine query where did I move files?
# Expected: Searches tc_logs using xAI SDK
```

### Test 3: Configuration
```powershell
/config
# Expected: Shows both chat and management keys (masked)
```

---

## Files to Modify

1. **Rename:**
   - `isaac/commands/togrok/` → `isaac/commands/mine/`

2. **Update:**
   - `isaac/commands/mine/command.yaml` - Change name/triggers
   - `isaac/commands/mine/run.py` - Use SDK, update text
   - `isaac/commands/ask/run.py` - Remove Collections logic
   - `isaac/ai/xai_collections_client.py` → `xai_collections_manager.py` - Use SDK
   - `requirements.txt` - Add xai-sdk
   - `~/.isaac/config.json` - Separate chat/management keys

3. **Remove:**
   - Collections routing from `/ask` handler
   - Raw HTTP calls to Collections API

---

## Success Criteria

✅ `/togrok` renamed to `/mine` everywhere  
✅ xAI SDK installed and integrated  
✅ Two separate API keys configured (chat vs management)  
✅ `/ask` does ONLY chat completions  
✅ `/mine` does ONLY Collections search via SDK  
✅ No more 404 errors (SDK handles endpoints)  
✅ Both commands tested and working  

---

**For Coding Agent:** Start with Phase 1 (rename), then Phase 3 (config structure), then Phase 2 (SDK integration). Test after each phase. The xAI SDK documentation will have correct endpoint/parameter structure.</content>
<parameter name="filePath">c:\Projects\Isaac-1\.claude\to_refactor\togrok_to_mine_rename.md