# Track 1.2: Command Queue Overlay - Complete Implementation Specification

**Target:** Coding Agent (Implement / YAML Maker)  
**Prerequisites:** ✅ Track 1.1 Complete (Dispatcher working)  
**Estimated Time:** 3-4 hours  
**Complexity:** Medium  
**Priority:** High (completes Track 1 foundation)

---

## Executive Summary

Implement local SQLite-based command queue to prevent data loss when cloud connection is unavailable. Commands queue locally, background thread auto-syncs when connection restores, user gets visual feedback via prompt indicator.

**Core Value:** User never loses commands due to network issues.

---

## Architecture Overview

### High-Level Flow

```
Command Execution Attempt
         ↓
Is Cloud Available? → YES → Execute normally
         ↓
        NO
         ↓
Queue Locally (SQLite)
         ↓
Update Prompt: isaac [OFFLINE: N queued]>
         ↓
Background Worker: Check connection every 30s
         ↓
Connection Restored → Dequeue & Sync
         ↓
Notification: "N queued commands synced"
         ↓
Prompt Returns: isaac>
```

### Component Map

```
isaac/queue/
├── command_queue.py         # SQLite persistence layer
└── sync_worker.py           # Background sync thread

isaac/core/
├── session_manager.py       # Initialize queue + worker
└── command_router.py        # Fallback to queue on cloud failure

isaac/ui/
└── permanent_shell.py       # Display [OFFLINE: N queued] indicator

isaac/commands/
├── queue/                   # View queued commands
│   ├── command.yaml
│   └── run.py
└── sync/                    # Force immediate sync
    ├── command.yaml
    └── run.py
```

---

## Database Schema

### SQLite Database
**Location:** `~/.isaac/queue.db`  
**Purpose:** Persist commands across restarts, track sync status

```sql
CREATE TABLE command_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    queued_at TEXT NOT NULL,              -- ISO8601 timestamp (UTC)
    command_type TEXT NOT NULL,           -- 'meta' | 'shell' | 'device_route'
    command_text TEXT NOT NULL,           -- Full command string
    target_device TEXT,                   -- For !alias routing (null = local)
    retry_count INTEGER DEFAULT 0,        -- Failed sync attempts
    last_retry_at TEXT,                   -- Last retry timestamp
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'syncing' | 'done' | 'failed'
    error_message TEXT,                   -- Last error (if failed)
    metadata TEXT                         -- JSON blob (tier, validation result, etc.)
);

CREATE INDEX idx_status ON command_queue(status);
CREATE INDEX idx_queued_at ON command_queue(queued_at);
```

**Indexes:**
- `idx_status` - Fast lookup for pending/failed commands
- `idx_queued_at` - Chronological sync order

---

## Implementation Steps

### Phase 1: Core Queue Manager (90 minutes)

**File:** `isaac/queue/command_queue.py`

