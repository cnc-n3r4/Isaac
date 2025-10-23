# Command Queue Overlay - Track 1.2

## Objective
Implement local command queue buffer for offline resilience, ensuring commands are never lost when cloud connection drops.

## Vision
**Problem:** User issues commands while offline → commands lost or fail silently  
**Solution:** Local SQLite queue buffers commands → auto-sync when connection returns → user never loses work

---

## User Experience

### Current Behavior (Without Queue)
```
User: /msg !laptop2 "deployment ready"
       ↓
Cloud unavailable → ERROR
Command lost forever ❌
```

### New Behavior (With Queue)
```
User: /msg !laptop2 "deployment ready"
       ↓
Cloud unavailable → Queue locally
       ↓
Prompt: isaac [OFFLINE]>
       ↓
Background: Connection restored → Auto-send queued commands
       ↓
Notification: "2 queued commands synced"
```

---

## Architecture

### Queue Database Schema
**File:** `~/.isaac/queue.db` (SQLite)

```sql
CREATE TABLE command_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    queued_at TEXT NOT NULL,           -- ISO timestamp
    command_type TEXT NOT NULL,        -- 'meta' | 'shell' | 'device_route'
    command_text TEXT NOT NULL,        -- Full command string
    target_device TEXT,                -- For !alias routing (null for local)
    retry_count INTEGER DEFAULT 0,
    last_retry_at TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'syncing' | 'done' | 'failed'
    error_message TEXT,
    metadata TEXT                      -- JSON blob (tier, validation, etc.)
);

CREATE INDEX idx_status ON command_queue(status);
CREATE INDEX idx_queued_at ON command_queue(queued_at);
```

---

## Files to Create

### 1. `isaac/queue/command_queue.py` (Core Queue Manager)

```python
from pathlib import Path
import sqlite3
import json
from datetime import datetime
from typing import Optional, List

class CommandQueue:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
        
    def enqueue(self, command: str, command_type: str, 
                target_device: Optional[str] = None, metadata: dict = None) -> int:
        """Add command to queue, return queue ID"""
        # INSERT INTO command_queue
        
    def dequeue_pending(self, limit: int = 10) -> List[dict]:
        """Get up to N pending commands"""
        # SELECT * FROM command_queue WHERE status='pending' LIMIT ?
        
    def mark_syncing(self, queue_id: int):
        """Mark command as currently syncing"""
        
    def mark_done(self, queue_id: int):
        """Mark command as successfully synced"""
        
    def mark_failed(self, queue_id: int, error: str):
        """Mark command as failed, increment retry_count"""
        
    def get_queue_status(self) -> dict:
        """Return queue statistics"""
        # {pending: N, failed: M, last_sync: timestamp}
        
    def clear_old_entries(self, days: int = 7):
        """Delete successfully synced entries older than N days"""
```

**Key Features:**
- SQLite for persistence (survives restarts)
- Atomic operations (no command loss)
- Retry tracking with exponential backoff
- Automatic cleanup of old entries

---

### 2. `isaac/queue/sync_worker.py` (Background Sync Thread)

```python
import threading
import time
from typing import Callable

class SyncWorker:
    def __init__(self, queue: CommandQueue, cloud_client, 
                 check_interval: int = 30):
        self.queue = queue
        self.cloud = cloud_client
        self.interval = check_interval
        self.running = False
        self._thread = None
        
    def start(self):
        """Start background sync thread"""
        self.running = True
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop background thread gracefully"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def _sync_loop(self):
        """Main sync loop with exponential backoff"""
        backoff = 1  # Start with 1 second
        
        while self.running:
            try:
                # Check cloud availability
                if not self.cloud.is_available():
                    time.sleep(self.interval)
                    continue
                
                # Get pending commands
                pending = self.queue.dequeue_pending(limit=10)
                
                if not pending:
                    backoff = 1  # Reset backoff
                    time.sleep(self.interval)
                    continue
                
                # Try to sync each command
                for cmd in pending:
                    try:
                        self._sync_command(cmd)
                        self.queue.mark_done(cmd['id'])
                        backoff = 1  # Success resets backoff
                    except Exception as e:
                        self.queue.mark_failed(cmd['id'], str(e))
                        backoff = min(backoff * 2, 300)  # Max 5 min
                
            except Exception as e:
                print(f"Sync worker error: {e}")
                time.sleep(backoff)
    
    def _sync_command(self, cmd: dict):
        """Sync single command to cloud/device"""
        if cmd['target_device']:
            # Route to device
            self.cloud.route_command(cmd['target_device'], cmd['command_text'])
        else:
            # Log to cloud history (for multi-machine sync)
            self.cloud.append_command_history(cmd['command_text'], cmd['metadata'])
```

**Key Features:**
- Daemon thread (auto-stops with main process)
- Exponential backoff on failures (1s → 2s → 4s → ... → 300s max)
- Batch processing (10 commands at a time)
- Graceful shutdown

---

### 3. `isaac/queue/__init__.py`
Export public API:
```python
from .command_queue import CommandQueue
from .sync_worker import SyncWorker

__all__ = ['CommandQueue', 'SyncWorker']
```

---

## Integration Points

### Update `isaac/core/session_manager.py`

