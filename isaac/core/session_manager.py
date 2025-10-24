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
        
        # Create isaac directory if it doesn't exist
        if not self.isaac_dir.exists():
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

        # NEW: Initialize queue and sync worker
        from isaac.queue.command_queue import CommandQueue
        from isaac.queue.sync_worker import SyncWorker

        queue_db = self.isaac_dir / 'queue.db'
        self.queue = CommandQueue(queue_db)

        self.sync_worker = SyncWorker(
            queue=self.queue,
            cloud_client=self.cloud,
            check_interval=30  # Check every 30 seconds
        )

        # Start background sync
        self.sync_worker.start()

        # Initialize file history integration (Phase 3)
        self.totalcmd_parser = None
        self.file_history_manager = None
        self.cron_manager = None
        self._init_file_history()

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

        # Load AI query history
        ai_history_file = self.isaac_dir / 'aiquery_history.json'
        if ai_history_file.exists():
            try:
                with open(ai_history_file, 'r') as f:
                    data = json.load(f)
                    self.ai_query_history = AIQueryHistory.from_dict(data)
            except Exception:
                pass  # Use empty history if file corrupted

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

    def _save_config(self):
        """Save config to config.json file."""
        config_file = self.isaac_dir / 'config.json'
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass  # Don't fail if save fails

    def set_config(self, key: str, value: Any):
        """Set a configuration value and save to disk."""
        self.config[key] = value
        self._save_config()

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

    def _save_ai_query_history(self):
        """Save AI query history to local file."""
        ai_history_file = self.isaac_dir / 'aiquery_history.json'
        with open(ai_history_file, 'w') as f:
            json.dump(self.ai_query_history.to_dict(), f, indent=2)

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
        
        # Save to disk
        self._save_ai_query_history()
        
        # Cloud sync (async-style error handling)
        if self.cloud:
            try:
                self.cloud.save_session_file('aiquery_history.json', self.ai_query_history.to_dict())
            except Exception:
                pass  # Don't block query logging if cloud fails

    def add_ai_query(self, query: str, translated_command: str, shell_name: str = "unknown"):
        """Alias for log_ai_query for backward compatibility."""
        self.log_ai_query(query, translated_command, shell_name=shell_name)

    def get_preferences(self) -> 'Preferences':
        """Get the loaded preferences."""
        return self.preferences

    def get_config(self) -> Dict[str, Any]:
        """Get the loaded configuration."""
        return self.config

    def get_recent_commands(self, limit: int = 10) -> list:
        """Get recent commands from history."""
        recent = self.command_history.commands[-limit:] if self.command_history.commands else []
        return [cmd['command'] for cmd in recent]

    def shutdown(self):
        """Graceful shutdown of session manager."""
        # Stop sync worker
        if hasattr(self, 'sync_worker'):
            self.sync_worker.stop()
        
        # Stop cron manager
        if hasattr(self, 'cron_manager') and self.cron_manager:
            self.cron_manager.stop()

    def get_queue_status(self) -> dict:
        """Expose queue status for UI."""
        return self.queue.get_queue_status()

    def force_sync(self) -> bool:
        """Force immediate synchronization of queued commands."""
        if not self.cloud:
            return False

        try:
            # Trigger immediate sync
            synced_count = self.sync_worker.force_sync()
            return synced_count > 0
        except Exception:
            return False
    
    def _init_file_history(self):
        """Initialize Total Commander log integration."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Default log path (configurable via preferences)
        log_path_str = self.preferences.data.get(
            'totalcmd_log_path',
            r'C:\Program Files\Total Commander\WINCMD.LOG'
        )
        log_path = Path(log_path_str)
        
        if not log_path.exists():
            logger.info("Total Commander log not found, skipping file history")
            return
        
        # Initialize parser
        from isaac.integrations.totalcmd_parser import TotalCommanderParser
        self.totalcmd_parser = TotalCommanderParser(log_path)
        
        # Initialize collection manager
        xai_config = self.config.get('xai', {})
        collections_config = xai_config.get('collections', {})
        api_key = collections_config.get('api_key') or self.config.get('xai_api_key') or self.config.get('api_key')
        if api_key:
            from isaac.integrations.xai_collections import FileHistoryCollectionManager
            from isaac.ai.xai_client import XaiClient
            
            xai_client = XaiClient(
                api_key=api_key,
                api_url=self.config.get('xai_api_url', 'https://api.x.ai/v1/chat/completions'),
                model=self.config.get('xai_model', 'grok-3')
            )
            
            self.file_history_manager = FileHistoryCollectionManager(xai_client)
            
            # Initialize cron manager
            from isaac.scheduler.cron_manager import CronManager
            self.cron_manager = CronManager()
            
            # Register periodic upload task
            upload_interval = self.preferences.data.get('file_history_upload_interval', 60)  # minutes
            self.cron_manager.register_task(
                name='upload_file_history',
                func=self._upload_file_history,
                interval_minutes=upload_interval,
                run_immediately=False
            )
            
            # Start cron manager
            self.cron_manager.start()
            
            logger.info(f"File history sync enabled (every {upload_interval}m)")
    
    def _upload_file_history(self):
        """Background task: Parse and upload new file operations."""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.totalcmd_parser or not self.file_history_manager:
            return
        
        try:
            # Parse new operations (incremental)
            operations = self.totalcmd_parser.parse_log(incremental=True)
            
            if operations:
                # Upload to xAI collection
                count = self.file_history_manager.upload_operations(operations)
                logger.info(f"Synced {count} file operations to AI collection")
        
        except Exception as e:
            logger.error(f"File history upload failed: {e}")
    
    def get_unix_alias_config(self) -> dict:
        """Get Unix alias configuration"""
        return {
            'enabled': self.config.get('enable_unix_aliases', True),
            'show_translation': self.config.get('show_translated_command', True),
            'overrides': self.config.get('alias_overrides', {})
        }

    def reload_config(self):
        """Reload config from disk, updating in-memory config."""
        config_file = self.isaac_dir / 'config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    # Replace config entirely with file contents
                    self.config = file_config
            except Exception:
                pass  # Keep existing config if reload fails