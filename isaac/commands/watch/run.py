# isaac/commands/watch/run.py

"""
Watch command - demonstrates file watching with change queue.
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from isaac.core.change_queue import BackgroundWorker, ChangeQueue
from isaac.core.file_watcher import FileWatcher


def process_changes(events):
    """Process a batch of change events."""
    for event in events:
        print(f"✓ Processed: {event.action} {event.path}")


def main():
    """Main entry point for watch command"""
    # Read payload from stdin (dispatcher sends args this way)
    import json
    import os
    import select

    # Check if stdin has data (running through dispatcher)
    if os.name == "nt":
        import msvcrt

        has_stdin = msvcrt.kbhit() or not sys.stdin.isatty()
    else:
        has_stdin = select.select([sys.stdin], [], [], 0)[0]

    args = {}
    if has_stdin:
        try:
            payload = json.loads(sys.stdin.read())
            args = payload.get("args", {})
        except (json.JSONDecodeError, KeyError):
            pass

    # Get paths to watch
    paths_str = args.get("paths", "")
    if paths_str:
        paths = [Path(p.strip()) for p in paths_str.split(",") if p.strip()]
    else:
        # Default: watch some files in current directory
        cwd = Path(".")
        paths = list(cwd.glob("*.py"))[:3]  # Watch up to 3 Python files
        if not paths:
            paths = [cwd / "README.md"] if (cwd / "README.md").exists() else []

    if not paths:
        print("No files to watch. Specify --paths or ensure .py files exist.")
        return

    print(f"Watching {len(paths)} files:")
    for p in paths:
        print(f"  {p}")
    print("Press Ctrl+C to stop...")

    # Create queue and worker
    queue = ChangeQueue()  # In-memory for demo
    worker = BackgroundWorker(queue, process_changes, interval=1.0)
    worker.start()

    # Create watcher
    watcher = FileWatcher(paths, queue=queue, poll_interval=1.0, debounce=0.5)
    watcher.start()

    try:
        # Run for a bit to demonstrate
        for i in range(30):  # 30 seconds
            pending = queue.count_pending()
            if pending > 0:
                print(f"Queue has {pending} pending changes")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        watcher.stop()
        worker.stop()
        print(f"Final queue status: {queue.count_pending()} pending changes")


if __name__ == "__main__":
    main()