```python
"""
Command Queue - SQLite-based command persistence for offline resilience.

Provides atomic queue operations with retry tracking and automatic cleanup.
"""
from pathlib import Path
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class CommandQueue:
    """Local command queue with SQLite persistence."""
    
    def __init__(self, db_path: Path):
        """
        Initialize queue manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"Command queue initialized at {db_path}")
    
    def _init_db(self):
        """Create queue table and indexes if not exists."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS command_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                queued_at TEXT NOT NULL,
                command_type TEXT NOT NULL,
                command_text TEXT NOT NULL,
                target_device TEXT,
                retry_count INTEGER DEFAULT 0,
                last_retry_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                error_message TEXT,
                metadata TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON command_queue(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_queued_at ON command_queue(queued_at)")
        conn.commit()
        conn.close()
    
    def enqueue(self, command: str, command_type: str, 
                target_device: Optional[str] = None, 
                metadata: Optional[Dict] = None) -> int:
        """
        Add command to queue.
        
        Args:
            command: Full command string
            command_type: 'meta' | 'shell' | 'device_route'
            target_device: Device alias for routing (None = local)
            metadata: Additional context (tier, validation, etc.)
        
        Returns:
            Queue ID for tracking
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("""
            INSERT INTO command_queue 
            (queued_at, command_type, command_text, target_device, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            command_type,
            command,
            target_device,
            json.dumps(metadata or {})
        ))
        queue_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Queued command #{queue_id}: {command_type} - {command[:50]}")
        return queue_id
    
    def dequeue_pending(self, limit: int = 10) -> List[Dict]:
        """
        Get pending commands in FIFO order.
        
        Args:
            limit: Maximum commands to retrieve
        
        Returns:
            List of command dicts with all fields
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT * FROM command_queue 
            WHERE status='pending' 
            ORDER BY queued_at ASC
            LIMIT ?
        """, (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
    
    def mark_syncing(self, queue_id: int):
        """Mark command as currently being synced."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            UPDATE command_queue 
            SET status='syncing', last_retry_at=?
            WHERE id=?
        """, (datetime.utcnow().isoformat(), queue_id))
        conn.commit()
        conn.close()
    
    def mark_done(self, queue_id: int):
        """Mark command as successfully synced."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            UPDATE command_queue 
            SET status='done'
            WHERE id=?
        """, (queue_id,))
        conn.commit()
        conn.close()
        logger.info(f"Command #{queue_id} synced successfully")
    
    def mark_failed(self, queue_id: int, error: str):
        """
        Mark command as failed, increment retry count.
        
        Args:
            queue_id: Command to mark
            error: Error message for logging
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            UPDATE command_queue 
            SET status='failed', 
                retry_count=retry_count+1,
                error_message=?,
                last_retry_at=?
            WHERE id=?
        """, (error, datetime.utcnow().isoformat(), queue_id))
        conn.commit()
        conn.close()
        logger.warning(f"Command #{queue_id} failed: {error}")
    
    def reset_stale_syncing(self, timeout_minutes: int = 5):
        """
        Reset 'syncing' commands stuck for > timeout back to 'pending'.
        Prevents deadlock if sync worker crashes mid-sync.
        
        Args:
            timeout_minutes: How long before considering stuck
        """
        cutoff = (datetime.utcnow() - timedelta(minutes=timeout_minutes)).isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("""
            UPDATE command_queue 
            SET status='pending'
            WHERE status='syncing' 
              AND last_retry_at < ?
        """, (cutoff,))
        updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        if updated > 0:
            logger.warning(f"Reset {updated} stale 'syncing' commands to 'pending'")
    
    def get_queue_status(self) -> Dict:
        """
        Get queue statistics.
        
        Returns:
            {pending: int, failed: int, done: int, last_sync: str}
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("""
            SELECT status, COUNT(*) as count 
            FROM command_queue 
            GROUP BY status
        """)
        stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get last successful sync timestamp
        cursor = conn.execute("""
            SELECT MAX(queued_at) FROM command_queue WHERE status='done'
        """)
        last_sync = cursor.fetchone()[0]
        conn.close()
        
        return {
            'pending': stats.get('pending', 0),
            'failed': stats.get('failed', 0),
            'done': stats.get('done', 0),
            'last_sync': last_sync
        }
    
    def clear_old_entries(self, days: int = 7):
        """
        Delete successfully synced commands older than N days.
        
        Args:
            days: Retention period for 'done' commands
        """
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("""
            DELETE FROM command_queue 
            WHERE status='done' 
              AND queued_at < ?
        """, (cutoff,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old queue entries")
```

**Testing Checklist for Phase 1:**
```python
# Test file: tests/test_command_queue.py
def test_enqueue_dequeue():
    # Create queue, enqueue command, verify retrieval
    
def test_mark_done():
    # Enqueue, mark done, verify not in pending
    
def test_mark_failed():
    # Enqueue, mark failed, check retry_count increments
    
def test_reset_stale():
    # Mark syncing with old timestamp, reset, verify pending
    
def test_get_status():
    # Enqueue multiple, verify stats correct
    
def test_cleanup():
    # Create old 'done' entries, clean up, verify deleted
```

---

### Phase 2: Background Sync Worker (60 minutes)

**File:** `isaac/queue/sync_worker.py`

