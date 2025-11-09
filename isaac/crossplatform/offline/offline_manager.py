"""
Offline Manager - Manages offline/online state and synchronization
"""

import asyncio
import socket
from datetime import datetime
from typing import Any, Callable, Dict


class OfflineManager:
    """
    Manages offline mode functionality and connectivity detection
    """

    def __init__(self, sync_queue, cache_manager):
        self.sync_queue = sync_queue
        self.cache_manager = cache_manager

        self.is_online = True
        self.last_online = datetime.utcnow().isoformat()
        self.last_sync = None

        self.connectivity_callbacks: list[Callable] = []

    async def start_monitoring(self, interval: int = 30):
        """
        Start monitoring network connectivity

        Args:
            interval: Check interval in seconds
        """
        while True:
            await self._check_connectivity()
            await asyncio.sleep(interval)

    async def _check_connectivity(self):
        """Check if internet connection is available"""
        previous_state = self.is_online

        try:
            # Try to connect to common DNS servers
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            self.is_online = True
            self.last_online = datetime.utcnow().isoformat()

        except OSError:
            self.is_online = False

        # If state changed, trigger callbacks
        if previous_state != self.is_online:
            await self._handle_connectivity_change(previous_state, self.is_online)

    async def _handle_connectivity_change(self, was_online: bool, is_now_online: bool):
        """
        Handle connectivity state change

        Args:
            was_online: Previous online state
            is_now_online: Current online state
        """
        if is_now_online and not was_online:
            # Just came back online
            print("Connection restored. Starting sync...")
            await self._sync_queued_operations()

        elif not is_now_online and was_online:
            # Just went offline
            print("Connection lost. Entering offline mode...")

        # Notify callbacks
        for callback in self.connectivity_callbacks:
            try:
                await callback(is_now_online)
            except Exception as e:
                print(f"Error in connectivity callback: {e}")

    async def _sync_queued_operations(self):
        """Sync all queued operations when coming back online"""
        try:
            result = await self.sync_queue.process_all()

            self.last_sync = datetime.utcnow().isoformat()

            print(f"Sync complete: {result['processed']} operations synced")

        except Exception as e:
            print(f"Error during sync: {e}")

    def register_connectivity_callback(self, callback: Callable):
        """
        Register a callback for connectivity changes

        Args:
            callback: Async function called with online state
        """
        self.connectivity_callbacks.append(callback)

    def get_status(self) -> Dict[str, Any]:
        """Get offline mode status"""
        return {
            "is_online": self.is_online,
            "last_online": self.last_online,
            "last_sync": self.last_sync,
            "queued_operations": self.sync_queue.get_queue_size(),
            "cache_size": self.cache_manager.get_cache_size(),
        }

    async def force_sync(self) -> Dict[str, Any]:
        """Force synchronization regardless of online state"""
        if not self.is_online:
            return {"success": False, "error": "Cannot sync while offline"}

        return await self._sync_queued_operations()

    def enable_offline_mode(self):
        """Manually enable offline mode"""
        self.is_online = False

    def disable_offline_mode(self):
        """Manually disable offline mode"""
        self.is_online = True

    async def queue_operation(
        self, operation_type: str, data: Dict[str, Any], priority: int = 5
    ) -> str:
        """
        Queue an operation for later sync

        Args:
            operation_type: Type of operation
            data: Operation data
            priority: Priority (1-10, higher = more important)

        Returns:
            Operation ID
        """
        return await self.sync_queue.add(operation_type, data, priority)

    async def execute_with_fallback(
        self, online_func: Callable, offline_func: Callable, *args, **kwargs
    ) -> Any:
        """
        Execute function with online/offline fallback

        Args:
            online_func: Function to call when online
            offline_func: Function to call when offline
            *args: Arguments to pass
            **kwargs: Keyword arguments to pass

        Returns:
            Function result
        """
        if self.is_online:
            try:
                return await online_func(*args, **kwargs)
            except Exception as e:
                print(f"Online function failed: {e}, falling back to offline")
                return await offline_func(*args, **kwargs)
        else:
            return await offline_func(*args, **kwargs)
