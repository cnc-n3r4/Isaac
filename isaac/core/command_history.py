"""
Command History System - Enhanced command history with search
"""

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CommandHistoryEntry:
    """A command history entry"""

    command: str
    timestamp: float
    success: bool
    execution_time: Optional[float] = None
    output_length: Optional[int] = None
    working_directory: Optional[str] = None
    session_id: Optional[str] = None
    tags: Optional[List[str]] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandHistoryEntry":
        """Create from dictionary"""
        return cls(**data)

    @property
    def age_seconds(self) -> float:
        """Get age in seconds"""
        return time.time() - self.timestamp

    @property
    def age_string(self) -> str:
        """Get human-readable age"""
        age = self.age_seconds

        if age < 60:
            return f"{int(age)}s ago"
        elif age < 3600:
            return f"{int(age / 60)}m ago"
        elif age < 86400:
            return f"{int(age / 3600)}h ago"
        else:
            return f"{int(age / 86400)}d ago"


class CommandHistory:
    """Enhanced command history with search and analytics"""

    def __init__(self, history_file: Optional[Path] = None, max_entries: int = 10000):
        if history_file is None:
            # Default to user's Isaac directory
            from pathlib import Path

            isaac_dir = Path.home() / ".isaac"
            isaac_dir.mkdir(exist_ok=True)
            history_file = isaac_dir / "command_history.json"

        self.history_file = history_file
        self.max_entries = max_entries
        self.entries: List[CommandHistoryEntry] = []
        self._load_history()

    def _load_history(self):
        """Load history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for entry_data in data.get("entries", []):
                    try:
                        entry = CommandHistoryEntry.from_dict(entry_data)
                        self.entries.append(entry)
                    except Exception:
                        continue

                # Sort by timestamp (newest first)
                self.entries.sort(key=lambda x: x.timestamp, reverse=True)

            except Exception as e:
                print(f"Warning: Could not load command history: {e}")

    def _save_history(self):
        """Save history to file"""
        try:
            # Keep only recent entries
            if len(self.entries) > self.max_entries:
                self.entries = self.entries[: self.max_entries]

            data = {
                "entries": [entry.to_dict() for entry in self.entries],
                "last_updated": time.time(),
            }

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error saving command history: {e}")

    def add_entry(
        self,
        command: str,
        success: bool = True,
        execution_time: Optional[float] = None,
        output_length: Optional[int] = None,
        working_directory: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ):
        """Add a command to history"""
        entry = CommandHistoryEntry(
            command=command,
            timestamp=time.time(),
            success=success,
            execution_time=execution_time,
            output_length=output_length,
            working_directory=working_directory,
            session_id=session_id,
            tags=tags or [],
        )

        self.entries.insert(0, entry)  # Add to beginning
        self._save_history()

    def get_recent(self, limit: int = 20) -> List[CommandHistoryEntry]:
        """Get recent command history"""
        return self.entries[:limit]

    def search_history(self, query: str, limit: int = 50) -> List[CommandHistoryEntry]:
        """Search command history"""
        query_lower = query.lower()
        matches = []

        for entry in self.entries:
            if query_lower in entry.command.lower():
                matches.append(entry)
                if len(matches) >= limit:
                    break

        return matches

    def get_commands_by_frequency(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently used commands"""
        command_counts = {}

        for entry in self.entries:
            command = entry.command.strip()
            if command:
                command_counts[command] = command_counts.get(command, 0) + 1

        # Sort by frequency
        sorted_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_commands[:limit]

    def get_failed_commands(self, limit: int = 20) -> List[CommandHistoryEntry]:
        """Get recently failed commands"""
        failed = [entry for entry in self.entries if not entry.success]
        return failed[:limit]

    def get_commands_by_pattern(self, pattern: str, limit: int = 20) -> List[CommandHistoryEntry]:
        """Get commands matching a pattern"""
        import re

        try:
            regex = re.compile(pattern, re.IGNORECASE)
            matches = [entry for entry in self.entries if regex.search(entry.command)]
            return matches[:limit]
        except re.error:
            # If regex is invalid, fall back to simple search
            return self.search_history(pattern, limit)

    def get_session_history(self, session_id: str, limit: int = 50) -> List[CommandHistoryEntry]:
        """Get commands from a specific session"""
        session_commands = [entry for entry in self.entries if entry.session_id == session_id]
        return session_commands[:limit]

    def clear_old_history(self, days_old: int = 30) -> int:
        """Clear history older than specified days"""
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)

        original_count = len(self.entries)
        self.entries = [entry for entry in self.entries if entry.timestamp >= cutoff_time]

        removed_count = original_count - len(self.entries)
        if removed_count > 0:
            self._save_history()

        return removed_count

    def export_history(self, file_path: Path, limit: Optional[int] = None) -> bool:
        """Export history to file"""
        try:
            export_entries = self.entries[:limit] if limit else self.entries

            data = {
                "exported_at": time.time(),
                "entries": [entry.to_dict() for entry in export_entries],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False

    def import_history(self, file_path: Path, merge: bool = True) -> int:
        """Import history from file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            imported = 0
            for entry_data in data.get("entries", []):
                try:
                    entry = CommandHistoryEntry.from_dict(entry_data)

                    # Check for duplicates if merging
                    if merge:
                        existing_commands = {e.command + str(e.timestamp) for e in self.entries}
                        entry_key = entry.command + str(entry.timestamp)
                        if entry_key in existing_commands:
                            continue

                    self.entries.append(entry)
                    imported += 1

                except Exception:
                    continue

            if imported > 0:
                self.entries.sort(key=lambda x: x.timestamp, reverse=True)
                self._save_history()

            return imported
        except Exception:
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get history statistics"""
        if not self.entries:
            return {"total_commands": 0}

        total_commands = len(self.entries)
        successful_commands = sum(1 for entry in self.entries if entry.success)
        failed_commands = total_commands - successful_commands

        # Time range
        oldest = min(entry.timestamp for entry in self.entries)
        newest = max(entry.timestamp for entry in self.entries)

        # Average execution time
        exec_times = [entry.execution_time for entry in self.entries if entry.execution_time]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else None

        # Sessions
        sessions = set(entry.session_id for entry in self.entries if entry.session_id)

        return {
            "total_commands": total_commands,
            "successful_commands": successful_commands,
            "failed_commands": failed_commands,
            "success_rate": successful_commands / total_commands if total_commands > 0 else 0,
            "oldest_command": oldest,
            "newest_command": newest,
            "time_span_days": (newest - oldest) / (24 * 60 * 60),
            "avg_execution_time": avg_exec_time,
            "unique_sessions": len(sessions),
            "most_used_commands": self.get_commands_by_frequency(5),
        }


# Global instance for easy access
command_history = CommandHistory()


def add_command_to_history(command: str, success: bool = True, **kwargs):
    """Convenience function to add command to history"""
    command_history.add_entry(command, success, **kwargs)


def get_recent_history(limit: int = 20) -> List[CommandHistoryEntry]:
    """Convenience function to get recent history"""
    return command_history.get_recent(limit)


def search_command_history(query: str, limit: int = 20) -> List[CommandHistoryEntry]:
    """Convenience function to search history"""
    return command_history.search_history(query, limit)
