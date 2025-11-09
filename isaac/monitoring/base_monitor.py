# isaac/monitoring/base_monitor.py

"""
Base Monitoring Agent - Foundation for autonomous AI assistant monitoring

Provides the base framework for creating monitoring agents that run in the background
and generate notifications for the message queue system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import threading
import time
import logging
from datetime import datetime, timedelta

from isaac.core.message_queue import MessageQueue, MessageType, MessagePriority

logger = logging.getLogger(__name__)


class BaseMonitor(ABC):
    """
    Base class for monitoring agents.

    Monitoring agents run in the background and check for conditions that should
    generate notifications for the user.
    """

    def __init__(self, name: str, check_interval_minutes: int = 60):
        """
        Initialize monitoring agent.

        Args:
            name: Unique name for this monitor
            check_interval_minutes: How often to perform checks
        """
        self.name = name
        self.check_interval = timedelta(minutes=check_interval_minutes)
        self.message_queue = MessageQueue()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_check = datetime.now() - self.check_interval  # Force immediate first check

        logger.info(f"Initialized monitor: {name} (checks every {check_interval_minutes}m)")

    def start(self):
        """Start the monitoring agent in a background thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True, name=f"Monitor-{self.name}")
        self.thread.start()
        logger.info(f"Started monitor: {self.name}")

    def stop(self):
        """Stop the monitoring agent."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"Stopped monitor: {self.name}")

    def _run_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                now = datetime.now()
                if now - self.last_check >= self.check_interval:
                    self._perform_check()
                    self.last_check = now

                # Sleep for 30 seconds between checks
                time.sleep(30)

            except Exception as e:
                logger.error(f"Error in monitor {self.name}: {e}")
                time.sleep(60)  # Sleep longer on error

    @abstractmethod
    def _perform_check(self):
        """
        Perform the actual monitoring check.

        This method should be implemented by subclasses to perform
        the specific monitoring logic and generate messages as needed.
        """

    def _send_message(self, message_type: MessageType, title: str,
                     content: str = "", priority: MessagePriority = MessagePriority.NORMAL,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Send a message to the message queue.

        Args:
            message_type: Type of message (system or code)
            title: Brief title/summary
            content: Detailed message content
            priority: Message priority level
            metadata: Additional structured data
        """
        try:
            message_id = self.message_queue.add_message(
                message_type, title, content, priority, metadata
            )
            logger.info(f"Monitor {self.name} sent {message_type.value} message: {title}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to send message from monitor {self.name}: {e}")
            return None