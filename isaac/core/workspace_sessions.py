#!/usr/bin/env python3
"""
Workspace Sessions Manager - Automatic workspace detection and AI session binding

Manages the relationship between workspaces, AI sessions, and knowledge bases.
Enables seamless switching between projects with preserved context.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkspaceSessionManager:
    """
    Manages workspace-to-session bindings

    Features:
    - Automatic workspace detection (git root, project markers)
    - Session binding per workspace
    - Knowledge base association
    - Workspace switching with context preservation
    - Persistent workspace metadata
    """

    # Files that indicate a project root
    PROJECT_MARKERS = {
        '.git',
        '.isaac',
        'package.json',
        'pyproject.toml',
        'Cargo.toml',
        'go.mod',
        'pom.xml',
        'build.gradle',
        'Makefile',
        'CMakeLists.txt'
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize workspace sessions manager

        Args:
            config_path: Path to workspace configuration file
        """
        if config_path is None:
            config_path = Path.home() / '.isaac' / 'workspaces.json'

        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Workspace metadata: workspace_path -> metadata
        self.workspaces: Dict[str, Dict[str, Any]] = {}

        # Current workspace
        self.current_workspace: Optional[str] = None

        # Load existing workspaces
        self._load_workspaces()

        logger.info(f"Workspace sessions manager initialized at {config_path}")

    def _load_workspaces(self):
        """Load workspace metadata from disk"""
        if not self.config_path.exists():
            logger.info("No existing workspaces file, starting fresh")
            return

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            self.workspaces = data.get('workspaces', {})
            self.current_workspace = data.get('current_workspace')

            logger.info(f"Loaded {len(self.workspaces)} workspace(s)")

        except Exception as e:
            logger.error(f"Failed to load workspaces: {e}")
            self.workspaces = {}

    def _save_workspaces(self):
        """Persist workspace metadata to disk"""
        try:
            data = {
                'workspaces': self.workspaces,
                'current_workspace': self.current_workspace,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self.workspaces)} workspace(s)")

        except Exception as e:
            logger.error(f"Failed to save workspaces: {e}")

    def detect_workspace(self, path: Optional[Path] = None) -> Optional[Path]:
        """
        Detect workspace root from current or given path

        Searches upward from path looking for project markers.

        Args:
            path: Starting path (default: current directory)

        Returns:
            Workspace root path or None
        """
        if path is None:
            path = Path.cwd()
        else:
            path = Path(path).resolve()

        # Search upward for project markers
        current = path
        while current != current.parent:
            # Check for project markers
            for marker in self.PROJECT_MARKERS:
                marker_path = current / marker
                if marker_path.exists():
                    logger.debug(f"Detected workspace at {current} (marker: {marker})")
                    return current

            # Move up one directory
            current = current.parent

        # No workspace detected
        logger.debug(f"No workspace detected from {path}")
        return None

    def get_workspace_name(self, workspace_path: Path) -> str:
        """
        Generate friendly workspace name from path

        Args:
            workspace_path: Workspace root path

        Returns:
            Workspace name (directory name + hash for uniqueness)
        """
        import hashlib

        path_str = str(workspace_path)
        path_hash = hashlib.sha256(path_str.encode()).hexdigest()[:8]

        # Use directory name + hash
        name = f"{workspace_path.name}_{path_hash}"

        return name

    def register_workspace(self, workspace_path: Path,
                          session_id: Optional[str] = None,
                          collection_id: Optional[str] = None) -> str:
        """
        Register a workspace with optional session/collection binding

        Args:
            workspace_path: Workspace root path
            session_id: Optional AI session ID
            collection_id: Optional xAI collection ID

        Returns:
            Workspace name
        """
        workspace_path = workspace_path.resolve()
        workspace_key = str(workspace_path)

        # Generate workspace name
        workspace_name = self.get_workspace_name(workspace_path)

        # Create or update metadata
        if workspace_key not in self.workspaces:
            self.workspaces[workspace_key] = {
                'name': workspace_name,
                'path': workspace_key,
                'created_at': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'session_id': session_id,
                'collection_id': collection_id
            }
            logger.info(f"Registered new workspace: {workspace_name} at {workspace_path}")
        else:
            # Update existing
            workspace_data = self.workspaces[workspace_key]
            workspace_data['last_accessed'] = datetime.now().isoformat()

            if session_id:
                workspace_data['session_id'] = session_id

            if collection_id:
                workspace_data['collection_id'] = collection_id

            logger.debug(f"Updated workspace: {workspace_name}")

        self._save_workspaces()
        return workspace_name

    def get_workspace_info(self, workspace_path: Path) -> Optional[Dict[str, Any]]:
        """
        Get workspace metadata

        Args:
            workspace_path: Workspace root path

        Returns:
            Workspace metadata or None if not registered
        """
        workspace_key = str(workspace_path.resolve())

        if workspace_key not in self.workspaces:
            return None

        return self.workspaces[workspace_key].copy()

    def switch_workspace(self, workspace_path: Path) -> Tuple[bool, str]:
        """
        Switch to a different workspace

        Args:
            workspace_path: Target workspace path

        Returns:
            Tuple of (success, message)
        """
        workspace_path = workspace_path.resolve()

        # Verify workspace exists
        if not workspace_path.exists():
            return False, f"Workspace path does not exist: {workspace_path}"

        # Register if not already registered
        workspace_key = str(workspace_path)
        if workspace_key not in self.workspaces:
            self.register_workspace(workspace_path)

        # Switch
        old_workspace = self.current_workspace
        self.current_workspace = workspace_key

        # Update last accessed
        self.workspaces[workspace_key]['last_accessed'] = datetime.now().isoformat()

        self._save_workspaces()

        workspace_name = self.workspaces[workspace_key]['name']

        if old_workspace:
            old_name = self.workspaces[old_workspace]['name'] if old_workspace in self.workspaces else 'unknown'
            logger.info(f"Switched workspace: {old_name} → {workspace_name}")
            return True, f"Switched from '{old_name}' to '{workspace_name}'"
        else:
            logger.info(f"Activated workspace: {workspace_name}")
            return True, f"Activated workspace '{workspace_name}'"

    def get_current_workspace(self) -> Optional[Dict[str, Any]]:
        """
        Get current workspace metadata

        Returns:
            Current workspace data or None
        """
        if not self.current_workspace:
            return None

        if self.current_workspace not in self.workspaces:
            return None

        return self.workspaces[self.current_workspace].copy()

    def bind_session(self, workspace_path: Path, session_id: str):
        """
        Bind AI session to workspace

        Args:
            workspace_path: Workspace root path
            session_id: AI session ID
        """
        workspace_key = str(workspace_path.resolve())

        if workspace_key not in self.workspaces:
            self.register_workspace(workspace_path, session_id=session_id)
        else:
            self.workspaces[workspace_key]['session_id'] = session_id
            self._save_workspaces()

        logger.info(f"Bound session {session_id} to workspace {workspace_path.name}")

    def bind_collection(self, workspace_path: Path, collection_id: str):
        """
        Bind xAI collection to workspace

        Args:
            workspace_path: Workspace root path
            collection_id: Collection ID
        """
        workspace_key = str(workspace_path.resolve())

        if workspace_key not in self.workspaces:
            self.register_workspace(workspace_path, collection_id=collection_id)
        else:
            self.workspaces[workspace_key]['collection_id'] = collection_id
            self._save_workspaces()

        logger.info(f"Bound collection {collection_id} to workspace {workspace_path.name}")

    def get_session_for_workspace(self, workspace_path: Path) -> Optional[str]:
        """
        Get AI session ID for workspace

        Args:
            workspace_path: Workspace root path

        Returns:
            Session ID or None
        """
        workspace_key = str(workspace_path.resolve())

        if workspace_key not in self.workspaces:
            return None

        return self.workspaces[workspace_key].get('session_id')

    def get_collection_for_workspace(self, workspace_path: Path) -> Optional[str]:
        """
        Get collection ID for workspace

        Args:
            workspace_path: Workspace root path

        Returns:
            Collection ID or None
        """
        workspace_key = str(workspace_path.resolve())

        if workspace_key not in self.workspaces:
            return None

        return self.workspaces[workspace_key].get('collection_id')

    def list_workspaces(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered workspaces

        Returns:
            Dict mapping workspace path to metadata
        """
        return self.workspaces.copy()

    def cleanup_invalid_workspaces(self) -> int:
        """
        Remove workspaces with invalid paths

        Returns:
            Number of workspaces removed
        """
        invalid = []

        for workspace_key in self.workspaces.keys():
            path = Path(workspace_key)
            if not path.exists():
                invalid.append(workspace_key)

        for workspace_key in invalid:
            logger.info(f"Removing invalid workspace: {workspace_key}")
            del self.workspaces[workspace_key]

        if invalid:
            self._save_workspaces()

        return len(invalid)

    def auto_detect_and_switch(self, path: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
        """
        Auto-detect workspace and switch to it

        Args:
            path: Starting path (default: current directory)

        Returns:
            Tuple of (success, workspace_name or None)
        """
        workspace_path = self.detect_workspace(path)

        if not workspace_path:
            return False, None

        success, message = self.switch_workspace(workspace_path)

        if success:
            workspace_name = self.workspaces[str(workspace_path)]['name']
            return True, workspace_name

        return False, None


# Global instance (lazy loaded)
_workspace_manager: Optional[WorkspaceSessionManager] = None


def get_workspace_manager() -> WorkspaceSessionManager:
    """Get or create global workspace manager instance"""
    global _workspace_manager

    if _workspace_manager is None:
        _workspace_manager = WorkspaceSessionManager()

    return _workspace_manager


if __name__ == '__main__':
    # Test the workspace manager
    import sys
    logging.basicConfig(level=logging.DEBUG)

    manager = WorkspaceSessionManager()

    print("=== Workspace Sessions Manager Test ===\n")

    # Detect current workspace
    workspace = manager.detect_workspace()
    if workspace:
        print(f"Detected workspace: {workspace}")

        # Register it
        name = manager.register_workspace(
            workspace,
            session_id="test_session_123",
            collection_id="test_collection_456"
        )
        print(f"Registered as: {name}")

        # Get info
        info = manager.get_workspace_info(workspace)
        if info:
            print(f"\nWorkspace info:")
            for key, value in info.items():
                print(f"  {key}: {value}")

        # Test bindings
        session_id = manager.get_session_for_workspace(workspace)
        collection_id = manager.get_collection_for_workspace(workspace)
        print(f"\nBindings:")
        print(f"  Session ID: {session_id}")
        print(f"  Collection ID: {collection_id}")

    else:
        print("No workspace detected")

    # List all workspaces
    print(f"\nAll workspaces: {len(manager.list_workspaces())}")
    for ws_path, ws_data in manager.list_workspaces().items():
        print(f"  {ws_data['name']}: {ws_path}")

    print(f"\n✓ Workspace metadata saved to: {manager.config_path}")
