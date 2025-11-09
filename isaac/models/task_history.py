"""
TaskHistory - Immutable logging for multi-step tasks
Append-only audit trail for task execution and failures
"""

import time
import uuid
from typing import Dict, List, Optional


class TaskHistory:
    """Track multi-step task execution (immutable log)."""

    def __init__(self, task_id: Optional[str] = None):
        """Initialize empty task history."""
        self.tasks: List[Dict] = []
        self.max_tasks = 100  # Limit stored tasks
        self.current_task_id = task_id

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
            "task_id": task_id,
            "timestamp": time.time(),
            "description": description,
            "mode": mode,
            "planned_steps": len(steps),
            "steps": [],  # Execution log (append-only)
            "status": "running",
            "machine_id": "",  # Set by session manager
        }

        self.tasks.append(entry)

        # Trim if exceeds max
        if len(self.tasks) > self.max_tasks:
            self.tasks = self.tasks[-self.max_tasks :]

        return task_id

    def log_step(
        self,
        task_id: str,
        step_num: int,
        command: str,
        status: str,
        output: str = "",
        error: str = "",
        recovery: str = "",
    ):
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
            "step": step_num,
            "command": command,
            "status": status,
            "timestamp": time.time(),
        }

        if output:
            step_entry["output"] = output
        if error:
            step_entry["error"] = error
        if recovery:
            step_entry["recovery"] = recovery

        # Append-only (immutable)
        task["steps"].append(step_entry)

    def complete_task(self, task_id: str, final_status: str):
        """
        Mark task as complete.

        Args:
            task_id: Task identifier
            final_status: 'completed', 'failed', or 'aborted'
        """
        task = self._find_task(task_id)
        if task:
            task["status"] = final_status
            task["completed_at"] = time.time()

    def _find_task(self, task_id: str) -> Optional[Dict]:
        """Find task by ID."""
        for task in self.tasks:
            if task["task_id"] == task_id:
                return task
        return None

    def get_recent(self, count: int = 10) -> List[Dict]:
        """Get N most recent tasks."""
        return self.tasks[-count:]

    def to_dict(self) -> Dict:
        """Serialize for cloud sync."""
        return {"tasks": self.tasks, "count": len(self.tasks), "max_tasks": self.max_tasks}

    @classmethod
    def from_dict(cls, data: Dict) -> "TaskHistory":
        """Deserialize from cloud."""
        history = cls()
        history.tasks = data.get("tasks", [])
        history.max_tasks = data.get("max_tasks", 100)
        return history
