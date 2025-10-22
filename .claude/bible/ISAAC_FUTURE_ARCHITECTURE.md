# Isaac Future Architecture - Complete Flow Chart

## Project Vision Summary

**Isaac: Intelligent System Assistant And Command**

A CLI-first, AI-enhanced orchestration platform that brings 1980s terminal simplicity to 2025's connected world. Everything is pipeable, everything is scriptable, no GUI required.

**Current Focus:** Build Isaac core (shell wrapper, AI integration, project management)  
**Future Vision:** Unified CLI interface for email, chat, web, files, and collaboration

---

## Master Command Flow Architecture

### Level 0: User Input → Isaac Router

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INPUT                              │
│  (@command, /command, !bang, regular shell, natural lang)   │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                  ISAAC COMMAND ROUTER                        │
│  - Classify input type                                       │
│  - Check authentication (key system)                         │
│  - Route to appropriate handler                              │
└──────┬──────┬──────┬──────┬──────┬──────┬──────────────────┘
       ↓      ↓      ↓      ↓      ↓      ↓
     @cmd   /cmd   !bang  shell  NL   piped
```

### Level 1: Command Type Routing

```
┌───────────────────────────────────────────────────────────────┐
│  COMMAND TYPE CLASSIFICATION                                  │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  @ Internal Commands (Isaac system)                           │
│  ├─ @workspace → WorkspaceContext                            │
│  ├─ @sandbox → SandboxManager                                │
│  ├─ @sync → CloudClient                                       │
│  ├─ @debug → DiagnosticSystem                                │
│  └─ @<name> → Workspace shortcut                             │
│                                                                │
│  / Isaac Commands (user-facing)                               │
│  ├─ /ask → AIValidator                                        │
│  ├─ /task → TaskPlanner                                       │
│  ├─ /projio → ProjectManager                                  │
│  ├─ /mine → CollectionsManager                                │
│  └─ /config → ConfigManager                                   │
│                                                                │
│  ! Bang Routing (cross-channel)                               │
│  ├─ !isaac → Isaac core                                       │
│  ├─ !sarah → Persona switcher                                 │
│  ├─ !telegram → Telegram integration                          │
│  └─ !<bot> → Bot dispatcher                                   │
│                                                                │
│  Shell Commands (tier-based safety)                           │
│  ├─ Tier ≤2 → Execute immediately                            │
│  └─ Tier ≥3 → AI validation required                         │
│                                                                │
│  Natural Language (isaac <query>)                             │
│  └─ AITranslator → Shell command → Route                     │
│                                                                │
│  Piped Input (stdin blob)                                     │
│  └─ Parse blob → Extract command → Route with context        │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

---

## Example Flow Charts (From Future Vision)

### Example 1: `/projio send | email:jimbob "here's the project"`

```
User Input: /projio send | email:jimbob "here's the project"
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. PARSE PIPELINE                                            │
│    Left: /projio send                                        │
│    Right: email:jimbob "here's the project"                 │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. EXECUTE LEFT SIDE: /projio send                          │
│    ├─ Check active workspace (@workspace context)           │
│    ├─ Workspace: jimbobs-project                            │
│    ├─ ProjectPackager.send()                                │
│    │  ├─ Collect files (respect .projio.json ignores)       │
│    │  ├─ Generate skeleton (if --include-skeleton)          │
│    │  ├─ Scan dependencies (if --include-deps)              │
│    │  └─ Create blob: {kind: "text", content: "...", ...}   │
│    └─ OUTPUT: Blob (text/json)                              │
└─────────────────────┬───────────────────────────────────────┘
                      ↓ (pipe)
┌─────────────────────────────────────────────────────────────┐
│ 3. EXECUTE RIGHT SIDE: email:jimbob "here's the project"   │
│    ├─ Protocol Handler: email:                              │
│    ├─ EmailIntegration.send()                               │
│    │  ├─ Parse recipient: jimbob → jimbob@example.com       │
│    │  ├─ Parse subject: "here's the project"                │
│    │  ├─ INPUT blob: Project snapshot (2.3MB)               │
│    │  ├─ AI enhancement:                                     │
│    │  │  └─ /ask "summarize this project in 3 sentences"    │
│    │  │     → "Web dashboard with auth system, ..."         │
│    │  ├─ Format email:                                       │
│    │  │  Subject: here's the project                        │
│    │  │  Body: AI summary + attachment link                 │
│    │  ├─ SMTP send (or API call)                            │
│    │  └─ Log to cloud: email_history.json                   │
│    └─ OUTPUT: "✉ Sent to: jimbob@example.com (2.3MB)"      │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. DISPLAY RESULT                                            │
│    ✉ Preparing project blob...                             │
│    ✉ AI summary: "Web dashboard with auth system"          │
│    ✉ Sent to: jimbob@example.com (2.3MB)                   │
└─────────────────────────────────────────────────────────────┘
```

