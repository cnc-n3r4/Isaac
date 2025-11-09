"""
Debug History - Remember past debugging sessions and solutions
Isaac's intelligent debug history system for learning from past experiences
"""

import json
import sqlite3
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib


@dataclass
class DebugSession:
    """Represents a debugging session."""
    session_id: str
    timestamp: float
    command: str
    error_message: str
    root_cause: str
    solution: str
    resolution_time: float  # seconds
    success: bool
    context: Dict[str, Any]
    tags: List[str]


@dataclass
class DebugPattern:
    """Represents a learned debugging pattern."""
    pattern_id: str
    error_pattern: str
    root_cause_pattern: str
    solution_template: str
    confidence: float
    occurrences: int
    last_seen: float
    tags: List[str]


@dataclass
class DebugInsight:
    """Represents an insight from debug history."""
    insight_id: str
    insight_type: str  # 'pattern', 'trend', 'correlation'
    description: str
    data: Dict[str, Any]
    confidence: float
    timestamp: float


class DebugHistoryManager:
    """Manages debug history and learns from past debugging sessions."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the debug history manager.

        Args:
            db_path: Path to the debug history database
        """
        if db_path is None:
            db_path = Path.home() / '.isaac' / 'debug_history.db'

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_database()

        # In-memory cache for patterns
        self.pattern_cache = {}
        self._load_patterns_cache()

    def _init_database(self):
        """Initialize the SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS debug_sessions (
                    session_id TEXT PRIMARY KEY,
                    timestamp REAL,
                    command TEXT,
                    error_message TEXT,
                    root_cause TEXT,
                    solution TEXT,
                    resolution_time REAL,
                    success INTEGER,
                    context TEXT,
                    tags TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS debug_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    error_pattern TEXT,
                    root_cause_pattern TEXT,
                    solution_template TEXT,
                    confidence REAL,
                    occurrences INTEGER,
                    last_seen REAL,
                    tags TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS debug_insights (
                    insight_id TEXT PRIMARY KEY,
                    insight_type TEXT,
                    description TEXT,
                    data TEXT,
                    confidence REAL,
                    timestamp REAL
                )
            ''')

            # Create indexes for better query performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_timestamp ON debug_sessions(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_command ON debug_sessions(command)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_patterns_error ON debug_patterns(error_pattern)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_insights_type ON debug_insights(insight_type)')

    def _load_patterns_cache(self):
        """Load debug patterns into memory cache."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT * FROM debug_patterns')
            for row in cursor.fetchall():
                pattern = DebugPattern(
                    pattern_id=row[0],
                    error_pattern=row[1],
                    root_cause_pattern=row[2],
                    solution_template=row[3],
                    confidence=row[4],
                    occurrences=row[5],
                    last_seen=row[6],
                    tags=json.loads(row[7]) if row[7] else []
                )
                self.pattern_cache[pattern.pattern_id] = pattern

    def record_debug_session(self, session: DebugSession):
        """Record a debugging session.

        Args:
            session: The debug session to record
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO debug_sessions
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id,
                session.timestamp,
                session.command,
                session.error_message,
                session.root_cause,
                session.solution,
                session.resolution_time,
                1 if session.success else 0,
                json.dumps(session.context),
                json.dumps(session.tags)
            ))

        # Update patterns based on this session
        self._update_patterns_from_session(session)

        # Generate insights if applicable
        self._generate_insights_from_session(session)

    def find_similar_issues(self, error_message: str, command: str = None,
                          limit: int = 5) -> List[DebugSession]:
        """Find similar past debugging issues.

        Args:
            error_message: Current error message
            command: Command that failed (optional)
            limit: Maximum number of results

        Returns:
            List of similar debug sessions
        """
        similar_sessions = []

        # Search by exact error message first
        with sqlite3.connect(self.db_path) as conn:
            if command:
                cursor = conn.execute('''
                    SELECT * FROM debug_sessions
                    WHERE error_message = ? AND command = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (error_message, command, limit))
            else:
                cursor = conn.execute('''
                    SELECT * FROM debug_sessions
                    WHERE error_message = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (error_message, limit))

            for row in cursor.fetchall():
                session = self._row_to_session(row)
                similar_sessions.append(session)

        # If no exact matches, search by pattern
        if not similar_sessions:
            error_keywords = self._extract_keywords(error_message)
            pattern_query = ' OR '.join(['error_message LIKE ?'] * len(error_keywords))
            params = [f'%{keyword}%' for keyword in error_keywords]

            if command:
                params.extend([command, limit])
                query = f'''
                    SELECT * FROM debug_sessions
                    WHERE ({pattern_query}) AND command = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                '''
            else:
                params.append(limit)
                query = f'''
                    SELECT * FROM debug_sessions
                    WHERE {pattern_query}
                    ORDER BY timestamp DESC
                    LIMIT ?
                '''

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                for row in cursor.fetchall():
                    session = self._row_to_session(row)
                    similar_sessions.append(session)

        return similar_sessions[:limit]

    def get_solution_suggestions(self, error_message: str, command: str = None) -> List[Dict[str, Any]]:
        """Get solution suggestions based on debug history.

        Args:
            error_message: Current error message
            command: Command that failed (optional)

        Returns:
            List of solution suggestions with confidence scores
        """
        suggestions = []

        # Find similar past sessions
        similar_sessions = self.find_similar_issues(error_message, command, limit=10)

        # Extract successful solutions
        successful_solutions = {}
        for session in similar_sessions:
            if session.success and session.solution:
                solution_key = session.solution.lower().strip()
                if solution_key not in successful_solutions:
                    successful_solutions[solution_key] = {
                        'solution': session.solution,
                        'count': 0,
                        'avg_resolution_time': 0,
                        'sessions': []
                    }
                successful_solutions[solution_key]['count'] += 1
                successful_solutions[solution_key]['avg_resolution_time'] += session.resolution_time
                successful_solutions[solution_key]['sessions'].append(session)

        # Calculate confidence and format suggestions
        for solution_data in successful_solutions.values():
            count = solution_data['count']
            avg_time = solution_data['avg_resolution_time'] / count if count > 0 else 0

            # Calculate confidence based on success rate and recency
            confidence = min(count / 5.0, 1.0)  # Max confidence at 5 occurrences

            # Boost confidence for recent solutions
            recent_sessions = [s for s in solution_data['sessions']
                             if s.timestamp > time.time() - 30 * 24 * 3600]  # Last 30 days
            if recent_sessions:
                confidence *= 1.2

            suggestions.append({
                'solution': solution_data['solution'],
                'confidence': confidence,
                'occurrences': count,
                'avg_resolution_time': avg_time,
                'recent_success': len(recent_sessions) > 0
            })

        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)

        return suggestions

    def get_debugging_insights(self, days: int = 30) -> List[DebugInsight]:
        """Get insights from debug history.

        Args:
            days: Number of days to look back

        Returns:
            List of debugging insights
        """
        insights = []
        cutoff_time = time.time() - (days * 24 * 3600)

        with sqlite3.connect(self.db_path) as conn:
            # Common error patterns
            cursor = conn.execute('''
                SELECT error_message, COUNT(*) as count
                FROM debug_sessions
                WHERE timestamp > ?
                GROUP BY error_message
                HAVING count > 1
                ORDER BY count DESC
                LIMIT 10
            ''', (cutoff_time,))

            for row in cursor.fetchall():
                error_message, count = row
                insights.append(DebugInsight(
                    insight_id=f"pattern_{hashlib.md5(error_message.encode()).hexdigest()[:8]}",
                    insight_type="pattern",
                    description=f"Common error pattern: '{error_message[:50]}...' occurs {count} times",
                    data={'error_message': error_message, 'occurrences': count},
                    confidence=min(count / 10.0, 1.0),
                    timestamp=time.time()
                ))

            # Command failure trends
            cursor = conn.execute('''
                SELECT command, COUNT(*) as total, SUM(success) as successful
                FROM debug_sessions
                WHERE timestamp > ?
                GROUP BY command
                HAVING total > 2
                ORDER BY (total - successful) DESC
                LIMIT 5
            ''', (cutoff_time,))

            for row in cursor.fetchall():
                command, total, successful = row
                failure_rate = (total - successful) / total
                if failure_rate > 0.5:
                    insights.append(DebugInsight(
                        insight_id=f"trend_{hashlib.md5(command.encode()).hexdigest()[:8]}",
                        insight_type="trend",
                        description=f"High failure rate for '{command}': {failure_rate:.1%} failure rate",
                        data={'command': command, 'failure_rate': failure_rate, 'total_attempts': total},
                        confidence=min(failure_rate, 1.0),
                        timestamp=time.time()
                    ))

        return insights

    def get_command_debugging_stats(self, command: str, days: int = 30) -> Dict[str, Any]:
        """Get debugging statistics for a specific command.

        Args:
            command: The command to analyze
            days: Number of days to look back

        Returns:
            Statistics about command debugging
        """
        cutoff_time = time.time() - (days * 24 * 3600)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT COUNT(*), AVG(resolution_time), SUM(success), AVG(timestamp)
                FROM debug_sessions
                WHERE command = ? AND timestamp > ?
            ''', (command, cutoff_time))

            row = cursor.fetchone()
            if row:
                total_sessions, avg_resolution_time, successful_sessions, avg_timestamp = row
                success_rate = successful_sessions / total_sessions if total_sessions > 0 else 0

                return {
                    'command': command,
                    'total_debug_sessions': total_sessions,
                    'success_rate': success_rate,
                    'avg_resolution_time': avg_resolution_time or 0,
                    'last_debugged': avg_timestamp or 0,
                    'days_analyzed': days
                }

        return {
            'command': command,
            'total_debug_sessions': 0,
            'success_rate': 0,
            'avg_resolution_time': 0,
            'last_debugged': 0,
            'days_analyzed': days
        }

    def export_debug_history(self, output_path: Path, format: str = 'json') -> bool:
        """Export debug history to a file.

        Args:
            output_path: Path to export to
            format: Export format ('json' or 'csv')

        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if format == 'json':
                    # Export sessions
                    cursor = conn.execute('SELECT * FROM debug_sessions')
                    sessions = []
                    for row in cursor.fetchall():
                        session = self._row_to_session(row)
                        sessions.append(asdict(session))

                    # Export patterns
                    cursor = conn.execute('SELECT * FROM debug_patterns')
                    patterns = []
                    for row in cursor.fetchall():
                        pattern = DebugPattern(
                            pattern_id=row[0],
                            error_pattern=row[1],
                            root_cause_pattern=row[2],
                            solution_template=row[3],
                            confidence=row[4],
                            occurrences=row[5],
                            last_seen=row[6],
                            tags=json.loads(row[7]) if row[7] else []
                        )
                        patterns.append(asdict(pattern))

                    export_data = {
                        'sessions': sessions,
                        'patterns': patterns,
                        'export_timestamp': time.time()
                    }

                    with open(output_path, 'w') as f:
                        json.dump(export_data, f, indent=2)

                elif format == 'csv':
                    # Export sessions as CSV
                    cursor = conn.execute('SELECT * FROM debug_sessions')
                    with open(output_path, 'w') as f:
                        f.write('session_id,timestamp,command,error_message,root_cause,solution,resolution_time,success,tags\n')
                        for row in cursor.fetchall():
                            # Escape commas and quotes in text fields
                            escaped_row = []
                            for field in row:
                                if isinstance(field, str):
                                    field = field.replace('"', '""')
                                    field = f'"{field}"'
                                escaped_row.append(str(field))
                            f.write(','.join(escaped_row) + '\n')

            return True

        except Exception as e:
            print(f"Error exporting debug history: {e}")
            return False

    def import_debug_history(self, input_path: Path) -> bool:
        """Import debug history from a file.

        Args:
            input_path: Path to import from

        Returns:
            True if successful
        """
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)

            with sqlite3.connect(self.db_path) as conn:
                # Import sessions
                for session_data in data.get('sessions', []):
                    session = DebugSession(**session_data)
                    self.record_debug_session(session)

            # Reload patterns cache
            self._load_patterns_cache()

            return True

        except Exception as e:
            print(f"Error importing debug history: {e}")
            return False

    def cleanup_old_history(self, days_to_keep: int = 365) -> int:
        """Clean up old debug history.

        Args:
            days_to_keep: Number of days of history to keep

        Returns:
            Number of records deleted
        """
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('DELETE FROM debug_sessions WHERE timestamp < ?', (cutoff_time,))
            deleted_count = cursor.rowcount

            # Also cleanup old insights
            cursor = conn.execute('DELETE FROM debug_insights WHERE timestamp < ?', (cutoff_time,))
            deleted_count += cursor.rowcount

            conn.commit()

        return deleted_count

    def _row_to_session(self, row) -> DebugSession:
        """Convert database row to DebugSession object."""
        return DebugSession(
            session_id=row[0],
            timestamp=row[1],
            command=row[2],
            error_message=row[3],
            root_cause=row[4],
            solution=row[5],
            resolution_time=row[6],
            success=bool(row[7]),
            context=json.loads(row[8]) if row[8] else {},
            tags=json.loads(row[9]) if row[9] else []
        )

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from error message for pattern matching."""
        # Simple keyword extraction - split on common separators and filter
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common stop words and short words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return list(set(keywords))[:10]  # Return up to 10 unique keywords

    def _update_patterns_from_session(self, session: DebugSession):
        """Update debug patterns based on a new session."""
        if not session.success:
            return

        # Create pattern key from error and root cause
        pattern_key = f"{session.error_message}|{session.root_cause}"

        # Check if pattern exists
        existing_pattern = None
        for pattern in self.pattern_cache.values():
            if pattern.error_pattern == session.error_message and pattern.root_cause_pattern == session.root_cause:
                existing_pattern = pattern
                break

        if existing_pattern:
            # Update existing pattern
            existing_pattern.occurrences += 1
            existing_pattern.last_seen = session.timestamp
            existing_pattern.confidence = min(existing_pattern.confidence + 0.1, 1.0)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE debug_patterns
                    SET occurrences = ?, last_seen = ?, confidence = ?
                    WHERE pattern_id = ?
                ''', (existing_pattern.occurrences, existing_pattern.last_seen,
                      existing_pattern.confidence, existing_pattern.pattern_id))

        else:
            # Create new pattern
            pattern_id = f"pattern_{hashlib.md5(pattern_key.encode()).hexdigest()[:8]}"
            new_pattern = DebugPattern(
                pattern_id=pattern_id,
                error_pattern=session.error_message,
                root_cause_pattern=session.root_cause,
                solution_template=session.solution,
                confidence=0.5,  # Start with moderate confidence
                occurrences=1,
                last_seen=session.timestamp,
                tags=session.tags
            )

            self.pattern_cache[pattern_id] = new_pattern

            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO debug_patterns
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    new_pattern.pattern_id,
                    new_pattern.error_pattern,
                    new_pattern.root_cause_pattern,
                    new_pattern.solution_template,
                    new_pattern.confidence,
                    new_pattern.occurrences,
                    new_pattern.last_seen,
                    json.dumps(new_pattern.tags)
                ))

    def _generate_insights_from_session(self, session: DebugSession):
        """Generate insights from a debug session."""
        # This could be expanded to detect trends, correlations, etc.
        # For now, just record the insight if it's a repeated error
        similar_count = len(self.find_similar_issues(session.error_message, session.command, limit=100))

        if similar_count > 3:
            insight = DebugInsight(
                insight_id=f"recurring_{hashlib.md5(session.error_message.encode()).hexdigest()[:8]}",
                insight_type="correlation",
                description=f"Recurring error pattern detected: '{session.error_message[:50]}...' has occurred {similar_count} times",
                data={
                    'error_message': session.error_message,
                    'occurrences': similar_count,
                    'command': session.command
                },
                confidence=min(similar_count / 10.0, 1.0),
                timestamp=time.time()
            )

            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO debug_insights
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    insight.insight_id,
                    insight.insight_type,
                    insight.description,
                    json.dumps(insight.data),
                    insight.confidence,
                    insight.timestamp
                ))