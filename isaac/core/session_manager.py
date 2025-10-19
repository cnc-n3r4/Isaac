"""SessionManager - Manages Isaac session data with cloud sync."""

import json
import os
from pathlib import Path
from typing import Dict, Any
import uuid


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
    
    def __init__(self):
        """Initialize session manager."""
        # Get user home directory
        self.home_dir = Path.home()
        self.isaac_dir = self.home_dir / '.isaac'
        self.isaac_dir.mkdir(exist_ok=True)
        
        # Generate machine ID
        self.machine_id = str(uuid.uuid4())[:8]
        
        # Load config
        self.config = self._load_config()
        
        # Initialize data objects
        self.preferences = Preferences()
        self.command_history = CommandHistory()
        
        # Initialize cloud sync if enabled
        self.cloud = None
        if self.config.get('sync_enabled', False):
            try:
                from isaac.api.cloud_client import CloudClient
                
                self.cloud = CloudClient(
                    api_url=self.config.get('api_url', ''),
                    api_key=self.config.get('api_key', ''),
                    user_id=self.config.get('user_id', self.machine_id)
                )
                
                # Verify API is reachable
                if not self.cloud.health_check():
                    print("Isaac > Cloud sync unavailable (API unreachable). Using local-only mode.")
                    self.cloud = None
                    
            except Exception as e:
                print(f"Isaac > Cloud sync initialization failed: {e}. Using local-only mode.")
                self.cloud = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from ~/.isaac/config.json."""
        config_file = self.isaac_dir / 'config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def load_from_local(self):
        """Load session data from local files."""
        # Load preferences
        prefs_file = self.isaac_dir / 'preferences.json'
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r') as f:
                    data = json.load(f)
                    self.preferences = Preferences.from_dict(data)
            except Exception:
                pass
        
        # Load command history
        history_file = self.isaac_dir / 'command_history.json'
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.command_history = CommandHistory.from_dict(data)
            except Exception:
                pass
        
        print("Isaac > Loaded from local storage.")
    
    def load_from_cloud(self):
        """Load session data from cloud if available.
        
        For MVP: Overwrites local data with cloud data (last-write-wins).
        Future: Merge strategies, conflict resolution.
        """
        if not self.cloud:
            return  # Cloud sync disabled
        
        try:
            # Load preferences from cloud (overwrite local)
            cloud_prefs = self.cloud.get_session_file('preferences.json')
            if cloud_prefs:
                self.preferences = Preferences.from_dict(cloud_prefs)
                print("Isaac > Loaded preferences from cloud.")
            
            # Load command history from cloud (overwrite local)
            cloud_history = self.cloud.get_session_file('command_history.json')
            if cloud_history:
                self.command_history = CommandHistory.from_dict(cloud_history)
                print("Isaac > Loaded command history from cloud.")
                
        except Exception as e:
            # Cloud load failed, use local data
            print(f"Isaac > Cloud load failed: {e}. Using local data.")
    
    def _log_command(self, command: str):
        """Log executed command to history."""
        # Add to history
        self.command_history.commands.append({
            'command': command,
            'timestamp': str(Path.home()),  # placeholder
            'machine_id': self.machine_id
        })
        
        # Save locally
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