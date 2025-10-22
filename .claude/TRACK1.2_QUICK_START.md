# Track 1.2: Command Queue Overlay - Quick Start Guide

**Prerequisites:** ✅ Track 1.1 (Dispatcher) complete  
**Time Estimate:** 3-4 hours  
**Status:** Ready to start immediately

---

## 🎯 What You're Building

**Problem:** Commands lost when cloud connection drops  
**Solution:** Local SQLite queue with auto-sync

### User Experience Change

**Before Track 1.2:**
```powershell
$> !laptop2 /status
ERROR: Cloud unavailable ❌
[Command lost forever]
```

**After Track 1.2:**
```powershell
$> !laptop2 /status
Command queued (#1) - will sync when online ✅

isaac [OFFLINE: 1 queued]>

[Connection restores]
isaac [OFFLINE]>  # Auto-syncing...
"1 queued command synced" ✅
isaac>  # Back online
```

---

## 📁 Files You'll Create

### 1. Queue Package (Core)
```
isaac/queue/
├── __init__.py
├── command_queue.py      # SQLite queue manager
└── sync_worker.py        # Background sync thread
```

### 2. Integration Updates
- `isaac/core/session_manager.py` - Initialize queue + worker
- `isaac/core/command_router.py` - Queue on cloud failure
- `isaac/ui/permanent_shell.py` - Offline indicator

### 3. New Meta-Commands (via Dispatcher!)
```
isaac/commands/queue/     # View queued commands
isaac/commands/sync/      # Force sync now
```

---

## 🚀 Step 1: Create Queue Manager (2 hours)

### 1a. Create directory structure

```powershell
mkdir isaac\queue
New-Item isaac\queue\__init__.py -ItemType File
code isaac\queue\command_queue.py
```

### 1b. Implement SQLite queue

**Copy this starter (from spec):**

```python
"""
Command Queue - SQLite-based command persistence for offline resilience.
"""
from pathlib import Path
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict

class CommandQueue:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Create queue table if not exists."""
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
        conn.commit()
        conn.close()
    
    def enqueue(self, command: str, command_type: str, 
                target_device: Optional[str] = None, metadata: dict = None) -> int:
        """Add command to queue, return queue ID."""
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
        return queue_id
    
    def dequeue_pending(self, limit: int = 10) -> List[Dict]:
        """Get up to N pending commands."""
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
    
    def mark_failed(self, queue_id: int, error: str):
        """Mark command as failed, increment retry_count."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            UPDATE command_queue 
            SET status='failed', 
                error_message=?, 
                retry_count=retry_count+1,
                last_retry_at=?
            WHERE id=?
        """, (error, datetime.utcnow().isoformat(), queue_id))
        conn.commit()
        conn.close()
    
    def get_queue_status(self) -> Dict:
        """Return queue statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("""
            SELECT status, COUNT(*) as count 
            FROM command_queue 
            GROUP BY status
        """)
        stats = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return {
            "pending": stats.get("pending", 0),
            "failed": stats.get("failed", 0),
            "done": stats.get("done", 0)
        }
```

### 1c. Write tests

```powershell
code tests\test_command_queue.py
```

**Test template:**

```python
import pytest
from pathlib import Path
from isaac.queue.command_queue import CommandQueue

def test_enqueue_dequeue(tmp_path):
    """Test basic enqueue and dequeue."""
    db_path = tmp_path / "queue.db"
    queue = CommandQueue(db_path)
    
    # Enqueue command
    queue_id = queue.enqueue(
        command="/status",
        command_type="device_route",
        target_device="laptop2"
    )
    
    assert queue_id > 0
    
    # Dequeue
    pending = queue.dequeue_pending()
    assert len(pending) == 1
    assert pending[0]["command_text"] == "/status"
    assert pending[0]["target_device"] == "laptop2"

def test_mark_done():
    """Test marking command as done."""
    # TODO
    pass

def test_queue_persistence(tmp_path):
    """Test queue survives restart."""
    # TODO
    pass
```

---

## 🔄 Step 2: Sync Worker (1 hour)

### 2a. Create sync worker

```powershell
code isaac\queue\sync_worker.py
```

**Starter template (from spec):**

```python
"""
Sync Worker - Background thread for auto-syncing queued commands.
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
        backoff = 1
        
        while self.running:
            try:
                # Check cloud availability
                if not self.cloud.is_available():
                    time.sleep(self.interval)
                    continue
                
                # Get pending commands
                pending = self.queue.dequeue_pending(limit=10)
                
                if not pending:
                    backoff = 1
                    time.sleep(self.interval)
                    continue
                
                # Sync each command
                for cmd in pending:
                    try:
                        self._sync_command(cmd)
                        self.queue.mark_done(cmd['id'])
                        backoff = 1
                    except Exception as e:
                        self.queue.mark_failed(cmd['id'], str(e))
                        backoff = min(backoff * 2, 300)
                
            except Exception as e:
                print(f"Sync worker error: {e}")
                time.sleep(backoff)
    
    def _sync_command(self, cmd: Dict):
        """Sync single command to cloud/device."""
        if cmd['target_device']:
            # Route to device
            self.cloud.route_command(cmd['target_device'], cmd['command_text'])
        else:
            # Log to cloud history
            metadata = json.loads(cmd.get('metadata', '{}'))
            self.cloud.append_command_history(cmd['command_text'], metadata)
```