### Example 2: `inbox:unread | /ask "anything urgent?"`

```
User Input: inbox:unread | /ask "anything urgent?"
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. EXECUTE LEFT: inbox:unread                               │
│    ├─ Protocol Handler: inbox:                              │
│    ├─ EmailIntegration.fetch_unread()                       │
│    │  ├─ Connect to email (IMAP/API)                        │
│    │  ├─ Fetch unread messages                              │
│    │  ├─ Format as blob:                                     │
│    │  │  {                                                   │
│    │  │    kind: "email_list",                              │
│    │  │    content: [                                        │
│    │  │      {from: "boss", subject: "Status?", body: ""},  │
│    │  │      {from: "jimbob", subject: "Thanks!", ...},     │
│    │  │      {from: "newsletter", subject: "AI Weekly"...}  │
│    │  │    ]                                                 │
│    │  │  }                                                   │
│    │  └─ OUTPUT: Email list blob                            │
└─────────────────────┬───────────────────────────────────────┘
                      ↓ (pipe)
┌─────────────────────────────────────────────────────────────┐
│ 2. EXECUTE RIGHT: /ask "anything urgent?"                   │
│    ├─ INPUT: Email list blob (3 messages)                   │
│    ├─ Query: "anything urgent?"                             │
│    ├─ AIValidator.analyze()                                 │
│    │  ├─ Context: 3 emails with subjects/senders            │
│    │  ├─ AI prompt:                                          │
│    │  │  "Analyze these emails for urgency:                 │
│    │  │   1. Boss: 'Status?' - SENDER: boss                │
│    │  │   2. Jimbob: 'Thanks!' - SENDER: jimbob             │
│    │  │   3. Newsletter: 'AI Weekly' - SENDER: auto"        │
│    │  ├─ AI response:                                        │
│    │  │  "Email #1 from boss is urgent - requesting status  │
│    │  │   update. Others can wait."                         │
│    │  └─ OUTPUT: AI analysis text                           │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. DISPLAY RESULT                                            │
│    Email #1 from boss is urgent - requesting status update. │
│    Others can wait.                                          │
└─────────────────────────────────────────────────────────────┘
```

### Example 3: `!telegram:@jimbob /projio send -pro my-app`

```
Telegram App: User types: !isaac !telegram:@jimbob /projio send -pro my-app
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. TELEGRAM BOT RECEIVES MESSAGE                            │
│    ├─ Parse: !isaac (route to Isaac)                        │
│    ├─ Command: !telegram:@jimbob /projio send -pro my-app   │
│    ├─ Enqueue to cloud:                                      │
│    │  {                                                      │
│    │    source: "telegram",                                 │
│    │    user_id: 12345,                                     │
│    │    command: "!telegram:@jimbob /projio send -pro...",  │
│    │    timestamp: "...",                                    │
│    │    key: "telegram-webhook"                             │
│    │  }                                                      │
│    └─ Cloud: command_queue.json updated                     │
└─────────────────────┬───────────────────────────────────────┘
                      ↓ (cloud)
┌─────────────────────────────────────────────────────────────┐
│ 2. ISAAC DAEMON POLLS CLOUD (every 5s)                      │
│    ├─ Fetch: command_queue.json                             │
│    ├─ Found: Command from telegram user                     │
│    ├─ Verify: key = "telegram-webhook" (matches daemon)     │
│    └─ ROUTE TO COMMAND ROUTER                               │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. PARSE COMMAND: !telegram:@jimbob /projio send -pro...   │
│    ├─ Protocol: !telegram: (Telegram integration)           │
│    ├─ Recipient: @jimbob                                     │
│    ├─ Content command: /projio send -pro my-app             │
│    └─ EXECUTE CONTENT COMMAND FIRST                         │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. EXECUTE: /projio send -pro my-app                        │
│    ├─ WorkspaceContext: Find workspace "my-app"             │
│    ├─ ProjectPackager.send(project_dir=my-app)              │
│    ├─ Create blob (files, skeleton, deps)                   │
│    └─ OUTPUT: Project blob (1.5MB)                          │
└─────────────────────┬───────────────────────────────────────┘
                      ↓ (pass blob to protocol handler)
┌─────────────────────────────────────────────────────────────┐
│ 5. EXECUTE PROTOCOL: !telegram:@jimbob                      │
│    ├─ TelegramIntegration.send_message()                    │
│    │  ├─ Recipient: @jimbob (Telegram username)             │
│    │  ├─ INPUT: Project blob (1.5MB)                        │
│    │  ├─ Format:                                             │
│    │  │  - Compress blob → .zip                             │
│    │  │  - AI summary: "my-app: React dashboard, 47 files"  │
│    │  │  - Upload to Telegram as document                   │
│    │  ├─ Telegram API: sendDocument()                       │
│    │  └─ Result: Message ID 67890                           │
│    └─ OUTPUT: "✈ Sent to @jimbob via Telegram (1.5MB)"     │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. SAVE RESULT TO CLOUD                                     │
│    ├─ command_results.json: Add result                      │
│    └─ Remove from command_queue.json                        │
└─────────────────────┬───────────────────────────────────────┘
                      ↓ (cloud)
┌─────────────────────────────────────────────────────────────┐
│ 7. TELEGRAM BOT POLLS FOR RESULT (every 1s, 30s timeout)   │
│    ├─ Found: Result for timestamp                           │
│    ├─ Extract: "✈ Sent to @jimbob via Telegram (1.5MB)"    │
│    └─ REPLY TO USER IN TELEGRAM                             │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. USER SEES IN TELEGRAM APP                                │
│    Isaac Bot:                                                │
│    ✈ Sent to @jimbob via Telegram (1.5MB)                  │
│                                                              │
│    (Jimbob also receives separate Telegram message with     │
│     the project.zip file)                                    │
└─────────────────────────────────────────────────────────────┘
```

