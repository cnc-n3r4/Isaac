# Isaac 2.0 Distributed System Implementation Plan

## Overview
This document outlines the 7-phase evolution of Isaac from a local AI-enhanced terminal assistant to a distributed multi-machine command system with offline caching, secure remote operations, and unified global AI context.

## Architecture Principles
- **Offline-First**: All operations work without internet/cloud connectivity
- **Security**: End-to-end encryption for sensitive data, HMAC authentication
- **Unified Experience**: Seamless operation across all machines in the home network
- **AI Enhancement**: Global command history provides rich context for AI queries
- **Backward Compatibility**: Existing local functionality remains unchanged

## Command Prefix System
- `/` prefix: Local meta-commands (introspection, configuration, local operations)
- `!` prefix: Remote operations (execute on other machines, messaging, distributed queries)
- No prefix: Standard shell commands with AI enhancement

## Phase 1: Command Prefix Foundation
**Goal**: Establish parsing and routing for / and ! commands

### Implementation
- Modify `permanent_shell.py` command parsing logic
- Add prefix detection before tier validation
- Route / commands to local handler, ! commands to distributed handler
- Maintain backward compatibility for unprefixed commands

### ASCII Flow
```
User Input
    ↓
Prefix Detection (/ ! or none)
    ↓
├── / → Local Command Handler
│       ├── /show history → Display local history
│       ├── /show config → Display configuration
│       └── /sync → Manual cloud sync
├── ! → Distributed Command Handler
│       ├── !exec machine cmd → Remote execution
│       ├── !msg machine text → Send message
│       └── !query pattern → Distributed search
└── none → Standard Shell + AI Enhancement
        ├── Tier Validation (1-4)
        └── Execute with AI correction
```

## Phase 2: Local / Commands
**Goal**: Implement introspection and local control commands

### Commands to Implement
- `/show history [n]` - Display recent command history
- `/show config` - Display current configuration
- `/show machines` - List known machines in network
- `/show status` - Show sync status and connectivity
- `/sync [force]` - Trigger manual cloud synchronization
- `/clear history` - Clear local command history
- `/set config key value` - Update configuration settings

### Database Schema (Local SQLite)
```
CREATE TABLE commands (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    command TEXT NOT NULL,
    output TEXT,
    machine_id TEXT,
    synced BOOLEAN DEFAULT FALSE
);

CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE machines (
    id TEXT PRIMARY KEY,
    name TEXT,
    ip_address TEXT,
    last_seen DATETIME,
    status TEXT
);
```

## Phase 3: Cloud Infrastructure
**Goal**: Build offline caching and cloud sync foundation

### Local Cache Implementation
```python
class LocalCache:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        # Create tables as shown above
    
    def store_command(self, command: str, output: str):
        # Insert with synced=False
    
    def get_unsynced_commands(self) -> List[Command]:
        # Return commands where synced=False
    
    def mark_synced(self, command_ids: List[int]):
        # Update synced=True for given IDs
```

### Sync Engine
```python
class SyncEngine:
    def __init__(self, cache: LocalCache, api_client: CloudAPI):
        self.cache = cache
        self.api_client = api_client
    
    def sync(self):
        unsynced = self.cache.get_unsynced_commands()
        if unsynced:
            self.api_client.upload_commands(unsynced)
            self.cache.mark_synced([c.id for c in unsynced])
        
        # Download new commands from other machines
        remote_commands = self.api_client.download_commands()
        for cmd in remote_commands:
            self.cache.store_remote_command(cmd)
```

### Cloud API Endpoints
- `POST /commands` - Upload command batch
- `GET /commands?since=timestamp` - Download new commands
- `POST /messages` - Send inter-machine messages
- `GET /messages?machine=target` - Retrieve messages

## Phase 4: Remote ! Commands
**Goal**: Enable execution and messaging across machines

### Commands to Implement
- `!exec <machine> <command>` - Execute command on remote machine
- `!msg <machine> <message>` - Send message to remote machine
- `!query <pattern>` - Search command history across all machines
- `!status <machine>` - Check remote machine status

### Message Flow
```
Local Isaac → Cloud Relay → Target Machine Isaac
    ↑                                       ↓
Cloud Relay ← Target Machine Response ← Local Isaac
```

### ASCII Database Schema (Cloud)
```
machines/
├── machine_1/
│   ├── commands/
│   │   ├── 2024-01-01.json
│   │   └── 2024-01-02.json
│   └── messages/
│       └── inbox.json
└── machine_2/
    └── ...
```

## Phase 5: Global History & Search
**Goal**: Unified search across all machines' command histories

