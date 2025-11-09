# isaac/monitoring/system_monitor.py

"""
System Monitor - Monitors system health and generates notifications

Checks for system updates, disk space, memory usage, and other system-level
conditions that might require user attention.
"""

import platform
import psutil
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from isaac.monitoring.base_monitor import BaseMonitor
from isaac.core.message_queue import MessageType, MessagePriority

logger = logging.getLogger(__name__)


class SystemMonitor(BaseMonitor):
    """
    Monitors system health and generates notifications for issues.
    """

    def __init__(self):
        super().__init__("system_monitor", check_interval_minutes=30)  # Check every 30 minutes
        self.last_update_check = datetime.now() - timedelta(days=1)  # Force first check

    def _perform_check(self):
        """Perform system health checks."""
        logger.debug("Performing system health checks")

        try:
            # Check disk space
            self._check_disk_space()

            # Check memory usage
            self._check_memory_usage()

            # Check for system updates (less frequently)
            if datetime.now() - self.last_update_check >= timedelta(hours=6):
                self._check_system_updates()
                self.last_update_check = datetime.now()

        except Exception as e:
            logger.error(f"Error during system check: {e}")

    def _check_disk_space(self):
        """Check disk space usage."""
        try:
            # Get disk usage for system drive
            if platform.system() == "Windows":
                disk = psutil.disk_usage('C:\\')
            else:
                disk = psutil.disk_usage('/')

            usage_percent = disk.percent

            if usage_percent > 90:
                self._send_message(
                    MessageType.SYSTEM,
                    "Critical: Low Disk Space",
                    f"System disk is {usage_percent:.1f}% full ({disk.free / (1024**3):.1f} GB free). "
                    "Consider cleaning up files or expanding storage.",
                    MessagePriority.URGENT,
                    {"disk_percent": usage_percent, "free_gb": disk.free / (1024**3)}
                )
            elif usage_percent > 80:
                self._send_message(
                    MessageType.SYSTEM,
                    "Warning: Low Disk Space",
                    f"System disk is {usage_percent:.1f}% full ({disk.free / (1024**3):.1f} GB free).",
                    MessagePriority.HIGH,
                    {"disk_percent": usage_percent, "free_gb": disk.free / (1024**3)}
                )

        except Exception as e:
            logger.error(f"Error checking disk space: {e}")

    def _check_memory_usage(self):
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent

            if usage_percent > 95:
                self._send_message(
                    MessageType.SYSTEM,
                    "Critical: High Memory Usage",
                    f"System memory is {usage_percent:.1f}% used. "
                    "Consider closing some applications.",
                    MessagePriority.URGENT,
                    {"memory_percent": usage_percent}
                )
            elif usage_percent > 85:
                self._send_message(
                    MessageType.SYSTEM,
                    "Warning: High Memory Usage",
                    f"System memory is {usage_percent:.1f}% used.",
                    MessagePriority.HIGH,
                    {"memory_percent": usage_percent}
                )

        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")

    def _check_system_updates(self):
        """Check for available system updates."""
        try:
            if platform.system() == "Windows":
                # Use winget or check Windows Update
                result = subprocess.run(
                    ["winget", "upgrade", "--include-unknown"],
                    capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0 and "No packages found" not in result.stdout:
                    # Parse available updates
                    lines = result.stdout.strip().split('\n')
                    update_count = len([line for line in lines if line.strip() and not line.startswith('-')])

                    if update_count > 0:
                        self._send_message(
                            MessageType.SYSTEM,
                            f"System Updates Available ({update_count})",
                            f"There are {update_count} system updates available. "
                            "Run 'winget upgrade --all' to install them.",
                            MessagePriority.NORMAL,
                            {"update_count": update_count, "platform": "windows"}
                        )

            elif platform.system() == "Linux":
                # Use apt for Debian/Ubuntu
                result = subprocess.run(
                    ["apt", "list", "--upgradable"],
                    capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    update_count = len([line for line in lines if line.strip() and '/' in line])

                    if update_count > 0:
                        self._send_message(
                            MessageType.SYSTEM,
                            f"System Updates Available ({update_count})",
                            f"There are {update_count} system updates available. "
                            "Run 'sudo apt update && sudo apt upgrade' to install them.",
                            MessagePriority.NORMAL,
                            {"update_count": update_count, "platform": "linux"}
                        )

        except subprocess.TimeoutExpired:
            logger.warning("System update check timed out")
        except FileNotFoundError:
            logger.debug("Update check command not available on this system")
        except Exception as e:
            logger.error(f"Error checking system updates: {e}")