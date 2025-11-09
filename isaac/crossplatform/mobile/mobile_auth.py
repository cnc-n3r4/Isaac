"""
Mobile Authentication - Authentication for mobile devices
"""

import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class MobileAuth:
    """
    Authentication manager for mobile devices
    """

    def __init__(self):
        self.pairing_codes: Dict[str, Dict[str, Any]] = {}
        self.mobile_sessions: Dict[str, Dict[str, Any]] = {}

    def generate_pairing_code(self, instance_id: str) -> str:
        """
        Generate a pairing code for mobile device setup

        Args:
            instance_id: Isaac instance identifier

        Returns:
            6-digit pairing code
        """
        # Generate 6-digit code
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])

        # Store with expiration
        self.pairing_codes[code] = {
            'code': code,
            'instance_id': instance_id,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
            'used': False
        }

        return code

    def validate_pairing_code(self, code: str, device_id: str) -> Optional[str]:
        """
        Validate pairing code and create mobile session

        Args:
            code: Pairing code
            device_id: Mobile device identifier

        Returns:
            Session token if valid, None otherwise
        """
        if code not in self.pairing_codes:
            return None

        pairing = self.pairing_codes[code]

        # Check if already used
        if pairing['used']:
            return None

        # Check if expired
        expires_at = datetime.fromisoformat(pairing['expires_at'])
        if datetime.utcnow() > expires_at:
            return None

        # Mark as used
        pairing['used'] = True

        # Create session token
        token = self.create_mobile_session(
            pairing['instance_id'],
            device_id
        )

        return token

    def create_mobile_session(
        self,
        instance_id: str,
        device_id: str
    ) -> str:
        """
        Create a mobile session

        Args:
            instance_id: Isaac instance
            device_id: Mobile device

        Returns:
            Session token
        """
        # Generate secure token
        token = secrets.token_urlsafe(32)

        self.mobile_sessions[token] = {
            'token': token,
            'instance_id': instance_id,
            'device_id': device_id,
            'created_at': datetime.utcnow().isoformat(),
            'last_used': datetime.utcnow().isoformat(),
            'active': True
        }

        return token

    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a mobile session token

        Args:
            token: Session token

        Returns:
            Session info if valid, None otherwise
        """
        session = self.mobile_sessions.get(token)

        if not session or not session['active']:
            return None

        # Update last used
        session['last_used'] = datetime.utcnow().isoformat()

        return session

    def revoke_session(self, token: str) -> bool:
        """Revoke a mobile session"""
        session = self.mobile_sessions.get(token)

        if session:
            session['active'] = False
            return True

        return False

    def list_active_sessions(self, instance_id: Optional[str] = None) -> list:
        """List active mobile sessions"""
        sessions = [
            {
                'instance_id': session['instance_id'],
                'device_id': session['device_id'],
                'created_at': session['created_at'],
                'last_used': session['last_used']
            }
            for session in self.mobile_sessions.values()
            if session['active']
        ]

        if instance_id:
            sessions = [s for s in sessions if s['instance_id'] == instance_id]

        return sessions

    def cleanup_expired_codes(self):
        """Remove expired pairing codes"""
        now = datetime.utcnow()
        expired = []

        for code, data in self.pairing_codes.items():
            expires_at = datetime.fromisoformat(data['expires_at'])
            if now > expires_at:
                expired.append(code)

        for code in expired:
            del self.pairing_codes[code]

    def get_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        active_codes = sum(
            1 for p in self.pairing_codes.values()
            if not p['used'] and datetime.utcnow() < datetime.fromisoformat(p['expires_at'])
        )

        return {
            'active_pairing_codes': active_codes,
            'total_sessions': len(self.mobile_sessions),
            'active_sessions': sum(1 for s in self.mobile_sessions.values() if s['active'])
        }