### Example 4: `@my-web-app` (workspace shortcut)

```
User Input: @my-web-app
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. PARSE: @ command                                          │
│    ├─ Check: Is this a reserved @ command?                  │
│    │  (@workspace, @sandbox, @sync, @debug?)                │
│    │  → NO                                                   │
│    ├─ Try: Workspace shortcut                               │
│    └─ ROUTE TO: WorkspaceContext.set_workspace()            │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. WORKSPACE CONTEXT: set_workspace("my-web-app")           │
│    ├─ Load: workspaces.json (from cloud)                    │
│    ├─ Fuzzy match: "my-web-app"                             │
│    │  └─ Found: {name: "my-web-app", path: "~/Projects/..."}│
│    ├─ Check: Locked by other terminal?                      │
│    │  └─ NO (or expired)                                    │
│    ├─ Update:                                                │
│    │  ├─ active_workspace = "my-web-app"                    │
│    │  ├─ last_accessed = NOW                                │
│    │  ├─ last_terminal = current terminal ID                │
│    │  └─ history.insert(0, "my-web-app")                    │
│    ├─ Save: workspaces.json (to cloud)                      │
│    └─ OUTPUT: "Workspace: old-workspace → my-web-app"       │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. DISPLAY RESULT                                            │
│    Workspace: jimbobs-project → my-web-app                  │
│                                                              │
│    (All subsequent /projio commands now use my-web-app)     │
└─────────────────────────────────────────────────────────────┘
```

### Example 5: `fetch:google.com | /ask "summarize this page"`

```
User Input: fetch:google.com | /ask "summarize this page"
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. EXECUTE LEFT: fetch:google.com                           │
│    ├─ Protocol Handler: fetch:                              │
│    ├─ WebIntegration.fetch_page()                           │
│    │  ├─ HTTP GET: https://google.com                       │
│    │  ├─ Extract: HTML content                              │
│    │  ├─ Parse: Remove scripts, styles, extract text        │
│    │  ├─ Format blob:                                        │
│    │  │  {                                                   │
│    │  │    kind: "webpage",                                 │
│    │  │    content: "Google\n\nSearch the world's info...", │
│    │  │    meta: {url: "google.com", title: "Google"}       │
│    │  │  }                                                   │
│    │  └─ OUTPUT: Webpage blob                               │
└─────────────────────┬───────────────────────────────────────┘
                      ↓ (pipe)
┌─────────────────────────────────────────────────────────────┐
│ 2. EXECUTE RIGHT: /ask "summarize this page"               │
│    ├─ INPUT: Webpage blob (text content)                    │
│    ├─ Query: "summarize this page"                          │
│    ├─ Smart truncation (if >8k chars)                       │
│    ├─ AI prompt:                                             │
│    │  "Summarize this webpage:                              │
│    │   URL: google.com                                       │
│    │   Content: <truncated text>"                           │
│    ├─ AI response:                                           │
│    │  "Google's homepage - search engine interface with     │
│    │   search box and links to services like Gmail, Images" │
│    └─ OUTPUT: Summary text                                  │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. DISPLAY RESULT                                            │
│    Google's homepage - search engine interface with search  │
│    box and links to services like Gmail, Images             │
└─────────────────────────────────────────────────────────────┘
```

---

## Protocol Handler Registry

**How Isaac knows what `email:`, `fetch:`, `!telegram:` means:**

