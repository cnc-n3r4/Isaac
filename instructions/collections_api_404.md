# Collections API 404 Error

**Issue:** Collections search returns 404 error when querying xAI Collections.

**User Test:**
```powershell
/ask what files have i recently deleted?
```

**Error:**
```
Collections search unavailable: Collections search error: 
Search API error 404: {"error":{"code":404,"message":"The requested resource was not found..."}}
```

**Current Endpoint:**
```python
POST https://api.x.ai/v1/collections/{collection_id}/search
```

**Config:**
- Collection ID: `collection_ea35fd69-106d-4ded-9359-e31248430774` (tc_logs)
- API Key: Present and working (chat queries succeed)
- Base URL: `https://api.x.ai/v1`

**Diagnosis:**
The endpoint URL structure is likely incorrect. xAI Collections API may use a different path.

**Possible Issues:**
1. **Wrong base path:** Maybe `/v1/collections` doesn't exist
2. **Different API version:** Collections might use `/v2` or different versioning
3. **Different endpoint pattern:** Might be `/search/collections` or `/collections/search` (without ID in path)
4. **Authentication method:** Collections might need different auth headers

**What to Check:**
1. **xAI Collections API Documentation:** Find official endpoint structure
2. **API Explorer:** Test endpoint directly with curl/Postman
3. **Collection ID format:** Verify `collection_ea35fd69...` is correct format
4. **Headers:** Check if Collections requires additional headers

**Test with curl:**
```bash
curl -X POST https://api.x.ai/v1/collections/collection_ea35fd69-106d-4ded-9359-e31248430774/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 5}'
```

**Alternative endpoints to try:**
- `POST /v1/search/collections/{id}`
- `POST /v1/collections/{id}/query`
- `POST /v2/collections/{id}/search`
- `POST /collections/{id}/search` (no `/v1`)

**Files Involved:**
- `isaac/ai/xai_collections_client.py` (lines 87-97)
- `isaac/commands/ask/run.py` (calls search_collection)

**Priority:** HIGH  
**Complexity:** LOW (just need correct endpoint URL)

---

**For Coding Agent:** 
1. Research xAI Collections API documentation for correct endpoint
2. Test endpoint with curl to verify format
3. Update `xai_collections_client.py` with correct URL structure
4. Add better error messages showing attempted URL for debugging
