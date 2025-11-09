# isaac/monitoring/monitor_manager.py

"""
Monitor Manager - Manages all monitoring agents

Provides centralized control for starting, stopping, and managing
all monitoring agents in the autonomous AI assistant system.
"""

import logging
from threading import Lock
from typing import Any, Dict, List, Optional

from isaac.monitoring.base_monitor import BaseMonitor
from isaac.monitoring.code_monitor import CodeMonitor
from isaac.monitoring.system_monitor import SystemMonitor

logger = logging.getLogger(__name__)


class MonitorManager:
    """
    Manages all monitoring agents for the autonomous AI assistant.
    """

    def __init__(self):
        self.monitors: Dict[str, BaseMonitor] = {}
        self.lock = Lock()
        self._initialized = False

    def initialize_monitors(self):
        """Initialize all available monitoring agents."""
        if self._initialized:
            return

        with self.lock:
            try:
                # System monitor
                system_monitor = SystemMonitor()
                self.monitors["system"] = system_monitor

                # Code monitor
                code_monitor = CodeMonitor()
                self.monitors["code"] = code_monitor

                # Future monitors can be added here:
                # self.monitors['cloud'] = CloudMonitor()
                # self.monitors['program'] = ProgramMonitor()

                self._initialized = True
                logger.info(f"Initialized {len(self.monitors)} monitoring agents")

            except Exception as e:
                logger.error(f"Error initializing monitors: {e}")

    def start_all(self):
        """Start all monitoring agents."""
        if not self._initialized:
            self.initialize_monitors()

        with self.lock:
            started_count = 0
            for name, monitor in self.monitors.items():
                try:
                    monitor.start()
                    started_count += 1
                    logger.info(f"Started monitor: {name}")
                except Exception as e:
                    logger.error(f"Failed to start monitor {name}: {e}")

            logger.info(f"Started {started_count}/{len(self.monitors)} monitoring agents")

    def stop_all(self):
        """Stop all monitoring agents."""
        with self.lock:
            stopped_count = 0
            for name, monitor in self.monitors.items():
                try:
                    monitor.stop()
                    stopped_count += 1
                    logger.info(f"Stopped monitor: {name}")
                except Exception as e:
                    logger.error(f"Failed to stop monitor {name}: {e}")

            logger.info(f"Stopped {stopped_count}/{len(self.monitors)} monitoring agents")

    def start_monitor(self, name: str) -> bool:
        """Start a specific monitoring agent."""
        with self.lock:
            if name not in self.monitors:
                logger.warning(f"Monitor not found: {name}")
                return False

            try:
                self.monitors[name].start()
                logger.info(f"Started monitor: {name}")
                return True
            except Exception as e:
                logger.error(f"Failed to start monitor {name}: {e}")
                return False

    def stop_monitor(self, name: str) -> bool:
        """Stop a specific monitoring agent."""
        with self.lock:
            if name not in self.monitors:
                logger.warning(f"Monitor not found: {name}")
                return False

            try:
                self.monitors[name].stop()
                logger.info(f"Stopped monitor: {name}")
                return True
            except Exception as e:
                logger.error(f"Failed to stop monitor {name}: {e}")
                return False

    def get_monitor_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all monitoring agents."""
        with self.lock:
            status = {}
            for name, monitor in self.monitors.items():
                status[name] = {
                    "running": monitor.running,
                    "check_interval_minutes": monitor.check_interval.total_seconds() / 60,
                    "last_check": monitor.last_check.isoformat() if monitor.last_check else None,
                }
            return status

    def list_monitors(self) -> List[str]:
        """Get list of available monitor names."""
        with self.lock:
            return list(self.monitors.keys())

    def get_monitor(self, name: str) -> Optional[BaseMonitor]:
        """Get a specific monitor instance."""
        with self.lock:
            return self.monitors.get(name)