```python
from isaac.queue import CommandQueue, SyncWorker

class SessionManager:
    def __init__(self, config_path: Path):
        # ... existing init ...
        
        # Initialize queue
        queue_path = self.config_dir / 'queue.db'
        self.queue = CommandQueue(queue_path)
        
        # Start sync worker
        self.sync_worker = SyncWorker(
            queue=self.queue,
            cloud_client=self.cloud,
            check_interval=30  # Check every 30 seconds
        )
        self.sync_worker.start()
    
    def shutdown(self):
        """Graceful shutdown"""
        if hasattr(self, 'sync_worker'):
            self.sync_worker.stop()
```

### Update `isaac/core/command_router.py`

```python
def _route_device(self, input_text: str):
    """Handle !alias routing with queue fallback"""
    alias, command = parse_device_command(input_text)
    
    # Try immediate routing
    if self.session.cloud.is_available():
        try:
            return self.session.cloud.route_command(alias, command)
        except Exception as e:
            # Failed, fall back to queue
            pass
    
    # Queue for later
    queue_id = self.session.queue.enqueue(
        command=command,
        command_type='device_route',
        target_device=alias,
        metadata={'queued_reason': 'cloud_unavailable'}
    )
    
    return {
        "ok": True,
        "kind": "text",
        "stdout": f"Command queued (#{queue_id}) - will sync when online",
        "meta": {"queued": True, "queue_id": queue_id}
    }
```

### Update `isaac/ui/permanent_shell.py`

```python
def _update_prompt(self):
    """Show offline indicator in prompt"""
    if not self.session.cloud.is_available():
        queue_status = self.session.queue.get_queue_status()
        pending = queue_status['pending']
        
        if pending > 0:
            self.prompt = f"isaac [OFFLINE: {pending} queued]> "
        else:
            self.prompt = "isaac [OFFLINE]> "
    else:
        self.prompt = "$> "
```

---

## Testing Checklist

### Unit Tests (`tests/test_command_queue.py`)
- [ ] Queue enqueue adds command to database
- [ ] Queue dequeue returns pending commands
- [ ] Mark done removes from pending
- [ ] Mark failed increments retry_count
- [ ] Clear old entries deletes >7 day records
- [ ] Queue survives process restart (SQLite persistence)

### Integration Tests (`tests/test_queue_integration.py`)
- [ ] Command queued when cloud unavailable
- [ ] Sync worker sends queued commands when online
- [ ] Exponential backoff on repeated failures
- [ ] Prompt shows "OFFLINE" indicator
- [ ] Prompt shows queued count when >0
- [ ] Graceful shutdown stops sync worker

### Stress Tests
- [ ] 100 commands queued while offline
- [ ] All 100 sync when online
- [ ] Queue handles database lock contention
- [ ] Memory usage stable over 1000+ queue entries

---

## Configuration

### Add to `~/.isaac/config.json`
```json
{
  "queue": {
    "enabled": true,
    "sync_interval_seconds": 30,
    "max_retry_count": 10,
    "cleanup_after_days": 7,
    "batch_size": 10
  }
}
```

---

## Success Criteria

### Must Have
1. ✅ Commands queued when cloud unavailable
2. ✅ Auto-sync when connection returns
3. ✅ Queue persists across restarts (SQLite)
4. ✅ Prompt shows offline indicator
5. ✅ Exponential backoff on failures

### Should Have
6. ✅ Queue status in `/status` output
7. ✅ Manual `/sync` command to force immediate sync
8. ✅ `/queue` command to view queued items
9. ✅ Notification when queued commands sync

### Nice to Have
10. Queue size limit (warn if >100 pending)
11. Priority queuing (urgent vs normal)
12. Conflict resolution (duplicate commands)

---

## Implementation Order

### Step 1: Database (1 hour)
1. Create `isaac/queue/` directory
2. Implement `command_queue.py` with SQLite schema
3. Write unit tests for queue operations

### Step 2: Sync Worker (1 hour)
1. Implement `sync_worker.py` background thread
2. Add exponential backoff logic
3. Test with simulated offline/online cycles

### Step 3: Integration (1 hour)
1. Update `SessionManager` to initialize queue
2. Update `CommandRouter` to queue on cloud failure
3. Update prompt to show offline indicator
4. Add `/queue` meta-command to view status

### Step 4: Polish (30 min)
1. Add sync notifications
2. Add manual `/sync` command
3. Test graceful shutdown
4. Update documentation

---

## Complexity: Medium
**Estimated time:** 3-4 hours  
**Priority:** HIGH (user trust - never lose commands)

---

## Dependencies

### Required
- **CommandDispatcher** (Track 1.1) - For `/queue` and `/sync` commands
- **CloudClient** - For `is_available()` and routing
- **SessionManager** - For lifecycle management

### Optional
- **Track 2.1: Job Lifecycle** - Enhanced queue with state tracking

---

## References
- `.github/copilot-instructions.md` - Next-Phase Roadmap (Command Queue Overlay)
- `.claude/bible/ISAAC_FINAL_DESIGN.md` - Session management architecture
- SQLite documentation: https://www.sqlite.org/

---

## Future Enhancements

### Phase 2 (Track 2.1 Integration)
- Sync queue with cloud job lifecycle state machine
- Track command execution on remote devices
- Show command progress in `/status -v`

### Phase 3 (Advanced Features)
- Priority queuing (urgent commands jump queue)
- Conflict detection (duplicate commands)
- Queue size alerts (warn if >100 pending)
- Selective sync (skip failed commands manually)

---

**Ready for handoff to implementation agent**
**Recommended: Complete Track 1.1 (Dispatcher) first, then implement Track 1.2**