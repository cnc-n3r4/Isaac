"""
Watch Command - Standardized Implementation

File watching and monitoring with change detection.
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse


class WatchCommand(BaseCommand):
    """File watching and monitoring"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute watch command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with watch operation results
        """
        try:
            from isaac.core.change_queue import BackgroundWorker, ChangeQueue
            from isaac.core.file_watcher import FileWatcher

            parser = FlagParser(args)

            # Get paths to watch
            paths_str = parser.get_flag("paths", "")
            if paths_str:
                paths = [Path(p.strip()) for p in paths_str.split(",") if p.strip()]
            else:
                # Get positional args as paths
                positional = parser.get_all_positional()
                if positional:
                    paths = [Path(p) for p in positional]
                else:
                    # Default: watch some files in current directory
                    cwd = Path(".")
                    paths = list(cwd.glob("*.py"))[:3]  # Watch up to 3 Python files
                    if not paths:
                        paths = [cwd / "README.md"] if (cwd / "README.md").exists() else []

            if not paths:
                return CommandResponse(
                    success=False,
                    error="No files to watch. Specify paths or ensure .py files exist.",
                    metadata={"error_code": "NO_FILES"}
                )

            output_lines = [f"Watching {len(paths)} files:"]
            for p in paths:
                output_lines.append(f"  {p}")
            output_lines.append("Press Ctrl+C to stop...")

            # Create queue and worker
            def process_changes(events):
                """Process a batch of change events."""
                for event in events:
                    output_lines.append(f"✓ Processed: {event.action} {event.path}")

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
                        output_lines.append(f"Queue has {pending} pending changes")
                    time.sleep(1)
            except KeyboardInterrupt:
                output_lines.append("\nStopping...")
            finally:
                watcher.stop()
                worker.stop()
                output_lines.append(f"Final queue status: {queue.count_pending()} pending changes")

            return CommandResponse(
                success=True,
                data="\n".join(output_lines),
                metadata={}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "WATCH_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="watch",
            description="File watching and monitoring with change detection",
            usage="/watch [paths...] [--paths <paths>]",
            examples=[
                "/watch file1.py file2.py    # Watch specific files",
                "/watch --paths src/,tests/  # Watch directories",
                "/watch                      # Watch current directory Python files"
            ],
            tier=1,  # Safe - read-only monitoring
            aliases=["monitor"],
            category="system"
        )
