"""
Auto-Investigation - Automatically analyze errors and gather diagnostic information
Isaac's smart debugging assistant for comprehensive error analysis
"""

import os
import re
import time
import platform
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import psutil


@dataclass
class DiagnosticInfo:
    """Container for diagnostic information gathered during investigation."""
    timestamp: float
    error_message: str
    command: str
    exit_code: int
    working_directory: str
    environment: Dict[str, str]
    system_info: Dict[str, Any]
    file_permissions: Dict[str, str]
    network_status: Dict[str, Any]
    process_info: Dict[str, Any]
    disk_usage: Dict[str, Any]
    memory_usage: Dict[str, Any]
    recent_logs: List[str]
    related_files: List[str]


@dataclass
class InvestigationResult:
    """Results of an automated investigation."""
    investigation_id: str
    timestamp: float
    error_category: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    confidence: float  # 0-1
    root_cause: str
    evidence: List[str]
    recommendations: List[str]
    diagnostic_data: DiagnosticInfo
    suggested_fixes: List[Dict[str, Any]]
    follow_up_actions: List[str]


class AutoInvestigator:
    """Automatically investigates errors and gathers comprehensive diagnostic information."""

    def __init__(self):
        """Initialize the auto-investigator."""
        self.investigation_history: Dict[str, InvestigationResult] = {}
        self.error_patterns = self._load_error_patterns()
        self.max_diagnostic_time = 30  # seconds
        self.max_log_lines = 100

    def _load_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load known error patterns and their characteristics."""
        return {
            'command_not_found': {
                'patterns': [r'command not found', r"'[^']+' is not recognized", r'bash: [^:]+: command not found'],
                'category': 'command_error',
                'severity': 'medium',
                'common_causes': ['PATH issues', 'missing package', 'typo in command'],
                'diagnostic_checks': ['check_path', 'check_installation', 'check_spelling']
            },
            'permission_denied': {
                'patterns': [r'Permission denied', r'Access is denied', r'Operation not permitted'],
                'category': 'permission_error',
                'severity': 'high',
                'common_causes': ['insufficient permissions', 'file ownership', 'SELinux/AppArmor'],
                'diagnostic_checks': ['check_permissions', 'check_ownership', 'check_selinux']
            },
            'file_not_found': {
                'patterns': [r'No such file or directory', r'File not found', r'cannot find the file'],
                'category': 'file_error',
                'severity': 'medium',
                'common_causes': ['wrong path', 'file deleted', 'case sensitivity'],
                'diagnostic_checks': ['check_path_exists', 'check_case_sensitivity', 'check_recent_changes']
            },
            'connection_refused': {
                'patterns': [r'Connection refused', r'Connection timed out', r'Network is unreachable'],
                'category': 'network_error',
                'severity': 'high',
                'common_causes': ['service not running', 'firewall', 'wrong port/host'],
                'diagnostic_checks': ['check_service_status', 'check_firewall', 'check_network_config']
            },
            'out_of_memory': {
                'patterns': [r'Out of memory', r'Cannot allocate memory', r'Memory allocation failed'],
                'category': 'resource_error',
                'severity': 'critical',
                'common_causes': ['insufficient RAM', 'memory leak', 'large data processing'],
                'diagnostic_checks': ['check_memory_usage', 'check_swap', 'check_process_memory']
            },
            'disk_full': {
                'patterns': [r'No space left on device', r'Disk full', r'Insufficient disk space'],
                'category': 'resource_error',
                'severity': 'high',
                'common_causes': ['disk full', 'quota exceeded', 'large files'],
                'diagnostic_checks': ['check_disk_usage', 'check_quotas', 'find_large_files']
            }
        }

    def investigate_error(self, command: str, error_output: str, exit_code: int,
                         working_dir: str = None) -> InvestigationResult:
        """Perform comprehensive investigation of an error.

        Args:
            command: The command that failed
            error_output: Error output from the command
            exit_code: Exit code from the command
            working_dir: Working directory where command was run

        Returns:
            Detailed investigation result
        """
        investigation_id = f"inv_{int(time.time())}_{hash(command) % 10000}"
        start_time = time.time()

        # Gather diagnostic information
        diagnostic_info = self._gather_diagnostics(command, error_output, exit_code, working_dir)

        # Analyze error patterns
        error_category, severity, confidence = self._analyze_error_patterns(error_output)

        # Determine root cause
        root_cause = self._determine_root_cause(error_category, diagnostic_info)

        # Gather evidence
        evidence = self._gather_evidence(error_category, diagnostic_info)

        # Generate recommendations
        recommendations = self._generate_recommendations(error_category, diagnostic_info)

        # Suggest fixes
        suggested_fixes = self._suggest_fixes(error_category, diagnostic_info, command)

        # Follow-up actions
        follow_up_actions = self._get_follow_up_actions(error_category)

        time.time() - start_time

        result = InvestigationResult(
            investigation_id=investigation_id,
            timestamp=time.time(),
            error_category=error_category,
            severity=severity,
            confidence=confidence,
            root_cause=root_cause,
            evidence=evidence,
            recommendations=recommendations,
            diagnostic_data=diagnostic_info,
            suggested_fixes=suggested_fixes,
            follow_up_actions=follow_up_actions
        )

        # Store in history
        self.investigation_history[investigation_id] = result

        return result

    def _gather_diagnostics(self, command: str, error_output: str, exit_code: int,
                           working_dir: str = None) -> DiagnosticInfo:
        """Gather comprehensive diagnostic information."""
        if working_dir is None:
            working_dir = os.getcwd()

        # Basic system info
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture(),
            'processor': platform.processor(),
            'cpu_count': os.cpu_count()
        }

        # Environment variables (filtered for safety)
        env_vars = {}
        safe_env_vars = ['PATH', 'HOME', 'USER', 'SHELL', 'PWD', 'LANG', 'LC_ALL']
        for var in safe_env_vars:
            if var in os.environ:
                env_vars[var] = os.environ[var]

        # File permissions for command-related files
        file_permissions = self._check_file_permissions(command, working_dir)

        # Network status
        network_status = self._check_network_status()

        # Process information
        process_info = self._get_process_info()

        # Disk and memory usage
        disk_usage = self._get_disk_usage()
        memory_usage = self._get_memory_usage()

        # Recent logs (if available)
        recent_logs = self._get_recent_logs()

        # Related files
        related_files = self._find_related_files(command, working_dir)

        return DiagnosticInfo(
            timestamp=time.time(),
            error_message=error_output,
            command=command,
            exit_code=exit_code,
            working_directory=working_dir,
            environment=env_vars,
            system_info=system_info,
            file_permissions=file_permissions,
            network_status=network_status,
            process_info=process_info,
            disk_usage=disk_usage,
            memory_usage=memory_usage,
            recent_logs=recent_logs,
            related_files=related_files
        )

    def _check_file_permissions(self, command: str, working_dir: str) -> Dict[str, str]:
        """Check permissions of files related to the command."""
        permissions = {}

        # Check the command itself if it's a file path
        if os.path.isfile(command):
            try:
                stat = os.stat(command)
                permissions[command] = oct(stat.st_mode)[-3:]
            except OSError:
                permissions[command] = "inaccessible"

        # Check working directory
        try:
            stat = os.stat(working_dir)
            permissions[working_dir] = oct(stat.st_mode)[-3:]
        except OSError:
            permissions[working_dir] = "inaccessible"

        return permissions

    def _check_network_status(self) -> Dict[str, Any]:
        """Check basic network connectivity."""
        network_info = {
            'has_internet': False,
            'dns_working': False
        }

        try:
            # Simple connectivity check
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            network_info['has_internet'] = True
            network_info['dns_working'] = True
        except OSError:
            pass

        return network_info

    def _get_process_info(self) -> Dict[str, Any]:
        """Get information about running processes."""
        try:
            current_process = psutil.Process()
            return {
                'pid': current_process.pid,
                'cpu_percent': current_process.cpu_percent(),
                'memory_percent': current_process.memory_percent(),
                'num_threads': current_process.num_threads(),
                'status': current_process.status()
            }
        except Exception:
            return {'error': 'Could not get process info'}

    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information."""
        try:
            disk = psutil.disk_usage('/')
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
        except Exception:
            return {'error': 'Could not get disk usage'}

    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information."""
        try:
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            }
        except Exception:
            return {'error': 'Could not get memory usage'}

    def _get_recent_logs(self) -> List[str]:
        """Get recent system logs."""
        logs = []

        # Try to get logs from common locations
        log_files = ['/var/log/syslog', '/var/log/messages', '/var/log/system.log']
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()[-self.max_log_lines:]
                        logs.extend([line.strip() for line in lines])
                except Exception:
                    pass

        return logs[-self.max_log_lines:]  # Limit total logs

    def _find_related_files(self, command: str, working_dir: str) -> List[str]:
        """Find files related to the command."""
        related = []

        # Extract potential file paths from command
        words = command.split()
        for word in words:
            if os.path.exists(word):
                related.append(word)
            elif os.path.exists(os.path.join(working_dir, word)):
                related.append(os.path.join(working_dir, word))

        return related

    def _analyze_error_patterns(self, error_output: str) -> Tuple[str, str, float]:
        """Analyze error output to categorize the error."""
        error_output_lower = error_output.lower()

        for error_type, pattern_info in self.error_patterns.items():
            for pattern in pattern_info['patterns']:
                if re.search(pattern, error_output_lower, re.IGNORECASE):
                    return (
                        pattern_info['category'],
                        pattern_info['severity'],
                        0.8  # High confidence for pattern matches
                    )

        # Default categorization
        return ('unknown_error', 'medium', 0.3)

    def _determine_root_cause(self, error_category: str, diagnostic: DiagnosticInfo) -> str:
        """Determine the likely root cause based on diagnostic information."""
        causes = {
            'command_error': self._analyze_command_error(diagnostic),
            'permission_error': self._analyze_permission_error(diagnostic),
            'file_error': self._analyze_file_error(diagnostic),
            'network_error': self._analyze_network_error(diagnostic),
            'resource_error': self._analyze_resource_error(diagnostic)
        }

        return causes.get(error_category, f"Unknown error in category: {error_category}")

    def _analyze_command_error(self, diagnostic: DiagnosticInfo) -> str:
        """Analyze command-related errors."""
        command_parts = diagnostic.command.split()
        if command_parts:
            cmd = command_parts[0]
            # Check if command exists in PATH
            if 'PATH' in diagnostic.environment:
                path_dirs = diagnostic.environment['PATH'].split(os.pathsep)
                for path_dir in path_dirs:
                    if os.path.exists(os.path.join(path_dir, cmd)):
                        return f"Command '{cmd}' exists but may have execution issues"
                return f"Command '{cmd}' not found in PATH"
        return "Command execution failed"

    def _analyze_permission_error(self, diagnostic: DiagnosticInfo) -> str:
        """Analyze permission-related errors."""
        # Check file permissions
        for file_path, perms in diagnostic.file_permissions.items():
            if perms == "inaccessible":
                return f"Cannot access {file_path} - permission denied"
        return "Insufficient permissions for operation"

    def _analyze_file_error(self, diagnostic: DiagnosticInfo) -> str:
        """Analyze file-related errors."""
        command_parts = diagnostic.command.split()
        for part in command_parts:
            if '/' in part or '\\' in part:  # Looks like a path
                if not os.path.exists(part):
                    return f"File or directory does not exist: {part}"
        return "File access error"

    def _analyze_network_error(self, diagnostic: DiagnosticInfo) -> str:
        """Analyze network-related errors."""
        if not diagnostic.network_status.get('has_internet', False):
            return "No internet connectivity"
        return "Network service or configuration issue"

    def _analyze_resource_error(self, diagnostic: DiagnosticInfo) -> str:
        """Analyze resource-related errors."""
        memory_percent = diagnostic.memory_usage.get('percent', 0)
        disk_percent = diagnostic.disk_usage.get('percent', 0)

        if memory_percent > 95:
            return "System is critically low on memory"
        elif disk_percent > 95:
            return "Disk is critically full"
        elif memory_percent > 80:
            return "System is low on memory"
        elif disk_percent > 80:
            return "Disk is nearly full"

        return "Resource exhaustion"

    def _gather_evidence(self, error_category: str, diagnostic: DiagnosticInfo) -> List[str]:
        """Gather evidence supporting the root cause analysis."""
        evidence = []

        if error_category == 'command_error':
            if 'PATH' in diagnostic.environment:
                evidence.append(f"PATH contains {len(diagnostic.environment['PATH'].split(os.pathsep))} directories")
            evidence.append(f"Working directory: {diagnostic.working_directory}")

        elif error_category == 'permission_error':
            for file_path, perms in diagnostic.file_permissions.items():
                evidence.append(f"{file_path}: permissions {perms}")

        elif error_category == 'resource_error':
            memory_percent = diagnostic.memory_usage.get('percent', 0)
            disk_percent = diagnostic.disk_usage.get('percent', 0)
            if memory_percent > 0:
                evidence.append(f"Memory usage: {memory_percent:.1f}%")
            if disk_percent > 0:
                evidence.append(f"Disk usage: {disk_percent:.1f}%")

        evidence.append(f"Exit code: {diagnostic.exit_code}")
        evidence.append(f"Platform: {diagnostic.system_info.get('platform', 'unknown')}")

        return evidence

    def _generate_recommendations(self, error_category: str, diagnostic: DiagnosticInfo) -> List[str]:
        """Generate recommendations based on the error analysis."""
        recommendations = []

        if error_category == 'command_error':
            recommendations.extend([
                "Check if the command is installed and in your PATH",
                "Verify command spelling and syntax",
                "Try using absolute paths instead of relative paths"
            ])

        elif error_category == 'permission_error':
            recommendations.extend([
                "Check file and directory permissions",
                "Try running with elevated privileges (sudo/admin)",
                "Verify file ownership matches your user"
            ])

        elif error_category == 'file_error':
            recommendations.extend([
                "Verify file paths are correct",
                "Check if files were moved or deleted",
                "Ensure proper case sensitivity in file names"
            ])

        elif error_category == 'network_error':
            recommendations.extend([
                "Check network connectivity",
                "Verify service is running on target host/port",
                "Check firewall settings"
            ])

        elif error_category == 'resource_error':
            recommendations.extend([
                "Free up system memory by closing unused applications",
                "Clear disk space by removing unnecessary files",
                "Consider increasing system resources"
            ])

        return recommendations

    def _suggest_fixes(self, error_category: str, diagnostic: DiagnosticInfo,
                      original_command: str) -> List[Dict[str, Any]]:
        """Suggest specific fixes for the error."""
        fixes = []

        if error_category == 'command_error':
            command_parts = original_command.split()
            if command_parts:
                cmd = command_parts[0]
                # Suggest package installation
                fixes.append({
                    'type': 'package_install',
                    'description': f"Install {cmd} package",
                    'commands': [f"apt-get install {cmd}", f"yum install {cmd}", f"brew install {cmd}"],
                    'confidence': 0.6
                })

        elif error_category == 'permission_error':
            fixes.append({
                'type': 'permission_fix',
                'description': "Fix permissions on affected files",
                'commands': [f"chmod +x {original_command}", f"sudo chown $USER {original_command}"],
                'confidence': 0.7
            })

        elif error_category == 'resource_error':
            memory_percent = diagnostic.memory_usage.get('percent', 0)
            disk_percent = diagnostic.disk_usage.get('percent', 0)

            if memory_percent > 80:
                fixes.append({
                    'type': 'memory_cleanup',
                    'description': "Free up memory",
                    'commands': ["kill unused processes", "clear system cache"],
                    'confidence': 0.8
                })

            if disk_percent > 80:
                fixes.append({
                    'type': 'disk_cleanup',
                    'description': "Free up disk space",
                    'commands': ["rm -rf ~/.cache/*", "docker system prune", "find . -name '*.log' -delete"],
                    'confidence': 0.8
                })

        return fixes

    def _get_follow_up_actions(self, error_category: str) -> List[str]:
        """Get follow-up actions for further investigation."""
        actions = [
            "Check system logs for additional error information",
            "Monitor system resources during similar operations",
            "Test the fix in a safe environment first"
        ]

        if error_category == 'network_error':
            actions.append("Test connectivity to related services")
        elif error_category == 'resource_error':
            actions.append("Monitor resource usage over time")

        return actions

    def get_investigation_history(self) -> List[InvestigationResult]:
        """Get history of all investigations."""
        return list(self.investigation_history.values())

    def get_investigation(self, investigation_id: str) -> Optional[InvestigationResult]:
        """Get a specific investigation by ID."""
        return self.investigation_history.get(investigation_id)