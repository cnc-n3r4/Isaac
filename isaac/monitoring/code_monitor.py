# isaac/monitoring/code_monitor.py

"""
Code Monitor - Monitors code quality and generates notifications

Checks for linting errors, test failures, and other code quality issues
that might require developer attention.
"""

import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from isaac.monitoring.base_monitor import BaseMonitor
from isaac.core.message_queue import MessageType, MessagePriority

logger = logging.getLogger(__name__)


class CodeMonitor(BaseMonitor):
    """
    Monitors code quality and generates notifications for issues.
    """

    def __init__(self, project_root: str = None):
        super().__init__("code_monitor", check_interval_minutes=15)  # Check every 15 minutes

        # Determine project root
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Try to find project root by looking for common indicators
            cwd = Path.cwd()
            for parent in [cwd] + list(cwd.parents):
                if (parent / 'setup.py').exists() or (parent / 'pyproject.toml').exists() or (parent / '.git').exists():
                    self.project_root = parent
                    break
            else:
                self.project_root = cwd

        logger.info(f"Code monitor watching: {self.project_root}")

    def _perform_check(self):
        """Perform code quality checks."""
        logger.debug("Performing code quality checks")

        try:
            # Check for Python linting issues
            self._check_python_linting()

            # Check for test failures
            self._check_test_failures()

            # Check for outdated dependencies
            self._check_outdated_dependencies()

        except Exception as e:
            logger.error(f"Error during code check: {e}")

    def _check_python_linting(self):
        """Check for Python linting issues using flake8 or pylint."""
        try:
            # Look for Python files
            python_files = list(self.project_root.rglob('*.py'))
            if not python_files:
                return

            # Try flake8 first
            try:
                result = subprocess.run(
                    ['flake8', '--count', '--select=E9,F63,F7,F82', '--show-source', '--statistics', str(self.project_root)],
                    capture_output=True, text=True, timeout=60, cwd=self.project_root
                )

                if result.returncode > 0:
                    error_count = int(result.stdout.strip().split('\n')[-1]) if result.stdout.strip() else 0

                    if error_count > 0:
                        self._send_message(
                            MessageType.CODE,
                            f"Python Linting Errors ({error_count})",
                            f"Found {error_count} critical Python linting errors. "
                            "Run 'flake8 .' to see details.",
                            MessagePriority.HIGH if error_count > 10 else MessagePriority.NORMAL,
                            {"error_count": error_count, "tool": "flake8"}
                        )

            except FileNotFoundError:
                # Try pylint if flake8 not available
                try:
                    result = subprocess.run(
                        ['pylint', '--errors-only', '--reports=no', str(self.project_root)],
                        capture_output=True, text=True, timeout=60, cwd=self.project_root
                    )

                    if result.returncode > 0:
                        lines = result.stdout.strip().split('\n')
                        error_count = len([line for line in lines if line.strip() and ':' in line])

                        if error_count > 0:
                            self._send_message(
                                MessageType.CODE,
                                f"Python Linting Errors ({error_count})",
                                f"Found {error_count} Python linting errors. "
                                "Run 'pylint .' to see details.",
                                MessagePriority.HIGH if error_count > 10 else MessagePriority.NORMAL,
                                {"error_count": error_count, "tool": "pylint"}
                            )

                except FileNotFoundError:
                    logger.debug("Neither flake8 nor pylint available for linting checks")

        except subprocess.TimeoutExpired:
            logger.warning("Python linting check timed out")
        except Exception as e:
            logger.error(f"Error checking Python linting: {e}")

    def _check_test_failures(self):
        """Check for test failures using pytest."""
        try:
            # Check if pytest is available and there are tests
            test_files = list(self.project_root.rglob('test_*.py'))
            if not test_files:
                return

            # Run pytest with minimal output
            result = subprocess.run(
                ['pytest', '--tb=no', '-q', '--disable-warnings'],
                capture_output=True, text=True, timeout=120, cwd=self.project_root
            )

            if result.returncode != 0:
                # Parse output for failure counts
                output_lines = result.stdout.strip().split('\n')
                failed_count = 0
                passed_count = 0

                for line in output_lines:
                    if 'failed' in line.lower():
                        try:
                            # Extract number from something like "5 failed"
                            parts = line.split()
                            for part in parts:
                                if part.isdigit():
                                    failed_count = int(part)
                                    break
                        except (ValueError, IndexError):
                            pass
                    elif 'passed' in line.lower():
                        try:
                            parts = line.split()
                            for part in parts:
                                if part.isdigit():
                                    passed_count = int(part)
                                    break
                        except (ValueError, IndexError):
                            pass

                if failed_count > 0:
                    self._send_message(
                        MessageType.CODE,
                        f"Test Failures ({failed_count})",
                        f"{failed_count} tests are failing, {passed_count} passed. "
                        "Run 'pytest' to see details.",
                        MessagePriority.HIGH,
                        {"failed_count": failed_count, "passed_count": passed_count}
                    )

        except subprocess.TimeoutExpired:
            logger.warning("Test check timed out")
        except FileNotFoundError:
            logger.debug("pytest not available for test checks")
        except Exception as e:
            logger.error(f"Error checking tests: {e}")

    def _check_outdated_dependencies(self):
        """Check for outdated Python dependencies."""
        try:
            # Check if requirements.txt exists
            req_file = self.project_root / 'requirements.txt'
            if not req_file.exists():
                return

            # Use pip list --outdated
            result = subprocess.run(
                ['pip', 'list', '--outdated', '--format=json'],
                capture_output=True, text=True, timeout=30, cwd=self.project_root
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    outdated = json.loads(result.stdout)
                    outdated_count = len(outdated)

                    if outdated_count > 0:
                        # Get major version updates
                        major_updates = [pkg for pkg in outdated
                                       if pkg.get('latest_version', '').split('.')[0] != pkg.get('version', '').split('.')[0]]

                        priority = MessagePriority.NORMAL
                        if len(major_updates) > 0:
                            priority = MessagePriority.HIGH

                        self._send_message(
                            MessageType.CODE,
                            f"Outdated Dependencies ({outdated_count})",
                            f"{outdated_count} Python packages have updates available. "
                            f"{len(major_updates)} are major version updates. "
                            "Run 'pip list --outdated' to see details.",
                            priority,
                            {"outdated_count": outdated_count, "major_updates": len(major_updates)}
                        )

                except json.JSONDecodeError:
                    logger.debug("Could not parse pip outdated output")

        except subprocess.TimeoutExpired:
            logger.warning("Dependency check timed out")
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")