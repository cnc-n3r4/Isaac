# Phase 4: Background Execution & Notifications

**Status:** ✅ Completed
**Version:** 1.0.0

## Overview

Phase 4 implements asynchronous background task execution with automatic notification support. Users can run commands in the background and receive notifications via the message queue when tasks complete.

## Features

### 1. Task Manager (`isaac/core/task_manager.py`)

Core component for managing background task execution:

- **Asynchronous Execution**: Spawn tasks that run in background threads
- **Task Tracking**: Monitor status, progress, and completion
- **Output Capture**: Capture stdout/stderr from background tasks
- **Concurrent Limits**: Configurable maximum concurrent tasks
- **Task Control**: Cancel running tasks, clear completed tasks

#### Task States

- `PENDING`: Task queued but not yet started
- `RUNNING`: Task currently executing
- `COMPLETED`: Task finished successfully (exit code 0)
- `FAILED`: Task finished with error (non-zero exit code)
- `CANCELLED`: Task was manually cancelled

#### Usage Example

```python
from isaac.core.task_manager import get_task_manager

# Get task manager instance
manager = get_task_manager()

# Spawn background task
task_id = manager.spawn_task(
    command='pytest tests/',
    task_type='code',
    priority='high',
    metadata={'project': 'isaac', 'suite': 'unit'}
)

# Check task status
task = manager.get_task(task_id)
print(f"Status: {task.status.value}")

# Get all running tasks
running = manager.get_all_tasks(status=TaskStatus.RUNNING)
```

### 2. Message Queue Integration

Automatic notification system for task completion:

- **Completion Notifications**: Automatically sends message when task completes
- **Type Routing**:
  - `!` (system) for system tasks
  - `¢` (code) for code tasks
- **Priority Mapping**: Failed tasks escalated to HIGH priority
- **Rich Metadata**: Task ID, command, duration, exit code included

#### Notification Flow

```
Task Completes → TaskManager → MessageQueue → /msg notification
```

Example notification:

```
[H] ¢ [123] ✓ Task completed: pytest tests/
    STDOUT:
    ============================= test session starts ==============================
    collected 42 items

    tests/test_core.py::test_example PASSED                                  [100%]
    ============================== 42 passed in 2.15s ===============================

    Exit code: 0
    Duration: 2.15s
```

### 3. /tasks Command

User interface for task management:

#### Commands

```bash
/tasks                   # List all tasks
/tasks --running         # Show only running tasks
/tasks --completed       # Show only completed tasks
/tasks --failed          # Show only failed tasks
/tasks --show <ID>       # Show detailed task info
/tasks --cancel <ID>     # Cancel a running task
/tasks --clear           # Clear completed/failed tasks
/tasks --stats           # Show execution statistics
```

#### Output Format

```
All Tasks (5):
────────────────────────────────────────────────────────────────────────────────
✓ ¢ [abc123] COMPLETED  2.3s            pytest tests/unit
⟳ ! [def456] RUNNING    5.1s (running)  system update check
✗ ¢ [ghi789] FAILED     0.5s            npm run build
    Exit code: 1
    Error: Module not found: 'react'...
```

**Status Icons:**
- `✓` Completed
- `✗` Failed
- `⟳` Running
- `⊘` Cancelled
- `○` Pending

**Type Icons:**
- `!` System operation
- `¢` Code operation

### 4. Execution Modes

Three execution modes for commands (future implementation):

1. **VERBOSE** (default): Synchronous, immediate output
2. **BACKGROUND**: Asynchronous, notify via /msg on completion
3. **PIPED**: Output directed to next command in pipeline

## Architecture

```
┌─────────────────┐
│  User Command   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dispatcher    │  (Future: execution mode routing)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TaskManager    │  ← Spawn background threads
│  - spawn_task() │  ← Capture stdout/stderr
│  - track state  │  ← Monitor completion
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐   ┌──────────────┐
│  Task Thread    │   │ MessageQueue │
│  - Execute cmd  │   │ - Store msg  │
│  - Capture I/O  │   │ - Notify     │
└────────┬────────┘   └──────────────┘
         │                 ▲
         └─────────────────┘
           On completion
```

## Integration

### Initialization

To enable background task notifications, call during ISAAC startup:

```python
from isaac.core.task_manager import integrate_with_message_queue

# Set up automatic notifications
integrate_with_message_queue()
```

This registers a global callback that sends a message whenever any task completes.

### Task Metadata

Tasks support custom metadata for tracking context:

```python
task_id = manager.spawn_task(
    command='./deploy.sh',
    task_type='system',
    priority='urgent',
    metadata={
        'environment': 'production',
        'version': '2.1.0',
        'triggered_by': 'ci_pipeline'
    }
)
```

Metadata is included in completion notifications.

## Statistics

Track task execution metrics:

```python
stats = manager.get_statistics()
# {
#     'total_tasks': 42,
#     'by_status': {'completed': 30, 'running': 2, 'failed': 10},
#     'by_type': {'code': 35, 'system': 7},
#     'max_concurrent': 10
# }
```

## Use Cases

### 1. Long-Running Tests

```python
# Run tests in background
manager.spawn_task(
    'pytest tests/ --cov',
    task_type='code',
    priority='high'
)

# User continues working
# Receives notification when tests complete
```

### 2. System Operations

```python
# Background system update
manager.spawn_task(
    'apt-get update && apt-get upgrade -y',
    task_type='system',
    priority='normal'
)
```

### 3. Build & Deploy

```python
# Multi-step deployment
manager.spawn_task(
    './build.sh && ./deploy.sh production',
    task_type='code',
    priority='urgent',
    metadata={'env': 'production', 'build_id': '1234'}
)
```

## Configuration

### Task Manager Settings

```python
from isaac.core.task_manager import TaskManager

# Custom configuration
manager = TaskManager(
    max_concurrent_tasks=5  # Limit concurrent tasks
)
```

### Message Priority Mapping

- `urgent` → MessagePriority.URGENT
- `high` → MessagePriority.HIGH
- `normal` → MessagePriority.NORMAL
- `low` → MessagePriority.LOW
- Task failures automatically elevated to HIGH

## Future Enhancements

### Command Dispatcher Integration

Planned integration with command dispatcher to support execution mode flags:

```bash
# Verbose mode (default)
isaac /grep "TODO" --recursive

# Background mode
isaac --background /grep "TODO" --recursive
# or
isaac -bg /grep "TODO" --recursive

# Piped mode
isaac /glob "**/*.py" | isaac /grep "def main"
```

### Persistent Task Storage

Future: Store tasks in database for cross-session persistence and recovery after restarts.

### Task Dependencies

Future: Support task chains and dependencies:

```python
build_task = manager.spawn_task('./build.sh')
test_task = manager.spawn_task(
    './test.sh',
    dependencies=[build_task]  # Run after build
)
```

### Progress Reporting

Future: Real-time progress updates for long-running tasks:

```python
task.report_progress(50, "Building artifacts...")
```

## Testing

Run the task manager tests:

```bash
# Basic functionality
python3 isaac/core/task_manager.py

# Integration with message queue
python3 <<EOF
from isaac.core.task_manager import integrate_with_message_queue
integrate_with_message_queue()
# ... spawn tasks ...
EOF
```

## Related Documentation

- [Message Queue System](./MESSAGE_QUEUE.md)
- [Command Plugin System](./PLUGIN_SYSTEM.md)
- [Phase 3: AI Routing](./PHASE3_AI_ROUTING.md)

## Version History

- **1.0.0** (2025-01-09): Initial implementation
  - TaskManager core component
  - /tasks command
  - MessageQueue integration
  - Task lifecycle management