```python
"""
Sync Worker - Background thread for automatic command queue sync.

Monitors cloud availability and syncs pending commands when online.
"""
import threading
import time
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)

class SyncWorker:
    """Background thread that syncs queued commands when cloud is available."""
    
    def __init__(self, queue, cloud_client, check_interval: int = 30):
        """
        Initialize sync worker.
        
        Args:
            queue: CommandQueue instance
            cloud_client: CloudClient instance (must have is_available() method)
            check_interval: Seconds between availability checks
        """
        self.queue = queue
        self.cloud = cloud_client
        self.interval = check_interval
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.on_sync_complete: Optional[Callable[[int], None]] = None
        logger.info(f"Sync worker initialized (check every {check_interval}s)")
    
    def start(self):
        """Start background sync thread."""
        if self.running:
            logger.warning("Sync worker already running")
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()
        logger.info("Sync worker started")
    
    def stop(self):
        """Stop background thread gracefully."""
        if not self.running:
            return
        
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Sync worker stopped")
    
    def force_sync(self) -> int:
        """
        Force immediate sync attempt (for /sync command).
        
        Returns:
            Number of commands successfully synced
        """
        logger.info("Force sync requested")
        return self._sync_batch()
    
    def _sync_loop(self):
        """Main background loop with exponential backoff."""
        consecutive_failures = 0
        
        while self.running:
            try:
                # Reset stale 'syncing' states (in case of crash)
                self.queue.reset_stale_syncing()
                
                # Check cloud availability
                if not self._is_cloud_available():
                    time.sleep(self.interval)
                    continue
                
                # Attempt batch sync
                synced_count = self._sync_batch()
                
                if synced_count > 0:
                    consecutive_failures = 0  # Reset backoff
                    logger.info(f"Successfully synced {synced_count} commands")
                    
                    # Notify UI
                    if self.on_sync_complete:
                        self.on_sync_complete(synced_count)
                
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Sync loop error: {e}")
            
            # Exponential backoff on failures (max 5 minutes)
            wait_time = min(self.interval * (2 ** consecutive_failures), 300)
            time.sleep(wait_time)
    
    def _is_cloud_available(self) -> bool:
        """Check if cloud API is reachable."""
        try:
            return self.cloud.is_available()
        except Exception as e:
            logger.debug(f"Cloud availability check failed: {e}")
            return False
    
    def _sync_batch(self, batch_size: int = 10) -> int:
        """
        Sync up to N pending commands.
        
        Args:
            batch_size: Max commands to sync in one batch
        
        Returns:
            Number successfully synced
        """
        pending = self.queue.dequeue_pending(limit=batch_size)
        
        if not pending:
            return 0
        
        synced_count = 0
        
        for cmd in pending:
            queue_id = cmd['id']
            
            try:
                # Mark as syncing (prevents duplicate processing)
                self.queue.mark_syncing(queue_id)
                
                # Execute sync based on command type
                success = self._sync_command(cmd)
                
                if success:
                    self.queue.mark_done(queue_id)
                    synced_count += 1
                else:
                    self.queue.mark_failed(queue_id, "Sync returned false")
                    
            except Exception as e:
                self.queue.mark_failed(queue_id, str(e))
                logger.error(f"Failed to sync command #{queue_id}: {e}")
        
        return synced_count
    
    def _sync_command(self, cmd: dict) -> bool:
        """
        Execute sync for a single command.
        
        Args:
            cmd: Command dict from queue
        
        Returns:
            True if successfully synced
        """
        command_type = cmd['command_type']
        command_text = cmd['command_text']
        target_device = cmd['target_device']
        
        if command_type == 'device_route':
            # Route to target device via cloud
            return self.cloud.route_command(target_device, command_text)
        
        elif command_type == 'meta':
            # Meta-command that needs cloud (e.g., /sync-history)
            return self.cloud.execute_cloud_meta(command_text)
        
        elif command_type == 'shell':
            # Shell command that was queued (rare, but possible)
            # Log to cloud history for roaming
            return self.cloud.log_command_history(command_text)
        
        else:
            logger.warning(f"Unknown command type: {command_type}")
            return False
```

