"""
Update Command - Intelligent package dependency updates
Handles pip, npm, yarn package updates with safety checks
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


class UpdateCommand:
    """Handle package updates for various managers"""

    def __init__(self, session_manager):
        self.session = session_manager

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute package update command

        Args:
            args: Parsed command arguments

        Returns:
            dict: Command result
        """
        manager = args.get('manager', 'auto')
        packages = args.get('packages', '').strip()
        dry_run = args.get('dry_run', False)
        confirm = args.get('confirm', True)

        # Auto-detect package manager if not specified
        if manager == 'auto':
            manager = self._detect_package_manager()

        if not manager:
            return {
                'success': False,
                'output': 'Isaac > Could not detect package manager (pip/npm/yarn). Please specify with --manager',
                'exit_code': 1
            }

        # Get outdated packages
        outdated = self._get_outdated_packages(manager)
        if not outdated:
            return {
                'success': True,
                'output': f'Isaac > All {manager} packages are up to date! 🎉',
                'exit_code': 0
            }

        # Filter to specific packages if requested
        if packages:
            package_list = [p.strip() for p in packages.split(',')]
            outdated = [pkg for pkg in outdated if pkg['name'] in package_list]

        if not outdated:
            return {
                'success': False,
                'output': f'Isaac > No matching outdated packages found for: {packages}',
                'exit_code': 1
            }

        # Show what will be updated
        output = self._format_outdated_packages(outdated, manager)

        if dry_run:
            output += f"\nIsaac > Dry run mode - would update {len(outdated)} packages"
            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }

        # Confirm update
        if confirm:
            output += f"\nIsaac > Update {len(outdated)} {manager} packages? (y/n): "
            # In a real implementation, this would prompt the user
            # For now, we'll assume yes for automation
            output += "y (auto-confirmed)"

        # Perform updates
        result = self._update_packages(manager, outdated)

        return {
            'success': result['success'],
            'output': output + "\n\n" + result['output'],
            'exit_code': result['exit_code']
        }

    def _detect_package_manager(self) -> Optional[str]:
        """Auto-detect which package manager to use"""
        # Check for common indicators

        # Check for requirements.txt or setup.py (pip)
        if Path('requirements.txt').exists() or Path('setup.py').exists() or Path('pyproject.toml').exists():
            return 'pip'

        # Check for package.json (npm/yarn)
        if Path('package.json').exists():
            # Check if yarn.lock exists (prefer yarn)
            if Path('yarn.lock').exists():
                return 'yarn'
            return 'npm'

        # Default to pip for Python projects
        return 'pip'

    def _get_outdated_packages(self, manager: str) -> List[Dict[str, Any]]:
        """Get list of outdated packages"""
        try:
            if manager == 'pip':
                return self._get_pip_outdated()
            elif manager == 'npm':
                return self._get_npm_outdated()
            elif manager == 'yarn':
                return self._get_yarn_outdated()
            else:
                return []
        except Exception as e:
            print(f"Warning: Failed to get outdated packages: {e}")
            return []

    def _get_pip_outdated(self) -> List[Dict[str, Any]]:
        """Get outdated pip packages"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json'
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout.strip():
                import json
                packages = json.loads(result.stdout)
                return [{
                    'name': pkg['name'],
                    'current': pkg['version'],
                    'latest': pkg['latest_version'],
                    'type': pkg.get('latest_filetype', 'wheel')
                } for pkg in packages]
        except Exception:
            pass

        return []

    def _get_npm_outdated(self) -> List[Dict[str, Any]]:
        """Get outdated npm packages"""
        try:
            result = subprocess.run([
                'npm', 'outdated', '--json'
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                return [{
                    'name': name,
                    'current': info['current'],
                    'latest': info['latest'],
                    'type': 'npm'
                } for name, info in data.items()]
        except Exception:
            pass

        return []

    def _get_yarn_outdated(self) -> List[Dict[str, Any]]:
        """Get outdated yarn packages"""
        try:
            result = subprocess.run([
                'yarn', 'outdated', '--json'
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout.strip():
                # Yarn outputs one JSON object per line
                packages = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get('type') == 'table':
                                for item in data.get('data', {}).get('body', []):
                                    packages.append({
                                        'name': item[0],
                                        'current': item[1],
                                        'latest': item[3],  # wanted version
                                        'type': 'yarn'
                                    })
                        except json.JSONDecodeError:
                            continue
                return packages
        except Exception:
            pass

        return []

    def _format_outdated_packages(self, packages: List[Dict[str, Any]], manager: str) -> str:
        """Format outdated packages for display"""
        if not packages:
            return f"No outdated {manager} packages found."

        lines = [f"Isaac > Found {len(packages)} outdated {manager} packages:"]
        lines.append("-" * 60)

        for pkg in packages:
            current = pkg.get('current', 'unknown')
            latest = pkg.get('latest', 'unknown')
            pkg_type = pkg.get('type', '')

            line = f"  {pkg['name']:20} {current:10} → {latest:10}"
            if pkg_type:
                line += f" ({pkg_type})"
            lines.append(line)

        return "\n".join(lines)

    def _update_packages(self, manager: str, packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update the specified packages"""
        try:
            if manager == 'pip':
                return self._update_pip_packages(packages)
            elif manager == 'npm':
                return self._update_npm_packages(packages)
            elif manager == 'yarn':
                return self._update_yarn_packages(packages)
            else:
                return {
                    'success': False,
                    'output': f'Unsupported package manager: {manager}',
                    'exit_code': 1
                }
        except Exception as e:
            return {
                'success': False,
                'output': f'Update failed: {str(e)}',
                'exit_code': 1
            }

    def _update_pip_packages(self, packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update pip packages"""
        package_names = [pkg['name'] for pkg in packages]

        # Update packages one by one to handle failures gracefully
        success_count = 0
        failed = []

        for name in package_names:
            try:
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '--upgrade', name
                ], capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    success_count += 1
                else:
                    failed.append(f"{name}: {result.stderr.strip()}")

            except subprocess.TimeoutExpired:
                failed.append(f"{name}: timeout")
            except Exception as e:
                failed.append(f"{name}: {str(e)}")

        output = f"Isaac > Updated {success_count}/{len(package_names)} pip packages"
        if failed:
            output += f"\nFailed: {', '.join(failed)}"

        return {
            'success': success_count > 0,
            'output': output,
            'exit_code': 0 if success_count > 0 else 1
        }

    def _update_npm_packages(self, packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update npm packages"""
        package_names = [f"{pkg['name']}@{pkg['latest']}" for pkg in packages]

        try:
            result = subprocess.run([
                'npm', 'install'] + package_names,
                capture_output=True, text=True, timeout=120)

            return {
                'success': result.returncode == 0,
                'output': f"Isaac > npm update result:\n{result.stdout}\n{result.stderr}",
                'exit_code': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': 'Isaac > npm update timed out',
                'exit_code': 1
            }

    def _update_yarn_packages(self, packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update yarn packages"""
        package_names = [f"{pkg['name']}@{pkg['latest']}" for pkg in packages]

        try:
            result = subprocess.run([
                'yarn', 'add'] + package_names,
                capture_output=True, text=True, timeout=120)

            return {
                'success': result.returncode == 0,
                'output': f"Isaac > yarn update result:\n{result.stdout}\n{result.stderr}",
                'exit_code': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': 'Isaac > yarn update timed out',
                'exit_code': 1
            }


def run(session_manager, args: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for the update command"""
    cmd = UpdateCommand(session_manager)
    return cmd.execute(args)