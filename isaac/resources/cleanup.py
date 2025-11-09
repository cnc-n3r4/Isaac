"""
Automatic Cleanup Manager

Smart garbage collection and resource cleanup.
"""

import os
import subprocess
import shutil
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json


@dataclass
class CleanupResult:
    """Result of a cleanup operation"""
    success: bool
    category: str
    description: str
    space_freed_mb: float
    items_cleaned: int
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class CleanupManager:
    """
    Manage automatic and manual resource cleanup

    Features:
    - Docker cleanup (images, containers, volumes)
    - Temp file cleanup
    - Package cache cleanup
    - Log rotation
    - Safe cleanup with confirmations
    - Cleanup history tracking
    """

    def __init__(self, history_file: Optional[str] = None):
        """Initialize cleanup manager"""
        if history_file is None:
            history_file = os.path.expanduser('~/.isaac/resources/cleanup_history.json')

        self.history_file = history_file
        self.cleanup_history: List[CleanupResult] = []
        self._load_history()

    def _load_history(self):
        """Load cleanup history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    # Note: We don't restore CleanupResult objects, just keep as dicts
                    self.cleanup_history = data.get('history', [])
            except (json.JSONDecodeError, KeyError):
                self.cleanup_history = []

    def _save_history(self):
        """Save cleanup history to file"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

        data = {
            'last_updated': datetime.now().isoformat(),
            'history': [
                r.to_dict() if isinstance(r, CleanupResult) else r
                for r in self.cleanup_history
            ]
        }

        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _add_result(self, result: CleanupResult):
        """Add cleanup result to history"""
        self.cleanup_history.append(result)
        self._save_history()

    def cleanup_docker_images(self, dangling_only: bool = True) -> CleanupResult:
        """
        Clean up Docker images

        Args:
            dangling_only: If True, only remove dangling images. If False, remove all unused images.

        Returns:
            CleanupResult
        """
        try:
            if dangling_only:
                # Count dangling images first
                count_result = subprocess.run(
                    ['docker', 'images', '-f', 'dangling=true', '-q'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                count = len(count_result.stdout.strip().split('\n')) if count_result.stdout.strip() else 0

                # Prune dangling images
                result = subprocess.run(
                    ['docker', 'image', 'prune', '-f'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                # Prune all unused images
                result = subprocess.run(
                    ['docker', 'image', 'prune', '-a', '-f'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                count = -1  # Unknown count for all images

            if result.returncode == 0:
                # Try to parse space reclaimed from output
                space_freed_mb = 0
                output = result.stdout

                if 'Total reclaimed space:' in output:
                    # Parse space from output like "Total reclaimed space: 1.234GB"
                    try:
                        space_line = [line for line in output.split('\n') if 'Total reclaimed space:' in line][0]
                        space_str = space_line.split(':')[1].strip()

                        if 'GB' in space_str:
                            space_freed_mb = float(space_str.replace('GB', '')) * 1024
                        elif 'MB' in space_str:
                            space_freed_mb = float(space_str.replace('MB', ''))
                        elif 'kB' in space_str:
                            space_freed_mb = float(space_str.replace('kB', '')) / 1024
                    except (IndexError, ValueError):
                        pass

                cleanup_result = CleanupResult(
                    success=True,
                    category='docker',
                    description=f'Cleaned up {"dangling" if dangling_only else "unused"} Docker images',
                    space_freed_mb=space_freed_mb,
                    items_cleaned=count if count >= 0 else 0
                )
            else:
                cleanup_result = CleanupResult(
                    success=False,
                    category='docker',
                    description='Failed to clean Docker images',
                    space_freed_mb=0,
                    items_cleaned=0,
                    error=result.stderr
                )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            cleanup_result = CleanupResult(
                success=False,
                category='docker',
                description='Docker not available',
                space_freed_mb=0,
                items_cleaned=0,
                error=str(e)
            )

        self._add_result(cleanup_result)
        return cleanup_result

    def cleanup_docker_containers(self) -> CleanupResult:
        """Clean up stopped Docker containers"""
        try:
            # Count stopped containers
            count_result = subprocess.run(
                ['docker', 'ps', '-a', '-f', 'status=exited', '-q'],
                capture_output=True,
                text=True,
                timeout=5
            )
            count = len(count_result.stdout.strip().split('\n')) if count_result.stdout.strip() else 0

            # Prune stopped containers
            result = subprocess.run(
                ['docker', 'container', 'prune', '-f'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                space_freed_mb = 0
                output = result.stdout

                if 'Total reclaimed space:' in output:
                    try:
                        space_line = [line for line in output.split('\n') if 'Total reclaimed space:' in line][0]
                        space_str = space_line.split(':')[1].strip()

                        if 'GB' in space_str:
                            space_freed_mb = float(space_str.replace('GB', '')) * 1024
                        elif 'MB' in space_str:
                            space_freed_mb = float(space_str.replace('MB', ''))
                    except (IndexError, ValueError):
                        pass

                cleanup_result = CleanupResult(
                    success=True,
                    category='docker',
                    description='Cleaned up stopped Docker containers',
                    space_freed_mb=space_freed_mb,
                    items_cleaned=count
                )
            else:
                cleanup_result = CleanupResult(
                    success=False,
                    category='docker',
                    description='Failed to clean Docker containers',
                    space_freed_mb=0,
                    items_cleaned=0,
                    error=result.stderr
                )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            cleanup_result = CleanupResult(
                success=False,
                category='docker',
                description='Docker not available',
                space_freed_mb=0,
                items_cleaned=0,
                error=str(e)
            )

        self._add_result(cleanup_result)
        return cleanup_result

    def cleanup_docker_volumes(self) -> CleanupResult:
        """Clean up unused Docker volumes"""
        try:
            # Count unused volumes
            count_result = subprocess.run(
                ['docker', 'volume', 'ls', '-f', 'dangling=true', '-q'],
                capture_output=True,
                text=True,
                timeout=5
            )
            count = len(count_result.stdout.strip().split('\n')) if count_result.stdout.strip() else 0

            # Prune volumes
            result = subprocess.run(
                ['docker', 'volume', 'prune', '-f'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                space_freed_mb = 0
                output = result.stdout

                if 'Total reclaimed space:' in output:
                    try:
                        space_line = [line for line in output.split('\n') if 'Total reclaimed space:' in line][0]
                        space_str = space_line.split(':')[1].strip()

                        if 'GB' in space_str:
                            space_freed_mb = float(space_str.replace('GB', '')) * 1024
                        elif 'MB' in space_str:
                            space_freed_mb = float(space_str.replace('MB', ''))
                    except (IndexError, ValueError):
                        pass

                cleanup_result = CleanupResult(
                    success=True,
                    category='docker',
                    description='Cleaned up unused Docker volumes',
                    space_freed_mb=space_freed_mb,
                    items_cleaned=count
                )
            else:
                cleanup_result = CleanupResult(
                    success=False,
                    category='docker',
                    description='Failed to clean Docker volumes',
                    space_freed_mb=0,
                    items_cleaned=0,
                    error=result.stderr
                )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            cleanup_result = CleanupResult(
                success=False,
                category='docker',
                description='Docker not available',
                space_freed_mb=0,
                items_cleaned=0,
                error=str(e)
            )

        self._add_result(cleanup_result)
        return cleanup_result

    def cleanup_package_cache(self, package_manager: str) -> CleanupResult:
        """
        Clean package manager cache

        Args:
            package_manager: 'pip', 'npm', or 'apt'

        Returns:
            CleanupResult
        """
        commands = {
            'pip': ['pip', 'cache', 'purge'],
            'npm': ['npm', 'cache', 'clean', '--force'],
            'apt': ['sudo', 'apt-get', 'clean']
        }

        if package_manager not in commands:
            cleanup_result = CleanupResult(
                success=False,
                category='package_cache',
                description=f'Unknown package manager: {package_manager}',
                space_freed_mb=0,
                items_cleaned=0,
                error='Invalid package manager'
            )
            self._add_result(cleanup_result)
            return cleanup_result

        try:
            result = subprocess.run(
                commands[package_manager],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                cleanup_result = CleanupResult(
                    success=True,
                    category='package_cache',
                    description=f'Cleaned {package_manager} cache',
                    space_freed_mb=0,  # Hard to measure precisely
                    items_cleaned=1
                )
            else:
                cleanup_result = CleanupResult(
                    success=False,
                    category='package_cache',
                    description=f'Failed to clean {package_manager} cache',
                    space_freed_mb=0,
                    items_cleaned=0,
                    error=result.stderr
                )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            cleanup_result = CleanupResult(
                success=False,
                category='package_cache',
                description=f'{package_manager} not available',
                space_freed_mb=0,
                items_cleaned=0,
                error=str(e)
            )

        self._add_result(cleanup_result)
        return cleanup_result

    def cleanup_temp_files(self, older_than_days: int = 7) -> CleanupResult:
        """
        Clean old temporary files

        Args:
            older_than_days: Remove files older than this many days

        Returns:
            CleanupResult
        """
        temp_dir = '/tmp'
        cutoff_time = datetime.now() - timedelta(days=older_than_days)

        try:
            space_freed = 0
            files_removed = 0

            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)

                try:
                    # Skip if not owned by current user
                    if os.stat(filepath).st_uid != os.getuid():
                        continue

                    # Check file age
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

                    if mtime < cutoff_time:
                        # Get size before removing
                        if os.path.isfile(filepath):
                            size = os.path.getsize(filepath)
                            os.remove(filepath)
                            space_freed += size
                            files_removed += 1
                        elif os.path.isdir(filepath):
                            size = sum(
                                os.path.getsize(os.path.join(dirpath, f))
                                for dirpath, _, filenames in os.walk(filepath)
                                for f in filenames
                            )
                            shutil.rmtree(filepath)
                            space_freed += size
                            files_removed += 1

                except (OSError, PermissionError):
                    continue

            cleanup_result = CleanupResult(
                success=True,
                category='temp_files',
                description=f'Cleaned temp files older than {older_than_days} days',
                space_freed_mb=space_freed / (1024 * 1024),
                items_cleaned=files_removed
            )

        except Exception as e:
            cleanup_result = CleanupResult(
                success=False,
                category='temp_files',
                description='Failed to clean temp files',
                space_freed_mb=0,
                items_cleaned=0,
                error=str(e)
            )

        self._add_result(cleanup_result)
        return cleanup_result

    def cleanup_all_docker(self) -> List[CleanupResult]:
        """Clean all Docker resources"""
        results = [
            self.cleanup_docker_containers(),
            self.cleanup_docker_images(dangling_only=True),
            self.cleanup_docker_volumes()
        ]
        return results

    def get_cleanup_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent cleanup history"""
        history = self.cleanup_history[-limit:] if limit > 0 else self.cleanup_history
        return [h.to_dict() if isinstance(h, CleanupResult) else h for h in reversed(history)]

    def get_total_space_freed(self) -> float:
        """Get total space freed across all cleanups (in MB)"""
        total = 0
        for result in self.cleanup_history:
            if isinstance(result, CleanupResult):
                total += result.space_freed_mb
            elif isinstance(result, dict):
                total += result.get('space_freed_mb', 0)
        return total