**Integration Point:** `CloudClient` must implement:
- `is_available() -> bool` - Quick health check
- `route_command(device, cmd) -> bool` - Send command to device
- `execute_cloud_meta(cmd) -> bool` - Execute cloud-dependent meta-command
- `log_command_history(cmd) -> bool` - Sync command to history

**Testing Checklist for Phase 2:**
```python
# Test file: tests/test_sync_worker.py
def test_worker_lifecycle():
    # Start, verify thread running, stop, verify joined
    
def test_sync_batch():
    # Queue commands, mock cloud available, verify synced
    
def test_offline_behavior():
    # Mock cloud unavailable, verify no sync attempts
    
def test_force_sync():
    # Call force_sync(), verify immediate processing
    
def test_exponential_backoff():
    # Simulate failures, verify wait time increases
```

---

### Phase 3: SessionManager Integration (30 minutes)

**File:** `isaac/core/session_manager.py`

**Changes needed:**

```python
# Add imports
from isaac.queue.command_queue import CommandQueue
from isaac.queue.sync_worker import SyncWorker

class SessionManager:
    def __init__(self, ...):
        # Existing initialization...
        
        # NEW: Initialize queue
        queue_db = self.isaac_dir / 'queue.db'
        self.queue = CommandQueue(queue_db)
        
        # NEW: Initialize sync worker
        self.sync_worker = SyncWorker(
            queue=self.queue,
            cloud_client=self.cloud_client,
            check_interval=30  # Check every 30 seconds
        )
        
        # NEW: Start background sync
        self.sync_worker.start()
        
        logger.info("Queue and sync worker initialized")
    
    def shutdown(self):
        """Graceful shutdown."""
        # NEW: Stop sync worker
        if hasattr(self, 'sync_worker'):
            self.sync_worker.stop()
        
        # Existing shutdown logic...
        logger.info("Session manager shutdown complete")
    
    def get_queue_status(self) -> dict:
        """Expose queue status for UI."""
        return self.queue.get_queue_status()
```

**Testing:**
- Verify queue initializes on session start
- Verify sync worker starts automatically
- Verify graceful shutdown on exit

---

### Phase 4: CommandRouter Integration (30 minutes)

**File:** `isaac/core/command_router.py`

**Add queue fallback on cloud failure:**

```python
def route_command(self, command: str, session: SessionManager) -> str:
    """Route command with queue fallback."""
    
    # Existing classification logic...
    
    if command.startswith('!'):
        # Device routing command
        device_alias, device_cmd = self._parse_device_route(command)
        
        try:
            # Attempt immediate routing
            result = session.cloud_client.route_command(device_alias, device_cmd)
            return result
            
        except CloudUnavailableError:
            # NEW: Queue for later sync
            queue_id = session.queue.enqueue(
                command=device_cmd,
                command_type='device_route',
                target_device=device_alias,
                metadata={'tier': self._get_tier(device_cmd)}
            )
            return f"Command queued (#{queue_id}) - will sync when online"
    
    # Existing routing logic...
```

**Testing:**
- Mock cloud unavailable
- Verify command queues instead of failing
- Verify queue ID returned to user

---

### Phase 5: UI Integration (30 minutes)

**File:** `isaac/ui/permanent_shell.py`

**Add offline indicator to prompt:**

```python
def _get_prompt(self, session: SessionManager) -> str:
    """Build prompt with queue status."""
    base_prompt = "isaac"
    
    # NEW: Check queue status
    queue_status = session.get_queue_status()
    pending_count = queue_status['pending']
    
    if pending_count > 0:
        # Show offline indicator with count
        return f"{base_prompt} [OFFLINE: {pending_count} queued]> "
    
    return f"{base_prompt}> "
```

**Add sync completion notification:**

```python
def _setup_sync_callback(self, session: SessionManager):
    """Register callback for sync completion notifications."""
    
    def on_sync_complete(count: int):
        # Print notification to terminal
        print(f"\n✅ {count} queued command(s) synced")
    
    session.sync_worker.on_sync_complete = on_sync_complete
```

