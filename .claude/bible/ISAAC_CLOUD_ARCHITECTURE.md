# Isaac Cloud Architecture

**Last Updated:** October 22, 2025  
**Status:** Active Development  
**Purpose:** Cloud caching strategy using xAI Collections + GoDaddy services

---

## Architecture Overview

Isaac uses **two cloud services** for different purposes:

```
┌────────────────────────────────────────────────────────┐
│  YOUR MACHINE (Isaac Shell)                            │
│  • Command execution                                    │
│  • Pipe engine                                          │
│  • AI command routing                                   │
└───────┬─────────────────────────┬──────────────────────┘
        │                         │
        │                         │
        ▼                         ▼
┌──────────────────────┐  ┌──────────────────────────┐
│ xAI Collections      │  │ GoDaddy PHP API          │
│ (Data Cache)         │  │ (Session Sync)           │
│                      │  │                          │
│ • Semantic search    │  │ • Command history        │
│ • Document storage   │  │ • User preferences       │
│ • Vector embeddings  │  │ • Session state          │
│ • AI analysis        │  │ • Machine awareness      │
└──────────────────────┘  └──────────────────────────┘
```

---

## Cloud Service 1: xAI Collections (Primary Cache)

### Purpose
**Long-term semantic document storage with AI-powered search**

### API Endpoint
`https://api.x.ai/v1/...` (Collections Management API)

### What Gets Stored
- Research documents (PDFs, markdown)
- News articles (fetched + parsed)
- Log files (system, application)
- Command output (piped data)
- Any text/JSON blobs

### Data Structure
```json
{
  "collection_id": "uuid-news-cache",
  "documents": [
    {
      "id": "doc-123",
      "content": "Article full text...",
      "metadata": {
        "source": "TechCrunch",
        "url": "https://...",
        "timestamp": "2025-10-22T10:00:00Z",
        "cast_by": "isaac",
        "original_file": "article.json"
      },
      "embedding": [0.123, 0.456, ...],  // Auto-generated
      "indexed": true
    }
  ]
}
```

### Operations

**Create Collection:**
```bash
$> /mine init news_cache
Collection 'news_cache' created (UUID: abc-123)
```

**Upload (Cast) Data:**
```bash
$> /mine cast article.pdf news_cache
Cast into mine: article.pdf → news_cache (1.2 MB)
Embedded and indexed in 2.3s
```

**Search (Dig):**
```bash
$> /mine dig "AI policy news"
🔍 Searching news_cache...
Found 3 relevant chunks:
1. "EU proposes new AI regulations..." (relevance: 0.89)
2. "White House announces AI framework..." (relevance: 0.82)
3. "Tech companies respond to policy..." (relevance: 0.76)
```

**List Collections:**
```bash
$> /mine ls
Collections:
• news_cache (40 documents, 15.2 MB)
• research_notes (12 documents, 3.8 MB)
• tc_logs (156 documents, 8.9 MB)
• cpf_logs (89 documents, 4.2 MB)
```

### Cost Model
- Storage: Pay for what you store (MB)
- Search: Pay per query (cheap)
- Embeddings: Auto-generated (included)
- No egress fees for search results

### Advantages
✅ Semantic search (vector similarity)  
✅ Natural language queries  
✅ Automatic embeddings  
✅ Cross-machine access  
✅ No schema maintenance  
✅ Built-in AI integration  

---

## Cloud Service 2: GoDaddy PHP API (Session Sync)

### Purpose
**Real-time session state sync across machines**

### API Endpoint
`https://n3r4.xyz/isaac/api/`

### Authentication
Bearer token in `~/.isaac/config.json`

### What Gets Stored
- Command history (per terminal)
- User preferences (settings)
- AI query history (private)
- Task execution logs
- Active collection context
- Last machine used

### Data Structure

**Session Files:**
```
preferences.json         - User settings, API keys, defaults
command_history.json     - Shell commands (machine-aware)
aiquery_history.json     - AI chat history (private)
task_history.json        - Multi-step task logs
learned_autofixes.json   - Correction patterns
learned_patterns.json    - User behavior patterns
```

