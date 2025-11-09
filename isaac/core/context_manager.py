"""
Context Management System
Persistent conversation state with project awareness and context retrieval
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class ConversationEntry:
    """Single conversation entry"""

    role: str  # 'user', 'assistant', 'tool', 'system'
    content: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationEntry":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ProjectContext:
    """Project-level context information"""

    root_directory: Optional[Path] = None
    current_directory: Optional[Path] = None
    working_files: Set[Path] = field(default_factory=set)
    recent_operations: List[Dict[str, Any]] = field(default_factory=list)
    project_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_directory": str(self.root_directory) if self.root_directory else None,
            "current_directory": str(self.current_directory) if self.current_directory else None,
            "working_files": [str(f) for f in self.working_files],
            "recent_operations": self.recent_operations,
            "project_metadata": self.project_metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectContext":
        return cls(
            root_directory=Path(data["root_directory"]) if data.get("root_directory") else None,
            current_directory=(
                Path(data["current_directory"]) if data.get("current_directory") else None
            ),
            working_files=set(Path(f) for f in data.get("working_files", [])),
            recent_operations=data.get("recent_operations", []),
            project_metadata=data.get("project_metadata", {}),
        )


class ConversationContext:
    """
    Persistent conversation state with project awareness.

    Manages conversation history, project context, and provides relevant context
    for AI interactions.
    """

    def __init__(self, context_file: Optional[Path] = None):
        if context_file is None:
            context_file = Path.home() / ".isaac" / "conversation_context.json"

        self.context_file = context_file
        self.context_file.parent.mkdir(parents=True, exist_ok=True)

        # Conversation state
        self.conversation_history: List[ConversationEntry] = []
        self.max_history_length = 100  # Keep last 100 entries

        # Project context
        self.project_context = ProjectContext()

        # Session state
        self.session_start_time = time.time()
        self.last_activity = time.time()

        # Load existing context
        self._load_context()

    def _load_context(self):
        """Load context from file"""
        if self.context_file.exists():
            try:
                with open(self.context_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Load conversation history
                self.conversation_history = [
                    ConversationEntry.from_dict(entry)
                    for entry in data.get("conversation_history", [])
                ]

                # Load project context
                if "project_context" in data:
                    self.project_context = ProjectContext.from_dict(data["project_context"])

                print(f"✅ Loaded context: {len(self.conversation_history)} entries")

            except Exception as e:
                print(f"Warning: Failed to load context: {e}")
                # Start with empty context

    def _save_context(self):
        """Save context to file"""
        try:
            data = {
                "conversation_history": [entry.to_dict() for entry in self.conversation_history],
                "project_context": self.project_context.to_dict(),
                "session_info": {
                    "start_time": self.session_start_time,
                    "last_activity": self.last_activity,
                },
            }

            with open(self.context_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Warning: Failed to save context: {e}")

    def add_entry(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a new conversation entry"""
        entry = ConversationEntry(
            role=role, content=content, timestamp=time.time(), metadata=metadata or {}
        )

        self.conversation_history.append(entry)

        # Trim history if too long
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length :]

        self.last_activity = time.time()
        self._save_context()

    def get_recent_history(self, limit: int = 10) -> List[ConversationEntry]:
        """Get recent conversation history"""
        return self.conversation_history[-limit:]

    def get_relevant_context(self, user_input: str, max_entries: int = 5) -> Dict[str, Any]:
        """
        Extract relevant context for AI based on user input.

        Uses simple keyword matching and recency for now.
        TODO: Implement semantic search and relevance scoring.
        """
        # Simple keyword extraction from user input
        user_words = set(user_input.lower().split())
        relevant_entries = []

        # Search through recent history for relevant entries
        for entry in reversed(self.conversation_history[-20:]):  # Last 20 entries
            entry_words = set(entry.content.lower().split())

            # Calculate word overlap
            overlap = len(user_words.intersection(entry_words))
            relevance_score = overlap / len(user_words) if user_words else 0

            if relevance_score > 0.1:  # At least 10% word overlap
                relevant_entries.append((entry, relevance_score))

        # Sort by relevance and recency
        relevant_entries.sort(key=lambda x: (x[1], x[0].timestamp), reverse=True)
        relevant_entries = relevant_entries[:max_entries]

        # Build context
        context = {
            "recent_history": [entry.to_dict() for entry, _ in relevant_entries],
            "working_files": [str(f) for f in self.project_context.working_files],
            "current_directory": (
                str(self.project_context.current_directory)
                if self.project_context.current_directory
                else None
            ),
            "project_root": (
                str(self.project_context.root_directory)
                if self.project_context.root_directory
                else None
            ),
            "recent_operations": self.project_context.recent_operations[-3:],  # Last 3 operations
        }

        return context

    def update_project_context(self, **kwargs):
        """Update project context information"""
        for key, value in kwargs.items():
            if key == "current_directory" and value:
                self.project_context.current_directory = Path(value)
            elif key == "root_directory" and value:
                self.project_context.root_directory = Path(value)
            elif key == "working_files" and isinstance(value, list):
                self.project_context.working_files.update(Path(f) for f in value)
            elif key == "project_metadata":
                self.project_context.project_metadata.update(value)

        self._save_context()

    def add_recent_operation(self, operation: Dict[str, Any]):
        """Add a recent operation to project context"""
        operation["timestamp"] = time.time()
        self.project_context.recent_operations.append(operation)

        # Keep only last 10 operations
        if len(self.project_context.recent_operations) > 10:
            self.project_context.recent_operations = self.project_context.recent_operations[-10:]

        self._save_context()

    def mark_file_as_working(self, file_path: str):
        """Mark a file as currently being worked on"""
        self.project_context.working_files.add(Path(file_path))
        self._save_context()

    def clear_old_context(self, days: int = 7):
        """Clear context older than specified days"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        # Filter conversation history
        self.conversation_history = [
            entry for entry in self.conversation_history if entry.timestamp > cutoff_time
        ]

        # Clear old operations
        self.project_context.recent_operations = [
            op
            for op in self.project_context.recent_operations
            if op.get("timestamp", 0) > cutoff_time
        ]

        self._save_context()
        print(f"✅ Cleared context older than {days} days")

    def get_statistics(self) -> Dict[str, Any]:
        """Get context statistics"""
        return {
            "conversation_entries": len(self.conversation_history),
            "working_files": len(self.project_context.working_files),
            "recent_operations": len(self.project_context.recent_operations),
            "session_duration": time.time() - self.session_start_time,
            "last_activity": time.time() - self.last_activity,
        }

    def export_context(self, export_file: Path):
        """Export context to a file"""
        data = {
            "conversation_history": [entry.to_dict() for entry in self.conversation_history],
            "project_context": self.project_context.to_dict(),
            "export_time": time.time(),
        }

        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Context exported to {export_file}")

    def import_context(self, import_file: Path):
        """Import context from a file"""
        with open(import_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Import conversation history
        self.conversation_history = [
            ConversationEntry.from_dict(entry) for entry in data.get("conversation_history", [])
        ]

        # Import project context
        if "project_context" in data:
            self.project_context = ProjectContext.from_dict(data["project_context"])

        self._save_context()
        print(f"✅ Context imported from {import_file}")
