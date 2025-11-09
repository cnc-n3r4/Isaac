#!/usr/bin/env python3
"""
/tasks command - View and manage background tasks

Provides interface for monitoring and controlling background task execution.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from isaac.core.task_manager import get_task_manager, TaskStatus


def main():
    """Main entry point for tasks command"""
    # Read payload from stdin
    import select
    import os

    # Check if stdin has data
    if os.name == 'nt':
        import msvcrt
        has_stdin = msvcrt.kbhit() or not sys.stdin.isatty()
    else:
        has_stdin = select.select([sys.stdin], [], [], 0)[0]

    if has_stdin:
        try:
            payload = json.loads(sys.stdin.read())
            command = payload.get("command", "/tasks")
            parts = command.split()
            args = parts[1:] if len(parts) > 1 else []
        except (json.JSONDecodeError, KeyError):
            args = sys.argv[1:]
    else:
        args = sys.argv[1:]

    # Get task manager
    task_manager = get_task_manager()

    # Parse arguments
    show_running = False
    show_completed = False
    show_failed = False
    show_stats = False
    show_id = None
    cancel_id = None
    clear_tasks = False

    i = 0
    while i < len(args):
        arg = args[i]

        if arg in ['--running', '-r']:
            show_running = True
        elif arg in ['--completed', '-c']:
            show_completed = True
        elif arg in ['--failed', '-f']:
            show_failed = True
        elif arg in ['--stats', '-s']:
            show_stats = True
        elif arg == '--show' and i + 1 < len(args):
            show_id = args[i + 1]
            i += 1
        elif arg == '--cancel' and i + 1 < len(args):
            cancel_id = args[i + 1]
            i += 1
        elif arg in ['--clear']:
            clear_tasks = True
        elif arg in ['--list', '-l']:
            pass  # Default behavior
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
            print_usage()
            sys.exit(1)

        i += 1

    # Handle operations

    # 1. Show statistics
    if show_stats:
        stats = task_manager.get_statistics()
        print("\n=== Task Statistics ===")
        print(f"Total tasks: {stats['total_tasks']}")
        print(f"Max concurrent: {stats['max_concurrent']}")
        print("\nBy Status:")
        for status, count in stats.get('by_status', {}).items():
            print(f"  {status}: {count}")
        print("\nBy Type:")
        for task_type, count in stats.get('by_type', {}).items():
            print(f"  {task_type}: {count}")
        return

    # 2. Show specific task
    if show_id:
        task = task_manager.get_task(show_id)
        if not task:
            print(f"✗ Task {show_id} not found")
            sys.exit(1)
        display_task_detail(task)
        return

    # 3. Cancel task
    if cancel_id:
        if task_manager.cancel_task(cancel_id):
            print(f"✓ Task {cancel_id} cancelled")
        else:
            print(f"✗ Failed to cancel task {cancel_id} (not found or not running)")
            sys.exit(1)
        return

    # 4. Clear completed tasks
    if clear_tasks:
        count = task_manager.clear_completed_tasks()
        print(f"✓ Cleared {count} completed/failed/cancelled task(s)")
        return

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
            print(f"\nNo {status_filter.value} tasks")
        else:
            print("\nNo tasks")
        return

    # Display tasks
    title = "Running Tasks" if show_running else \
            "Completed Tasks" if show_completed else \
            "Failed Tasks" if show_failed else \
            "All Tasks"

    print(f"\n{title} ({len(tasks)}):")
    print("─" * 80)

    for task in tasks:
        display_task_summary(task)


def display_task_summary(task):
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
        duration_str = format_duration(duration)
    elif task.start_time:
        duration = (datetime.now() - task.start_time).total_seconds()
        duration_str = format_duration(duration) + " (running)"
    else:
        duration_str = "N/A"

    # Command (truncated)
    command = task.command
    if len(command) > 60:
        command = command[:57] + "..."

    print(f"{status_icon} {type_icon} [{task.task_id}] {status:10} {duration_str:15} {command}")

    # Show exit code if failed
    if task.status == TaskStatus.FAILED and task.exit_code is not None:
        print(f"    Exit code: {task.exit_code}")

    # Show error preview if present
    if task.stderr and len(task.stderr.strip()) > 0:
        error_preview = task.stderr.strip().split('\n')[0]
        if len(error_preview) > 70:
            error_preview = error_preview[:67] + "..."
        print(f"    Error: {error_preview}")

    print()


def display_task_detail(task):
    """Display full task details"""
    print("\n" + "=" * 80)
    print(f"Task ID: {task.task_id}")
    print(f"Command: {task.command}")
    print(f"Type: {task.task_type}")
    print(f"Priority: {task.priority}")
    print(f"Status: {task.status.value}")

    if task.start_time:
        print(f"Started: {task.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    if task.end_time:
        print(f"Ended: {task.end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    if task.start_time and task.end_time:
        duration = (task.end_time - task.start_time).total_seconds()
        print(f"Duration: {format_duration(duration)}")

    if task.exit_code is not None:
        print(f"Exit Code: {task.exit_code}")

    print("=" * 80)

    if task.stdout:
        print("\nSTDOUT:")
        print("─" * 80)
        print(task.stdout)
        print("─" * 80)

    if task.stderr:
        print("\nSTDERR:")
        print("─" * 80)
        print(task.stderr)
        print("─" * 80)

    if task.metadata:
        print("\nMetadata:")
        print("─" * 80)
        for key, value in task.metadata.items():
            print(f"  {key}: {value}")
        print("─" * 80)

    print()


def format_duration(seconds: float) -> str:
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


def print_usage():
    """Print usage information"""
    print("Usage: /tasks [OPTIONS]", file=sys.stderr)
    print("  --list, -l             List all tasks (default)", file=sys.stderr)
    print("  --running, -r          Show running tasks", file=sys.stderr)
    print("  --completed, -c        Show completed tasks", file=sys.stderr)
    print("  --failed, -f           Show failed tasks", file=sys.stderr)
    print("  --show ID              Show task details", file=sys.stderr)
    print("  --cancel ID            Cancel running task", file=sys.stderr)
    print("  --clear                Clear completed tasks", file=sys.stderr)
    print("  --stats, -s            Show statistics", file=sys.stderr)


if __name__ == "__main__":
    main()