**Testing:**
- Queue command, verify prompt shows `[OFFLINE: 1 queued]>`
- Mock sync completion, verify notification prints
- Verify prompt returns to normal after sync

---

### Phase 6: Meta-Commands (30 minutes)

#### `/queue` Command - View queued commands

**File:** `isaac/commands/queue/command.yaml`

```yaml
version: "1.0"
command:
  name: queue
  description: "View queued commands awaiting sync"
  category: "system"
  
triggers:
  - prefix: "/"
    pattern: "^queue(\\s+(.*))?$"
    capture: "args"

arguments: []

runtime:
  handler: "run.py"
  timeout_ms: 2000
  stdin: false

security:
  tier: 1
  resources:
    max_stdout_kib: 10
```

**File:** `isaac/commands/queue/run.py`

```python
#!/usr/bin/env python3
"""Handler for /queue command."""
import sys
import json
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.core.session_manager import SessionManager

def main():
    # Load envelope
    envelope = json.load(sys.stdin) if sys.stdin.isatty() == False else {}
    
    # Get session
    session = SessionManager.get_instance()
    
    # Get queue status
    status = session.get_queue_status()
    pending = session.queue.dequeue_pending(limit=50)
    
    # Format output
    output = []
    output.append(f"Queue Status: {status['pending']} pending, {status['failed']} failed")
    output.append("")
    
    if not pending:
        output.append("No commands queued")
    else:
        for cmd in pending:
            output.append(f"#{cmd['id']}: {cmd['command_text'][:60]}")
            output.append(f"  Type: {cmd['command_type']} | Queued: {cmd['queued_at']}")
            if cmd['target_device']:
                output.append(f"  Target: {cmd['target_device']}")
            output.append("")
    
    # Write envelope response
    print(json.dumps({
        "status": "success",
        "stdout": "\n".join(output)
    }))

if __name__ == "__main__":
    main()
```

#### `/sync` Command - Force immediate sync

**File:** `isaac/commands/sync/command.yaml`

```yaml
version: "1.0"
command:
  name: sync
  description: "Force immediate queue sync"
  category: "system"
  
triggers:
  - prefix: "/"
    pattern: "^sync$"

arguments: []

runtime:
  handler: "run.py"
  timeout_ms: 5000
  stdin: false

security:
  tier: 1
  resources:
    max_stdout_kib: 5
```

**File:** `isaac/commands/sync/run.py`

```python
#!/usr/bin/env python3
"""Handler for /sync command."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.core.session_manager import SessionManager

def main():
    session = SessionManager.get_instance()
    
    # Force sync
    try:
        count = session.sync_worker.force_sync()
        
        if count > 0:
            message = f"✅ Synced {count} queued command(s)"
        else:
            status = session.get_queue_status()
            if status['pending'] == 0:
                message = "No commands to sync"
            else:
                message = "Cloud unavailable - commands remain queued"
        
        print(json.dumps({
            "status": "success",
            "stdout": message
        }))
    
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "stderr": f"Sync failed: {e}"
        }))

if __name__ == "__main__":
    main()
```

---

## Testing Strategy

### Unit Tests
```powershell
pytest tests/test_command_queue.py -v
pytest tests/test_sync_worker.py -v
```

### Integration Tests
```python
# tests/test_queue_integration.py

def test_offline_command_queuing(mock_cloud_unavailable):
    """Verify commands queue when cloud unavailable."""
    # Mock cloud down
    # Issue !device command
    # Verify queued
    # Verify prompt shows [OFFLINE]

def test_auto_sync_on_reconnect(mock_cloud_recovery):
    """Verify auto-sync when cloud comes back online."""
    # Queue commands while offline
    # Restore cloud mock
    # Wait for sync worker cycle
    # Verify commands synced
    # Verify prompt returns to normal

def test_queue_persistence(restart_isaac):
    """Verify queue survives restart."""
    # Queue command
    # Shutdown Isaac
    # Restart Isaac
    # Verify command still queued
```

### Manual Testing Scenarios

1. **Offline Queuing:**
   ```powershell
   # Disconnect network
   $> !laptop2 /status
   Command queued (#1) - will sync when online
   isaac [OFFLINE: 1 queued]>
   ```

