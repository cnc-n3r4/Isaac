#!/usr/bin/env python3
"""
ISAAC Task Manager - Background Task Execution

Manages background task execution with notification support.
Tasks run asynchronously and notify via message queue on completion.
"""

import os
import sys
import json
import time
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import uuid


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMode(Enum):
    """Command execution modes"""
    VERBOSE = "verbose"      # Immediate output (default)
    BACKGROUND = "background"  # Run in background, notify on completion
    PIPED = "piped"         # Output to pipe for next command


class Task:
    """Represents a background task"""

    def __init__(
        self,
        task_id: str,
        command: str,
        task_type: str = "code",
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
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
            'task_id': self.task_id,
            'command': self.command,
            'task_type': self.task_type,
            'priority': self.priority,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'exit_code': self.exit_code,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'metadata': self.metadata
        }


class TaskManager:
    """
    Manages background task execution

    Features:
    - Spawn and track background tasks
    - Capture task output
    - Send notifications on completion
    - Task status queries
    """

    def __init__(self, max_concurrent_tasks: int = 10):
        """
        Initialize task manager

        Args:
            max_concurrent_tasks: Maximum number of concurrent background tasks
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: Dict[str, Task] = {}
        self.lock = threading.Lock()

        # Callback for task completion notifications
        self.on_task_complete: Optional[Callable[[Task], None]] = None

    def spawn_task(
        self,
        command: str,
        task_type: str = "code",
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[Task], None]] = None
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
            metadata=metadata
        )

        # Check concurrent task limit
        with self.lock:
            running_count = sum(
                1 for t in self.tasks.values()
                if t.status == TaskStatus.RUNNING
            )

            if running_count >= self.max_concurrent_tasks:
                task.status = TaskStatus.FAILED
                task.stderr = f"Maximum concurrent tasks ({self.max_concurrent_tasks}) reached"
                self.tasks[task_id] = task
                return task_id

            # Store task
            self.tasks[task_id] = task

        # Spawn execution thread
        thread = threading.Thread(
            target=self._execute_task,
            args=(task, callback),
            daemon=True
        )
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

        try:
            # Execute command
            # For ISAAC commands, we need to call through the dispatcher
            # For now, execute as shell command
            process = subprocess.Popen(
                task.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
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
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[str] = None
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

        return True

    def clear_completed_tasks(self) -> int:
        """
        Clear all completed/failed/cancelled tasks

        Returns:
            Number of tasks cleared
        """
        with self.lock:
            to_remove = [
                tid for tid, task in self.tasks.items()
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            ]

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
                'total_tasks': total,
                'by_status': by_status,
                'by_type': by_type,
                'max_concurrent': self.max_concurrent_tasks
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
    from isaac.core.message_queue import MessageQueue, MessageType, MessagePriority

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
            "low": MessagePriority.LOW
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
            'task_id': task.task_id,
            'command': task.command,
            'status': task.status.value,
            'exit_code': task.exit_code,
            'duration_seconds': (
                (task.end_time - task.start_time).total_seconds()
                if task.start_time and task.end_time
                else None
            )
        }
        metadata.update(task.metadata)

        # Send message
        message_queue.add_message(
            message_type=msg_type,
            title=title,
            content=content,
            priority=msg_priority,
            metadata=metadata
        )

    # Set global completion handler
    task_manager.on_task_complete = notify_on_completion


if __name__ == '__main__':
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
