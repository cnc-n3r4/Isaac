"""
Background task scheduler for periodic jobs.
"""
import threading
import time
import logging
from typing import Callable, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CronManager:
    """Simple cron-like scheduler for background tasks."""
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.running = False
        self._thread = None
    
    def register_task(self, name: str, func: Callable, 
                      interval_minutes: int, run_immediately: bool = False):
        """
        Register periodic task.
        
        Args:
            name: Unique task name
            func: Callable to execute
            interval_minutes: Run every N minutes
            run_immediately: Run on registration
        """
        self.tasks[name] = {
            "func": func,
            "interval": timedelta(minutes=interval_minutes),
            "last_run": datetime.now() if run_immediately else None,
            "next_run": datetime.now() if run_immediately else 
                        datetime.now() + timedelta(minutes=interval_minutes)
        }
        logger.info(f"Registered task: {name} (every {interval_minutes}m)")
    
    def start(self):
        """Start scheduler thread."""
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Cron manager started")
    
    def stop(self):
        """Stop scheduler gracefully."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Cron manager stopped")
    
    def _run_loop(self):
        """Main scheduler loop."""
        while self.running:
            now = datetime.now()
            
            for task_name, task in self.tasks.items():
                if now >= task['next_run']:
                    try:
                        logger.debug(f"Running task: {task_name}")
                        task['func']()
                        task['last_run'] = now
                        task['next_run'] = now + task['interval']
                    except Exception as e:
                        logger.error(f"Task {task_name} failed: {e}")
            
            # Check every 60 seconds
            time.sleep(60)