2. **Auto-Sync on Reconnect:**
   ```powershell
   # Reconnect network
   # Wait 30 seconds
   ✅ 1 queued command(s) synced
   isaac>
   ```

3. **View Queue:**
   ```powershell
   isaac [OFFLINE: 3 queued]> /queue
   Queue Status: 3 pending, 0 failed
   
   #1: /status
     Type: device_route | Queued: 2025-10-21T15:30:00
     Target: laptop2
   
   #2: deployment ready
     Type: device_route | Queued: 2025-10-21T15:31:00
     Target: laptop2
   ```

4. **Force Sync:**
   ```powershell
   isaac [OFFLINE: 2 queued]> /sync
   ✅ Synced 2 queued command(s)
   isaac>
   ```

---

## Success Criteria

- ✅ Commands queue locally when cloud unavailable
- ✅ Queue persists across Isaac restarts
- ✅ Background worker auto-syncs every 30 seconds
- ✅ Prompt shows `[OFFLINE: N queued]` indicator
- ✅ Sync completion notification displays
- ✅ `/queue` shows pending commands
- ✅ `/sync` forces immediate sync
- ✅ Stale 'syncing' states auto-reset
- ✅ Old 'done' entries auto-cleanup (7 days)
- ✅ All tests pass (unit + integration)

---

## Implementation Timeline

| Phase | Task | Time | Dependencies |
|-------|------|------|--------------|
| 1 | CommandQueue (SQLite) | 90 min | None |
| 2 | SyncWorker (background thread) | 60 min | Phase 1 |
| 3 | SessionManager integration | 30 min | Phase 1-2 |
| 4 | CommandRouter fallback | 30 min | Phase 3 |
| 5 | UI integration (prompt) | 30 min | Phase 3 |
| 6 | Meta-commands (/queue, /sync) | 30 min | Phase 1-5 |
| **Total** | | **4 hours** | |

---

## Error Handling

### Cloud Unavailability Detection

```python
class CloudUnavailableError(Exception):
    """Raised when cloud API is unreachable."""
    pass

# In cloud_client.py
def is_available(self) -> bool:
    """Quick health check (2-second timeout)."""
    try:
        response = requests.get(f"{self.api_url}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False
```

### Sync Failure Handling

- **Transient errors:** Mark failed, retry on next cycle
- **Permanent errors:** Mark failed, log to stderr, user can view with `/queue`
- **Max retries:** After 3 failures, stop retrying, require manual `/sync`

### Database Corruption

- Queue database is append-only (low corruption risk)
- If corrupted: Rename to `.bak`, create fresh DB, log warning
- User can recover via manual SQL export if needed

---

## Future Enhancements (Post-Track 1)

1. **Priority Queue:** High-priority commands sync first
2. **Conflict Resolution:** Detect duplicate queued commands
3. **Quota Limits:** Max queue size (prevent disk bloat)
4. **Retry Backoff:** Per-command exponential backoff
5. **Queue Analytics:** Track average sync latency, failure rate

---

## Dependencies

### Python Packages (already in requirements.txt)
- `sqlite3` (built-in)
- `threading` (built-in)
- `requests` (existing)

### Isaac Components
- `SessionManager` - Must expose `queue` and `sync_worker` attributes
- `CloudClient` - Must implement `is_available()`, `route_command()`, etc.
- `CommandRouter` - Must catch `CloudUnavailableError` and queue

---

## Handoff Notes for Coding Agent

**Start here:**
1. Read this spec completely
2. Create `isaac/queue/` directory
3. Implement `command_queue.py` (Phase 1)
4. Write unit tests for Phase 1
5. Proceed sequentially through phases 2-6

**Don't skip:**
- Error handling (especially cloud unavailable detection)
- Logging (every queue operation should log)
- Thread safety (SQLite connections per-thread)

**Ask if unclear:**
- CloudClient API contract (methods, exceptions)
- SessionManager singleton pattern
- Terminal output formatting preferences

---

**Specification complete. Ready for implementation.**
