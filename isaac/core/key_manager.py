"""
Key System for Isaac Authentication
Manages authentication keys for multi-channel access
"""

import json
import os
import bcrypt
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random


class KeyManager:
    """Manage authentication keys for Isaac access"""

    KEY_TYPES = {
        "user": {
            "permissions": ["read", "write", "execute", "ai", "cloud"],
            "interactive": True,
            "description": "Full interactive user session"
        },
        "daemon": {
            "permissions": ["read", "write", "execute", "webhook"],
            "interactive": False,
            "description": "Background service for webhooks/cron"
        },
        "readonly": {
            "permissions": ["read", "cloud"],
            "interactive": True,
            "description": "View-only access (status, logs)"
        },
        "oneshot": {
            "permissions": ["read", "execute_safe"],
            "interactive": False,
            "description": "Single command execution (tier ≤2 only)"
        },
        "persona": {
            "permissions": ["read", "write", "execute", "ai", "persona_switch"],
            "interactive": True,
            "description": "Switch to different persona (Sarah, etc.)"
        }
    }

    REJECTION_MESSAGES = [
        "i dont do this shit for free",
        "get a key, pal",
        "nice try, no key = no service",
        "authentication required, buddy",
        "lo siento, pally-o. get a key!",
        "you think I work for free? cute.",
        "key first, questions later"
    ]

    def __init__(self, isaac_dir: Path = None):
        """Initialize key manager"""
        if isaac_dir is None:
            isaac_dir = Path.home() / '.isaac'
        self.isaac_dir = isaac_dir
        self.keys_file = isaac_dir / 'keys.json'
        self.master_key_file = isaac_dir / '.master_key'
        self._ensure_keys_file()

    def _ensure_keys_file(self):
        """Ensure keys.json exists with proper structure"""
        if not self.keys_file.exists():
            self.isaac_dir.mkdir(parents=True, exist_ok=True)
            default_keys = {
                "keys": [],
                "rejection_messages": self.REJECTION_MESSAGES.copy()
            }
            with open(self.keys_file, 'w') as f:
                json.dump(default_keys, f, indent=2)

    def _check_master_key_override(self, provided_key: str) -> Optional[Dict[str, Any]]:
        """Check for master key override mechanisms"""
        # 1. Environment variable override (highest priority)
        env_master = os.environ.get('ISAAC_MASTER_KEY')
        if env_master and provided_key == env_master:
            return {
                "name": "env_master_key",
                "type": "user",  # Full permissions
                "permissions": ["read", "write", "execute", "ai", "cloud", "admin"],
                "interactive": True,
                "master_override": True,
                "source": "environment_variable"
            }

        # 2. Master key file override
        if self.master_key_file.exists():
            try:
                with open(self.master_key_file, 'r') as f:
                    master_key = f.read().strip()
                    if master_key and provided_key == master_key:
                        return {
                            "name": "file_master_key",
                            "type": "user",  # Full permissions
                            "permissions": ["read", "write", "execute", "ai", "cloud", "admin"],
                            "interactive": True,
                            "master_override": True,
                            "source": "master_key_file"
                        }
            except Exception:
                pass  # Ignore file read errors

        # 3. Development emergency key (only in debug mode)
        if os.environ.get('ISAAC_DEBUG') == 'true':
            dev_key = "isaac_dev_master_2024"
            if provided_key == dev_key:
                return {
                    "name": "dev_master_key",
                    "type": "user",
                    "permissions": ["read", "write", "execute", "ai", "cloud", "admin"],
                    "interactive": True,
                    "master_override": True,
                    "source": "development_key"
                }

        return None

    def set_master_key(self, master_key: str) -> bool:
        """Set a master key in the master key file"""
        try:
            with open(self.master_key_file, 'w') as f:
                f.write(master_key)
            # Set restrictive permissions (readable only by owner)
            self.master_key_file.chmod(0o600)
            return True
        except Exception:
            return False

    def get_master_key_status(self) -> Dict[str, Any]:
        """Get status of master key mechanisms"""
        status = {
            "environment_variable": bool(os.environ.get('ISAAC_MASTER_KEY')),
            "master_key_file": self.master_key_file.exists(),
            "development_key": os.environ.get('ISAAC_DEBUG') == 'true'
        }

        # Don't reveal the actual keys, just their existence
        if status["master_key_file"]:
            try:
                stat = self.master_key_file.stat()
                status["file_permissions"] = oct(stat.st_mode)[-3:]
                status["file_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except Exception:
                status["file_permissions"] = "unknown"
                status["file_modified"] = "unknown"

        return status

    def remove_master_key(self) -> bool:
        """Remove the master key file"""
        try:
            if self.master_key_file.exists():
                self.master_key_file.unlink()
            return True
        except Exception:
            return False

    def load_keys(self) -> Dict[str, Any]:
        """Load keys from file"""
        try:
            with open(self.keys_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {"keys": [], "rejection_messages": self.REJECTION_MESSAGES.copy()}

    def save_keys(self, data: Dict[str, Any]):
        """Save keys to file"""
        with open(self.keys_file, 'w') as f:
            json.dump(data, f, indent=2)

    def create_key(self, name: str, key_type: str, password: str,
                   expires_days: Optional[int] = None, persona: Optional[str] = None) -> bool:
        """Create a new authentication key"""
        if key_type not in self.KEY_TYPES:
            return False

        # Generate bcrypt hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

        # Create key entry
        key_entry = {
            "name": name,
            "type": key_type,
            "hash": hashed.decode('utf-8'),
            "created": datetime.now().isoformat(),
            "last_used": None,
            "expires": None
        }

        if expires_days:
            expires = datetime.now() + timedelta(days=expires_days)
            key_entry["expires"] = expires.isoformat()

        if key_type == "persona" and persona:
            key_entry["persona"] = persona

        # Load existing keys
        data = self.load_keys()

        # Check if key name already exists
        if any(k["name"] == name for k in data["keys"]):
            return False

        # Add new key
        data["keys"].append(key_entry)
        self.save_keys(data)
        return True

    def create_random_key(self, key_type: str, name: Optional[str] = None,
                         expires_days: Optional[int] = None, persona: Optional[str] = None) -> tuple[str, str]:
        """Create a key with random password and return (password, key_id)"""
        if key_type not in self.KEY_TYPES:
            raise ValueError(f"Invalid key type: {key_type}")

        # Generate random password/key
        password = secrets.token_urlsafe(16)  # 22 characters

        # Use name or generate one
        if name is None:
            name = f"{key_type}_{secrets.token_hex(4)}"

        if self.create_key(name, key_type, password, expires_days, persona):
            return password, name
        else:
            raise ValueError(f"Key name '{name}' already exists")

    def authenticate(self, name_or_key: str, password: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Authenticate with key name and password, or single key for CLI"""
        # First, check for master key overrides
        master_auth = self._check_master_key_override(name_or_key)
        if master_auth:
            return master_auth

        data = self.load_keys()

        # If password is None, treat name_or_key as a single-use key
        if password is None:
            # For single-key auth, we need to find a key where the hash matches the provided key
            # This is less secure but convenient for CLI usage
            for key in data["keys"]:
                # Check if expired
                if key.get("expires"):
                    expires = datetime.fromisoformat(key["expires"])
                    if datetime.now() > expires:
                        continue

                # For CLI convenience, check if the provided key matches the hash directly
                # This allows using the key as both identifier and password
                try:
                    if bcrypt.checkpw(name_or_key.encode('utf-8'), key["hash"].encode('utf-8')):
                        # Update last_used
                        key["last_used"] = datetime.now().isoformat()
                        self.save_keys(data)
                        return key
                except Exception:
                    continue
            return None

        # Original name/password authentication
        for key in data["keys"]:
            if key["name"] == name_or_key:
                # Check if expired
                if key.get("expires"):
                    expires = datetime.fromisoformat(key["expires"])
                    if datetime.now() > expires:
                        return None

                # Verify password
                if bcrypt.checkpw(password.encode('utf-8'), key["hash"].encode('utf-8')):
                    # Update last_used
                    key["last_used"] = datetime.now().isoformat()
                    self.save_keys(data)
                    return key

        return None

    def get_key_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a key (without hash)"""
        data = self.load_keys()

        for key in data["keys"]:
            if key["name"] == name:
                # Return copy without hash
                info = key.copy()
                info.pop("hash", None)
                return info

        return None

    def list_keys(self) -> List[Dict[str, Any]]:
        """List all keys (without hashes)"""
        data = self.load_keys()
        keys_info = []

        for key in data["keys"]:
            info = key.copy()
            info.pop("hash", None)
            keys_info.append(info)

        return keys_info

    def delete_key(self, name: str) -> bool:
        """Delete a key"""
        data = self.load_keys()
        original_count = len(data["keys"])

        data["keys"] = [k for k in data["keys"] if k["name"] != name]

        if len(data["keys"]) < original_count:
            self.save_keys(data)
            return True

        return False

    def get_rejection_message(self) -> str:
        """Get a random rejection message"""
        data = self.load_keys()
        messages = data.get("rejection_messages", self.REJECTION_MESSAGES)
        return random.choice(messages)

    def has_permission(self, key_info: Dict[str, Any], permission: str) -> bool:
        """Check if key has specific permission"""
        key_type = key_info.get("type")
        if not key_type or key_type not in self.KEY_TYPES:
            return False

        permissions = self.KEY_TYPES[key_type]["permissions"]
        return permission in permissions

    def is_interactive_allowed(self, key_info: Dict[str, Any]) -> bool:
        """Check if key allows interactive sessions"""
        key_type = key_info.get("type")
        if not key_type or key_type not in self.KEY_TYPES:
            return False

        return self.KEY_TYPES[key_type]["interactive"]