**Example - preferences.json:**
```json
{
  "user": {
    "name": "username",
    "email": "user@example.com"
  },
  "xai": {
    "api_key": "xai-...",
    "model": "grok-3",
    "collections": {
      "news_cache": "uuid-abc-123",
      "research_notes": "uuid-def-456"
    }
  },
  "cloud": {
    "enabled": true,
    "sync_interval": 300
  },
  "active_collection": "news_cache"
}
```

**Example - command_history.json:**
```json
{
  "terminal_id": "desktop-powershell-001",
  "machine": "desktop-pc",
  "history": [
    {
      "command": "/mine dig \"AI news\"",
      "timestamp": "2025-10-22T10:15:00Z",
      "exit_code": 0,
      "tier": 1
    }
  ]
}
```

### Operations

**Save Session:**
```http
POST https://n3r4.xyz/isaac/api/save_session.php
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "user123",
  "session_type": "preferences",
  "data": {...}
}
```

**Load Session:**
```http
GET https://n3r4.xyz/isaac/api/get_session.php?user_id=user123&type=preferences
Authorization: Bearer <token>
```

### Sync Frequency
- **On change:** Preferences updated immediately
- **Periodic:** Command history every 5 minutes
- **On exit:** Final sync before Isaac closes

### Advantages
✅ Multi-machine continuity  
✅ Arrow-key history works everywhere  
✅ Settings sync automatically  
✅ Backup/restore built-in  

---

## Data Flow: Collections vs Session

### When to Use Collections (xAI)

**Long-term data storage:**
- Documents for research
- News articles for digest
- Log files for analysis
- Any content you'll query with AI

**Pattern:**
```bash
$> /mine cast <data>      # Write once
$> /mine dig "query"      # Read many times
```

### When to Use Session Sync (GoDaddy)

**Ephemeral state:**
- Command history
- Current settings
- Active collection
- Recent AI chats

**Pattern:**
```python
# Automatic background sync
session.save_preferences()  # Triggered on change
session.save_history()      # Triggered every 5 min
```

---

## Cloud Caching Strategy

### Cache Hierarchy

```
Level 1: Local RAM
├─ Active command results (current session)
├─ Recently used Collections data
└─ In-flight pipe transformations

Level 2: xAI Collections (Cloud Cache)
├─ Semantic document storage
├─ Query results (vector search)
└─ AI analysis outputs

Level 3: GoDaddy Session (Cloud State)
├─ Preferences (global settings)
├─ Command history (per-machine)
└─ AI chat log (cross-machine)
```

### Write Strategy

**Immediate write:**
- User preferences changes
- New documents to Collections

**Batched write:**
- Command history (every 5 min)
- AI query log (every 10 min)

**Deferred write:**
- Analytics data
- Usage statistics

### Read Strategy

**Cache first:**
```python
# Check Collections before re-fetching
if collection_has("news_cache", recent=6_hours):
    # Use cached data
    results = /mine dig "query"
else:
    # Refresh cache
    fetch_and_cache()
```

**Smart prefetch:**
```python
# Preload frequently used collections
on_startup:
    if user.active_collection:
        preload(user.active_collection)
```

---

## Cost Optimization

### Collections (xAI)

**Expensive:**
- ❌ Uploading large files repeatedly
- ❌ Re-embedding same content
- ❌ Storing duplicate data

**Cheap:**
- ✅ Semantic search queries
- ✅ Reading cached results
- ✅ Incremental updates

**Strategy:**
```bash
# Don't do this (wasteful):
$> curl api.example.com/data | /mine cast cache_name  # Every minute

# Do this (smart caching):
$> curl api.example.com/data | /mine cast cache_name  # Every 6 hours
$> /mine dig "recent updates"                         # Anytime
```

### Session Sync (GoDaddy)

**Your own server = Cost-effective**
- PHP hosting already paid for
- Minimal API calls (background sync)
- Small data size (KB, not MB)

**Optimization:**
- Compress JSON before sending
- Only sync changed fields
- Batch multiple updates

---

## Offline Resilience

### When Cloud is Unavailable

**Collections (xAI):**
```bash
$> /mine cast data.json
⚠️ Cloud unavailable. Queuing upload...
[Stored locally: ~/.isaac/queue/pending_001.json]

# When connection returns:
[Isaac: Cloud reconnected. Uploading 3 queued items...]
✓ Uploaded data.json → news_cache
```

