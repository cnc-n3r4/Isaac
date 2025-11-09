"""
AI Pair Programming Mode - Phase 4.2
Isaac as an active pair programmer, working alongside the developer.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import uuid

from isaac.core.session_manager import SessionManager


class PairRole(Enum):
    """Roles in pair programming."""
    DRIVER = "driver"  # Writing code
    NAVIGATOR = "navigator"  # Reviewing and guiding
    BOTH = "both"  # Collaborative mode


class PairStyle(Enum):
    """Pairing styles."""
    PING_PONG = "ping_pong"  # Switch roles frequently
    DRIVER_NAVIGATOR = "driver_navigator"  # Traditional pairing
    COLLABORATIVE = "collaborative"  # Work together on same task
    ASYNCHRONOUS = "asynchronous"  # Work on different tasks


@dataclass
class PairingSession:
    """A pair programming session."""
    id: str
    start_time: float
    end_time: Optional[float]
    pair_style: str
    current_role: str  # Isaac's current role
    human_role: str  # Human's current role
    task_description: str
    files_touched: List[str]
    context: Dict[str, Any]
    active: bool = True
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PairProgrammingMode:
    """AI Pair Programming Mode - Isaac as active pair programmer."""

    def __init__(self, session_manager: SessionManager):
        """Initialize pair programming mode.

        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
        self.data_dir = Path.home() / '.isaac' / 'pairing'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Database for session storage
        self.db_path = self.data_dir / 'sessions.db'
        self._init_database()

        # Current active session
        self.active_session: Optional[PairingSession] = None

    def _init_database(self):
        """Initialize SQLite database for session storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pairing_sessions (
                    id TEXT PRIMARY KEY,
                    start_time REAL,
                    end_time REAL,
                    pair_style TEXT,
                    current_role TEXT,
                    human_role TEXT,
                    task_description TEXT,
                    files_touched TEXT,
                    context TEXT,
                    active BOOLEAN,
                    metadata TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_start_time ON pairing_sessions(start_time)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_active ON pairing_sessions(active)')

    def start_session(
        self,
        task_description: str,
        pair_style: PairStyle = PairStyle.DRIVER_NAVIGATOR,
        isaac_role: PairRole = PairRole.NAVIGATOR,
        context: Optional[Dict[str, Any]] = None
    ) -> PairingSession:
        """Start a new pairing session.

        Args:
            task_description: What you're working on
            pair_style: Pairing style to use
            isaac_role: Isaac's initial role
            context: Additional context

        Returns:
            Created pairing session
        """
        # End any active session first
        if self.active_session:
            self.end_session(self.active_session.id)

        # Determine human role based on Isaac's role
        human_role = PairRole.DRIVER if isaac_role == PairRole.NAVIGATOR else PairRole.NAVIGATOR
        if isaac_role == PairRole.BOTH:
            human_role = PairRole.BOTH

        session = PairingSession(
            id=str(uuid.uuid4()),
            start_time=datetime.now().timestamp(),
            end_time=None,
            pair_style=pair_style.value,
            current_role=isaac_role.value,
            human_role=human_role.value,
            task_description=task_description,
            files_touched=[],
            context=context or {},
            active=True
        )

        self._save_session(session)
        self.active_session = session

        return session

    def end_session(self, session_id: str) -> bool:
        """End a pairing session.

        Args:
            session_id: Session ID to end

        Returns:
            True if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE pairing_sessions
                SET end_time = ?, active = 0
                WHERE id = ?
            ''', (datetime.now().timestamp(), session_id))

        if self.active_session and self.active_session.id == session_id:
            self.active_session.active = False
            self.active_session.end_time = datetime.now().timestamp()
            self.active_session = None

        return True

    def switch_roles(self) -> Tuple[str, str]:
        """Switch roles between Isaac and human.

        Returns:
            Tuple of (isaac_new_role, human_new_role)
        """
        if not self.active_session:
            raise ValueError("No active pairing session")

        # Switch roles
        isaac_role = self.active_session.current_role
        human_role = self.active_session.human_role

        if isaac_role == PairRole.DRIVER.value:
            new_isaac_role = PairRole.NAVIGATOR.value
            new_human_role = PairRole.DRIVER.value
        elif isaac_role == PairRole.NAVIGATOR.value:
            new_isaac_role = PairRole.DRIVER.value
            new_human_role = PairRole.NAVIGATOR.value
        else:
            # Already in BOTH mode, no switch needed
            return isaac_role, human_role

        self.active_session.current_role = new_isaac_role
        self.active_session.human_role = new_human_role
        self._save_session(self.active_session)

        return new_isaac_role, new_human_role

    def add_file_touched(self, file_path: str):
        """Track a file that was modified during pairing.

        Args:
            file_path: Path to the file
        """
        if not self.active_session:
            return

        if file_path not in self.active_session.files_touched:
            self.active_session.files_touched.append(file_path)
            self._save_session(self.active_session)

    def update_context(self, key: str, value: Any):
        """Update session context.

        Args:
            key: Context key
            value: Context value
        """
        if not self.active_session:
            return

        self.active_session.context[key] = value
        self._save_session(self.active_session)

    def get_active_session(self) -> Optional[PairingSession]:
        """Get the current active session.

        Returns:
            Active session or None
        """
        return self.active_session

    def get_session_history(self, limit: int = 10) -> List[PairingSession]:
        """Get recent pairing sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of recent sessions
        """
        sessions = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, start_time, end_time, pair_style, current_role, human_role,
                       task_description, files_touched, context, active, metadata
                FROM pairing_sessions
                ORDER BY start_time DESC
                LIMIT ?
            ''', (limit,))

            for row in cursor:
                session = PairingSession(
                    id=row[0],
                    start_time=row[1],
                    end_time=row[2],
                    pair_style=row[3],
                    current_role=row[4],
                    human_role=row[5],
                    task_description=row[6],
                    files_touched=json.loads(row[7]) if row[7] else [],
                    context=json.loads(row[8]) if row[8] else {},
                    active=bool(row[9]),
                    metadata=json.loads(row[10]) if row[10] else {}
                )
                sessions.append(session)

        return sessions

    def get_pairing_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get pairing statistics for the last N days.

        Args:
            days: Number of days to look back

        Returns:
            Statistics dictionary
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        with sqlite3.connect(self.db_path) as conn:
            # Total sessions
            cursor = conn.execute('''
                SELECT COUNT(*) FROM pairing_sessions
                WHERE start_time >= ?
            ''', (cutoff_time,))
            total_sessions = cursor.fetchone()[0]

            # Total time spent pairing
            cursor = conn.execute('''
                SELECT SUM(end_time - start_time) FROM pairing_sessions
                WHERE start_time >= ? AND end_time IS NOT NULL
            ''', (cutoff_time,))
            total_time = cursor.fetchone()[0] or 0

            # Most used pairing style
            cursor = conn.execute('''
                SELECT pair_style, COUNT(*) as count FROM pairing_sessions
                WHERE start_time >= ?
                GROUP BY pair_style
                ORDER BY count DESC
                LIMIT 1
            ''', (cutoff_time,))
            result = cursor.fetchone()
            most_used_style = result[0] if result else None

            # Average session duration
            avg_duration = total_time / total_sessions if total_sessions > 0 else 0

            # Files modified count
            cursor = conn.execute('''
                SELECT files_touched FROM pairing_sessions
                WHERE start_time >= ?
            ''', (cutoff_time,))
            all_files = set()
            for row in cursor:
                if row[0]:
                    files = json.loads(row[0])
                    all_files.update(files)

        return {
            'total_sessions': total_sessions,
            'total_time_seconds': total_time,
            'average_duration_seconds': avg_duration,
            'most_used_style': most_used_style,
            'unique_files_modified': len(all_files),
            'period_days': days
        }

    def _save_session(self, session: PairingSession):
        """Save session to database.

        Args:
            session: Session to save
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO pairing_sessions
                (id, start_time, end_time, pair_style, current_role, human_role,
                 task_description, files_touched, context, active, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.id,
                session.start_time,
                session.end_time,
                session.pair_style,
                session.current_role,
                session.human_role,
                session.task_description,
                json.dumps(session.files_touched),
                json.dumps(session.context),
                session.active,
                json.dumps(session.metadata or {})
            ))

    def cleanup(self):
        """Cleanup resources."""
        # End any active session
        if self.active_session:
            self.end_session(self.active_session.id)