---

## 🔗 Step 3: Integration (1 hour)

### 3a. Update SessionManager

```powershell
code isaac\core\session_manager.py
```

**Add to `__init__` method:**

```python
from isaac.queue import CommandQueue, SyncWorker

# In SessionManager.__init__():

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
```

**Add shutdown method:**

```python
def shutdown(self):
    """Graceful shutdown."""
    if hasattr(self, 'sync_worker'):
        self.sync_worker.stop()
```

### 3b. Update CommandRouter

```powershell
code isaac\core\command_router.py
```

**Update `_route_device` method:**

```python
def _route_device(self, input_text: str):
    """Handle !alias routing with queue fallback."""
    # Parse: !laptop2 /status
    parts = input_text[1:].split(None, 1)
    if len(parts) != 2:
        return {"ok": False, "error": {"message": "Usage: !alias /command"}}
    
    alias, command = parts
    
    # Try immediate routing
    if self.session.cloud.is_available():
        try:
            return self.session.cloud.route_command(alias, command)
        except Exception:
            pass  # Fall back to queue
    
    # Queue for later
    queue_id = self.session.queue.enqueue(
        command=command,
        command_type='device_route',
        target_device=alias
    )
    
    return {
        "ok": True,
        "kind": "text",
        "stdout": f"Command queued (#{queue_id}) - will sync when online",
        "meta": {"queued": True, "queue_id": queue_id}
    }
```

### 3c. Update Prompt (Offline Indicator)

```powershell
code isaac\ui\permanent_shell.py
```

**Update prompt method:**

```python
def _update_prompt(self):
    """Show offline indicator in prompt."""
    if not self.session.cloud.is_available():
        stats = self.session.queue.get_queue_status()
        pending = stats.get('pending', 0)
        
        if pending > 0:
            self.prompt = f"isaac [OFFLINE: {pending} queued]> "
        else:
            self.prompt = "isaac [OFFLINE]> "
    else:
        self.prompt = "$> "
```

---

## 🎯 Step 4: Add Queue Commands (30 min)

### 4a. Create `/queue` command (view queued items)

```powershell
mkdir isaac\commands\queue
code isaac\commands\queue\command.yaml
code isaac\commands\queue\run.py
```

**Manifest:**
```yaml
name: queue
version: 1.0.0
summary: "View queued commands waiting to sync"
triggers: ["/queue"]
args: []
stdin: false
stdout: { type: text }
security:
  scope: user
  allow_remote: false
  resources: { timeout_ms: 1000, max_stdout_kib: 16 }
runtime:
  entry: "run.py"
  interpreter: "python"
```

**Handler:**
```python
import sys, json

def main():
    payload = json.loads(sys.stdin.read())
    session = payload["session"]
    
    pending = session.queue.dequeue_pending(limit=50)
    
    if not pending:
        output = "Queue is empty."
    else:
        lines = ["Queued commands:"]
        for cmd in pending:
            lines.append(f"  #{cmd['id']}: {cmd['command_text']} → {cmd['target_device']}")
        output = "\n".join(lines)
    
    print(json.dumps({"ok": True, "kind": "text", "stdout": output, "meta": {}}))

if __name__ == "__main__":
    main()
```

### 4b. Create `/sync` command (force sync now)

```powershell
mkdir isaac\commands\sync
code isaac\commands\sync\command.yaml
code isaac\commands\sync\run.py
```

---

## ✅ Testing Checklist

```powershell
# Test queue operations
pytest tests\test_command_queue.py -v

# Test sync worker
pytest tests\test_sync_worker.py -v

# Test integration
pytest tests\test_queue_integration.py -v

# Regression test (all existing tests)
pytest tests\ -v
```

---

## 🎯 Success Criteria

After completion, verify:

- [ ] Commands queue when cloud unavailable
- [ ] Auto-sync within 30s of connection restore
- [ ] Prompt shows: `isaac [OFFLINE: N queued]>`
- [ ] Queue survives process restart
- [ ] `/queue` command shows queued items
- [ ] `/sync` command forces immediate sync
- [ ] All existing tests still pass

---

## 📚 Reference Materials

**Keep open:**
1. `.claude/mail/to_implement/command_queue_overlay_spec.md` - Full spec
2. `.claude/bible/TRACK1_LOCAL_QOL.md` - Track overview
3. `TRACK1.1_COMPLETE.md` - What you just built

---

## ⏱️ Timeline Estimate

- **Hour 1:** Command queue (SQLite implementation)
- **Hour 2:** Queue tests + sync worker
- **Hour 3:** Integration (SessionManager, CommandRouter, prompt)
- **Hour 4:** Meta-commands (`/queue`, `/sync`) + polish

**Total:** 3-4 hours

---

## 🚀 First Command to Run

```powershell
# Read the full spec
code .claude\mail\to_implement\command_queue_overlay_spec.md

# Create queue directory
mkdir isaac\queue
New-Item isaac\queue\__init__.py -ItemType File

# Start with queue manager
code isaac\queue\command_queue.py
```

---

**Ready?** Start by reading the spec, then create the queue directory. You've got the dispatcher foundation - now add resilience! 🎯
