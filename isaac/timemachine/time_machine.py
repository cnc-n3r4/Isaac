"""
Time Machine - Automatic workspace snapshots and timeline navigation
Isaac's temporal workspace management system
"""

import json
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from isaac.bubbles.manager import BubbleManager, WorkspaceState


@dataclass
class TimelineEntry:
    """Entry in the workspace timeline."""
    timestamp: float
    bubble_id: str
    change_type: str  # 'auto', 'manual', 'restore', 'branch_switch', etc.
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimelineSnapshot:
    """Snapshot of timeline state."""
    entries: List[TimelineEntry] = field(default_factory=list)
    current_index: int = -1
    total_entries: int = 0


class TimeMachine:
    """Manages automatic snapshots and timeline navigation."""

    def __init__(self, bubble_manager: BubbleManager, storage_path: Optional[Path] = None):
        """Initialize time machine.

        Args:
            bubble_manager: Bubble manager instance
            storage_path: Path to store timeline data
        """
        self.bubble_manager = bubble_manager

        if storage_path is None:
            isaac_dir = Path.home() / '.isaac'
            isaac_dir.mkdir(exist_ok=True)
            storage_path = isaac_dir / 'time_machine'

        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

        # Timeline data
        self.timeline_file = self.storage_path / 'timeline.json'
        self.timeline = self._load_timeline()

        # Auto-snapshot settings
        self.auto_snapshot_enabled = True
        self.snapshot_interval_minutes = 30  # Every 30 minutes
        self.max_snapshots = 100  # Keep last 100 snapshots
        self.min_snapshot_interval_seconds = 300  # Minimum 5 minutes between snapshots

        # Background thread for auto-snapshots
        self.snapshot_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Track last snapshot time
        self.last_snapshot_time = time.time()

        # Start auto-snapshot if enabled
        if self.auto_snapshot_enabled:
            self._start_auto_snapshot()

    def _load_timeline(self) -> TimelineSnapshot:
        """Load timeline from disk."""
        if self.timeline_file.exists():
            try:
                with open(self.timeline_file, 'r') as f:
                    data = json.load(f)

                entries = []
                for entry_data in data.get('entries', []):
                    entry = TimelineEntry(**entry_data)
                    entries.append(entry)

                return TimelineSnapshot(
                    entries=entries,
                    current_index=data.get('current_index', -1),
                    total_entries=len(entries)
                )
            except Exception:
                pass

        return TimelineSnapshot()

    def _save_timeline(self) -> None:
        """Save timeline to disk."""
        data = {
            'entries': [entry.__dict__ for entry in self.timeline.entries],
            'current_index': self.timeline.current_index,
            'total_entries': self.timeline.total_entries
        }

        try:
            with open(self.timeline_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def create_snapshot(self, description: str = "", change_type: str = "manual",
                       force: bool = False) -> Optional[WorkspaceState]:
        """Create a new timeline snapshot.

        Args:
            description: Description of the snapshot
            change_type: Type of change ('auto', 'manual', 'restore', etc.)
            force: Force creation even if minimum interval hasn't passed

        Returns:
            Created bubble state or None if failed
        """
        current_time = time.time()

        # Check minimum interval (unless forced)
        if not force and (current_time - self.last_snapshot_time) < self.min_snapshot_interval_seconds:
            return None

        # Create bubble snapshot
        timestamp = datetime.fromtimestamp(current_time)
        bubble_name = f"Timeline_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        bubble = self.bubble_manager.create_bubble(
            name=bubble_name,
            description=description or f"Timeline snapshot: {change_type}",
            tags=["timeline", change_type]
        )

        # Add to timeline
        entry = TimelineEntry(
            timestamp=current_time,
            bubble_id=bubble.bubble_id,
            change_type=change_type,
            description=description or f"Automatic {change_type} snapshot",
            metadata={
                'bubble_name': bubble.name,
                'workspace_path': bubble.cwd,
                'git_branch': bubble.git_branch
            }
        )

        self.timeline.entries.append(entry)
        self.timeline.total_entries += 1
        self.timeline.current_index = len(self.timeline.entries) - 1

        # Clean up old snapshots if we exceed max
        self._cleanup_old_snapshots()

        # Save timeline
        self._save_timeline()

        # Update last snapshot time
        self.last_snapshot_time = current_time

        return bubble

    def _cleanup_old_snapshots(self) -> None:
        """Remove old snapshots to stay within limits."""
        if len(self.timeline.entries) <= self.max_snapshots:
            return

        # Remove oldest entries
        entries_to_remove = len(self.timeline.entries) - self.max_snapshots

        for i in range(entries_to_remove):
            old_entry = self.timeline.entries[i]
            # Delete the bubble
            self.bubble_manager.delete_bubble(old_entry.bubble_id)

        # Remove from timeline
        self.timeline.entries = self.timeline.entries[entries_to_remove:]
        self.timeline.total_entries = len(self.timeline.entries)

        # Adjust current index
        if self.timeline.current_index >= entries_to_remove:
            self.timeline.current_index -= entries_to_remove
        else:
            self.timeline.current_index = -1

    def get_timeline(self, limit: int = 50) -> List[TimelineEntry]:
        """Get timeline entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of timeline entries (newest first)
        """
        return list(reversed(self.timeline.entries[-limit:]))

    def restore_to_timestamp(self, target_timestamp: float) -> bool:
        """Restore workspace to a specific timestamp.

        Args:
            target_timestamp: Unix timestamp to restore to

        Returns:
            True if restoration successful
        """
        # Find the closest snapshot before or at the target timestamp
        closest_entry = None
        for entry in reversed(self.timeline.entries):
            if entry.timestamp <= target_timestamp:
                closest_entry = entry
                break

        if not closest_entry:
            return False

        # Restore the bubble
        success = self.bubble_manager.restore_bubble(closest_entry.bubble_id)

        if success:
            # Add restore entry to timeline
            restore_entry = TimelineEntry(
                timestamp=time.time(),
                bubble_id=closest_entry.bubble_id,
                change_type="restore",
                description=f"Restored to {datetime.fromtimestamp(closest_entry.timestamp).strftime('%Y-%m-%d %H:%M:%S')}",
                metadata={'restored_from': closest_entry.timestamp}
            )

            self.timeline.entries.append(restore_entry)
            self.timeline.total_entries += 1
            self.timeline.current_index = len(self.timeline.entries) - 1
            self._save_timeline()

        return success

    def restore_to_entry(self, entry_index: int) -> bool:
        """Restore to a specific timeline entry.

        Args:
            entry_index: Index in timeline entries

        Returns:
            True if restoration successful
        """
        if entry_index < 0 or entry_index >= len(self.timeline.entries):
            return False

        entry = self.timeline.entries[entry_index]

        # Restore the bubble
        success = self.bubble_manager.restore_bubble(entry.bubble_id)

        if success:
            # Add restore entry to timeline
            restore_entry = TimelineEntry(
                timestamp=time.time(),
                bubble_id=entry.bubble_id,
                change_type="restore",
                description=f"Restored to timeline entry {entry_index}",
                metadata={'restored_entry_index': entry_index}
            )

            self.timeline.entries.append(restore_entry)
            self.timeline.total_entries += 1
            self.timeline.current_index = len(self.timeline.entries) - 1
            self._save_timeline()

        return success

    def get_snapshot_info(self, bubble_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a snapshot.

        Args:
            bubble_id: Bubble ID to get info for

        Returns:
            Snapshot information or None if not found
        """
        bubble = self.bubble_manager.get_bubble(bubble_id)
        if not bubble:
            return None

        # Find timeline entry
        timeline_entry = None
        for entry in self.timeline.entries:
            if entry.bubble_id == bubble_id:
                timeline_entry = entry
                break

        return {
            'bubble': bubble,
            'timeline_entry': timeline_entry,
            'age_seconds': time.time() - bubble.timestamp if timeline_entry else 0,
            'age_formatted': self._format_age(time.time() - bubble.timestamp) if timeline_entry else "Unknown"
        }

    def search_timeline(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search timeline for entries matching query.

        Args:
            query: Search query (case-insensitive)
            limit: Maximum results to return

        Returns:
            List of matching timeline entries with bubble info
        """
        results = []
        query_lower = query.lower()

        for entry in reversed(self.timeline.entries):
            # Search in description, change_type, and bubble name
            searchable_text = f"{entry.description} {entry.change_type} {entry.metadata.get('bubble_name', '')}".lower()

            if query_lower in searchable_text:
                bubble_info = self.get_snapshot_info(entry.bubble_id)
                if bubble_info:
                    results.append({
                        'entry': entry,
                        'bubble_info': bubble_info
                    })

                    if len(results) >= limit:
                        break

        return results

    def get_timeline_stats(self) -> Dict[str, Any]:
        """Get timeline statistics."""
        if not self.timeline.entries:
            return {'total_snapshots': 0, 'oldest': None, 'newest': None, 'span_days': 0}

        oldest = min(entry.timestamp for entry in self.timeline.entries)
        newest = max(entry.timestamp for entry in self.timeline.entries)
        span_seconds = newest - oldest

        # Count by change type
        change_types = {}
        for entry in self.timeline.entries:
            change_types[entry.change_type] = change_types.get(entry.change_type, 0) + 1

        return {
            'total_snapshots': len(self.timeline.entries),
            'oldest': datetime.fromtimestamp(oldest).isoformat(),
            'newest': datetime.fromtimestamp(newest).isoformat(),
            'span_days': span_seconds / (24 * 3600),
            'change_types': change_types,
            'auto_snapshots': change_types.get('auto', 0),
            'manual_snapshots': change_types.get('manual', 0)
        }

    def _start_auto_snapshot(self) -> None:
        """Start automatic snapshot background thread."""
        def snapshot_worker():
            """Background worker for automatic snapshots."""
            while not self.stop_event.is_set():
                try:
                    # Wait for next snapshot interval
                    self.stop_event.wait(self.snapshot_interval_minutes * 60)

                    if self.stop_event.is_set():
                        break

                    # Create automatic snapshot
                    self.create_snapshot(
                        description="Automatic timeline snapshot",
                        change_type="auto",
                        force=True
                    )

                except Exception as e:
                    # Log error but continue
                    print(f"Auto-snapshot error: {e}")
                    time.sleep(60)  # Wait a minute before retrying

        self.snapshot_thread = threading.Thread(target=snapshot_worker, daemon=True)
        self.snapshot_thread.start()

    def stop_auto_snapshot(self) -> None:
        """Stop automatic snapshot thread."""
        if self.stop_event:
            self.stop_event.set()

        if self.snapshot_thread and self.snapshot_thread.is_alive():
            self.snapshot_thread.join(timeout=5)

    def _format_age(self, seconds: float) -> str:
        """Format age in human-readable form."""
        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h ago"
        else:
            return f"{int(seconds / 86400)}d ago"

    def __del__(self):
        """Cleanup on destruction."""
        self.stop_auto_snapshot()