### Search Implementation
```python
class GlobalSearch:
    def search(self, pattern: str, machines: List[str] = None) -> List[SearchResult]:
        # Search local cache first (offline)
        local_results = self._search_local(pattern)
        
        # If online, search cloud for other machines
        if self._is_online():
            cloud_results = self.api_client.search_commands(pattern, machines)
            return self._merge_results(local_results, cloud_results)
        
        return local_results
```

### Features
- Full-text search across all command history
- Filter by machine, date range, command type
- Offline search in local cache
- Real-time sync of search indexes

## Phase 6: AI Global Context
**Goal**: Enhance AI responses with global command history context

### Context Building
```python
def build_ai_context(self, query: str) -> str:
    # Get recent global commands
    recent_commands = self.global_search.get_recent_commands(limit=50)
    
    # Build context string
    context = "Recent command history across all machines:\\n"
    for cmd in recent_commands:
        context += f"- {cmd.machine}: {cmd.command}\\n"
    
    return context
```

### Enhanced System Prompt
```
You are Isaac, an AI-enhanced terminal assistant with access to command history across multiple machines in a home network.

Recent activity:
{machine_name}: ls -la
{machine_name}: git status
{other_machine}: docker ps

User query: {query}

Provide helpful responses and command suggestions based on this global context.
```

## Phase 7: Security & Encryption
**Goal**: Implement end-to-end encryption and secure authentication

### Security Features
- **E2E Encryption**: Sensitive data encrypted with machine-specific keys
- **HMAC Authentication**: API requests signed with shared secrets
- **TTL Tokens**: Time-limited authentication tokens
- **Certificate Pinning**: Prevent MITM attacks on cloud relay

### Encryption Flow
```
Sensitive Data → Encrypt with Machine Key → Store/Transmit
    ↓
Receive → Decrypt with Machine Key → Process
```

### Key Management
- Machine-specific encryption keys stored locally
- Cloud relay uses HMAC for request authentication
- Certificate-based authentication for machine registration

## Implementation Timeline
1. **Phase 1**: 1-2 weeks - Command prefix parsing
2. **Phase 2**: 1 week - Local / commands and SQLite cache
3. **Phase 3**: 2 weeks - Cloud sync infrastructure
4. **Phase 4**: 2 weeks - Remote ! commands
5. **Phase 5**: 1 week - Global search
6. **Phase 6**: 1 week - AI context integration
7. **Phase 7**: 2 weeks - Security hardening

## Testing Strategy
- Unit tests for each component
- Integration tests for sync functionality
- End-to-end tests for distributed operations
- Offline simulation tests
- Security penetration testing

## Migration Strategy
- Maintain backward compatibility throughout
- Gradual rollout: start with local features, add distributed features incrementally
- Configuration flags to enable/disable distributed features
- Automatic database migration for schema updates

## Success Criteria
- All commands work offline
- Seamless sync when connectivity restored
- Secure communication between machines
- AI responses improved with global context
- No breaking changes to existing functionality


┌─────────────────┐    ┌──────────────────┐
│   ISAAC LOCAL   │    │   LOCAL CACHE    │
│                 │    │   (SQLite)       │
│ • Commands      │◄──►│ • pending_cmds   │
│ • AI Queries    │    │ • pending_ai     │
│ • Messages      │    │ • pending_msgs   │
│ • History       │    │ • local_history  │
└─────────┬───────┘    └─────────┬────────┘
          │                      │
          │                      │
          ▼                      ▼
   ┌─────────────┐       ┌─────────────┐
   │   CLOUD     │       │   SYNC      │
   │   RELAY     │◄─────►│   ENGINE    │
   └─────────────┘       └─────────────┘



┌─────────────────────────────────────┐
│         CLOUD RELAY/HUB             │
│  (Auth, Routing, Encrypted Storage) │
│                                     │
│  ┌─────────────────┐ ┌────────────┐ │
│  │ CMD_HISTORY_DB  │ │ AI_HISTORY │ │
│  │ (encrypted)     │ │ (encrypted)│ │
│  └─────────┬───────┘ └─────┬──────┘ │
└───────────┼────────────────┼────────┘
            │                │
    (encrypted)      (encrypted)
            │                │
┌───────────┼────────────────┼────────┐
│ MACHINE A │              MACHINE B │
│ • /search, /history       • /help  │
│ • !machineB cmd           • !machineA cmd │
│ • local shell cmds        • AI queries    │
│ • AI queries              • local shell   │
└─────────────────────────────┼────────┘
                              │
                       (E2E encrypted)