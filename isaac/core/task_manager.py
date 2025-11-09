#!/usr/bin/env python3
"""
ISAAC Task Manager - Background Task Execution

Manages background task execution with notification support.
Tasks run asynchronously and notify via message queue on completion.
"""

import json
import shlex
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMode(Enum):
    """Command execution modes"""

    VERBOSE = "verbose"  # Immediate output (default)
    BACKGROUND = "background"  # Run in background, notify on completion
    PIPED = "piped"  # Output to pipe for next command


class Task:
    """Represents a background task"""

    def __init__(
        self,
        task_id: str,
        command: str,
        task_type: str = "code",
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id
        self.command = command
        self.task_type = task_type  # "system" or "code"
        self.priority = priority
        self.metadata = metadata or {}

        self.status = TaskStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.exit_code: Optional[int] = None
        self.stdout: str = ""
        self.stderr: str = ""
        self.process: Optional[subprocess.Popen] = None
        self.thread: Optional[threading.Thread] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation"""
        return {
            "task_id": self.task_id,
            "command": self.command,
            "task_type": self.task_type,
            "priority": self.priority,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Task":
        """Create task from dictionary representation"""
        task = Task(
            task_id=data["task_id"],
            command=data["command"],
            task_type=data.get("task_type", "code"),
            priority=data.get("priority", "normal"),
            metadata=data.get("metadata", {}),
        )
        task.status = TaskStatus(data["status"])
        task.start_time = (
            datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None
        )
        task.end_time = datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None
        task.exit_code = data.get("exit_code")
        task.stdout = data.get("stdout", "")
        task.stderr = data.get("stderr", "")
        return task


class TaskManager:
    """
    Manages background task execution

    Features:
    - Spawn and track background tasks
    - Capture task output
    - Send notifications on completion
    - Task status queries
    """

    def __init__(self, max_concurrent_tasks: int = 10, db_path: Optional[Path] = None):
        """
        Initialize task manager

        Args:
            max_concurrent_tasks: Maximum number of concurrent background tasks
            db_path: Path to SQLite database for persistent storage
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: Dict[str, Task] = {}
        self.lock = threading.Lock()

        # Callback for task completion notifications
        self.on_task_complete: Optional[Callable[[Task], None]] = None

        # Persistent storage
        if db_path is None:
            db_path = Path.home() / ".isaac" / "tasks.db"
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._load_tasks_from_db()

    def _init_db(self):
        """Initialize task database schema"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                command TEXT NOT NULL,
                task_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                exit_code INTEGER,
                stdout TEXT,
                stderr TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_status
            ON tasks(status)
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_created
            ON tasks(created_at DESC)
        """
        )
        conn.commit()
        conn.close()

    def _load_tasks_from_db(self):
        """Load existing tasks from database on startup"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Only load tasks that are not completed/failed/cancelled
        # Or load recent completed tasks (last 24 hours) for reference
        cursor.execute(
            """
            SELECT * FROM tasks
            WHERE status IN ('pending', 'running')
               OR (status IN ('completed', 'failed', 'cancelled')
                   AND datetime(created_at) > datetime('now', '-1 day'))
            ORDER BY created_at DESC
        """
        )

        for row in cursor.fetchall():
            task_data = {
                "task_id": row["task_id"],
                "command": row["command"],
                "task_type": row["task_type"],
                "priority": row["priority"],
                "status": row["status"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "exit_code": row["exit_code"],
                "stdout": row["stdout"] or "",
                "stderr": row["stderr"] or "",
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            }

            task = Task.from_dict(task_data)

            # Don't restart running tasks - mark them as failed
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.FAILED
                task.stderr = "Task was interrupted (ISAAC restart)"
                task.end_time = datetime.now()
                self._update_task_in_db(task)

            self.tasks[task.task_id] = task

        conn.close()

    def _save_task_to_db(self, task: Task):
        """Save task to database"""
        conn = sqlite3.connect(str(self.db_path))

        conn.execute(
            """
            INSERT OR REPLACE INTO tasks
            (task_id, command, task_type, priority, status, start_time, end_time,
             exit_code, stdout, stderr, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                task.task_id,
                task.command,
                task.task_type,
                task.priority,
                task.status.value,
                task.start_time.isoformat() if task.start_time else None,
                task.end_time.isoformat() if task.end_time else None,
                task.exit_code,
                task.stdout,
                task.stderr,
                json.dumps(task.metadata),
                task.start_time.isoformat() if task.start_time else datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

    def _update_task_in_db(self, task: Task):
        """Update task in database"""
        conn = sqlite3.connect(str(self.db_path))

        conn.execute(
            """
            UPDATE tasks
            SET status = ?, start_time = ?, end_time = ?, exit_code = ?,
                stdout = ?, stderr = ?
            WHERE task_id = ?
        """,
            (
                task.status.value,
                task.start_time.isoformat() if task.start_time else None,
                task.end_time.isoformat() if task.end_time else None,
                task.exit_code,
                task.stdout,
                task.stderr,
                task.task_id,
            ),
        )

        conn.commit()
        conn.close()

    def spawn_task(
        self,
        command: str,
        task_type: str = "code",
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[Task], None]] = None,
    ) -> str:
        """
        Spawn a background task

        Args:
            command: Command to execute
            task_type: "system" or "code" (for notification routing)
            priority: Task priority (urgent, high, normal, low)
            metadata: Additional task metadata
            callback: Optional callback function when task completes

        Returns:
            Task ID
        """
        # Generate task ID
        task_id = str(uuid.uuid4())[:8]

        # Create task
        task = Task(
            task_id=task_id,
            command=command,
            task_type=task_type,
            priority=priority,
            metadata=metadata,
        )

        # Check concurrent task limit
        with self.lock:
            running_count = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)

            if running_count >= self.max_concurrent_tasks:
                task.status = TaskStatus.FAILED
                task.stderr = f"Maximum concurrent tasks ({self.max_concurrent_tasks}) reached"
                self.tasks[task_id] = task
                return task_id

            # Store task
            self.tasks[task_id] = task

            # Save to database
            self._save_task_to_db(task)

        # Spawn execution thread
        thread = threading.Thread(target=self._execute_task, args=(task, callback), daemon=True)
        task.thread = thread
        thread.start()

        return task_id

    def _execute_task(self, task: Task, callback: Optional[Callable[[Task], None]] = None):
        """
        Execute task in background thread

        Args:
            task: Task to execute
            callback: Optional completion callback
        """
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        self._update_task_in_db(task)  # Persist running status

        try:
            # Execute command
            # For ISAAC commands, we need to call through the dispatcher
            # Use shlex.split() to safely parse the command and disable shell=True
            process = subprocess.Popen(
                shlex.split(task.command),
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            task.process = process

            # Wait for completion and capture output
            stdout, stderr = process.communicate()

            task.stdout = stdout
            task.stderr = stderr
            task.exit_code = process.returncode
            task.end_time = datetime.now()

            if task.exit_code == 0:
                task.status = TaskStatus.COMPLETED
            else:
                task.status = TaskStatus.FAILED

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.stderr = f"Task execution error: {str(e)}"
            task.exit_code = -1
            task.end_time = datetime.now()

        # Persist final state
        self._update_task_in_db(task)

        # Trigger callbacks
        if callback:
            try:
                callback(task)
            except Exception as e:
                print(f"Error in task callback: {e}", file=sys.stderr)

        if self.on_task_complete:
            try:
                self.on_task_complete(task)
            except Exception as e:
                print(f"Error in global completion handler: {e}", file=sys.stderr)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        with self.lock:
            return self.tasks.get(task_id)

    def get_all_tasks(
        self, status: Optional[TaskStatus] = None, task_type: Optional[str] = None
    ) -> List[Task]:
        """
        Get all tasks with optional filtering

        Args:
            status: Filter by task status
            task_type: Filter by task type (system/code)

        Returns:
            List of matching tasks
        """
        with self.lock:
            tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]

        # Sort by start time (most recent first)
        tasks.sort(key=lambda t: t.start_time or datetime.min, reverse=True)

        return tasks

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task

        Args:
            task_id: Task ID to cancel

        Returns:
            True if task was cancelled, False otherwise
        """
        task = self.get_task(task_id)

        if not task:
            return False

        if task.status != TaskStatus.RUNNING:
            return False

        # Terminate process if running
        if task.process:
            try:
                task.process.terminate()
                task.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                task.process.kill()
            except Exception:
                pass

        task.status = TaskStatus.CANCELLED
        task.end_time = datetime.now()
        self._update_task_in_db(task)  # Persist cancellation

        return True

    def clear_completed_tasks(self) -> int:
        """
        Clear all completed/failed/cancelled tasks

        Returns:
            Number of tasks cleared
        """
        with self.lock:
            to_remove = [
                tid
                for tid, task in self.tasks.items()
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            ]

            # Remove from database
            if to_remove:
                conn = sqlite3.connect(str(self.db_path))
                placeholders = ",".join("?" * len(to_remove))
                conn.execute(f"DELETE FROM tasks WHERE task_id IN ({placeholders})", to_remove)
                conn.commit()
                conn.close()

            # Remove from memory
            for tid in to_remove:
                del self.tasks[tid]

            return len(to_remove)

    def get_statistics(self) -> Dict[str, Any]:
        """Get task execution statistics"""
        with self.lock:
            total = len(self.tasks)
            by_status = {}
            by_type = {}

            for task in self.tasks.values():
                # Count by status
                status = task.status.value
                by_status[status] = by_status.get(status, 0) + 1

                # Count by type
                task_type = task.task_type
                by_type[task_type] = by_type.get(task_type, 0) + 1

            return {
                "total_tasks": total,
                "by_status": by_status,
                "by_type": by_type,
                "max_concurrent": self.max_concurrent_tasks,
            }


# Global task manager instance
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get or create global task manager instance"""
    global _task_manager

    if _task_manager is None:
        _task_manager = TaskManager()

    return _task_manager


