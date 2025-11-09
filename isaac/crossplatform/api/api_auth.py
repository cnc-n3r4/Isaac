"""
API Authentication - Manage API keys and authentication
"""

import hashlib
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import jwt


class APIAuth:
    """
    Manages API authentication and authorization
    """

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_api_key(
        self,
        name: str,
        scopes: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None
    ) -> str:
        """
        Create a new API key

        Args:
            name: Name/description for the key
            scopes: List of permission scopes
            expires_in_days: Optional expiration in days

        Returns:
            API key
        """
        # Generate random API key
        api_key = f"isaac_{secrets.token_urlsafe(32)}"

        # Hash the key for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        expires_at = None
        if expires_in_days:
            expires_at = (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat()

        self.api_keys[key_hash] = {
            'hash': key_hash,
            'name': name,
            'scopes': scopes or ['*'],
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': expires_at,
            'active': True,
            'last_used': None,
            'usage_count': 0
        }

        return api_key

    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key

        Args:
            api_key: API key to validate

        Returns:
            Key info if valid, None otherwise
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        if key_hash not in self.api_keys:
            return None

        key_info = self.api_keys[key_hash]

        # Check if active
        if not key_info['active']:
            return None

        # Check if expired
        if key_info['expires_at']:
            expires_at = datetime.fromisoformat(key_info['expires_at'])
            if datetime.utcnow() > expires_at:
                key_info['active'] = False
                return None

        # Update usage stats
        key_info['last_used'] = datetime.utcnow().isoformat()
        key_info['usage_count'] += 1

        return key_info

    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        if key_hash in self.api_keys:
            self.api_keys[key_hash]['active'] = False
            return True

        return False

    def list_api_keys(self) -> List[Dict[str, Any]]:
        """List all API keys (without exposing actual keys)"""
        return [
            {
                'name': key['name'],
                'scopes': key['scopes'],
                'created_at': key['created_at'],
                'expires_at': key['expires_at'],
                'active': key['active'],
                'last_used': key['last_used'],
                'usage_count': key['usage_count']
            }
            for key in self.api_keys.values()
        ]

    def create_session_token(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_hours: int = 24
    ) -> str:
        """
        Create a JWT session token

        Args:
            user_id: User identifier
            metadata: Optional metadata to include
            expires_in_hours: Token expiration in hours

        Returns:
            JWT token
        """
        payload = {
            'user_id': user_id,
            'metadata': metadata or {},
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours)
        }

        token = jwt.encode(payload, self.secret_key, algorithm='HS256')

        # Store session
        self.sessions[user_id] = {
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': payload['exp'].isoformat(),
            'metadata': metadata
        }

        return token

    def validate_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT session token

        Args:
            token: JWT token

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def revoke_session(self, user_id: str) -> bool:
        """Revoke a user session"""
        if user_id in self.sessions:
            del self.sessions[user_id]
            return True

        return False

    def check_scope(self, key_info: Dict[str, Any], required_scope: str) -> bool:
        """
        Check if API key has required scope

        Args:
            key_info: Key information from validate_api_key
            required_scope: Required scope

        Returns:
            True if key has scope
        """
        scopes = key_info.get('scopes', [])

        # Wildcard scope grants all permissions
        if '*' in scopes:
            return True

        return required_scope in scopes

    def get_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        total_keys = len(self.api_keys)
        active_keys = sum(1 for k in self.api_keys.values() if k['active'])
        total_usage = sum(k['usage_count'] for k in self.api_keys.values())

        return {
            'total_api_keys': total_keys,
            'active_api_keys': active_keys,
            'total_usage': total_usage,
            'active_sessions': len(self.sessions)
        }
