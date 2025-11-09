"""
Pair Programming Metrics - Phase 4.2
Track and analyze pair programming effectiveness.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

from isaac.core.session_manager import SessionManager


@dataclass
class PairingMetrics:
    """Metrics for a pairing session."""
    session_id: str
    duration_seconds: float
    tasks_completed: int
    tasks_total: int
    suggestions_made: int
    suggestions_accepted: int
    code_reviews_performed: int
    files_modified: int
    lines_added: int
    lines_removed: int
    role_switches: int
    productivity_score: float  # 0-100
    collaboration_score: float  # 0-100
    code_quality_score: float  # 0-100
    learning_score: float  # 0-100
    overall_score: float  # 0-100
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PairMetrics:
    """Track and analyze pair programming metrics."""

    def __init__(self, session_manager: SessionManager):
        """Initialize pair metrics.

        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
        self.data_dir = Path.home() / '.isaac' / 'pairing'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Database for metrics storage
        self.db_path = self.data_dir / 'metrics.db'
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for metrics storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS session_metrics (
                    session_id TEXT PRIMARY KEY,
                    duration_seconds REAL,
                    tasks_completed INTEGER,
                    tasks_total INTEGER,
                    suggestions_made INTEGER,
                    suggestions_accepted INTEGER,
                    code_reviews_performed INTEGER,
                    files_modified INTEGER,
                    lines_added INTEGER,
                    lines_removed INTEGER,
                    role_switches INTEGER,
                    productivity_score REAL,
                    collaboration_score REAL,
                    code_quality_score REAL,
                    learning_score REAL,
                    overall_score REAL,
                    metadata TEXT
                )
            ''')

            # Track individual events for detailed analysis
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metric_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp REAL,
                    event_type TEXT,
                    event_data TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_session_events ON metric_events(session_id)')

    def record_event(
        self,
        session_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """Record a metric event.

        Args:
            session_id: Session ID
            event_type: Type of event
            event_data: Event data
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO metric_events (session_id, timestamp, event_type, event_data)
                VALUES (?, ?, ?, ?)
            ''', (
                session_id,
                datetime.now().timestamp(),
                event_type,
                json.dumps(event_data)
            ))

    def calculate_session_metrics(
        self,
        session_id: str,
        session_data: Dict[str, Any]
    ) -> PairingMetrics:
        """Calculate comprehensive metrics for a session.

        Args:
            session_id: Session ID
            session_data: Session data

        Returns:
            Calculated metrics
        """
        # Get all events for this session
        events = self._get_session_events(session_id)

        # Count event types
        event_counts = defaultdict(int)
        for event in events:
            event_counts[event['event_type']] += 1

        # Calculate basic metrics
        duration = session_data.get('end_time', datetime.now().timestamp()) - session_data.get('start_time', 0)
        tasks_completed = event_counts.get('task_completed', 0)
        tasks_total = session_data.get('tasks_total', 0)
        suggestions_made = event_counts.get('suggestion_made', 0)
        suggestions_accepted = event_counts.get('suggestion_accepted', 0)
        code_reviews = event_counts.get('code_review', 0)
        files_modified = len(session_data.get('files_touched', []))
        lines_added = sum(e['event_data'].get('lines_added', 0) for e in events if e['event_type'] == 'code_edit')
        lines_removed = sum(e['event_data'].get('lines_removed', 0) for e in events if e['event_type'] == 'code_edit')
        role_switches = event_counts.get('role_switch', 0)

        # Calculate scores
        productivity_score = self._calculate_productivity_score(
            duration, tasks_completed, tasks_total, files_modified
        )

        collaboration_score = self._calculate_collaboration_score(
            role_switches, suggestions_made, suggestions_accepted, code_reviews
        )

        code_quality_score = self._calculate_code_quality_score(
            code_reviews, suggestions_made, events
        )

        learning_score = self._calculate_learning_score(
            suggestions_accepted, event_counts, duration
        )

        overall_score = (
            productivity_score * 0.3 +
            collaboration_score * 0.25 +
            code_quality_score * 0.25 +
            learning_score * 0.2
        )

        metrics = PairingMetrics(
            session_id=session_id,
            duration_seconds=duration,
            tasks_completed=tasks_completed,
            tasks_total=tasks_total,
            suggestions_made=suggestions_made,
            suggestions_accepted=suggestions_accepted,
            code_reviews_performed=code_reviews,
            files_modified=files_modified,
            lines_added=lines_added,
            lines_removed=lines_removed,
            role_switches=role_switches,
            productivity_score=productivity_score,
            collaboration_score=collaboration_score,
            code_quality_score=code_quality_score,
            learning_score=learning_score,
            overall_score=overall_score
        )

        self._save_metrics(metrics)
        return metrics

    def _calculate_productivity_score(
        self,
        duration: float,
        tasks_completed: int,
        tasks_total: int,
        files_modified: int
    ) -> float:
        """Calculate productivity score.

        Args:
            duration: Session duration in seconds
            tasks_completed: Number of completed tasks
            tasks_total: Total number of tasks
            files_modified: Number of files modified

        Returns:
            Productivity score (0-100)
        """
        if duration == 0 or tasks_total == 0:
            return 0.0

        # Task completion rate
        completion_rate = tasks_completed / tasks_total

        # Tasks per hour
        hours = duration / 3600
        tasks_per_hour = tasks_completed / hours if hours > 0 else 0

        # Files per hour
        files_per_hour = files_modified / hours if hours > 0 else 0

        # Weighted score
        score = (
            completion_rate * 50 +  # 50% weight on completion
            min(tasks_per_hour / 3 * 30, 30) +  # 30% weight on task velocity (max 3/hr)
            min(files_per_hour / 5 * 20, 20)  # 20% weight on file velocity (max 5/hr)
        )

        return min(100.0, score)

    def _calculate_collaboration_score(
        self,
        role_switches: int,
        suggestions_made: int,
        suggestions_accepted: int,
        code_reviews: int
    ) -> float:
        """Calculate collaboration score.

        Args:
            role_switches: Number of role switches
            suggestions_made: Number of suggestions made
            suggestions_accepted: Number of suggestions accepted
            code_reviews: Number of code reviews

        Returns:
            Collaboration score (0-100)
        """
        score = 0.0

        # Role switching (good collaboration has regular switching)
        if role_switches >= 5:
            score += 30
        elif role_switches >= 3:
            score += 20
        elif role_switches >= 1:
            score += 10

        # Suggestion engagement
        if suggestions_made > 0:
            acceptance_rate = suggestions_accepted / suggestions_made
            score += acceptance_rate * 40  # Up to 40 points

        # Code review engagement
        if code_reviews >= 5:
            score += 30
        elif code_reviews >= 3:
            score += 20
        elif code_reviews >= 1:
            score += 10

        return min(100.0, score)

    def _calculate_code_quality_score(
        self,
        code_reviews: int,
        suggestions_made: int,
        events: List[Dict[str, Any]]
    ) -> float:
        """Calculate code quality score.

        Args:
            code_reviews: Number of code reviews
            suggestions_made: Number of suggestions
            events: All session events

        Returns:
            Code quality score (0-100)
        """
        score = 50.0  # Base score

        # Code review engagement
        if code_reviews >= 5:
            score += 20
        elif code_reviews >= 3:
            score += 10

        # Suggestion quality (more suggestions generally means more attention to quality)
        if suggestions_made >= 10:
            score += 20
        elif suggestions_made >= 5:
            score += 10

        # Test-related events
        test_events = sum(1 for e in events if 'test' in e['event_type'].lower())
        if test_events >= 3:
            score += 10

        return min(100.0, score)

    def _calculate_learning_score(
        self,
        suggestions_accepted: int,
        event_counts: Dict[str, int],
        duration: float
    ) -> float:
        """Calculate learning score.

        Args:
            suggestions_accepted: Number of accepted suggestions
            event_counts: Event counts by type
            duration: Session duration

        Returns:
            Learning score (0-100)
        """
        score = 0.0

        # Accepting suggestions shows learning
        if suggestions_accepted >= 10:
            score += 40
        elif suggestions_accepted >= 5:
            score += 25
        elif suggestions_accepted >= 1:
            score += 10

        # Pattern learning events
        pattern_events = event_counts.get('pattern_learned', 0)
        score += min(pattern_events * 10, 30)

        # Preference learning events
        preference_events = event_counts.get('preference_learned', 0)
        score += min(preference_events * 10, 30)

        return min(100.0, score)

    def _get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all events for a session.

        Args:
            session_id: Session ID

        Returns:
            List of events
        """
        events = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT timestamp, event_type, event_data
                FROM metric_events
                WHERE session_id = ?
                ORDER BY timestamp ASC
            ''', (session_id,))

            for row in cursor:
                events.append({
                    'timestamp': row[0],
                    'event_type': row[1],
                    'event_data': json.loads(row[2]) if row[2] else {}
                })

        return events

    def get_metrics(self, session_id: str) -> Optional[PairingMetrics]:
        """Get metrics for a session.

        Args:
            session_id: Session ID

        Returns:
            Metrics or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT session_id, duration_seconds, tasks_completed, tasks_total,
                       suggestions_made, suggestions_accepted, code_reviews_performed,
                       files_modified, lines_added, lines_removed, role_switches,
                       productivity_score, collaboration_score, code_quality_score,
                       learning_score, overall_score, metadata
                FROM session_metrics
                WHERE session_id = ?
            ''', (session_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return PairingMetrics(
                session_id=row[0],
                duration_seconds=row[1],
                tasks_completed=row[2],
                tasks_total=row[3],
                suggestions_made=row[4],
                suggestions_accepted=row[5],
                code_reviews_performed=row[6],
                files_modified=row[7],
                lines_added=row[8],
                lines_removed=row[9],
                role_switches=row[10],
                productivity_score=row[11],
                collaboration_score=row[12],
                code_quality_score=row[13],
                learning_score=row[14],
                overall_score=row[15],
                metadata=json.loads(row[16]) if row[16] else {}
            )

    def get_aggregate_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get aggregate metrics over a period.

        Args:
            days: Number of days to aggregate

        Returns:
            Aggregate metrics
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        with sqlite3.connect(self.db_path) as conn:
            # Get all sessions in period
            cursor = conn.execute('''
                SELECT session_id FROM metric_events
                WHERE timestamp >= ?
                GROUP BY session_id
            ''', (cutoff_time,))

            session_ids = [row[0] for row in cursor]

        if not session_ids:
            return {
                'period_days': days,
                'total_sessions': 0,
                'average_scores': {},
                'totals': {}
            }

        # Get metrics for all sessions
        all_metrics = []
        for session_id in session_ids:
            metrics = self.get_metrics(session_id)
            if metrics:
                all_metrics.append(metrics)

        # Calculate aggregates
        total_sessions = len(all_metrics)

        avg_productivity = sum(m.productivity_score for m in all_metrics) / total_sessions if total_sessions > 0 else 0
        avg_collaboration = sum(m.collaboration_score for m in all_metrics) / total_sessions if total_sessions > 0 else 0
        avg_quality = sum(m.code_quality_score for m in all_metrics) / total_sessions if total_sessions > 0 else 0
        avg_learning = sum(m.learning_score for m in all_metrics) / total_sessions if total_sessions > 0 else 0
        avg_overall = sum(m.overall_score for m in all_metrics) / total_sessions if total_sessions > 0 else 0

        total_tasks = sum(m.tasks_completed for m in all_metrics)
        total_suggestions = sum(m.suggestions_made for m in all_metrics)
        total_reviews = sum(m.code_reviews_performed for m in all_metrics)
        total_duration = sum(m.duration_seconds for m in all_metrics)

        return {
            'period_days': days,
            'total_sessions': total_sessions,
            'average_scores': {
                'productivity': avg_productivity,
                'collaboration': avg_collaboration,
                'code_quality': avg_quality,
                'learning': avg_learning,
                'overall': avg_overall
            },
            'totals': {
                'tasks_completed': total_tasks,
                'suggestions_made': total_suggestions,
                'code_reviews_performed': total_reviews,
                'total_hours': total_duration / 3600
            }
        }

    def _save_metrics(self, metrics: PairingMetrics):
        """Save metrics to database.

        Args:
            metrics: Metrics to save
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO session_metrics
                (session_id, duration_seconds, tasks_completed, tasks_total,
                 suggestions_made, suggestions_accepted, code_reviews_performed,
                 files_modified, lines_added, lines_removed, role_switches,
                 productivity_score, collaboration_score, code_quality_score,
                 learning_score, overall_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.session_id,
                metrics.duration_seconds,
                metrics.tasks_completed,
                metrics.tasks_total,
                metrics.suggestions_made,
                metrics.suggestions_accepted,
                metrics.code_reviews_performed,
                metrics.files_modified,
                metrics.lines_added,
                metrics.lines_removed,
                metrics.role_switches,
                metrics.productivity_score,
                metrics.collaboration_score,
                metrics.code_quality_score,
                metrics.learning_score,
                metrics.overall_score,
                json.dumps(metrics.metadata or {})
            ))
