"""
Web Terminal - Terminal interface for web browsers
"""

import asyncio
from typing import Dict, Any, Optional, Callable
import uuid


class WebTerminal:
    """
    Manages web-based terminal sessions
    """

    def __init__(self, isaac_core):
        self.isaac_core = isaac_core
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, workspace_id: Optional[str] = None) -> str:
        """
        Create a new terminal session

        Args:
            workspace_id: Optional workspace identifier

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())

        self.sessions[session_id] = {
            'id': session_id,
            'workspace_id': workspace_id,
            'history': [],
            'environment': {},
            'cwd': '/',
            'active': True
        }

        return session_id

    async def execute_command(
        self,
        session_id: str,
        command: str,
        stream_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute command in terminal session

        Args:
            session_id: Session identifier
            command: Command to execute
            stream_callback: Optional callback for streaming output

        Returns:
            Execution result
        """
        session = self.sessions.get(session_id)

        if not session:
            return {'error': 'Session not found'}

        # Add to history
        session['history'].append({
            'command': command,
            'timestamp': asyncio.get_event_loop().time()
        })

        # TODO: Execute command using isaac_core
        # For now, return mock result
        result = {
            'command': command,
            'output': f'Executed: {command}',
            'exit_code': 0,
            'cwd': session['cwd']
        }

        if stream_callback:
            await stream_callback(result['output'])

        return result

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        return self.sessions.get(session_id)

    def get_session_history(self, session_id: str, limit: int = 100) -> list:
        """Get command history for session"""
        session = self.sessions.get(session_id)

        if not session:
            return []

        return session['history'][-limit:]

    def close_session(self, session_id: str) -> bool:
        """Close a terminal session"""
        if session_id in self.sessions:
            self.sessions[session_id]['active'] = False
            return True

        return False

    def list_sessions(self) -> list:
        """List all active sessions"""
        return [
            {
                'id': session['id'],
                'workspace_id': session['workspace_id'],
                'active': session['active'],
                'command_count': len(session['history'])
            }
            for session in self.sessions.values()
        ]
