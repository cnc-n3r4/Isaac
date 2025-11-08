# isaac/queue/sync_worker.py

"""
Sync Worker - Background thread for automatic command queue sync.

Monitors cloud availability and syncs pending commands when online.
"""

import threading
import time
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class SyncWorker:
    """Background thread that syncs queued commands when cloud is available."""

    def __init__(self, queue, cloud_client, check_interval: int = 30):
        """
        Initialize sync worker.

        Args:
            queue: CommandQueue instance
            cloud_client: CloudClient instance (must have is_available() method)
            check_interval: Seconds between availability checks
        """
        self.queue = queue
        self.cloud = cloud_client
        self.interval = check_interval
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.on_sync_complete: Optional[Callable[[int], None]] = None
        logger.info(f"Sync worker initialized (check every {check_interval}s)")

    def start(self):
        """Start background sync thread."""
        if self.running:
            logger.warning("Sync worker already running")
            return

        self.running = True
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()
        logger.info("Sync worker started")

    def stop(self):
        """Stop background thread gracefully."""
        if not self.running:
            return

        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Sync worker stopped")

    def force_sync(self) -> int:
        """
        Force immediate sync attempt (for /sync command).

        Returns:
            Number of commands successfully synced
        """
        logger.info("Force sync requested")
        return self._sync_batch()

    def _sync_loop(self):
        """Main background loop with exponential backoff."""
        consecutive_failures = 0

        while self.running:
            try:
                # Reset stale 'syncing' states (in case of crash)
                self.queue.reset_stale_syncing()

                # Check cloud availability
                if not self._is_cloud_available():
                    time.sleep(self.interval)
                    continue

                # Attempt batch sync
                synced_count = self._sync_batch()

                if synced_count > 0:
                    consecutive_failures = 0  # Reset backoff
                    logger.info(f"Successfully synced {synced_count} commands")

                    # Notify UI
                    if self.on_sync_complete:
                        self.on_sync_complete(synced_count)

            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Sync loop error: {e}")

            # Exponential backoff on failures (max 5 minutes)
            wait_time = min(self.interval * (2 ** consecutive_failures), 300)
            time.sleep(wait_time)

    def _is_cloud_available(self) -> bool:
        """Check if cloud API is reachable."""
        try:
            return self.cloud.is_available()
        except Exception as e:
            logger.debug(f"Cloud availability check failed: {e}")
            return False

    def _sync_batch(self, batch_size: int = 10) -> int:
        """
        Sync up to N pending commands.

        Args:
            batch_size: Max commands to sync in one batch

        Returns:
            Number successfully synced
        """
        pending = self.queue.dequeue_pending(limit=batch_size)

        if not pending:
            return 0

        synced_count = 0

        for cmd in pending:
            queue_id = cmd['id']

            try:
                # Mark as syncing (prevents duplicate processing)
                self.queue.mark_syncing(queue_id)

                # Execute sync based on command type
                success = self._sync_command(cmd)

                if success:
                    self.queue.mark_done(queue_id)
                    synced_count += 1
                else:
                    self.queue.mark_failed(queue_id, "Sync returned false")

            except Exception as e:
                self.queue.mark_failed(queue_id, str(e))
                logger.error(f"Failed to sync command #{queue_id}: {e}")

        return synced_count

    def _sync_command(self, cmd: dict) -> bool:
        """
        Execute sync for a single command.

        Args:
            cmd: Command dict from queue

        Returns:
            True if successfully synced
        """
        command_type = cmd['command_type']
        command_text = cmd['command_text']
        target_device = cmd['target_device']

        if command_type == 'device_route':
            # Route to target device via cloud
            return self.cloud.route_command(target_device, command_text)

        elif command_type == 'meta':
            # Meta-command that needs cloud (e.g., /sync-history)
            return self.cloud.execute_cloud_meta(command_text)

        elif command_type == 'shell':
            # Shell command that was queued (rare, but possible)
            # Log to cloud history for roaming
            return self.cloud.log_command_history(command_text)

        else:
            logger.warning(f"Unknown command type: {command_type}")
            return False