"""
SandboxEnforcer - Implements sandbox isolation and security controls
SAFETY-CRITICAL: Enforces workspace isolation and prevents unsafe operations
"""

import shlex
from pathlib import Path
from typing import List, Optional


class SandboxEnforcer:
    """Enforces sandbox isolation and security policies"""

    # System paths that should be blocked
    BLOCKED_SYSTEM_PATHS = {
        # Unix-like systems
        '/etc', '/sys', '/proc', '/dev', '/boot', '/root', '/usr/sbin',
        # Windows systems
        'C:\\Windows', 'C:\\System32', 'C:\\Program Files', 'C:\\Program Files (x86)',
        'C:\\Users\\Administrator', 'C:\\Users\\Default', 'C:\\Users\\Public',
        # Common sensitive directories
        '/var/log', '/var/run', '/var/spool', '/var/lock',
        'C:\\ProgramData', 'C:\\$Recycle.Bin'
    }

    def __init__(self, session_manager):
        """Initialize with session manager for config access"""
        self.session = session_manager
        self._load_config()

    def _load_config(self):
        """Load sandbox configuration from session"""
        config = self.session.get_config()

        # Sandbox settings
        self.enabled = config.get('sandbox.enabled', False)
        self.root_dir = Path(config.get('sandbox.root_dir', '~/.isaac/sandboxes')).expanduser()
        self.block_system_paths = config.get('sandbox.block_system_paths', True)
        self.max_file_size_mb = config.get('sandbox.max_file_size_mb', 100)
        self.allowed_commands = set(config.get('sandbox.allowed_commands', ['pip', 'npm', 'git', 'python', 'node']))

        # Workspace settings
        self.workspace_enabled = config.get('workspace.enabled', False)
        self.workspace_root = Path(config.get('workspace.root_dir', '~/.isaac/workspaces')).expanduser()

    def is_sandbox_enabled(self) -> bool:
        """Check if sandbox is enabled"""
        return self.enabled

    def validate_path_access(self, path: str) -> bool:
        """Validate if a path is allowed for access"""
        if not self.enabled:
            return True  # No restrictions when disabled

        try:
            resolved_path = Path(path).resolve()
            path_str = str(resolved_path)

            # Block system paths if enabled
            if self.block_system_paths:
                for blocked_path in self.BLOCKED_SYSTEM_PATHS:
                    if path_str.startswith(blocked_path):
                        return False

            # Allow access within sandbox root
            if self.root_dir.exists() and resolved_path.is_relative_to(self.root_dir):
                return True

            # Allow access within workspace root if workspaces enabled
            if self.workspace_enabled and self.workspace_root.exists() and resolved_path.is_relative_to(self.workspace_root):
                return True

            # Allow access to user's home directory (but not system areas)
            home = Path.home()
            if resolved_path.is_relative_to(home):
                # Block sensitive home subdirectories
                sensitive_dirs = ['.ssh', '.gnupg', '.config/systemd', '.local/share/systemd']
                for sensitive in sensitive_dirs:
                    if resolved_path.is_relative_to(home / sensitive):
                        return False
                return True

            # Block everything else
            return False

        except (OSError, RuntimeError):
            # Path resolution failed - block access
            return False

    def validate_command(self, command: str) -> bool:
        """Validate if a command is allowed in sandbox"""
        if not self.enabled:
            return True

        try:
            # Parse the command to get the base command
            parts = shlex.split(command)
            if not parts:
                return False

            base_cmd = parts[0].lower()

            # Check against allowed commands
            if base_cmd in self.allowed_commands:
                return True

            # Allow full paths to allowed commands
            try:
                cmd_path = Path(base_cmd)
                if cmd_path.is_absolute():
                    cmd_name = cmd_path.name.lower()
                    if cmd_name in self.allowed_commands:
                        return True
            except Exception:
                pass

            return False

        except Exception:
            return False

    def validate_file_size(self, path: str) -> bool:
        """Validate file size is within limits"""
        if not self.enabled:
            return True

        try:
            file_path = Path(path)
            if file_path.exists() and file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                return size_mb <= self.max_file_size_mb
            return True  # Allow non-existent files or directories
        except Exception:
            return False

    def get_sandbox_root(self) -> Path:
        """Get the sandbox root directory"""
        return self.root_dir

    def get_workspace_root(self) -> Path:
        """Get the workspace root directory"""
        return self.workspace_root

    def create_sandbox_workspace(self, name: str) -> Optional[Path]:
        """Create a new sandbox workspace"""
        if not self.enabled:
            return None

        workspace_path = self.root_dir / name
        try:
            workspace_path.mkdir(parents=True, exist_ok=True)
            return workspace_path
        except Exception:
            return None

    def create_user_workspace(self, name: str) -> Optional[Path]:
        """Create a new user workspace"""
        if not self.workspace_enabled:
            return None

        workspace_path = self.workspace_root / name
        try:
            workspace_path.mkdir(parents=True, exist_ok=True)
            return workspace_path
        except Exception:
            return None

    def list_sandboxes(self) -> List[str]:
        """List available sandboxes"""
        if not self.root_dir.exists():
            return []

        try:
            return [d.name for d in self.root_dir.iterdir() if d.is_dir()]
        except Exception:
            return []

    def list_workspaces(self) -> List[str]:
        """List available workspaces"""
        if not self.workspace_root.exists():
            return []

        try:
            return [d.name for d in self.workspace_root.iterdir() if d.is_dir()]
        except Exception:
            return []

    def switch_workspace(self, name: str) -> bool:
        """Switch to a different workspace (changes current directory)"""
        if not self.workspace_enabled:
            return False

        workspace_path = self.workspace_root / name
        if not workspace_path.exists() or not workspace_path.is_dir():
            return False

        try:
            import os
            os.chdir(str(workspace_path))
            return True
        except Exception:
            return False

    def delete_workspace(self, name: str) -> bool:
        """Delete a workspace and all its contents"""
        if not self.workspace_enabled:
            return False

        workspace_path = self.workspace_root / name
        if not workspace_path.exists():
            return False

        try:
            import shutil
            shutil.rmtree(str(workspace_path))
            return True
        except Exception:
            return False

    def create_workspace(self, name: str) -> bool:
        """Create a new workspace (alias for create_user_workspace)"""
        return self.create_user_workspace(name) is not None

    def enforce_command(self, command: str, cwd: Optional[str] = None) -> Optional[str]:
        """Enforce sandbox rules on a command. Returns modified command or None if blocked."""
        if not self.enabled:
            return command

        # Validate the command itself
        if not self.validate_command(command):
            return None

        # If cwd is specified, validate it
        if cwd and not self.validate_path_access(cwd):
            return None

        # Command is allowed
        return command

    def enforce_file_access(self, path: str, operation: str = 'read') -> bool:
        """Enforce sandbox rules on file access"""
        if not self.enabled:
            return True

        # Validate path access
        if not self.validate_path_access(path):
            return False

        # Validate file size for read operations
        if operation in ('read', 'copy', 'move'):
            if not self.validate_file_size(path):
                return False

        return True