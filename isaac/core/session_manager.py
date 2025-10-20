"""SessionManager - Manages Isaac session data with cloud sync."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import uuid

from isaac.models.task_history import TaskHistory
from isaac.models.aiquery_history import AIQueryHistory


class Preferences:
    """User preferences storage."""

    def __init__(self):
        self.data: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return self.data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Preferences':
        prefs = cls()
        prefs.data = data
        return prefs


class CommandHistory:
    """Command execution history."""

    def __init__(self):
        self.commands: list = []

    def to_dict(self) -> Dict[str, Any]:
        return {'commands': self.commands}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandHistory':
        history = cls()
        history.commands = data.get('commands', [])
        return history


class SessionManager:
    """Manages Isaac session data with optional cloud sync."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, shell_adapter = None):
        """Initialize session manager.

        Args:
            config: Configuration dictionary with API settings
            shell_adapter: Shell adapter for command execution
        """
        # Get user home directory
        self.home_dir = Path.home()
        self.isaac_dir = self.home_dir / '.isaac'
        self.isaac_dir.mkdir(exist_ok=True)

        # Store config and adapter
        self.config = config or {}
        self.shell_adapter = shell_adapter

        # Load config from disk if it exists
        self._load_config()

        # Generate machine ID if not provided
        if 'machine_id' not in self.config:
            self.config['machine_id'] = str(uuid.uuid4())[:8]

        # Initialize data structures
        self.preferences = Preferences()
        self.command_history = CommandHistory()
        self.ai_query_history = AIQueryHistory()
        self.task_history = TaskHistory()

        # Initialize cloud sync if enabled
        self.cloud = None
        if self.config.get('sync_enabled', False):
            try:
                from isaac.api.cloud_client import CloudClient

                self.cloud = CloudClient(
                    api_url=self.config.get('api_url', ''),
                    api_key=self.config.get('api_key', ''),
                    user_id=self.config.get('user_id', self.config['machine_id'])
                )
            except ImportError:
                # Cloud client not available
                pass

        # Load existing session data
        self._load_session_data()

    def _load_session_data(self):
        """Load session data from local files."""
        # Load preferences
        prefs_file = self.isaac_dir / 'preferences.json'
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r') as f:
                    data = json.load(f)
                    self.preferences = Preferences.from_dict(data)
            except Exception:
                pass  # Use defaults if file corrupted

        # Load command history
        history_file = self.isaac_dir / 'command_history.json'
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.command_history = CommandHistory.from_dict(data)
            except Exception:
                pass  # Use empty history if file corrupted

        # Load task history
        task_file = self.isaac_dir / 'task_history.json'
        if task_file.exists():
            try:
                with open(task_file, 'r') as f:
                    data = json.load(f)
                    self.task_history = TaskHistory.from_dict(data)
            except Exception:
                pass  # Use empty task history if file corrupted

    def _load_config(self):
        """Load config from config.json file."""
        config_file = self.isaac_dir / 'config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    # Merge file config with passed config (file takes precedence)
                    self.config.update(file_config)
            except Exception:
                pass  # Use defaults if file corrupted

    def log_command(self, command: str, exit_code: int = 0, shell_name: str = "unknown"):
        """Log executed command to history."""
        import time
        import platform

        entry = {
            'command': command,
            'timestamp': time.time(),
            'exit_code': exit_code,
            'shell': shell_name,
            'machine_id': self.config.get('machine_id', 'unknown')
        }

        self.command_history.commands.append(entry)

        # Keep only last 1000 commands
        if len(self.command_history.commands) > 1000:
            self.command_history.commands = self.command_history.commands[-1000:]

        # Save to disk
        self._save_command_history()

        # Cloud sync (async-style error handling)
        if self.cloud:
            try:
                self.cloud.save_session_file('command_history.json', self.command_history.to_dict())
            except Exception:
                pass  # Don't block command execution if cloud fails

    def _save_command_history(self):
        """Save command history to local file."""
        history_file = self.isaac_dir / 'command_history.json'
        with open(history_file, 'w') as f:
            json.dump(self.command_history.to_dict(), f, indent=2)

    def _save_preferences(self):
        """Save user preferences to disk."""
        prefs_file = self.isaac_dir / 'preferences.json'
        with open(prefs_file, 'w') as f:
            json.dump(self.preferences.to_dict(), f, indent=2)

        # Sync to cloud if available
        if self.cloud:
            try:
                self.cloud.save_session_file('preferences.json', self.preferences.to_dict())
            except Exception:
                pass  # Local save succeeded, cloud optional

    def log_ai_query(self, query: str, translated_command: str, explanation: str = "", executed: bool = False, shell_name: str = "unknown"):
        """Log AI query for privacy-focused history."""
        self.ai_query_history.add(
            query=query,
            command=translated_command,
            shell=shell_name,
            executed=executed,
            result='executed' if executed else 'translated'
        )

    def add_ai_query(self, query: str, translated_command: str, shell_name: str = "unknown"):
        """Alias for log_ai_query for backward compatibility."""
        self.log_ai_query(query, translated_command, shell_name=shell_name)

    def get_preferences(self) -> 'Preferences':
        """Get the loaded preferences."""
        return self.preferences

    def get_config(self) -> Dict[str, Any]:
        """Get the loaded configuration."""
        return self.config
        # Local save
        task_file = self.isaac_dir / 'task_history.json'
        with open(task_file, 'w') as f:
            json.dump(self.task_history.to_dict(), f, indent=2)

        # Cloud sync
        if self.cloud:
            try:
                self.cloud.save_session_file('task_history.json', self.task_history.to_dict())
            except Exception:
                pass