**Session Sync (GoDaddy):**
```bash
$> /config cloud off
Cloud sync disabled. Working offline.
[Commands still saved locally: ~/.isaac/local_history.json]

$> /config cloud on
Cloud sync enabled. Syncing 47 commands...
✓ Session synced
```

### Local Fallback

```python
# In session_manager.py
def save_preferences(self):
    try:
        # Try cloud first
        self.cloud_client.save("preferences", self.prefs)
    except ConnectionError:
        # Fall back to local
        self.save_local("preferences", self.prefs)
        self.queue_sync("preferences")
```

---

## Security & Privacy

### API Keys

**Stored locally:**
```json
// ~/.isaac/config.json
{
  "xai": {
    "api_key": "xai-..."    // Your xAI key
  },
  "cloud": {
    "bearer_token": "..."   // Your GoDaddy token
  }
}
```

**Never transmitted:**
- Keys stay on your machine
- Cloud sync uses tokens, not keys
- Collections API uses your xAI key directly

### Data Privacy

**Collections (xAI):**
- Your account, your data
- Subject to xAI privacy policy
- Encrypted in transit (HTTPS)

**Session Sync (GoDaddy):**
- Your server, your control
- Can implement custom encryption
- Can add IP whitelisting

### Sensitive Data

**Don't cache:**
- Passwords, tokens, secrets
- Personal health data
- Financial records

**Do cache:**
- Research notes
- News articles
- Public logs
- Command history (non-sensitive)

---

## Scaling Considerations

### Growing Collections

**News Cache Example:**
```
Day 1:   40 articles (cron every 6h) =   160 articles
Week 1:  160 × 7 days               = 1,120 articles
Month 1: 1,120 × 4 weeks            = 4,480 articles
```

**Management strategy:**
```bash
# Prune old entries (future)
$> /mine prune news_cache --older-than 30d
Removed 2,240 articles older than 30 days
Collection now: 2,240 articles (10.2 MB)

# Or rotate collections
$> /mine init news_cache_nov_2025
$> /mine cast latest_news.json news_cache_nov_2025
```

### API Rate Limits

**xAI Collections:**
- Check their rate limits
- Implement backoff/retry
- Queue if limit reached

**GoDaddy Session:**
- Your server, your limits
- Can implement rate limiting in PHP
- Can add caching layer (Redis)

---

## Multi-User Considerations (Future)

### Shared Collections

```bash
# User 1:
$> /mine cast report.pdf team_research

# User 2 (same team):
$> /mine use team_research
$> /mine dig "what did we learn?"
```

**Requirements:**
- xAI Collections permissions (if supported)
- Shared access tokens
- Team namespace in config

### Private Collections

```bash
$> /mine cast personal_notes.md private_notes --private
Collection 'private_notes' is private (only you can access)
```

---

## Monitoring & Debugging

### Cloud Health Check

```bash
$> /status
Isaac Status:
• Shell: PowerShell 5.1
• Cloud Sync: ☁️  Online (n3r4.xyz)
• AI: 🤖 Connected (xAI grok-3)
• Collections: 4 available (18.2 MB total)
• Last sync: 2 minutes ago
```

### Debug Mode

```bash
$> /config debug on
Debug mode enabled. Logging API calls...

$> /mine dig "test"
[DEBUG] Collections API: GET /search
[DEBUG] Request: {"query": "test", "collection": "news_cache"}
[DEBUG] Response: 200 OK (234ms)
[DEBUG] Results: 3 chunks found
```

---

## Next Steps

### Phase 1 Piping Enables:
1. **Pipe to Collections:** `python fetch.py | /mine cast`
2. **Pipe from Collections:** `/mine dig "query" | /save`
3. **Chain analysis:** `/mine dig | /analyze | /save`

### Your Workflow:
1. ✅ Collections configured (tc_logs, cpf_logs)
2. ✅ Session sync working (GoDaddy API)
3. 🚧 Phase 1 piping (in progress)
4. 🚧 News digest cron (after piping)
5. 🎯 Query cached data anytime

**You're building a personal semantic cache for everything that matters to you.** 🚀
