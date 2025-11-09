"""
Workspace Bubbles - Complete workspace state capture and restoration
"""

import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import os
import psutil
import subprocess


@dataclass
class WorkspaceState:
    """Complete workspace state snapshot"""
    bubble_id: str
    timestamp: float
    name: str
    description: str

    # Core state components
    cwd: str
    git_branch: Optional[str]
    git_status: Dict[str, Any]
    environment: Dict[str, str]
    running_processes: List[Dict[str, Any]]
    open_files: List[str]

    # Additional state components
    recent_commands: Optional[List[str]] = None  # Recent shell commands
    background_jobs: Optional[List[Dict[str, Any]]] = None  # Background jobs
    system_info: Optional[Dict[str, Any]] = None  # System load, memory, etc.

    # Versioning
    version: int = 1  # Version number
    parent_id: Optional[str] = None  # ID of parent bubble for versioning

    # Metadata
    tags: Optional[List[str]] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.recent_commands is None:
            self.recent_commands = []
        if self.background_jobs is None:
            self.background_jobs = []
        if self.system_info is None:
            self.system_info = {}


class BubbleManager:
    """Manages workspace bubbles - complete state snapshots"""

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            isaac_dir = Path.home() / '.isaac'
            isaac_dir.mkdir(exist_ok=True)
            storage_path = isaac_dir / 'bubbles'

        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

    def create_bubble(self, name: str = "", description: str = "",
                     tags: Optional[List[str]] = None) -> WorkspaceState:
        """Create a new workspace bubble capturing current state"""

        # Generate unique ID
        bubble_id = str(uuid.uuid4())[:8]

        # Capture all state components
        state = WorkspaceState(
            bubble_id=bubble_id,
            timestamp=time.time(),
            name=name or f"Bubble {bubble_id}",
            description=description,
            cwd=os.getcwd(),
            git_branch=self._get_git_branch(),
            git_status=self._get_git_status(),
            environment=self._get_environment(),
            running_processes=self._get_running_processes(),
            open_files=self._get_open_files(),
            recent_commands=self._get_recent_commands(),
            background_jobs=self._get_background_jobs(),
            system_info=self._get_system_info(),
            tags=tags or []
        )

        # Save the bubble
        self._save_bubble(state)

        return state

    def list_bubbles(self) -> List[WorkspaceState]:
        """List all saved bubbles"""
        bubbles = []
        for bubble_file in self.storage_path.glob("*.json"):
            try:
                with open(bubble_file, 'r') as f:
                    data = json.load(f)
                    bubbles.append(WorkspaceState(**data))
            except Exception as e:
                print(f"Warning: Could not load bubble {bubble_file}: {e}")

        # Sort by timestamp (newest first)
        bubbles.sort(key=lambda b: b.timestamp, reverse=True)
        return bubbles

    def get_bubble(self, bubble_id: str) -> Optional[WorkspaceState]:
        """Get a specific bubble by ID"""
        bubble_file = self.storage_path / f"{bubble_id}.json"
        if bubble_file.exists():
            try:
                with open(bubble_file, 'r') as f:
                    data = json.load(f)
                    return WorkspaceState(**data)
            except Exception as e:
                print(f"Error loading bubble {bubble_id}: {e}")
        return None

    def delete_bubble(self, bubble_id: str) -> bool:
        """Delete a bubble"""
        bubble_file = self.storage_path / f"{bubble_id}.json"
        if bubble_file.exists():
            bubble_file.unlink()
            return True
        return False

    def restore_bubble(self, bubble_id: str) -> bool:
        """Restore workspace to bubble state"""
        bubble = self.get_bubble(bubble_id)
        if not bubble:
            return False

        try:
            # Change to the saved directory
            os.chdir(bubble.cwd)

            # Restore environment variables
            for key, value in bubble.environment.items():
                os.environ[key] = value

            # Note: We can't restore running processes or open files
            # as those are runtime state that may not be restorable

            print(f"Restored workspace to bubble '{bubble.name}'")
            return True

        except Exception as e:
            print(f"Error restoring bubble: {e}")
            return False

    def _save_bubble(self, state: WorkspaceState):
        """Save bubble to disk"""
        bubble_file = self.storage_path / f"{state.bubble_id}.json"
        with open(bubble_file, 'w') as f:
            json.dump(asdict(state), f, indent=2)

    def _get_git_branch(self) -> Optional[str]:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True, text=True, cwd=os.getcwd()
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    def _get_git_status(self) -> Dict[str, Any]:
        """Get git status information"""
        status = {
            'is_git_repo': False,
            'modified_files': [],
            'untracked_files': [],
            'staged_files': []
        }

        try:
            # Check if we're in a git repo
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True, text=True, cwd=os.getcwd()
            )

            if result.returncode == 0:
                status['is_git_repo'] = True

                for line in result.stdout.splitlines():
                    if line.startswith('M ') or line.startswith('MM '):
                        status['modified_files'].append(line[3:])
                    elif line.startswith('?? '):
                        status['untracked_files'].append(line[3:])
                    elif line.startswith('A ') or line.startswith('AM '):
                        status['staged_files'].append(line[3:])

        except:
            pass

        return status

    def _get_environment(self) -> Dict[str, str]:
        """Get relevant environment variables"""
        # Only capture important environment variables
        important_vars = [
            'PATH', 'PYTHONPATH', 'VIRTUAL_ENV', 'CONDA_DEFAULT_ENV',
            'NODE_ENV', 'JAVA_HOME', 'HOME', 'USER', 'SHELL'
        ]

        env = {}
        for var in important_vars:
            value = os.environ.get(var)
            if value:
                env[var] = value

        return env

    def _get_running_processes(self) -> List[Dict[str, Any]]:
        """Get information about running processes"""
        processes = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
                try:
                    info = proc.info
                    # Only include processes that might be relevant to development
                    if info['cwd'] and os.getcwd() in info['cwd']:
                        processes.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'cmdline': info['cmdline'] or [],
                            'cwd': info['cwd']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except:
            pass

        return processes[:20]  # Limit to 20 most relevant processes

    def _get_open_files(self) -> List[str]:
        """Get list of potentially open/active files (best effort)"""
        open_files = []
        os.getcwd()

        try:
            # Look for recently modified files (last 30 minutes)
            import glob
            recent_files = []
            cutoff_time = time.time() - (30 * 60)  # 30 minutes ago

            for pattern in ['**/*.py', '**/*.md', '**/*.txt', '**/*.json', '**/*.yaml', '**/*.yml']:
                for file_path in glob.glob(pattern, recursive=True):
                    if os.path.isfile(file_path):
                        mtime = os.path.getmtime(file_path)
                        if mtime > cutoff_time:
                            recent_files.append(file_path)

            # Sort by modification time (most recent first) and take top 10
            recent_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
            open_files = recent_files[:10]

            # Look for editor-specific indicators
            editor_indicators = [
                '.vscode/settings.json',
                '.vscode/workspace.code-workspace',
                '.idea/workspace.xml',
                '*.swp',  # vim swap files
                '*.tmp',  # temporary files
            ]

            for indicator in editor_indicators:
                for file_path in glob.glob(indicator, recursive=True):
                    if file_path not in open_files:
                        open_files.append(file_path)

        except Exception:
            # If anything fails, return empty list rather than crashing
            pass

        return open_files[:15]  # Limit to 15 files max

    def _get_recent_commands(self) -> List[str]:
        """Get recent shell commands (best effort)"""
        recent_commands = []

        try:
            # Try to read shell history files
            history_files = [
                os.path.expanduser('~/.bash_history'),
                os.path.expanduser('~/.zsh_history'),
                os.path.expanduser('~/.fish_history'),
                os.path.expanduser('~/AppData/Roaming/Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt'),  # PowerShell
            ]

            for history_file in history_files:
                if os.path.exists(history_file):
                    try:
                        with open(history_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            # Get last 10 commands
                            recent_commands = [line.strip() for line in lines[-10:] if line.strip()]
                            break  # Use first history file found
                    except:
                        continue

        except:
            pass

        return recent_commands

    def _get_background_jobs(self) -> List[Dict[str, Any]]:
        """Get background jobs/processes"""
        background_jobs = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
                try:
                    info = proc.info
                    # Look for background processes (not interactive shells)
                    if info['status'] in ['running', 'sleeping'] and info['cwd']:
                        # Simple heuristic: processes that might be background jobs
                        cmdline = info.get('cmdline', [])
                        if cmdline and not any(term in ' '.join(cmdline).lower() for term in ['powershell', 'bash', 'zsh', 'fish', 'cmd']):
                            background_jobs.append({
                                'pid': info['pid'],
                                'name': info['name'],
                                'cmdline': cmdline,
                                'cwd': info['cwd']
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except:
            pass

        return background_jobs[:10]  # Limit to 10 jobs

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        system_info = {}

        try:
            # CPU and memory info
            system_info['cpu_percent'] = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            system_info['memory_percent'] = memory.percent
            system_info['memory_used_gb'] = round(memory.used / (1024**3), 2)
            system_info['memory_total_gb'] = round(memory.total / (1024**3), 2)

            # Disk usage for current drive
            try:
                disk = psutil.disk_usage(os.getcwd())
                system_info['disk_percent'] = disk.percent
                system_info['disk_free_gb'] = round(disk.free / (1024**3), 2)
            except:
                pass

            # Network connections (simplified)
            try:
                connections = psutil.net_connections()
                system_info['network_connections'] = len(connections)
            except:
                pass

        except:
            pass

        return system_info

    def suspend_bubble(self, bubble_id: str, suspend_processes: bool = False) -> bool:
        """Suspend a workspace bubble (freeze state)"""
        bubble = self.get_bubble(bubble_id)
        if not bubble:
            return False

        try:
            # Ensure tags is a list
            if bubble.tags is None:
                bubble.tags = []

            # Mark bubble as suspended by adding metadata
            bubble.tags.append('suspended')
            bubble.description += ' [SUSPENDED]'

            if suspend_processes:
                # Attempt to suspend relevant processes
                suspended_pids = []
                for proc_info in bubble.running_processes:
                    pid = proc_info.get('pid')
                    if pid:
                        try:
                            proc = psutil.Process(pid)
                            if proc.status() == 'running':
                                proc.suspend()
                                suspended_pids.append(pid)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

                # Add suspension info to bubble
                bubble.tags.append(f'suspended_pids:{",".join(map(str, suspended_pids))}')

            # Save the updated bubble
            self._save_bubble(bubble)
            return True

        except Exception as e:
            print(f"Error suspending bubble: {e}")
            return False

            if suspend_processes:
                # Attempt to suspend relevant processes
                suspended_pids = []
                for proc_info in bubble.running_processes:
                    pid = proc_info.get('pid')
                    if pid:
                        try:
                            proc = psutil.Process(pid)
                            if proc.status() == 'running':
                                proc.suspend()
                                suspended_pids.append(pid)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

                # Add suspension info to bubble
                bubble.tags.append(f'suspended_pids:{",".join(map(str, suspended_pids))}')

            # Save the updated bubble
            self._save_bubble(bubble)
            return True

        except Exception as e:
            print(f"Error suspending bubble: {e}")
            return False

    def resume_bubble(self, bubble_id: str) -> bool:
        """Resume a suspended workspace bubble"""
        bubble = self.get_bubble(bubble_id)
        if not bubble:
            return False

        try:
            # Ensure tags is a list
            if bubble.tags is None:
                bubble.tags = []

            # Check if bubble is suspended
            if 'suspended' not in bubble.tags:
                return False

            # Resume suspended processes
            suspended_pid_tag = None
            for tag in bubble.tags:
                if tag.startswith('suspended_pids:'):
                    suspended_pid_tag = tag
                    break

            if suspended_pid_tag:
                pid_str = suspended_pid_tag.split(':', 1)[1]
                suspended_pids = [int(pid) for pid in pid_str.split(',') if pid]

                for pid in suspended_pids:
                    try:
                        proc = psutil.Process(pid)
                        if proc.status() == 'stopped':
                            proc.resume()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            # Remove suspension tags
            bubble.tags = [tag for tag in bubble.tags if not tag.startswith('suspended')]
            bubble.description = bubble.description.replace(' [SUSPENDED]', '')

            # Save the updated bubble
            self._save_bubble(bubble)
            return True

        except Exception as e:
            print(f"Error resuming bubble: {e}")
            return False

    def create_bubble_version(self, parent_bubble_id: str, name: Optional[str] = None,
                             description: Optional[str] = None) -> Optional[WorkspaceState]:
        """Create a new version of an existing bubble"""
        parent_bubble = self.get_bubble(parent_bubble_id)
        if not parent_bubble:
            return None

        # Create new bubble with updated state
        new_bubble = self.create_bubble(
            name=name or f"{parent_bubble.name} v{parent_bubble.version + 1}",
            description=description or f"Version {parent_bubble.version + 1} of {parent_bubble.name}",
            tags=parent_bubble.tags.copy() if parent_bubble.tags else []
        )

        # Set versioning info
        try:
            parent_version = int(parent_bubble.version) if isinstance(parent_bubble.version, str) else parent_bubble.version
        except (ValueError, TypeError):
            parent_version = 1

        new_bubble.version = parent_version + 1
        new_bubble.parent_id = parent_bubble_id

        # Save the updated bubble
        self._save_bubble(new_bubble)

        return new_bubble

    def get_bubble_versions(self, bubble_id: str) -> List[WorkspaceState]:
        """Get all versions of a bubble (including the original)"""
        versions = []

        # Find the root bubble
        current = self.get_bubble(bubble_id)
        if not current:
            return versions

        # Walk up to find the root
        root_id = bubble_id
        while current and current.parent_id:
            root_id = current.parent_id
            current = self.get_bubble(current.parent_id)

        # Now collect all versions from the root
        all_bubbles = self.list_bubbles()

        # Build version chain
        version_chain = {}
        for bubble in all_bubbles:
            if bubble.bubble_id == root_id or bubble.parent_id == root_id:
                version_chain[bubble.version] = bubble
            # Also check deeper chains
            current_check = bubble
            while current_check and current_check.parent_id:
                if current_check.parent_id == root_id:
                    version_chain[bubble.version] = bubble
                    break
                current_check = self.get_bubble(current_check.parent_id)

        # Return sorted by version (handle mixed types)
        def version_key(v):
            try:
                return int(v) if isinstance(v, str) else v
            except (ValueError, TypeError):
                return 0

        return [version_chain[v] for v in sorted(version_chain.keys(), key=version_key)]