def integrate_with_message_queue():
    """
    Integrate task manager with message queue for notifications

    This should be called during ISAAC initialization to set up
    automatic notifications when background tasks complete.
    """
    from isaac.core.message_queue import MessagePriority, MessageQueue, MessageType

    task_manager = get_task_manager()
    message_queue = MessageQueue()

    def notify_on_completion(task: Task):
        """Send notification when task completes"""
        # Determine message type
        msg_type = MessageType.SYSTEM if task.task_type == "system" else MessageType.CODE

        # Determine priority based on task status and priority
        # Map task priority string to MessagePriority enum
        priority_map = {
            "urgent": MessagePriority.URGENT,
            "high": MessagePriority.HIGH,
            "normal": MessagePriority.NORMAL,
            "low": MessagePriority.LOW,
        }

        if task.status == TaskStatus.FAILED:
            msg_priority = MessagePriority.HIGH
        else:
            msg_priority = priority_map.get(task.priority, MessagePriority.NORMAL)

        # Create title
        if task.status == TaskStatus.COMPLETED:
            title = f"✓ Task completed: {task.command[:50]}"
        elif task.status == TaskStatus.FAILED:
            title = f"✗ Task failed: {task.command[:50]}"
        else:
            title = f"Task {task.status.value}: {task.command[:50]}"

        # Create content
        content_parts = []

        if task.stdout:
            content_parts.append("STDOUT:")
            content_parts.append(task.stdout)

        if task.stderr:
            content_parts.append("\nSTDERR:")
            content_parts.append(task.stderr)

        if task.exit_code is not None:
            content_parts.append(f"\nExit code: {task.exit_code}")

        content = "\n".join(content_parts) if content_parts else "No output"

        # Create metadata
        metadata = {
            "task_id": task.task_id,
            "command": task.command,
            "status": task.status.value,
            "exit_code": task.exit_code,
            "duration_seconds": (
                (task.end_time - task.start_time).total_seconds()
                if task.start_time and task.end_time
                else None
            ),
        }
        metadata.update(task.metadata)

        # Send message
        message_queue.add_message(
            message_type=msg_type,
            title=title,
            content=content,
            priority=msg_priority,
            metadata=metadata,
        )

    # Set global completion handler
    task_manager.on_task_complete = notify_on_completion


if __name__ == "__main__":
    # Test the task manager
    manager = get_task_manager()

    # Spawn test task
    print("Spawning test task...")
    task_id = manager.spawn_task("echo 'Hello from background task' && sleep 2 && echo 'Done!'")
    print(f"Task ID: {task_id}")

    # Wait a bit
    time.sleep(1)

    # Check status
    task = manager.get_task(task_id)
    if task:
        print(f"Task status: {task.status.value}")

    # Wait for completion
    time.sleep(3)

    # Check final status
    task = manager.get_task(task_id)
    if task:
        print(f"Final status: {task.status.value}")
        print(f"Exit code: {task.exit_code}")
        print(f"Output: {task.stdout}")

    # Get statistics
    stats = manager.get_statistics()
    print(f"\nStatistics: {json.dumps(stats, indent=2)}")
