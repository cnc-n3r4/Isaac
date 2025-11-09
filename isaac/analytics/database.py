"""
Analytics Database

Stores all analytics data with efficient querying capabilities.
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager


class AnalyticsDatabase:
    """Database for storing analytics data"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize analytics database"""
        if db_path is None:
            isaac_dir = os.path.expanduser("~/.isaac")
            os.makedirs(isaac_dir, exist_ok=True)
            db_path = os.path.join(isaac_dir, "analytics.db")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            # Productivity metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS productivity_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    metric_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metadata TEXT
                )
            """)

            # Code quality metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS code_quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    file_path TEXT,
                    metric_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    before_value REAL,
                    after_value REAL,
                    metadata TEXT
                )
            """)

            # Learning analytics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    learning_type TEXT NOT NULL,
                    learning_item TEXT NOT NULL,
                    confidence REAL,
                    usage_count INTEGER DEFAULT 0,
                    success_rate REAL,
                    metadata TEXT
                )
            """)

            # Team analytics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS team_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    team_id TEXT,
                    user_id TEXT,
                    activity_type TEXT NOT NULL,
                    activity_name TEXT NOT NULL,
                    activity_value REAL,
                    metadata TEXT
                )
            """)

            # Command execution analytics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS command_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    command_name TEXT NOT NULL,
                    execution_time REAL NOT NULL,
                    success INTEGER NOT NULL,
                    error_message TEXT,
                    metadata TEXT
                )
            """)

            # Custom metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    metric_category TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    tags TEXT,
                    metadata TEXT
                )
            """)

            # Create indexes for efficient querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_productivity_timestamp
                ON productivity_metrics(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_code_quality_timestamp
                ON code_quality_metrics(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_learning_timestamp
                ON learning_analytics(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_team_timestamp
                ON team_analytics(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_command_timestamp
                ON command_analytics(timestamp)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def record_productivity_metric(
        self,
        metric_type: str,
        metric_name: str,
        metric_value: float,
        session_id: Optional[str] = None,
        metadata: Optional[str] = None
    ):
        """Record a productivity metric"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO productivity_metrics
                (timestamp, session_id, metric_type, metric_name, metric_value, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                session_id,
                metric_type,
                metric_name,
                metric_value,
                metadata
            ))
            conn.commit()

    def record_code_quality_metric(
        self,
        metric_type: str,
        metric_name: str,
        metric_value: float,
        file_path: Optional[str] = None,
        before_value: Optional[float] = None,
        after_value: Optional[float] = None,
        session_id: Optional[str] = None,
        metadata: Optional[str] = None
    ):
        """Record a code quality metric"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO code_quality_metrics
                (timestamp, session_id, file_path, metric_type, metric_name,
                 metric_value, before_value, after_value, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                session_id,
                file_path,
                metric_type,
                metric_name,
                metric_value,
                before_value,
                after_value,
                metadata
            ))
            conn.commit()

    def record_learning_metric(
        self,
        learning_type: str,
        learning_item: str,
        confidence: float,
        usage_count: int = 0,
        success_rate: Optional[float] = None,
        session_id: Optional[str] = None,
        metadata: Optional[str] = None
    ):
        """Record a learning analytics metric"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO learning_analytics
                (timestamp, session_id, learning_type, learning_item,
                 confidence, usage_count, success_rate, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                session_id,
                learning_type,
                learning_item,
                confidence,
                usage_count,
                success_rate,
                metadata
            ))
            conn.commit()

    def record_team_activity(
        self,
        activity_type: str,
        activity_name: str,
        activity_value: float,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[str] = None
    ):
        """Record a team analytics activity"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO team_analytics
                (timestamp, team_id, user_id, activity_type, activity_name,
                 activity_value, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                team_id,
                user_id,
                activity_type,
                activity_name,
                activity_value,
                metadata
            ))
            conn.commit()

    def record_command_execution(
        self,
        command_name: str,
        execution_time: float,
        success: bool,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[str] = None
    ):
        """Record command execution analytics"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO command_analytics
                (timestamp, session_id, command_name, execution_time,
                 success, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                session_id,
                command_name,
                execution_time,
                1 if success else 0,
                error_message,
                metadata
            ))
            conn.commit()

    def record_custom_metric(
        self,
        metric_category: str,
        metric_name: str,
        metric_value: float,
        tags: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[str] = None
    ):
        """Record a custom metric"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO custom_metrics
                (timestamp, session_id, metric_category, metric_name,
                 metric_value, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                session_id,
                metric_category,
                metric_name,
                metric_value,
                tags,
                metadata
            ))
            conn.commit()

    def query_metrics(
        self,
        table: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query metrics with optional filters"""
        query = f"SELECT * FROM {table} WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        if filters:
            for key, value in filters.items():
                query += f" AND {key} = ?"
                params.append(value)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_aggregate_stats(
        self,
        table: str,
        metric_column: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregate statistics for a metric"""
        query = f"""
            SELECT
                COUNT(*) as count,
                AVG({metric_column}) as avg,
                MIN({metric_column}) as min,
                MAX({metric_column}) as max,
                SUM({metric_column}) as sum
        """

        if group_by:
            query += f", {group_by}"

        query += f" FROM {table} WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        if group_by:
            query += f" GROUP BY {group_by}"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            if group_by:
                return [dict(row) for row in cursor.fetchall()]
            else:
                row = cursor.fetchone()
                return dict(row) if row else {}

    def clear_old_data(self, days: int = 90):
        """Clear analytics data older than specified days"""
        cutoff = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        cutoff = cutoff.replace(day=cutoff.day - days)
        cutoff_str = cutoff.isoformat()

        tables = [
            'productivity_metrics',
            'code_quality_metrics',
            'learning_analytics',
            'team_analytics',
            'command_analytics',
            'custom_metrics'
        ]

        with self._get_connection() as conn:
            for table in tables:
                conn.execute(
                    f"DELETE FROM {table} WHERE timestamp < ?",
                    (cutoff_str,)
                )
            conn.commit()
