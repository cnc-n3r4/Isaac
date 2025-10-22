# Track 1.2: Command Queue Overlay - Quick Start

**Prerequisites:** ✅ Track 1.1 Complete (Dispatcher working)  
**Time Estimate:** 3-4 hours  
**Goal:** Never lose commands when offline

---

## 🎯 What You're Building

**Before (Current State):**
```
User: !laptop2 /status
       ↓
Cloud unavailable → ERROR ❌
Command lost forever
```

**After (Track 1.2):**
```
User: !laptop2 /status
       ↓
Cloud unavailable → Queue locally ✅
       ↓
Prompt: isaac [OFFLINE: 1 queued]>
       ↓
Background: Connection restored → Auto-sync
       ↓
Notification: "1 queued command synced"
```

---

## 🚀 Launch Sequence

### Step 1: Read the Spec (5 minutes)

```powershell
code .claude\mail\to_implement\command_queue_overlay_spec.md
```

**Focus on:**
- SQLite queue schema (Section 0)
- Two core modules (Sections 1-2)
- Integration points (Section 3)

---

### Step 2: Create Queue Directory (1 minute)

```powershell
# Create directory
mkdir isaac\queue

# Create __init__.py
New-Item isaac\queue\__init__.py -ItemType File

# Verify structure
tree isaac /F
```

---

### Step 3: Implement Command Queue (First 2 hours)

#### 3a. Create the file
```powershell
code isaac\queue\command_queue.py
```

#### 3b. Use this starter template

```python
"""
Command Queue - SQLite-based command persistence for offline resilience.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

class CommandQueue:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database with schema."""
        conn = sqlite3.connect(self.db_path)
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
                target_device: Optional[str] = None, metadata: dict = None) -> int:
        """Add command to queue, return queue ID."""
        # TODO: Implement
        pass
    
    def dequeue_pending(self, limit: int = 10) -> List[Dict]:
        """Get up to N pending commands."""
        # TODO: Implement
        pass
    
    def mark_done(self, queue_id: int):
        """Mark command as successfully synced."""
        # TODO: Implement
        pass
    
    def mark_failed(self, queue_id: int, error: str):
        """Mark command as failed, increment retry_count."""
        # TODO: Implement
        pass
    
    def get_queue_status(self) -> Dict:
        """Return queue statistics."""
        # TODO: Implement
        pass
```

#### 3c. Write tests first

```powershell
code tests\test_command_queue.py
```

**Starter test template:**

```python
"""
Tests for command_queue.py
"""
import pytest
from pathlib import Path
from isaac.queue.command_queue import CommandQueue

def test_enqueue_command(tmp_path):
    """Test adding command to queue"""
    db_path = tmp_path / "queue.db"
    queue = CommandQueue(db_path)
    
    queue_id = queue.enqueue(
        command="/status",
        command_type="meta",
        target_device=None
    )
    
    assert queue_id > 0
    
    # Verify it's in pending state
    pending = queue.dequeue_pending()
    assert len(pending) == 1
    assert pending[0]["command_text"] == "/status"

def test_mark_done():
    """Test marking command as completed"""
    # TODO: Implement
    pass

def test_queue_survives_restart(tmp_path):
    """Test that queue persists across restarts"""
    # TODO: Implement
    pass
```

---

### Step 4: Implement Sync Worker (Next 2 hours)

```powershell
code isaac\queue\sync_worker.py
```

**Starter template:**

```python
"""
Sync Worker - Background thread for syncing queued commands.
"""
import threading
import time
from typing import Callable

class SyncWorker:
    def __init__(self, queue, cloud_client, check_interval: int = 30):
        self.queue = queue
        self.cloud = cloud_client
        self.interval = check_interval
        self.running = False
        self._thread = None
    
    def start(self):
        """Start background sync thread."""
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop background thread gracefully."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def _sync_loop(self):
        """Main sync loop with exponential backoff."""
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
    
    def _sync_command(self, cmd: Dict):
        """Sync single command to cloud/device."""
        # TODO: Implement routing logic
        pass
```

---

### Step 5: Integration with SessionManager (1 hour)

**Update `isaac/core/session_manager.py`:**

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
            check_interval=30
        )
        self.sync_worker.start()
    
    def shutdown(self):
        """Graceful shutdown."""
        if hasattr(self, 'sync_worker'):
            self.sync_worker.stop()
