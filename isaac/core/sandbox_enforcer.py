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
        workspace_config = config.get('workspace', {})
        self.workspace_enabled = workspace_config.get('enabled', False)
        self.workspace_root = Path(workspace_config.get('root_dir', '~/.isaac/workspaces')).expanduser()

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

    def create_user_workspace(self, name: str, create_venv: bool = False, create_collection: bool = False) -> Optional[Path]:
        """Create a new user workspace with optional venv and collection"""
        if not self.workspace_enabled:
            return None

        workspace_path = self.workspace_root / name
        try:
            workspace_path.mkdir(parents=True, exist_ok=True)
            
            # Optionally create virtual environment
            if create_venv:
                self._create_workspace_venv(workspace_path)
            
            # Optionally create xAI collection
            collection_id = None
            if create_collection:
                collection_id = self._create_workspace_collection(name)
            
            # Create workspace metadata
            from datetime import datetime
            metadata = {
                'name': name,
                'created_at': datetime.now().isoformat(),
                'collection_id': collection_id,
                'has_venv': create_venv
            }
            self._save_workspace_metadata(name, metadata)
            
            return workspace_path
        except Exception:
            return None

    def _create_workspace_venv(self, workspace_path: Path) -> bool:
        """Create a virtual environment in the workspace"""
        try:
            import subprocess
            import sys
            
            venv_path = workspace_path / '.venv'
            if venv_path.exists():
                return True  # Already exists
            
            # Create virtual environment
            result = subprocess.run([
                sys.executable, '-m', 'venv', str(venv_path)
            ], capture_output=True, text=True, cwd=str(workspace_path))
            
            if result.returncode == 0:
                # Create activation script for convenience
                self._create_venv_activation_script(workspace_path, venv_path)
                return True
            else:
                print(f"Warning: Failed to create venv: {result.stderr}")
                return False
        except Exception as e:
            print(f"Warning: Exception creating venv: {e}")
            return False

    def _create_venv_activation_script(self, workspace_path: Path, venv_path: Path):
        """Create a convenience activation script"""
        try:
            script_path = workspace_path / 'activate_venv.bat'  # Windows
            with open(script_path, 'w') as f:
                f.write('@echo off\n')
                f.write(f'call "{venv_path}\\Scripts\\activate.bat"\n')
                f.write('echo Virtual environment activated\n')
                f.write('echo Run "deactivate" to exit\n')
        except Exception:
            pass  # Non-critical, ignore errors

    def _create_workspace_collection(self, workspace_name: str) -> Optional[str]:
        """Create an xAI collection for the workspace"""
        try:
            # Import xAI client
            from xai_sdk import Client
            
            # Get xAI config from session
            config = self.session.get_config()
            xai_config = config.get('xai', {})
            collections_config = xai_config.get('collections', {})
            
            api_key = collections_config.get('api_key')
            management_api_key = collections_config.get('management_api_key', api_key)
            
            if not api_key:
                print("Warning: No xAI API key configured, skipping collection creation")
                return None
            
            # Initialize client
            api_host = collections_config.get('api_host', 'api.x.ai')
            management_api_host = collections_config.get('management_api_host', 'management-api.x.ai')
            timeout = collections_config.get('timeout_seconds', 3600)
            
            client = Client(
                api_key=api_key,
                management_api_key=management_api_key,
                api_host=api_host,
                management_api_host=management_api_host,
                timeout=timeout
            )
            
            # Create collection with workspace name
            collection_name = f"workspace-{workspace_name}"
            
            # Check if collection already exists
            collections_response = client.collections.list()
            if any(c.collection_name == collection_name for c in collections_response.collections):
                print(f"Warning: Collection '{collection_name}' already exists")
                # Find and return existing collection ID
                for c in collections_response.collections:
                    if c.collection_name == collection_name:
                        return c.collection_id
            
            # Create new collection
            collection = client.collections.create(name=collection_name)
            return collection.collection_id
            
        except ImportError:
            print("Warning: xai_sdk not available, skipping collection creation")
            return None
        except Exception as e:
            print(f"Warning: Failed to create workspace collection: {e}")
            return None

    def _save_workspace_metadata(self, workspace_name: str, metadata: dict):
        """Save workspace metadata to JSON file"""
        try:
            workspace_path = self.workspace_root / workspace_name
            metadata_file = workspace_path / '.workspace.json'
            
            with open(metadata_file, 'w') as f:
                import json
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save workspace metadata: {e}")

    def get_workspace_metadata(self, workspace_name: str) -> Optional[dict]:
        """Get workspace metadata"""
        try:
            workspace_path = self.workspace_root / workspace_name
            metadata_file = workspace_path / '.workspace.json'
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    import json
                    return json.load(f)
        except Exception:
            pass
        return None

    def get_workspace_collection_id(self, workspace_name: str) -> Optional[str]:
        """Get the collection ID associated with a workspace"""
        metadata = self.get_workspace_metadata(workspace_name)
        return metadata.get('collection_id') if metadata else None

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

    def switch_workspace(self, name: str, session=None) -> bool:
        """Switch to a different workspace (changes current directory)"""
        if not self.workspace_enabled:
            return False

        workspace_path = self.workspace_root / name
        if not workspace_path.exists() or not workspace_path.is_dir():
            return False

        try:
            import os
            os.chdir(str(workspace_path))
            # Update session with current workspace if session provided
            if session:
                session.current_workspace = name
            return True
        except Exception:
            return False

    def delete_workspace(self, name: str, preserve_collection: bool = False) -> bool:
        """Delete a workspace and optionally preserve its collection"""
        if not self.workspace_enabled:
            return False

        workspace_path = self.workspace_root / name
        if not workspace_path.exists():
            return False

        try:
            # Get workspace metadata before deletion
            metadata = self.get_workspace_metadata(name)
            
            # If preserving collection, just remove collection association
            if preserve_collection and metadata:
                metadata['collection_id'] = None
                self._save_workspace_metadata(name, metadata)
            
            # Delete the workspace directory
            import shutil
            shutil.rmtree(str(workspace_path))
            
            # Note: Collection is preserved in xAI (not deleted)
            return True
        except Exception:
            return False

    def create_workspace(self, name: str, create_venv: bool = False, create_collection: bool = False) -> bool:
        """Create a new workspace (alias for create_user_workspace)"""
        return self.create_user_workspace(name, create_venv, create_collection) is not None

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