"""
Workspace Bubbles - Capture and restore complete workspace states
Isaac's time-travel feature for seamless context switching
"""

import json
import os
import psutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from isaac.core.session_manager import SessionManager


@dataclass
class BubbleState:
    """Complete workspace state snapshot."""
    bubble_id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    workspace_path: str = ""

    # State components
    git_state: Dict[str, Any] = field(default_factory=dict)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    running_processes: List[Dict[str, Any]] = field(default_factory=list)
    open_files: List[str] = field(default_factory=list)
    shell_history: List[str] = field(default_factory=list)
    terminal_state: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    tags: List[str] = field(default_factory=list)
    version: str = "1.0"
    parent_bubble: Optional[str] = None


@dataclass
class BubbleMetadata:
    """Metadata for bubble management."""
    total_bubbles: int = 0
    last_backup: Optional[datetime] = None
    auto_save_enabled: bool = True
    max_bubbles: int = 50


class BubbleManager:
    """Manages workspace bubbles for state capture and restoration."""

    def __init__(self, session_manager: SessionManager):
        """Initialize bubble manager.

        Args:
            session_manager: Session manager for persistence
        """
        self.session = session_manager
        self.bubbles_dir = Path.home() / '.isaac' / 'bubbles'
        self.bubbles_dir.mkdir(exist_ok=True)

        self.metadata_file = self.bubbles_dir / 'metadata.json'
        self.metadata = self._load_metadata()

        # Current bubble tracking
        self.current_bubble: Optional[BubbleState] = None
        self.suspended_bubbles: Dict[str, BubbleState] = {}

    def _load_metadata(self) -> BubbleMetadata:
        """Load bubble metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                return BubbleMetadata(**data)
            except (json.JSONDecodeError, KeyError):
                pass
        return BubbleMetadata()

    def _save_metadata(self) -> None:
        """Save bubble metadata to disk."""
        data = {
            'total_bubbles': self.metadata.total_bubbles,
            'last_backup': self.metadata.last_backup.isoformat() if self.metadata.last_backup else None,
            'auto_save_enabled': self.metadata.auto_save_enabled,
            'max_bubbles': self.metadata.max_bubbles
        }

        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Don't fail if we can't save metadata

    def create_bubble(self, name: str, description: str = "", tags: List[str] = None) -> BubbleState:
        """Create a new bubble capturing current workspace state.

        Args:
            name: Bubble name
            description: Optional description
            tags: Optional tags for organization

        Returns:
            Created bubble state
        """
        bubble_id = f"{name}_{int(datetime.now().timestamp())}"

        bubble = BubbleState(
            bubble_id=bubble_id,
            name=name,
            description=description,
            workspace_path=os.getcwd(),
            tags=tags or []
        )

        # Capture all state components
        bubble.git_state = self._capture_git_state()
        bubble.environment_vars = self._capture_environment()
        bubble.running_processes = self._capture_processes()
        bubble.open_files = self._capture_open_files()
        bubble.shell_history = self._capture_shell_history()
        bubble.terminal_state = self._capture_terminal_state()

        # Save bubble to disk
        self._save_bubble(bubble)

        # Update metadata
        self.metadata.total_bubbles += 1
        self.metadata.last_backup = datetime.now()
        self._save_metadata()

        # Set as current bubble
        self.current_bubble = bubble

        return bubble

    def suspend_bubble(self, bubble_id: str) -> bool:
        """Suspend a bubble (freeze its state).

        Args:
            bubble_id: Bubble to suspend

        Returns:
            True if suspended successfully
        """
        if bubble_id not in self.suspended_bubbles:
            # Find bubble by ID
            bubble = self._load_bubble(bubble_id)
            if bubble:
                self.suspended_bubbles[bubble_id] = bubble
                return True
        return False

    def resume_bubble(self, bubble_id: str) -> bool:
        """Resume a suspended bubble.

        Args:
            bubble_id: Bubble to resume

        Returns:
            True if resumed successfully
        """
        if bubble_id in self.suspended_bubbles:
            bubble = self.suspended_bubbles[bubble_id]

            # Restore state components
            success = self._restore_bubble_state(bubble)

            if success:
                self.current_bubble = bubble
                del self.suspended_bubbles[bubble_id]

            return success

        # Try to load from disk
        bubble = self._load_bubble(bubble_id)
        if bubble:
            success = self._restore_bubble_state(bubble)
            if success:
                self.current_bubble = bubble
            return success

        return False

    def list_bubbles(self, tag_filter: str = None) -> List[BubbleState]:
        """List all available bubbles.

        Args:
            tag_filter: Optional tag to filter by

        Returns:
            List of bubble states
        """
        bubbles = []

        # Load all bubble files
        for bubble_file in self.bubbles_dir.glob('*.json'):
            if bubble_file.name != 'metadata.json':
                try:
                    with open(bubble_file, 'r') as f:
                        data = json.load(f)
                    bubble = BubbleState(**data)
                    bubble.created_at = datetime.fromisoformat(data['created_at'])

                    if tag_filter is None or tag_filter in bubble.tags:
                        bubbles.append(bubble)
                except Exception:
                    continue

        return sorted(bubbles, key=lambda b: b.created_at, reverse=True)

    def delete_bubble(self, bubble_id: str) -> bool:
        """Delete a bubble.

        Args:
            bubble_id: Bubble to delete

        Returns:
            True if deleted successfully
        """
        bubble_file = self.bubbles_dir / f'{bubble_id}.json'
        if bubble_file.exists():
            bubble_file.unlink()
            self.metadata.total_bubbles = max(0, self.metadata.total_bubbles - 1)
            self._save_metadata()
            return True
        return False

    def export_bubble(self, bubble_id: str, export_path: str) -> bool:
        """Export a bubble for sharing.

        Args:
            bubble_id: Bubble to export
            export_path: Path to export to

        Returns:
            True if exported successfully
        """
        bubble = self._load_bubble(bubble_id)
        if not bubble:
            return False

        try:
            with open(export_path, 'w') as f:
                data = {
                    'bubble_id': bubble.bubble_id,
                    'name': bubble.name,
                    'description': bubble.description,
                    'created_at': bubble.created_at.isoformat(),
                    'workspace_path': bubble.workspace_path,
                    'git_state': bubble.git_state,
                    'environment_vars': bubble.environment_vars,
                    'running_processes': bubble.running_processes,
                    'open_files': bubble.open_files,
                    'shell_history': bubble.shell_history,
                    'terminal_state': bubble.terminal_state,
                    'tags': bubble.tags,
                    'version': bubble.version,
                    'parent_bubble': bubble.parent_bubble
                }
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    def import_bubble(self, import_path: str) -> Optional[BubbleState]:
        """Import a bubble from file.

        Args:
            import_path: Path to import from

        Returns:
            Imported bubble or None if failed
        """
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)

            bubble = BubbleState(**data)
            bubble.created_at = datetime.fromisoformat(data['created_at'])

            # Save imported bubble
            self._save_bubble(bubble)
            self.metadata.total_bubbles += 1
            self._save_metadata()

            return bubble
        except Exception:
            return None

    def _capture_git_state(self) -> Dict[str, Any]:
        """Capture current git repository state."""
        try:
            # Get current branch
            result = subprocess.run(['git', 'branch', '--show-current'],
                                  capture_output=True, text=True, cwd=os.getcwd())
            current_branch = result.stdout.strip() if result.returncode == 0 else None

            # Get status
            result = subprocess.run(['git', 'status', '--porcelain'],
                                  capture_output=True, text=True, cwd=os.getcwd())
            status = result.stdout.strip() if result.returncode == 0 else ""

            # Get recent commits
            result = subprocess.run(['git', 'log', '--oneline', '-5'],
                                  capture_output=True, text=True, cwd=os.getcwd())
            recent_commits = result.stdout.strip() if result.returncode == 0 else ""

            return {
                'current_branch': current_branch,
                'status': status,
                'recent_commits': recent_commits,
                'is_git_repo': True
            }
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {'is_git_repo': False}

    def _capture_environment(self) -> Dict[str, str]:
        """Capture relevant environment variables."""
        relevant_vars = [
            'PATH', 'PYTHONPATH', 'NODE_PATH', 'JAVA_HOME', 'HOME', 'USER',
            'SHELL', 'TERM', 'EDITOR', 'VISUAL', 'PAGER'
        ]

        env = {}
        for var in relevant_vars:
            value = os.environ.get(var)
            if value:
                env[var] = value

        return env

    def _capture_processes(self) -> List[Dict[str, Any]]:
        """Capture running processes related to the workspace."""
        processes = []
        workspace_path = os.getcwd()

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
                try:
                    info = proc.info
                    if info['cwd'] and workspace_path in info['cwd']:
                        processes.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'cmdline': info['cmdline'],
                            'cwd': info['cwd']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        return processes[:20]  # Limit to 20 processes

    def _capture_open_files(self) -> List[str]:
        """Capture list of open files in workspace."""
        open_files = []
        workspace_path = os.getcwd()

        try:
            for proc in psutil.process_iter():
                try:
                    for file in proc.open_files():
                        if file.path.startswith(workspace_path):
                            open_files.append(file.path)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        return list(set(open_files))[:50]  # Limit and deduplicate

    def _capture_shell_history(self) -> List[str]:
        """Capture recent shell command history."""
        # This would integrate with the command history system
        # For now, return empty list
        return []

    def _capture_terminal_state(self) -> Dict[str, Any]:
        """Capture terminal-specific state."""
        return {
            'current_directory': os.getcwd(),
            'terminal_type': os.environ.get('TERM', 'unknown'),
            'shell': os.environ.get('SHELL', 'unknown')
        }

    def _restore_bubble_state(self, bubble: BubbleState) -> bool:
        """Restore workspace state from bubble.

        Args:
            bubble: Bubble to restore from

        Returns:
            True if restoration successful
        """
        try:
            # Change to workspace directory
            if bubble.workspace_path and os.path.exists(bubble.workspace_path):
                os.chdir(bubble.workspace_path)

            # Restore environment variables
            for key, value in bubble.environment_vars.items():
                os.environ[key] = value

            # Note: We don't restore processes or open files as that would be complex
            # and potentially dangerous. Those would need special handling.

            print(f"Restored bubble '{bubble.name}' - workspace state loaded")
            return True

        except Exception as e:
            print(f"Failed to restore bubble: {e}")
            return False

    def _save_bubble(self, bubble: BubbleState) -> None:
        """Save bubble to disk."""
        bubble_file = self.bubbles_dir / f'{bubble.bubble_id}.json'

        data = {
            'bubble_id': bubble.bubble_id,
            'name': bubble.name,
            'description': bubble.description,
            'created_at': bubble.created_at.isoformat(),
            'workspace_path': bubble.workspace_path,
            'git_state': bubble.git_state,
            'environment_vars': bubble.environment_vars,
            'running_processes': bubble.running_processes,
            'open_files': bubble.open_files,
            'shell_history': bubble.shell_history,
            'terminal_state': bubble.terminal_state,
            'tags': bubble.tags,
            'version': bubble.version,
            'parent_bubble': bubble.parent_bubble
        }

        try:
            with open(bubble_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save bubble: {e}")

    def _load_bubble(self, bubble_id: str) -> Optional[BubbleState]:
        """Load bubble from disk."""
        bubble_file = self.bubbles_dir / f'{bubble_id}.json'

        if not bubble_file.exists():
            return None

        try:
            with open(bubble_file, 'r') as f:
                data = json.load(f)

            bubble = BubbleState(**data)
            bubble.created_at = datetime.fromisoformat(data['created_at'])
            return bubble
        except Exception:
            return None</content>
<parameter name="filePath">c:\Projects\Isaac2\isaac\bubbles\bubble_manager.py