```

---

### Step 6: Update Command Router (30 minutes)

**Update `isaac/core/command_router.py`:**

```python
def _route_device(self, input_text: str):
    """Handle !alias routing with queue fallback."""
    alias, command = parse_device_command(input_text)
    
    # Try immediate routing
    if self.session.cloud.is_available():
        try:
            return self.session.cloud.route_command(alias, command)
        except Exception as e:
            pass  # Fall through to queue
    
    # Queue for later
    queue_id = self.session.queue.enqueue(
        command=command,
        command_type='device_route',
        target_device=alias
    )
    
    return CommandResult(
        success=True,
        output=f"Command queued (#{queue_id}) - will sync when online",
        exit_code=0
    )
```

---

### Step 7: Update Prompt for Offline Indicator (30 minutes)

**Update `isaac/ui/permanent_shell.py`:**

```python
def _update_prompt(self):
    """Show offline indicator in prompt."""
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

### Step 8: Add Queue Meta-Commands (30 minutes)

**Create `/queue` command:**

```powershell
mkdir isaac\commands\queue
code isaac\commands\queue\command.yaml
code isaac\commands\queue\run.py
```

**Manifest:**
```yaml
name: queue
version: 1.0.0
summary: "View queued commands"
triggers: ["/queue"]
args: []
stdin: false
stdout:
  type: text
security:
  scope: user
  allow_remote: false
  resources:
    timeout_ms: 1000
    max_stdout_kib: 64
runtime:
  entry: "run.py"
  interpreter: "python"
```

---

## 📋 Implementation Checklist

### Phase 1: Core Queue (2 hours)
- [ ] `command_queue.py` with SQLite schema
- [ ] `enqueue()` adds commands
- [ ] `dequeue_pending()` retrieves commands
- [ ] `mark_done()` / `mark_failed()` update status
- [ ] `get_queue_status()` returns stats
- [ ] Tests passing

### Phase 2: Sync Worker (2 hours)
- [ ] `sync_worker.py` background thread
- [ ] Exponential backoff on failures
- [ ] Graceful shutdown
- [ ] Connection checking
- [ ] Tests passing

### Phase 3: Integration (1 hour)
- [ ] SessionManager initializes queue
- [ ] CommandRouter queues on cloud failure
- [ ] Prompt shows offline indicator
- [ ] `/queue` command shows status
- [ ] `/sync` command forces sync

### Phase 4: Testing (30 minutes)
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Regression tests pass (no breaking changes)
- [ ] Manual testing: disconnect network, queue commands, reconnect

---

## 🧪 Testing Workflow

```powershell
# Run queue tests
pytest tests\test_command_queue.py -v

# Run sync worker tests
pytest tests\test_sync_worker.py -v

# Run integration tests
pytest tests\test_queue_integration.py -v

# Full regression test
pytest tests\ -v
```

---

## 📊 Success Criteria

After Track 1.2, you should have:

- [ ] Commands queue when cloud unavailable
- [ ] Auto-sync within 30s of connection restore
- [ ] Prompt shows: `isaac [OFFLINE: N queued]>`
- [ ] Queue survives process restarts
- [ ] `/queue` shows pending commands
- [ ] `/sync` forces immediate sync
- [ ] All tests passing

---

## 🎯 Estimated Timeline

**Hour 1-2:** Command Queue
- SQLite schema
- Enqueue/dequeue logic
- Tests

**Hour 3-4:** Sync Worker
- Background thread
- Exponential backoff
- Tests

**Hour 5:** Integration
- SessionManager updates
- CommandRouter fallback
- Prompt indicator

**Hour 6:** Polish
- `/queue` and `/sync` commands
- Testing
- Documentation

**Total: 3-4 hours** (plus testing/polish)

---

## 🚀 First Commands to Run

```powershell
# 1. Read the full spec
code .claude\mail\to_implement\command_queue_overlay_spec.md

# 2. Create queue directory
mkdir isaac\queue
New-Item isaac\queue\__init__.py -ItemType File

# 3. Start with queue implementation
code isaac\queue\command_queue.py

# 4. Create tests
code tests\test_command_queue.py

# 5. Run tests (TDD cycle)
pytest tests\test_command_queue.py -v
```

---

## 💡 Pro Tips

1. **Test offline mode manually:**
   - Disconnect network
   - Try device routing: `!laptop2 /status`
   - Check prompt shows offline indicator
   - Reconnect network
   - Verify auto-sync

2. **Use SQLite browser for debugging:**
   - Download DB Browser for SQLite
   - Open `~/.isaac/queue.db`
   - Inspect queue table directly

3. **Monitor sync worker:**
   - Add logging to `_sync_loop()`
   - Watch for backoff behavior
   - Verify graceful shutdown

---

**Ready?** Start with: `code .claude\mail\to_implement\command_queue_overlay_spec.md`

**Next milestone:** Track 1 COMPLETE! 🎉