```
┌─────────────────────────────────────────────────────────────┐
│  PROTOCOL HANDLER REGISTRY                                   │
│  (isaac/integrations/protocol_registry.py)                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  email:      → EmailIntegration (SMTP/IMAP/API)             │
│  inbox:      → EmailIntegration.inbox()                     │
│  fetch:      → WebIntegration (HTTP/HTTPS)                  │
│  !telegram:  → TelegramIntegration                          │
│  !discord:   → DiscordIntegration (future)                  │
│  !slack:     → SlackIntegration (future)                    │
│  dropbox:    → DropboxIntegration (future)                  │
│  gdrive:     → GoogleDriveIntegration (future)              │
│  ftp:        → FTPIntegration (future)                      │
│  github:     → GitHubIntegration (future)                   │
│  twitter:    → TwitterIntegration (future)                  │
│  calendar:   → CalendarIntegration (future)                 │
│  todo:       → TodoIntegration (future)                     │
│                                                               │
│  Each integration implements:                                │
│  - send(blob) → Send data out                               │
│  - fetch(query) → Fetch data in                             │
│  - format(blob) → Convert to integration format             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Current vs Future Implementation

### Phase 1: CURRENT (Building Now)

```
✅ Core Isaac shell wrapper
✅ Command routing (/ask, /task, /mine, /config)
✅ Tier-based safety system
✅ AI integration (xAI Grok)
✅ Cloud sync (PHP API)
✅ Collections integration (/mine)
✅ Config console (MVP)
🔄 /projio port (in progress)
```

### Phase 2: Foundation (Next 3-6 months)

```
📋 Key system (authentication)
📋 @workspace context manager
📋 Sandbox system
📋 Isaac-Root (Janitor)
📋 Telegram integration (daemon mode)
📋 !bang routing system
📋 Protocol handler registry (foundation)
```

### Phase 3: Integration Wave 1 (6-12 months)

```
🔮 email: protocol (SMTP/IMAP)
🔮 inbox: protocol
🔮 fetch: protocol (web scraping)
🔮 !telegram: full integration
🔮 dropbox: / gdrive: protocols
🔮 Workspace snapshots/export/import
```

### Phase 4: Integration Wave 2 (12-18 months)

```
🔮 !discord:, !slack: protocols
🔮 github: protocol (API integration)
🔮 calendar:, todo: protocols
🔮 twitter:, linkedin: protocols (if APIs allow)
🔮 Advanced piping (multi-stage workflows)
🔮 Bot ecosystem (code-bot, test-bot, deploy-bot)
```

---

## Key Architecture Principles

### 1. Everything is a Blob
```python
# Standard blob format
{
  "kind": "text|json|webpage|email|project|workspace",
  "content": "...",  # The actual data
  "meta": {          # Metadata for context
    "source_command": "/projio send",
    "timestamp": "...",
    "size": 1234
  }
}
```

### 2. Piping is First-Class
```bash
# Every command can be:
# - Input: Accept stdin blob
# - Output: Produce stdout blob
# - Composed: Chain with | operator

/projio send | /ask "review" | /save result.txt
```

### 3. Protocols are Pluggable
```python
# New protocol = new class
class MyProtocolIntegration(BaseIntegration):
    def send(self, blob): ...
    def fetch(self, query): ...
    
# Register
register_protocol("myproto:", MyProtocolIntegration)

# Use
$> myproto:send "data"
```

### 4. Cloud Sync Enables Multi-Terminal
```bash
# Laptop: Start task
/task "deploy project"

# Desktop: See task (cloud-synced)
/task list  # Shows laptop's task

# Phone: Monitor status
!telegram !isaac !task status 1
```

### 5. AI Enhances Everything
```bash
# AI summarizes emails
inbox:unread | /ask "urgent?"

# AI reviews code
/projio send | /ask "security issues?"

# AI formats output
/projio skeleton | /ask "make this professional" | email:client
```

---

## Success Metrics

**When Isaac is "done" (v1.0):**
- ✅ Can manage projects (/projio)
- ✅ Can orchestrate tasks (/task)
- ✅ Can query AI (/ask)
- ✅ Can store knowledge (/mine)
- ✅ Syncs across machines (cloud)
- ✅ Sandbox-safe (tier system)
- ✅ Multi-terminal aware (@workspace)
- ✅ Key-authenticated (security)
- ✅ Telegram-controllable (!bang)

**When Isaac is "amazing" (v2.0+):**
- ✅ Sends emails from CLI (email:)
- ✅ Fetches web pages (fetch:)
- ✅ Integrates with chat (Telegram/Discord/Slack)
- ✅ Shares files (Dropbox/GDrive)
- ✅ Bot ecosystem (code-bot, deploy-bot)
- ✅ Everything pipeable, everything scriptable
- ✅ 1980s CLI aesthetic, 2025 AI power

---

**Current Status:** Building Phase 1 (Core Isaac)  
**Next Focus:** Complete /projio port, fix Collections search bug  
**Long-term Vision:** CLI revolution - take back the terminal! 🚀

---

*"For a good long while, it's just Isaac. Our Intelligent System Assistant And Command."*
