# Implementation: Task History Model

## Goal
Create TaskHistory model for immutable task logging (append-only audit trail).

**Time Estimate:** 30 minutes

---

## File to Create

**Path:** `isaac/models/task_history.py`

**Lines:** ~80

---

## Complete Implementation

```python
"""
TaskHistory - Immutable logging for multi-step tasks
Append-only audit trail for task execution and failures
"""

from typing import List, Dict
import time
import uuid


class TaskHistory:
    """Track multi-step task execution (immutable log)."""
    
    def __init__(self):
        """Initialize empty task history."""
        self.tasks: List[Dict] = []
        self.max_tasks = 100  # Limit stored tasks
    
    def create_task(self, description: str, mode: str, steps: List[Dict]) -> str:
        """
        Create new task entry.
        
        Args:
            description: Task description
            mode: Execution mode (autonomous/approve-once/step-by-step)
            steps: List of planned steps
            
        Returns:
            str: task_id
        """
        task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        
        entry = {
            'task_id': task_id,
            'timestamp': time.time(),
            'description': description,
            'mode': mode,
            'planned_steps': len(steps),
            'steps': [],  # Execution log (append-only)
            'status': 'running',
            'machine_id': ''  # Set by session manager
        }
        
        self.tasks.append(entry)
        
        # Trim if exceeds max
        if len(self.tasks) > self.max_tasks:
            self.tasks = self.tasks[-self.max_tasks:]
        
        return task_id
    
    def log_step(self, task_id: str, step_num: int, command: str, 
                 status: str, output: str = '', error: str = '', recovery: str = ''):
        """
        Log task step execution (immutable).
        
        Args:
            task_id: Task identifier
            step_num: Step number (1-based)
            command: Command executed
            status: 'success' or 'failed'
            output: Command output (if success)
            error: Error message (if failed)
            recovery: Recovery action taken (if applicable)
        """
        task = self._find_task(task_id)
        if not task:
            return
        
        step_entry = {
            'step': step_num,
            'command': command,
            'status': status,
            'timestamp': time.time()
        }
        
        if output:
            step_entry['output'] = output
        if error:
            step_entry['error'] = error
        if recovery:
            step_entry['recovery'] = recovery
        
        # Append-only (immutable)
        task['steps'].append(step_entry)
    
    def complete_task(self, task_id: str, final_status: str):
        """
        Mark task as complete.
        
        Args:
            task_id: Task identifier
            final_status: 'completed', 'failed', or 'aborted'
        """
        task = self._find_task(task_id)
        if task:
            task['status'] = final_status
            task['completed_at'] = time.time()
    
    def _find_task(self, task_id: str) -> Dict:
        """Find task by ID."""
        for task in self.tasks:
            if task['task_id'] == task_id:
                return task
        return None
    
    def get_recent(self, count: int = 10) -> List[Dict]:
        """Get N most recent tasks."""
        return self.tasks[-count:]
    
    def to_dict(self) -> Dict:
        """Serialize for cloud sync."""
        return {
            'tasks': self.tasks,
            'count': len(self.tasks),
            'max_tasks': self.max_tasks
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TaskHistory':
        """Deserialize from cloud."""
        history = cls()
        history.tasks = data.get('tasks', [])
        history.max_tasks = data.get('max_tasks', 100)
        return history
```

---

## Integration with SessionManager

**File to modify:** `isaac/core/session_manager.py`

**Add to __init__():**
```python
self.task_history = TaskHistory()  # Track multi-step tasks
```

**Add to load_from_local():**
```python
# Load task history
task_path = os.path.join(self.session_dir, 'task_history.json')
if os.path.exists(task_path):
    with open(task_path, 'r') as f:
        task_data = json.load(f)
        self.task_history = TaskHistory.from_dict(task_data)
```

**Add to load_from_cloud():**
```python
# Load task history
cloud_tasks = self.cloud.get_session_file('task_history.json')
if cloud_tasks:
    self.task_history = TaskHistory.from_dict(cloud_tasks)
```

**Add save method:**
```python
def save_task_history(self):
    """Save task history to local and cloud."""
    # Local save
    task_path = os.path.join(self.session_dir, 'task_history.json')
    with open(task_path, 'w') as f:
        json.dump(self.task_history.to_dict(), f, indent=2)
    
    # Cloud sync
    if self.cloud:
        try:
            self.cloud.save_session_file('task_history.json', self.task_history.to_dict())
        except Exception:
            pass
```

---

## Verification Steps

```bash
# 1. Check syntax
python -m py_compile isaac/models/task_history.py

# 2. Test import
python -c "from isaac.models.task_history import TaskHistory; print('✅ Import successful')"

# 3. Test basic functionality
python -c "
from isaac.models.task_history import TaskHistory
h = TaskHistory()
task_id = h.create_task('test task', 'autonomous', [])
h.log_step(task_id, 1, 'ls', 'success', output='file1 file2')
h.complete_task(task_id, 'completed')
print(f'✅ Created task: {task_id}')
print(f'Tasks: {len(h.tasks)}')
"
```

**Expected Output:**
```
✅ Import successful
✅ Created task: task_...
Tasks: 1
```

---

## Common Pitfalls

⚠️ **Pitfall 1: Modifying task history**
- Symptom: Audit trail corrupted
- Fix: Only append, never modify existing entries

⚠️ **Pitfall 2: Unbounded growth**
- Symptom: task_history.json grows forever
- Fix: max_tasks limit (100) already implemented

⚠️ **Pitfall 3: Not setting machine_id**
- Symptom: Can't identify which machine ran task
- Fix: SessionManager should set this when creating task

---

**END OF IMPLEMENTATION**
