"""
Tasks Command - Standardized Implementation

View and manage background task execution.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.core.task_manager import TaskStatus, get_task_manager


class TasksCommand(BaseCommand):
    """View and manage background tasks"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute tasks command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with task information
        """
        parser = FlagParser(args)

        # Check for help
        if parser.has_flag('help', ['h']):
            return CommandResponse(
                success=True,
                data=self.get_help()
            )

        # Get task manager
        task_manager = get_task_manager()

        # Parse flags
        show_running = parser.has_flag('running', ['r'])
        show_completed = parser.has_flag('completed', ['c'])
        show_failed = parser.has_flag('failed', ['f'])
        show_stats = parser.has_flag('stats', ['s'])
        show_id = parser.get_flag('show')
        cancel_id = parser.get_flag('cancel')
        clear_tasks = parser.has_flag('clear')

        # Handle operations

        # 1. Show statistics
        if show_stats:
            stats = task_manager.get_statistics()
            output = "\n=== Task Statistics ===\n"
            output += f"Total tasks: {stats['total_tasks']}\n"
            output += f"Max concurrent: {stats['max_concurrent']}\n"
            output += "\nBy Status:\n"
            for status, count in stats.get("by_status", {}).items():
                output += f"  {status}: {count}\n"
            output += "\nBy Type:\n"
            for task_type, count in stats.get("by_type", {}).items():
                output += f"  {task_type}: {count}\n"

            return CommandResponse(
                success=True,
                data=output,
                metadata={"operation": "stats", "stats": stats}
            )

        # 2. Show specific task
        if show_id:
            try:
                task_id = str(show_id)
                task = task_manager.get_task(task_id)
                if not task:
                    return CommandResponse(
                        success=False,
                        error=f"Task {task_id} not found",
                        metadata={"error_code": "NOT_FOUND"}
                    )

                output = self._display_task_detail(task)
                return CommandResponse(
                    success=True,
                    data=output,
                    metadata={"operation": "show", "task_id": task_id}
                )
            except Exception as e:
                return CommandResponse(
                    success=False,
                    error=f"Error showing task: {e}",
                    metadata={"error_code": "SHOW_ERROR"}
                )

        # 3. Cancel task
        if cancel_id:
            try:
                task_id = str(cancel_id)
                if task_manager.cancel_task(task_id):
                    return CommandResponse(
                        success=True,
                        data=f"Task {task_id} cancelled",
                        metadata={"operation": "cancel", "task_id": task_id}
                    )
                else:
                    return CommandResponse(
                        success=False,
                        error=f"Failed to cancel task {task_id} (not found or not running)",
                        metadata={"error_code": "CANCEL_FAILED"}
                    )
            except Exception as e:
                return CommandResponse(
                    success=False,
                    error=f"Error cancelling task: {e}",
                    metadata={"error_code": "CANCEL_ERROR"}
                )

        # 4. Clear completed tasks
        if clear_tasks:
            count = task_manager.clear_completed_tasks()
            return CommandResponse(
                success=True,
                data=f"Cleared {count} completed/failed/cancelled task(s)",
                metadata={"operation": "clear", "count": count}
            )

        # 5. List tasks (default)
        status_filter = None
        if show_running:
            status_filter = TaskStatus.RUNNING
        elif show_completed:
            status_filter = TaskStatus.COMPLETED
        elif show_failed:
            status_filter = TaskStatus.FAILED

        tasks = task_manager.get_all_tasks(status=status_filter)

        if not tasks:
            if status_filter:
                output = f"\nNo {status_filter.value} tasks"
            else:
                output = "\nNo tasks"

            return CommandResponse(
                success=True,
                data=output,
                metadata={"operation": "list", "count": 0}
            )

        # Display tasks
        title = (
            "Running Tasks" if show_running
            else "Completed Tasks" if show_completed
            else "Failed Tasks" if show_failed
            else "All Tasks"
        )

        output = f"\n{title} ({len(tasks)}):\n"
        output += "─" * 80 + "\n"

        for task in tasks:
            output += self._display_task_summary(task)

        return CommandResponse(
            success=True,
            data=output,
            metadata={"operation": "list", "count": len(tasks)}
        )

    def _display_task_summary(self, task) -> str:
        """Display task in summary format"""
        # Status indicator
        status = task.status.value.upper()
        if task.status == TaskStatus.RUNNING:
            status_icon = "⟳"
        elif task.status == TaskStatus.COMPLETED:
            status_icon = "✓"
        elif task.status == TaskStatus.FAILED:
            status_icon = "✗"
        elif task.status == TaskStatus.CANCELLED:
            status_icon = "⊘"
        else:
            status_icon = "○"

        # Type indicator
        type_icon = "!" if task.task_type == "system" else "¢"

        # Duration
        if task.start_time and task.end_time:
            duration = (task.end_time - task.start_time).total_seconds()
            duration_str = self._format_duration(duration)
        elif task.start_time:
            duration = (datetime.now() - task.start_time).total_seconds()
            duration_str = self._format_duration(duration) + " (running)"
        else:
            duration_str = "N/A"

        # Command (truncated)
        command = task.command
        if len(command) > 60:
            command = command[:57] + "..."

        output = f"{status_icon} {type_icon} [{task.task_id}] {status:10} {duration_str:15} {command}\n"

        # Show exit code if failed
        if task.status == TaskStatus.FAILED and task.exit_code is not None:
            output += f"    Exit code: {task.exit_code}\n"

        # Show error preview if present
        if task.stderr and len(task.stderr.strip()) > 0:
            error_preview = task.stderr.strip().split("\n")[0]
            if len(error_preview) > 70:
                error_preview = error_preview[:67] + "..."
            output += f"    Error: {error_preview}\n"

        output += "\n"
        return output

    def _display_task_detail(self, task) -> str:
        """Display full task details"""
        output = "\n" + "=" * 80 + "\n"
        output += f"Task ID: {task.task_id}\n"
        output += f"Command: {task.command}\n"
        output += f"Type: {task.task_type}\n"
        output += f"Priority: {task.priority}\n"
        output += f"Status: {task.status.value}\n"

        if task.start_time:
            output += f"Started: {task.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"

        if task.end_time:
            output += f"Ended: {task.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"

        if task.start_time and task.end_time:
            duration = (task.end_time - task.start_time).total_seconds()
            output += f"Duration: {self._format_duration(duration)}\n"

        if task.exit_code is not None:
            output += f"Exit Code: {task.exit_code}\n"

        output += "=" * 80 + "\n"

        if task.stdout:
            output += "\nSTDOUT:\n"
            output += "─" * 80 + "\n"
            output += task.stdout + "\n"
            output += "─" * 80 + "\n"

        if task.stderr:
            output += "\nSTDERR:\n"
            output += "─" * 80 + "\n"
            output += task.stderr + "\n"
            output += "─" * 80 + "\n"

        if task.metadata:
            output += "\nMetadata:\n"
            output += "─" * 80 + "\n"
            for key, value in task.metadata.items():
                output += f"  {key}: {value}\n"
            output += "─" * 80 + "\n"

        return output

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="tasks",
            description="View and manage background task execution",
            usage="/tasks [--running|--completed|--failed] [--show ID] [--cancel ID] [--clear] [--stats]",
            examples=[
                "/tasks  # List all tasks",
                "/tasks --running  # Show running tasks only",
                "/tasks --show 123  # Show task details",
                "/tasks --cancel 456  # Cancel running task",
                "/tasks --clear  # Clear completed tasks",
                "/tasks --stats  # Show task statistics"
            ],
            tier=1,  # Safe - read-only mostly, cancel is safe
            aliases=["task", "jobs"],
            category="system"
        )
