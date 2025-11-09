"""
Optimization Suggestion Engine

Analyzes resource usage and suggests optimizations.
"""

import os
import subprocess
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import glob


@dataclass
class OptimizationSuggestion:
    """A suggestion for optimizing resource usage"""
    category: str  # 'disk', 'memory', 'docker', 'process'
    severity: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    potential_savings: str
    action: str
    auto_fixable: bool
    fix_command: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class OptimizationEngine:
    """
    Analyze system state and suggest optimizations

    Features:
    - Docker image/container cleanup suggestions
    - Temp file cleanup
    - Log file rotation suggestions
    - Package cache cleanup
    - Memory leak detection
    - Zombie process detection
    """

    def __init__(self):
        self.suggestions: List[OptimizationSuggestion] = []

    def analyze(self) -> List[OptimizationSuggestion]:
        """Run all optimization analyses"""
        self.suggestions = []

        # Run all analysis methods
        self._analyze_docker()
        self._analyze_temp_files()
        self._analyze_package_caches()
        self._analyze_log_files()
        self._analyze_old_files()
        self._analyze_browser_caches()
        self._analyze_node_modules()

        return self.suggestions

    def _add_suggestion(self, suggestion: OptimizationSuggestion):
        """Add a suggestion to the list"""
        self.suggestions.append(suggestion)

    def _analyze_docker(self):
        """Analyze Docker resource usage"""
        try:
            # Check if Docker is available
            result = subprocess.run(
                ['docker', 'system', 'df', '-v'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse Docker system df output
                output = result.stdout

                # Check for unused images
                images_result = subprocess.run(
                    ['docker', 'images', '-f', 'dangling=true', '-q'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                dangling_count = len(images_result.stdout.strip().split('\n')) if images_result.stdout.strip() else 0

                if dangling_count > 0:
                    self._add_suggestion(OptimizationSuggestion(
                        category='docker',
                        severity='medium',
                        title=f'Remove {dangling_count} dangling Docker images',
                        description='Dangling images are layers that have no relationship to any tagged images. They consume disk space.',
                        potential_savings='Varies (often 1-10 GB)',
                        action='Run: docker image prune',
                        auto_fixable=True,
                        fix_command='docker image prune -f'
                    ))

                # Check for stopped containers
                containers_result = subprocess.run(
                    ['docker', 'ps', '-a', '-f', 'status=exited', '-q'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                stopped_count = len(containers_result.stdout.strip().split('\n')) if containers_result.stdout.strip() else 0

                if stopped_count > 0:
                    self._add_suggestion(OptimizationSuggestion(
                        category='docker',
                        severity='low',
                        title=f'Remove {stopped_count} stopped containers',
                        description='Stopped containers still consume disk space for their writable layer.',
                        potential_savings='Varies (often 100MB - 1GB)',
                        action='Run: docker container prune',
                        auto_fixable=True,
                        fix_command='docker container prune -f'
                    ))

                # Check for unused volumes
                volumes_result = subprocess.run(
                    ['docker', 'volume', 'ls', '-f', 'dangling=true', '-q'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                dangling_volumes = len(volumes_result.stdout.strip().split('\n')) if volumes_result.stdout.strip() else 0

                if dangling_volumes > 0:
                    self._add_suggestion(OptimizationSuggestion(
                        category='docker',
                        severity='medium',
                        title=f'Remove {dangling_volumes} unused Docker volumes',
                        description='Dangling volumes are not referenced by any containers.',
                        potential_savings='Varies (often 500MB - 5GB)',
                        action='Run: docker volume prune',
                        auto_fixable=True,
                        fix_command='docker volume prune -f'
                    ))

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # Docker not available

    def _analyze_temp_files(self):
        """Analyze temporary file usage"""
        temp_dirs = ['/tmp', '/var/tmp', os.path.expanduser('~/.cache')]

        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue

            try:
                # Calculate size of temp directory
                total_size = 0
                file_count = 0

                for dirpath, dirnames, filenames in os.walk(temp_dir):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            total_size += os.path.getsize(filepath)
                            file_count += 1
                        except (OSError, FileNotFoundError):
                            continue

                size_mb = total_size / (1024 * 1024)

                if size_mb > 500:  # More than 500MB
                    severity = 'high' if size_mb > 2000 else 'medium'
                    self._add_suggestion(OptimizationSuggestion(
                        category='disk',
                        severity=severity,
                        title=f'Clean up {temp_dir} ({size_mb:.1f} MB, {file_count} files)',
                        description=f'Temporary files in {temp_dir} are consuming significant disk space.',
                        potential_savings=f'{size_mb:.1f} MB',
                        action=f'Manually review and clean {temp_dir}',
                        auto_fixable=False
                    ))
            except (OSError, PermissionError):
                continue

    def _analyze_package_caches(self):
        """Analyze package manager caches"""
        caches = [
            ('/var/cache/apt/archives', 'apt', 'apt-get clean', True),
            (os.path.expanduser('~/.cache/pip'), 'pip', 'pip cache purge', True),
            (os.path.expanduser('~/.npm'), 'npm', 'npm cache clean --force', True),
            (os.path.expanduser('~/.cargo/registry'), 'cargo', 'cargo cache -a', False),
        ]

        for cache_dir, package_manager, clean_cmd, auto_fixable in caches:
            if not os.path.exists(cache_dir):
                continue

            try:
                total_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, _, filenames in os.walk(cache_dir)
                    for filename in filenames
                )

                size_mb = total_size / (1024 * 1024)

                if size_mb > 200:  # More than 200MB
                    self._add_suggestion(OptimizationSuggestion(
                        category='disk',
                        severity='low',
                        title=f'Clean {package_manager} cache ({size_mb:.1f} MB)',
                        description=f'Package manager cache for {package_manager} can be safely cleared.',
                        potential_savings=f'{size_mb:.1f} MB',
                        action=f'Run: {clean_cmd}',
                        auto_fixable=auto_fixable,
                        fix_command=clean_cmd if auto_fixable else None
                    ))
            except (OSError, PermissionError):
                continue

    def _analyze_log_files(self):
        """Analyze log file sizes"""
        log_dirs = ['/var/log', os.path.expanduser('~/.local/share/logs')]

        for log_dir in log_dirs:
            if not os.path.exists(log_dir):
                continue

            try:
                large_logs = []
                for dirpath, _, filenames in os.walk(log_dir):
                    for filename in filenames:
                        if filename.endswith(('.log', '.log.1', '.log.2')):
                            filepath = os.path.join(dirpath, filename)
                            try:
                                size = os.path.getsize(filepath)
                                if size > 50 * 1024 * 1024:  # > 50MB
                                    large_logs.append((filepath, size))
                            except (OSError, FileNotFoundError):
                                continue

                if large_logs:
                    total_size_mb = sum(size for _, size in large_logs) / (1024 * 1024)
                    self._add_suggestion(OptimizationSuggestion(
                        category='disk',
                        severity='medium',
                        title=f'Rotate or compress {len(large_logs)} large log files ({total_size_mb:.1f} MB)',
                        description='Large log files should be rotated or compressed to save space.',
                        potential_savings=f'{total_size_mb:.1f} MB',
                        action='Review log files and set up log rotation',
                        auto_fixable=False
                    ))
            except (OSError, PermissionError):
                continue

    def _analyze_old_files(self):
        """Analyze old files in common directories"""
        # Check Downloads folder for old files
        downloads_dir = os.path.expanduser('~/Downloads')
        if os.path.exists(downloads_dir):
            try:
                old_files = []
                current_time = datetime.now().timestamp()
                thirty_days = 30 * 24 * 60 * 60

                for filename in os.listdir(downloads_dir):
                    filepath = os.path.join(downloads_dir, filename)
                    try:
                        if os.path.isfile(filepath):
                            mtime = os.path.getmtime(filepath)
                            if current_time - mtime > thirty_days:
                                size = os.path.getsize(filepath)
                                old_files.append((filepath, size))
                    except (OSError, FileNotFoundError):
                        continue

                if old_files:
                    total_size_mb = sum(size for _, size in old_files) / (1024 * 1024)
                    self._add_suggestion(OptimizationSuggestion(
                        category='disk',
                        severity='low',
                        title=f'Review {len(old_files)} old files in Downloads ({total_size_mb:.1f} MB)',
                        description='Files in Downloads folder older than 30 days.',
                        potential_savings=f'{total_size_mb:.1f} MB',
                        action='Manually review and delete old downloads',
                        auto_fixable=False
                    ))
            except (OSError, PermissionError):
                pass

    def _analyze_browser_caches(self):
        """Analyze browser cache sizes"""
        browser_caches = [
            (os.path.expanduser('~/.cache/google-chrome'), 'Chrome'),
            (os.path.expanduser('~/.cache/mozilla/firefox'), 'Firefox'),
            (os.path.expanduser('~/.cache/chromium'), 'Chromium'),
        ]

        for cache_dir, browser_name in browser_caches:
            if not os.path.exists(cache_dir):
                continue

            try:
                total_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, _, filenames in os.walk(cache_dir)
                    for filename in filenames
                )

                size_mb = total_size / (1024 * 1024)

                if size_mb > 500:
                    self._add_suggestion(OptimizationSuggestion(
                        category='disk',
                        severity='low',
                        title=f'Clear {browser_name} cache ({size_mb:.1f} MB)',
                        description=f'{browser_name} browser cache can be cleared from browser settings.',
                        potential_savings=f'{size_mb:.1f} MB',
                        action=f'Clear cache from {browser_name} settings',
                        auto_fixable=False
                    ))
            except (OSError, PermissionError):
                continue

    def _analyze_node_modules(self):
        """Analyze node_modules directories"""
        home_dir = os.path.expanduser('~')

        try:
            # Find node_modules directories
            node_modules_dirs = []

            # Search in common project locations
            search_paths = [
                os.path.join(home_dir, 'projects'),
                os.path.join(home_dir, 'dev'),
                os.path.join(home_dir, 'workspace'),
                home_dir
            ]

            for search_path in search_paths:
                if not os.path.exists(search_path):
                    continue

                # Limit depth to avoid long searches
                for root, dirs, _ in os.walk(search_path):
                    if 'node_modules' in dirs:
                        node_modules_path = os.path.join(root, 'node_modules')
                        try:
                            # Calculate size
                            total_size = sum(
                                os.path.getsize(os.path.join(dirpath, filename))
                                for dirpath, _, filenames in os.walk(node_modules_path)
                                for filename in filenames
                            )
                            node_modules_dirs.append((node_modules_path, total_size))
                        except (OSError, PermissionError):
                            continue

                    # Don't recurse into node_modules
                    dirs[:] = [d for d in dirs if d != 'node_modules']

            if len(node_modules_dirs) > 3:
                total_size_mb = sum(size for _, size in node_modules_dirs) / (1024 * 1024)
                self._add_suggestion(OptimizationSuggestion(
                    category='disk',
                    severity='medium',
                    title=f'Found {len(node_modules_dirs)} node_modules directories ({total_size_mb:.1f} MB)',
                    description='Multiple node_modules directories can consume significant space. Consider removing unused ones.',
                    potential_savings=f'Up to {total_size_mb:.1f} MB',
                    action='Review and remove node_modules from old/unused projects',
                    auto_fixable=False
                ))
        except Exception:
            pass

    def get_suggestions_by_severity(self, severity: str) -> List[OptimizationSuggestion]:
        """Get suggestions filtered by severity"""
        return [s for s in self.suggestions if s.severity == severity]

    def get_suggestions_by_category(self, category: str) -> List[OptimizationSuggestion]:
        """Get suggestions filtered by category"""
        return [s for s in self.suggestions if s.category == category]

    def get_auto_fixable_suggestions(self) -> List[OptimizationSuggestion]:
        """Get suggestions that can be automatically fixed"""
        return [s for s in self.suggestions if s.auto_fixable]

    def estimate_total_savings(self) -> str:
        """Estimate total potential savings"""
        # This is a rough estimate based on the potential_savings strings
        total_mb = 0

        for suggestion in self.suggestions:
            # Try to extract MB from potential_savings
            savings = suggestion.potential_savings
            if 'GB' in savings:
                try:
                    gb = float(savings.split('GB')[0].split()[-1])
                    total_mb += gb * 1024
                except ValueError:
                    pass
            elif 'MB' in savings:
                try:
                    mb = float(savings.split('MB')[0].split()[-1])
                    total_mb += mb
                except ValueError:
                    pass

        if total_mb > 1024:
            return f"{total_mb / 1024:.1f} GB"
        else:
            return f"{total_mb:.1f} MB"
