#!/usr/bin/env python3
"""
XAI Session Manager - Persistent 24-hour AI Memory

Manages xAI session IDs for persistent conversation context.
xAI native sessions last 24 hours - this manager handles:
- Session creation and persistence
- Workspace-session binding
- Automatic session rotation (20h refresh)
- Session bridging for continuity beyond 24h
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)


class XAISessionManager:
    """
    Manages persistent xAI sessions for workspace isolation and 24-hour memory.

    Features:
    - One session per workspace (context isolation)
    - Automatic session rotation before 24h expiry
    - Session bridging for seamless continuity
    - Persistent storage across ISAAC restarts
    """

    # Session lifecycle constants
    SESSION_MAX_AGE = timedelta(hours=24)  # xAI native limit
    SESSION_ROTATION_TIME = timedelta(hours=20)  # Rotate before expiry
    SESSION_BRIDGE_OVERLAP = timedelta(hours=2)  # Overlap for context transfer

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize session manager

        Args:
            config_path: Path to sessions.json storage file
        """
        if config_path is None:
            config_path = Path.home() / '.isaac' / 'sessions.json'

        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory cache: workspace -> session data
        self.sessions: Dict[str, Dict[str, Any]] = {}

        # Load existing sessions
        self._load_sessions()

        logger.info(f"Session manager initialized at {config_path}")

    def _load_sessions(self):
        """Load sessions from persistent storage"""
        if not self.config_path.exists():
            logger.info("No existing sessions file, starting fresh")
            return

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            # Load and validate each session
            for workspace, session_data in data.items():
                created_at = datetime.fromisoformat(session_data['created_at'])
                age = datetime.now() - created_at

                # Only load sessions younger than 24h
                if age < self.SESSION_MAX_AGE:
                    self.sessions[workspace] = session_data
                    logger.debug(f"Loaded session for workspace '{workspace}' (age: {age})")
                else:
                    logger.debug(f"Expired session for workspace '{workspace}' (age: {age})")

            logger.info(f"Loaded {len(self.sessions)} active session(s)")

        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            self.sessions = {}

    def _save_sessions(self):
        """Persist sessions to storage"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.sessions, f, indent=2)
            logger.debug(f"Saved {len(self.sessions)} session(s)")
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def _generate_session_id(self, workspace: str) -> str:
        """
        Generate deterministic session ID for workspace

        Format: isaac_ws_{workspace}_{hash}_{timestamp}

        Args:
            workspace: Workspace name

        Returns:
            Unique session ID
        """
        timestamp = str(int(time.time()))

        # Create hash from workspace name for uniqueness
        workspace_hash = hashlib.sha256(workspace.encode()).hexdigest()[:8]

        return f"isaac_ws_{workspace}_{workspace_hash}_{timestamp}"

    def get_or_create_session(self, workspace: str = 'default') -> str:
        """
        Get existing session or create new one for workspace

        Handles:
        - Session creation for new workspaces
        - Session validation (age check)
        - Automatic rotation if nearing expiry
        - Session bridging for continuity

        Args:
            workspace: Workspace name (default: 'default')

        Returns:
            Active session ID
        """
        # Check if session exists and is valid
        if workspace in self.sessions:
            session_data = self.sessions[workspace]
            created_at = datetime.fromisoformat(session_data['created_at'])
            age = datetime.now() - created_at

            # Check if rotation needed (20h threshold)
            if age < self.SESSION_ROTATION_TIME:
                logger.debug(f"Using existing session for '{workspace}' (age: {age})")
                session_data['last_used'] = datetime.now().isoformat()
                self._save_sessions()
                return session_data['session_id']

            # Rotation needed - create new session with bridging
            logger.info(f"Rotating session for '{workspace}' (age: {age})")
            return self._rotate_session(workspace, session_data)

        # Create new session
        logger.info(f"Creating new session for workspace '{workspace}'")
        return self._create_session(workspace)

    def _create_session(self, workspace: str) -> str:
        """
        Create new session for workspace

        Args:
            workspace: Workspace name

        Returns:
            New session ID
        """
        session_id = self._generate_session_id(workspace)

        session_data = {
            'session_id': session_id,
            'workspace': workspace,
            'created_at': datetime.now().isoformat(),
            'last_used': datetime.now().isoformat(),
            'rotation_count': 0,
            'previous_session': None
        }

        self.sessions[workspace] = session_data
        self._save_sessions()

        logger.info(f"Created session {session_id} for workspace '{workspace}'")
        return session_id

    def _rotate_session(self, workspace: str, old_session: Dict[str, Any]) -> str:
        """
        Rotate session before expiry with bridging support

        Creates new session while keeping reference to old session
        for context bridging.

        Args:
            workspace: Workspace name
            old_session: Previous session data

        Returns:
            New session ID
        """
        new_session_id = self._generate_session_id(workspace)

        # Create new session with bridge to old
        session_data = {
            'session_id': new_session_id,
            'workspace': workspace,
            'created_at': datetime.now().isoformat(),
            'last_used': datetime.now().isoformat(),
            'rotation_count': old_session.get('rotation_count', 0) + 1,
            'previous_session': old_session['session_id'],  # Bridge
            'bridge_created_at': datetime.now().isoformat()
        }

        self.sessions[workspace] = session_data
        self._save_sessions()

        logger.info(f"Rotated session for '{workspace}': {old_session['session_id']} → {new_session_id}")
        return new_session_id

    def get_session_info(self, workspace: str = 'default') -> Optional[Dict[str, Any]]:
        """
        Get session metadata for workspace

        Args:
            workspace: Workspace name

        Returns:
            Session metadata or None if not found
        """
        if workspace not in self.sessions:
            return None

        session_data = self.sessions[workspace]
        created_at = datetime.fromisoformat(session_data['created_at'])
        age = datetime.now() - created_at
        remaining = self.SESSION_MAX_AGE - age

        return {
            'session_id': session_data['session_id'],
            'workspace': workspace,
            'age': str(age).split('.')[0],  # Remove microseconds
            'remaining': str(remaining).split('.')[0],
            'rotation_count': session_data.get('rotation_count', 0),
            'needs_rotation': age >= self.SESSION_ROTATION_TIME,
            'has_bridge': session_data.get('previous_session') is not None
        }

    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get info for all active sessions

        Returns:
            Dict mapping workspace to session info
        """
        result = {}
        for workspace in self.sessions.keys():
            info = self.get_session_info(workspace)
            if info:
                result[workspace] = info
        return result

    def invalidate_session(self, workspace: str) -> bool:
        """
        Manually invalidate session for workspace

        Args:
            workspace: Workspace name

        Returns:
            True if session was invalidated, False if not found
        """
        if workspace in self.sessions:
            logger.info(f"Invalidating session for workspace '{workspace}'")
            del self.sessions[workspace]
            self._save_sessions()
            return True
        return False

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions (>24h)

        Returns:
            Number of sessions removed
        """
        expired = []

        for workspace, session_data in self.sessions.items():
            created_at = datetime.fromisoformat(session_data['created_at'])
            age = datetime.now() - created_at

            if age >= self.SESSION_MAX_AGE:
                expired.append(workspace)

        for workspace in expired:
            logger.info(f"Removing expired session for workspace '{workspace}'")
            del self.sessions[workspace]

        if expired:
            self._save_sessions()

        return len(expired)

    def get_context_bridge_info(self, workspace: str) -> Optional[str]:
        """
        Get previous session ID for context bridging

        When a session is rotated, the previous session ID can be used
        to fetch recent context and transfer it to the new session.

        Args:
            workspace: Workspace name

        Returns:
            Previous session ID or None
        """
        if workspace not in self.sessions:
            return None

        session_data = self.sessions[workspace]
        previous = session_data.get('previous_session')

        if previous:
            # Check if bridge is still within overlap window
            bridge_time = datetime.fromisoformat(session_data.get('bridge_created_at', '2000-01-01'))
            bridge_age = datetime.now() - bridge_time

            if bridge_age < self.SESSION_BRIDGE_OVERLAP:
                return previous

        return None


# Global instance (lazy loaded)
_session_manager: Optional[XAISessionManager] = None


def get_session_manager() -> XAISessionManager:
    """Get or create global session manager instance"""
    global _session_manager

    if _session_manager is None:
        _session_manager = XAISessionManager()

    return _session_manager


if __name__ == '__main__':
    # Test the session manager
    logging.basicConfig(level=logging.DEBUG)

    manager = XAISessionManager()

    print("=== Session Manager Test ===\n")

    # Create sessions for different workspaces
    workspaces = ['default', 'project-alpha', 'api-refactor']

    for ws in workspaces:
        session_id = manager.get_or_create_session(ws)
        print(f"Workspace '{ws}': {session_id}")

    print("\n=== Session Info ===\n")

    for ws in workspaces:
        info = manager.get_session_info(ws)
        if info:
            print(f"{ws}:")
            print(f"  Session ID: {info['session_id']}")
            print(f"  Age: {info['age']}")
            print(f"  Remaining: {info['remaining']}")
            print(f"  Rotations: {info['rotation_count']}")
            print()

    print(f"\n✓ Sessions saved to: {manager.config_path}")
