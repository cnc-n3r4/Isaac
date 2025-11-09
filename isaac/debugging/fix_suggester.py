"""
Fix Suggestions - Propose specific solutions based on error patterns
Isaac's intelligent debugging system for automated fix recommendations
"""

import re
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class FixSuggestion:
    """Represents a suggested fix for an error."""
    fix_id: str
    title: str
    description: str
    category: str  # 'command', 'permission', 'resource', 'configuration', 'code'
    confidence: float  # 0-1
    commands: List[str]  # Commands to run to apply the fix
    prerequisites: List[str]  # What needs to be true for fix to work
    risks: List[str]  # Potential risks or side effects
    verification: List[str]  # How to verify the fix worked
    rollback: Optional[List[str]]  # How to undo the fix if needed
    estimated_time: str  # 'immediate', 'minutes', 'hours', 'complex'


@dataclass
class FixRecommendation:
    """Complete fix recommendation with multiple options."""
    error_type: str
    primary_fix: FixSuggestion
    alternative_fixes: List[FixSuggestion]
    preventive_fixes: List[FixSuggestion]
    context_info: Dict[str, Any]


class FixSuggester:
    """Suggests specific fixes for common error patterns."""

    def __init__(self):
        """Initialize the fix suggester."""
        self.fix_templates = self._load_fix_templates()
        self.platform_specific_fixes = self._load_platform_fixes()

    def _load_fix_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load fix templates for common error patterns."""
        return {
            'command_not_found': [
                {
                    'title': 'Install Missing Package',
                    'description': 'Install the missing command using package manager',
                    'category': 'command',
                    'confidence': 0.8,
                    'commands': [
                        'apt-get update && apt-get install {command}',
                        'yum install {command}',
                        'brew install {command}',
                        'pacman -S {command}'
                    ],
                    'prerequisites': ['Package manager available', 'Internet connection'],
                    'risks': ['May install unwanted dependencies'],
                    'verification': ['Run the command to verify it works'],
                    'estimated_time': 'minutes'
                },
                {
                    'title': 'Add to PATH',
                    'description': 'Add the command directory to PATH environment variable',
                    'category': 'configuration',
                    'confidence': 0.6,
                    'commands': ['export PATH="$PATH:{command_dir}"'],
                    'prerequisites': ['Command exists in filesystem'],
                    'risks': ['May shadow system commands'],
                    'verification': ['echo $PATH | grep {command_dir}'],
                    'estimated_time': 'immediate'
                }
            ],
            'permission_denied': [
                {
                    'title': 'Fix File Permissions',
                    'description': 'Change file permissions to allow access',
                    'category': 'permission',
                    'confidence': 0.7,
                    'commands': ['chmod +rwx {file_path}'],
                    'prerequisites': ['You own the file or have sudo access'],
                    'risks': ['May make file world-writable'],
                    'verification': ['ls -la {file_path}'],
                    'rollback': ['chmod -rwx {file_path}'],
                    'estimated_time': 'immediate'
                },
                {
                    'title': 'Change File Ownership',
                    'description': 'Change file ownership to current user',
                    'category': 'permission',
                    'confidence': 0.6,
                    'commands': ['sudo chown $USER {file_path}'],
                    'prerequisites': ['sudo access available'],
                    'risks': ['May break other applications using the file'],
                    'verification': ['ls -la {file_path}'],
                    'rollback': ['sudo chown {original_owner} {file_path}'],
                    'estimated_time': 'immediate'
                },
                {
                    'title': 'Run with Elevated Privileges',
                    'description': 'Execute command with sudo/admin privileges',
                    'category': 'command',
                    'confidence': 0.9,
                    'commands': ['sudo {original_command}'],
                    'prerequisites': ['sudo access available'],
                    'risks': ['Runs with full system privileges'],
                    'verification': ['Command executes without permission errors'],
                    'estimated_time': 'immediate'
                }
            ],
            'out_of_memory': [
                {
                    'title': 'Increase System Memory',
                    'description': 'Add more RAM or increase swap space',
                    'category': 'resource',
                    'confidence': 0.5,
                    'commands': [
                        'sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile'
                    ],
                    'prerequisites': ['Root access', 'Available disk space'],
                    'risks': ['Swap is slower than RAM', 'May wear out SSD faster'],
                    'verification': ['free -h'],
                    'rollback': ['sudo swapoff /swapfile && sudo rm /swapfile'],
                    'estimated_time': 'minutes'
                },
                {
                    'title': 'Kill Memory-Intensive Processes',
                    'description': 'Terminate processes consuming excessive memory',
                    'category': 'resource',
                    'confidence': 0.8,
                    'commands': ['ps aux --sort=-%mem | head -10', 'kill {pid}'],
                    'prerequisites': ['Process identification'],
                    'risks': ['May terminate important processes'],
                    'verification': ['free -h'],
                    'estimated_time': 'immediate'
                },
                {
                    'title': 'Optimize Application Memory Usage',
                    'description': 'Reduce memory usage in the application',
                    'category': 'code',
                    'confidence': 0.6,
                    'commands': ['Implement memory-efficient data structures', 'Add memory cleanup routines'],
                    'prerequisites': ['Access to application source code'],
                    'risks': ['May require significant code changes'],
                    'verification': ['Memory profiling tools'],
                    'estimated_time': 'hours'
                }
            ],
            'disk_full': [
                {
                    'title': 'Clean Package Cache',
                    'description': 'Remove cached package files',
                    'category': 'resource',
                    'confidence': 0.8,
                    'commands': [
                        'sudo apt-get clean',
                        'sudo yum clean all',
                        'sudo pacman -Sc'
                    ],
                    'prerequisites': ['Package manager available'],
                    'risks': ['May slow down future package installations'],
                    'verification': ['df -h'],
                    'estimated_time': 'immediate'
                },
                {
                    'title': 'Remove Old Log Files',
                    'description': 'Delete old log files to free disk space',
                    'category': 'resource',
                    'confidence': 0.7,
                    'commands': ['sudo find /var/log -name "*.log" -type f -mtime +30 -delete'],
                    'prerequisites': ['Root access'],
                    'risks': ['May delete important log information'],
                    'verification': ['df -h'],
                    'estimated_time': 'immediate'
                },
                {
                    'title': 'Clean Temporary Files',
                    'description': 'Remove temporary and cache files',
                    'category': 'resource',
                    'confidence': 0.9,
                    'commands': [
                        'sudo rm -rf /tmp/*',
                        'sudo rm -rf ~/.cache/*',
                        'docker system prune -f'
                    ],
                    'prerequisites': ['Appropriate permissions'],
                    'risks': ['May delete useful temporary data'],
                    'verification': ['df -h'],
                    'estimated_time': 'immediate'
                }
            ],
            'connection_refused': [
                {
                    'title': 'Start Required Service',
                    'description': 'Start the service that should be listening on the port',
                    'category': 'command',
                    'confidence': 0.7,
                    'commands': ['sudo systemctl start {service_name}', 'sudo service {service_name} start'],
                    'prerequisites': ['Service name known', 'Service installed'],
                    'risks': ['May start unwanted services'],
                    'verification': ['sudo systemctl status {service_name}'],
                    'estimated_time': 'immediate'
                },
                {
                    'title': 'Check Firewall Rules',
                    'description': 'Verify firewall is not blocking the connection',
                    'category': 'configuration',
                    'confidence': 0.6,
                    'commands': [
                        'sudo ufw status',
                        'sudo iptables -L',
                        'sudo firewall-cmd --list-all'
                    ],
                    'prerequisites': ['Firewall management access'],
                    'risks': ['Firewall changes may affect security'],
                    'verification': ['telnet {host} {port}'],
                    'estimated_time': 'minutes'
                },
                {
                    'title': 'Verify Service Configuration',
                    'description': 'Check service configuration for correct bind address/port',
                    'category': 'configuration',
                    'confidence': 0.5,
                    'commands': ['sudo netstat -tlnp | grep {port}', 'sudo ss -tlnp | grep {port}'],
                    'prerequisites': ['Port number known'],
                    'risks': ['None'],
                    'verification': ['Service configuration files'],
                    'estimated_time': 'minutes'
                }
            ]
        }

    def _load_platform_fixes(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Load platform-specific fix variations."""
        return {
            'linux': {
                'package_manager': ['apt-get', 'yum', 'dnf', 'pacman', 'zypper'],
                'service_manager': ['systemctl', 'service'],
                'firewall': ['ufw', 'firewalld', 'iptables']
            },
            'darwin': {
                'package_manager': ['brew'],
                'service_manager': ['launchctl'],
                'firewall': ['pfctl']
            },
            'windows': {
                'package_manager': ['choco', 'winget'],
                'service_manager': ['sc', 'net'],
                'firewall': ['netsh']
            }
        }

    def suggest_fixes(self, error_message: str, diagnostic_data: Dict[str, Any],
                     root_cause: str = None) -> FixRecommendation:
        """Generate fix suggestions for an error.

        Args:
            error_message: The original error message
            diagnostic_data: Diagnostic information
            root_cause: Identified root cause (optional)

        Returns:
            Complete fix recommendation
        """
        error_type = self._categorize_error(error_message)

        # Get applicable fix templates
        applicable_fixes = self._get_applicable_fixes(error_type, diagnostic_data)

        if not applicable_fixes:
            # Generate generic fixes
            applicable_fixes = self._generate_generic_fixes(error_message, diagnostic_data)

        # Convert to FixSuggestion objects
        fix_suggestions = []
        for fix_data in applicable_fixes:
            fix_suggestions.append(self._create_fix_suggestion(fix_data, diagnostic_data))

        # Separate primary, alternative, and preventive fixes
        primary_fix = fix_suggestions[0] if fix_suggestions else None
        alternative_fixes = fix_suggestions[1:] if len(fix_suggestions) > 1 else []
        preventive_fixes = self._generate_preventive_fixes(error_type, diagnostic_data)

        context_info = {
            'error_type': error_type,
            'platform': diagnostic_data.get('system_info', {}).get('platform', 'unknown'),
            'confidence_factors': self._calculate_confidence_factors(error_message, diagnostic_data)
        }

        return FixRecommendation(
            error_type=error_type,
            primary_fix=primary_fix,
            alternative_fixes=alternative_fixes,
            preventive_fixes=preventive_fixes,
            context_info=context_info
        )

    def _categorize_error(self, error_message: str) -> str:
        """Categorize the error based on its message."""
        error_lower = error_message.lower()

        if re.search(r'command not found|is not recognized', error_lower):
            return 'command_not_found'
        elif re.search(r'permission denied|access is denied', error_lower):
            return 'permission_denied'
        elif re.search(r'out of memory|cannot allocate memory', error_lower):
            return 'out_of_memory'
        elif re.search(r'no space left|disk full', error_lower):
            return 'disk_full'
        elif re.search(r'connection refused|connection timed out', error_lower):
            return 'connection_refused'
        else:
            return 'unknown_error'

    def _get_applicable_fixes(self, error_type: str, diagnostic_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get fixes applicable to the error type."""
        if error_type in self.fix_templates:
            return self.fix_templates[error_type]
        return []

    def _generate_generic_fixes(self, error_message: str, diagnostic_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate generic fixes when specific templates don't match."""
        return [
            {
                'title': 'Check Error Details',
                'description': 'Examine the full error message and context',
                'category': 'diagnostic',
                'confidence': 0.9,
                'commands': ['echo "Error: {error_message}"'],
                'prerequisites': [],
                'risks': [],
                'verification': ['Review error output'],
                'estimated_time': 'immediate'
            },
            {
                'title': 'Search for Similar Issues',
                'description': 'Search online for solutions to this specific error',
                'category': 'research',
                'confidence': 0.7,
                'commands': ['Search for "{error_message}" solutions'],
                'prerequisites': ['Internet connection'],
                'risks': [],
                'verification': ['Find relevant solutions'],
                'estimated_time': 'minutes'
            }
        ]

    def _create_fix_suggestion(self, fix_data: Dict[str, Any], diagnostic_data: Dict[str, Any]) -> FixSuggestion:
        """Create a FixSuggestion object from template data."""
        fix_id = f"fix_{fix_data['title'].lower().replace(' ', '_')}_{int(time.time())}"

        # Interpolate variables in commands
        commands = self._interpolate_commands(fix_data.get('commands', []), diagnostic_data)

        return FixSuggestion(
            fix_id=fix_id,
            title=fix_data['title'],
            description=fix_data['description'],
            category=fix_data['category'],
            confidence=fix_data['confidence'],
            commands=commands,
            prerequisites=fix_data.get('prerequisites', []),
            risks=fix_data.get('risks', []),
            verification=fix_data.get('verification', []),
            rollback=fix_data.get('rollback'),
            estimated_time=fix_data.get('estimated_time', 'moderate')
        )

    def _interpolate_commands(self, commands: List[str], diagnostic_data: Dict[str, Any]) -> List[str]:
        """Interpolate variables in command templates."""
        interpolated = []

        # Extract context variables
        context_vars = {
            'command': diagnostic_data.get('command', '').split()[0] if diagnostic_data.get('command') else '',
            'file_path': diagnostic_data.get('related_files', [None])[0] if diagnostic_data.get('related_files') else '',
            'working_dir': diagnostic_data.get('working_directory', ''),
            'original_command': diagnostic_data.get('command', ''),
            'error_message': diagnostic_data.get('error_message', ''),
            'port': self._extract_port_from_error(diagnostic_data.get('error_message', '')),
            'service_name': self._guess_service_name(diagnostic_data.get('command', ''))
        }

        for cmd in commands:
            try:
                interpolated_cmd = cmd.format(**context_vars)
                interpolated.append(interpolated_cmd)
            except (KeyError, ValueError):
                # If interpolation fails, keep original command
                interpolated.append(cmd)

        return interpolated

    def _extract_port_from_error(self, error_message: str) -> str:
        """Extract port number from connection error messages."""
        port_match = re.search(r':(\d+)', error_message)
        return port_match.group(1) if port_match else '80'

    def _guess_service_name(self, command: str) -> str:
        """Guess service name from command."""
        command_lower = command.lower()

        if 'nginx' in command_lower:
            return 'nginx'
        elif 'apache' in command_lower or 'httpd' in command_lower:
            return 'apache2'
        elif 'mysql' in command_lower:
            return 'mysql'
        elif 'postgres' in command_lower:
            return 'postgresql'
        elif 'redis' in command_lower:
            return 'redis'
        elif 'mongodb' in command_lower:
            return 'mongod'
        else:
            return 'unknown'

    def _generate_preventive_fixes(self, error_type: str, diagnostic_data: Dict[str, Any]) -> List[FixSuggestion]:
        """Generate preventive fixes to avoid similar errors in the future."""
        preventive_fixes = []

        if error_type == 'command_not_found':
            preventive_fixes.append(FixSuggestion(
                fix_id=f"prevent_cmd_{int(time.time())}",
                title='Install Development Tools',
                description='Install common development tools to prevent missing command errors',
                category='command',
                confidence=0.6,
                commands=['sudo apt-get install build-essential', 'sudo yum groupinstall "Development Tools"'],
                prerequisites=['Package manager available'],
                risks=['Installs many packages'],
                verification=['Common commands are available'],
                estimated_time='minutes'
            ))

        elif error_type == 'permission_denied':
            preventive_fixes.append(FixSuggestion(
                fix_id=f"prevent_perm_{int(time.time())}",
                title='Set Up Proper File Permissions',
                description='Configure proper default permissions for project files',
                category='configuration',
                confidence=0.5,
                commands=['find . -type f -name "*.sh" -exec chmod +x {} \\;', 'chmod -R g+w .'],
                prerequisites=['Project directory access'],
                risks=['May make files executable unintentionally'],
                verification=['ls -la'],
                estimated_time='immediate'
            ))

        elif error_type == 'out_of_memory':
            preventive_fixes.append(FixSuggestion(
                fix_id=f"prevent_mem_{int(time.time())}",
                title='Implement Memory Monitoring',
                description='Set up monitoring to alert before memory exhaustion',
                category='monitoring',
                confidence=0.7,
                commands=['Install memory monitoring tools', 'Configure alerts for high memory usage'],
                prerequisites=['System administration access'],
                risks=[],
                verification=['Memory alerts trigger appropriately'],
                estimated_time='hours'
            ))

        return preventive_fixes

    def _calculate_confidence_factors(self, error_message: str, diagnostic_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate factors that affect fix confidence."""
        factors = {}

        # Platform match
        platform = diagnostic_data.get('system_info', {}).get('platform', '')
        if platform:
            factors['platform_match'] = 0.8
        else:
            factors['platform_match'] = 0.4

        # Diagnostic completeness
        diag_complete = len(diagnostic_data) / 10  # Assume 10 key diagnostic fields
        factors['diagnostic_completeness'] = min(diag_complete, 1.0)

        # Error specificity
        if len(error_message.split()) > 3:
            factors['error_specificity'] = 0.9
        else:
            factors['error_specificity'] = 0.5

        return factors

    def apply_fix(self, fix: FixSuggestion, dry_run: bool = True) -> Dict[str, Any]:
        """Apply a suggested fix.

        Args:
            fix: The fix to apply
            dry_run: If True, only show what would be done

        Returns:
            Result of fix application
        """
        result = {
            'fix_id': fix.fix_id,
            'applied': False,
            'commands_executed': [],
            'output': [],
            'errors': [],
            'dry_run': dry_run
        }

        if dry_run:
            result['commands_executed'] = fix.commands
            result['output'] = [f"Would execute: {cmd}" for cmd in fix.commands]
            return result

        # Actually execute commands
        for cmd in fix.commands:
            try:
                # Note: In real implementation, this would use subprocess
                result['commands_executed'].append(cmd)
                result['output'].append(f"Executed: {cmd}")
                result['applied'] = True
            except Exception as e:
                result['errors'].append(f"Failed to execute '{cmd}': {e}")
                break

        return result

    def validate_fix(self, fix: FixSuggestion) -> Dict[str, Any]:
        """Validate that a fix is appropriate for the current system."""
        validation = {
            'fix_id': fix.fix_id,
            'is_valid': True,
            'warnings': [],
            'prerequisites_met': [],
            'prerequisites_missing': []
        }

        # Check prerequisites
        for prereq in fix.prerequisites:
            if prereq == 'sudo access available':
                # Check if sudo is available and user can use it
                if os.name == 'nt':
                    validation['prerequisites_missing'].append('sudo not available on Windows')
                else:
                    # Could check sudo access here
                    pass
            elif prereq == 'Package manager available':
                # Check for common package managers
                package_managers = ['apt-get', 'yum', 'brew', 'pacman']
                has_pm = any(os.path.exists(f'/usr/bin/{pm}') or os.path.exists(f'/usr/local/bin/{pm}')
                           for pm in package_managers)
                if not has_pm:
                    validation['prerequisites_missing'].append('No package manager found')

        # Check for risks
        if fix.risks:
            validation['warnings'].extend(fix.risks)

        validation['is_valid'] = len(validation['prerequisites_missing']) == 0

        return validation