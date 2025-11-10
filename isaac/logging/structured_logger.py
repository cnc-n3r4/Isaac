"""
Structured Logger - Collection-based JSONL logging for Isaac's self-awareness

This module provides structured logging to JSONL files organized by collection.
Isaac uses this to track its learning, patterns, and evolution over time.
"""

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class LogEvent:
    """Represents a structured log event."""

    timestamp: str  # ISO 8601 format
    event_type: str  # e.g., 'pattern_learned', 'suggestion_generated', 'warning'
    collection: str  # e.g., 'log-learning', 'log-suggestions'
    data: Dict[str, Any]  # Event-specific data
    metadata: Optional[Dict[str, Any]] = None  # Optional metadata

    def to_json(self) -> str:
        """Convert to JSON string for JSONL storage."""
        return json.dumps(asdict(self), default=str)


class StructuredLogger:
    """
    Collection-based JSONL logger for Isaac's self-awareness.

    Logs are organized by collection and stored in monthly files:
    ~/.isaac/logs/[collection-name]/YYYY-MM.jsonl

    Example usage:
        logger = StructuredLogger()
        logger.log_pattern_learned(
            pattern_id="pattern_123",
            pattern_type="command_error",
            confidence=0.85
        )
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize structured logger.

        Args:
            base_dir: Base directory for logs (defaults to ~/.isaac/logs)
        """
        self.base_dir = base_dir or (Path.home() / ".isaac" / "logs")
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Thread safety for concurrent logging
        self._lock = threading.Lock()

        # Cache for file handles (avoid reopening constantly)
        self._file_handles: Dict[str, Any] = {}

    def _get_log_file_path(self, collection: str) -> Path:
        """
        Get the current log file path for a collection.

        Args:
            collection: Collection name (e.g., 'log-learning')

        Returns:
            Path to the current month's log file
        """
        # Organize by month: YYYY-MM.jsonl
        current_month = datetime.now().strftime("%Y-%m")
        collection_dir = self.base_dir / collection
        collection_dir.mkdir(parents=True, exist_ok=True)
        return collection_dir / f"{current_month}.jsonl"

    def log_event(
        self,
        event_type: str,
        collection: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a structured event to a collection.

        Args:
            event_type: Type of event (e.g., 'pattern_learned')
            collection: Collection name (e.g., 'log-learning')
            data: Event-specific data
            metadata: Optional metadata
        """
        event = LogEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            collection=collection,
            data=data,
            metadata=metadata or {}
        )

        log_file = self._get_log_file_path(collection)

        try:
            with self._lock:
                with open(log_file, "a") as f:
                    f.write(event.to_json() + "\n")
        except Exception as e:
            # Fallback to print if logging fails (avoid infinite loops)
            print(f"[StructuredLogger] Failed to log event: {e}")

    # ===== Learning & Pattern Events =====

    def log_pattern_learned(
        self,
        pattern_id: str,
        pattern_type: str,
        description: str,
        confidence: float,
        trigger_conditions: Optional[Dict[str, Any]] = None,
        correction_action: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log a newly learned pattern.

        Args:
            pattern_id: Unique pattern identifier
            pattern_type: Type of pattern (e.g., 'command_error')
            description: Human-readable description
            confidence: Confidence score (0-1)
            trigger_conditions: Conditions that trigger this pattern
            correction_action: Suggested correction action
            **kwargs: Additional pattern-specific data
        """
        self.log_event(
            event_type="pattern_learned",
            collection="log-learning",
            data={
                "pattern_id": pattern_id,
                "pattern_type": pattern_type,
                "description": description,
                "confidence": confidence,
                "trigger_conditions": trigger_conditions or {},
                "correction_action": correction_action,
                **kwargs
            }
        )

    def log_suggestion_generated(
        self,
        suggestion_id: str,
        suggestion_type: str,
        title: str,
        description: str,
        confidence: float,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Log a proactive suggestion generation.

        Args:
            suggestion_id: Unique suggestion identifier
            suggestion_type: Type of suggestion
            title: Suggestion title
            description: Suggestion description
            confidence: Confidence score
            context: Context that triggered the suggestion
            **kwargs: Additional data
        """
        self.log_event(
            event_type="suggestion_generated",
            collection="log-suggestions",
            data={
                "suggestion_id": suggestion_id,
                "suggestion_type": suggestion_type,
                "title": title,
                "description": description,
                "confidence": confidence,
                "context": context or {},
                **kwargs
            }
        )

    def log_suggestion_accepted(
        self,
        suggestion_id: str,
        action_taken: str,
        **kwargs
    ) -> None:
        """Log when a user accepts/acts on a suggestion."""
        self.log_event(
            event_type="suggestion_accepted",
            collection="log-suggestions",
            data={
                "suggestion_id": suggestion_id,
                "action_taken": action_taken,
                **kwargs
            }
        )

    def log_warning(
        self,
        warning_type: str,
        message: str,
        source: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Log a warning event.

        Args:
            warning_type: Type of warning
            message: Warning message
            source: Source of the warning (file, module, etc.)
            details: Additional details
            **kwargs: Additional data
        """
        self.log_event(
            event_type="warning",
            collection="log-warnings",
            data={
                "warning_type": warning_type,
                "message": message,
                "source": source,
                "details": details or {},
                **kwargs
            }
        )

    def log_error(
        self,
        error_type: str,
        message: str,
        source: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log an error event."""
        self.log_event(
            event_type="error",
            collection="log-warnings",
            data={
                "error_type": error_type,
                "message": message,
                "source": source,
                "details": details or {},
                **kwargs
            }
        )

    def log_mistake_recorded(
        self,
        mistake_id: str,
        mistake_type: str,
        description: str,
        correction: str,
        severity: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Log a recorded mistake for learning.

        Args:
            mistake_id: Unique mistake identifier
            mistake_type: Type of mistake
            description: Description of the mistake
            correction: User's correction
            severity: Severity level
            context: Context of the mistake
            **kwargs: Additional data
        """
        self.log_event(
            event_type="mistake_recorded",
            collection="log-learning",
            data={
                "mistake_id": mistake_id,
                "mistake_type": mistake_type,
                "description": description,
                "correction": correction,
                "severity": severity,
                "context": context or {},
                **kwargs
            }
        )

    def log_workflow_detected(
        self,
        workflow_id: str,
        commands: List[str],
        frequency: int,
        confidence: float,
        **kwargs
    ) -> None:
        """Log a detected workflow pattern."""
        self.log_event(
            event_type="workflow_detected",
            collection="log-learning",
            data={
                "workflow_id": workflow_id,
                "commands": commands,
                "frequency": frequency,
                "confidence": confidence,
                **kwargs
            }
        )

    # ===== Query Methods =====

    def query_collection(
        self,
        collection: str,
        event_type: Optional[str] = None,
        limit: Optional[int] = None,
        since: Optional[datetime] = None
    ) -> List[LogEvent]:
        """
        Query events from a collection.

        Args:
            collection: Collection name
            event_type: Filter by event type
            limit: Maximum number of events to return
            since: Only return events after this timestamp

        Returns:
            List of LogEvent objects
        """
        events = []
        collection_dir = self.base_dir / collection

        if not collection_dir.exists():
            return events

        # Read all JSONL files in the collection (sorted by date)
        log_files = sorted(collection_dir.glob("*.jsonl"), reverse=True)

        for log_file in log_files:
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        if not line.strip():
                            continue

                        try:
                            event_dict = json.loads(line)
                            event = LogEvent(**event_dict)

                            # Apply filters
                            if event_type and event.event_type != event_type:
                                continue

                            if since:
                                event_time = datetime.fromisoformat(event.timestamp)
                                if event_time < since:
                                    continue

                            events.append(event)

                            # Check limit
                            if limit and len(events) >= limit:
                                return events

                        except (json.JSONDecodeError, TypeError) as e:
                            # Skip malformed lines
                            continue

            except Exception as e:
                print(f"[StructuredLogger] Error reading {log_file}: {e}")
                continue

        return events

    def get_recent_patterns(self, limit: int = 10) -> List[LogEvent]:
        """Get recently learned patterns."""
        return self.query_collection(
            collection="log-learning",
            event_type="pattern_learned",
            limit=limit
        )

    def get_recent_suggestions(self, limit: int = 10) -> List[LogEvent]:
        """Get recently generated suggestions."""
        return self.query_collection(
            collection="log-suggestions",
            event_type="suggestion_generated",
            limit=limit
        )

    def get_recent_warnings(self, limit: int = 10) -> List[LogEvent]:
        """Get recent warnings."""
        return self.query_collection(
            collection="log-warnings",
            limit=limit
        )

    def get_learning_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get a summary of learning activity.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with learning statistics
        """
        since = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        since = since.replace(day=since.day - days)

        patterns = self.query_collection(
            collection="log-learning",
            event_type="pattern_learned",
            since=since
        )

        suggestions = self.query_collection(
            collection="log-suggestions",
            event_type="suggestion_generated",
            since=since
        )

        mistakes = self.query_collection(
            collection="log-learning",
            event_type="mistake_recorded",
            since=since
        )

        return {
            "period_days": days,
            "patterns_learned": len(patterns),
            "suggestions_generated": len(suggestions),
            "mistakes_recorded": len(mistakes),
            "pattern_types": self._count_by_field(patterns, "data.pattern_type"),
            "suggestion_types": self._count_by_field(suggestions, "data.suggestion_type"),
            "avg_pattern_confidence": self._avg_field(patterns, "data.confidence"),
            "avg_suggestion_confidence": self._avg_field(suggestions, "data.confidence"),
        }

    def _count_by_field(self, events: List[LogEvent], field_path: str) -> Dict[str, int]:
        """Count events by a nested field."""
        counts = {}
        for event in events:
            value = self._get_nested_field(event, field_path)
            if value:
                counts[str(value)] = counts.get(str(value), 0) + 1
        return counts

    def _avg_field(self, events: List[LogEvent], field_path: str) -> Optional[float]:
        """Calculate average of a numeric field."""
        values = []
        for event in events:
            value = self._get_nested_field(event, field_path)
            if value is not None and isinstance(value, (int, float)):
                values.append(float(value))

        return sum(values) / len(values) if values else None

    def _get_nested_field(self, event: LogEvent, field_path: str) -> Any:
        """Get a nested field from an event (e.g., 'data.pattern_type')."""
        parts = field_path.split(".")
        obj = event

        for part in parts:
            if isinstance(obj, LogEvent):
                obj = getattr(obj, part, None)
            elif isinstance(obj, dict):
                obj = obj.get(part)
            else:
                return None

            if obj is None:
                return None

        return obj


# Global instance for convenience
_global_logger: Optional[StructuredLogger] = None


def get_logger() -> StructuredLogger:
    """Get the global structured logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger()
    return _global_logger
