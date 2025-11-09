#!/usr/bin/env python3
"""
Fallback Manager - Graceful degradation when services are unavailable

Handles API failures, network issues, and provides fallback strategies
for critical ISAAC functionality.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ServiceStatus:
    """Track service availability status"""

    def __init__(self, name: str):
        self.name = name
        self.available = True
        self.last_success: Optional[datetime] = None
        self.last_failure: Optional[datetime] = None
        self.consecutive_failures = 0
        self.failure_threshold = 3  # Mark unavailable after 3 consecutive failures
        self.recovery_check_interval = timedelta(minutes=5)

    def record_success(self):
        """Record successful service call"""
        self.available = True
        self.last_success = datetime.now()
        self.consecutive_failures = 0
        logger.debug(f"Service {self.name}: Success")

    def record_failure(self, error: str):
        """Record service failure"""
        self.last_failure = datetime.now()
        self.consecutive_failures += 1

        if self.consecutive_failures >= self.failure_threshold:
            if self.available:
                logger.warning(
                    f"Service {self.name}: Marked unavailable after {self.consecutive_failures} failures"
                )
                self.available = False
        else:
            logger.debug(
                f"Service {self.name}: Failure ({self.consecutive_failures}/{self.failure_threshold}): {error}"
            )

    def should_retry(self) -> bool:
        """Check if service should be retried"""
        if self.available:
            return True

        # If service is unavailable, only retry after recovery interval
        if self.last_failure:
            time_since_failure = datetime.now() - self.last_failure
            if time_since_failure >= self.recovery_check_interval:
                logger.info(f"Service {self.name}: Attempting recovery check")
                return True

        return False

    def get_status(self) -> Dict[str, Any]:
        """Get service status info"""
        return {
            "name": self.name,
            "available": self.available,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "consecutive_failures": self.consecutive_failures,
        }


class FallbackManager:
    """
    Manages service fallbacks and graceful degradation

    Features:
    - Service health tracking
    - Automatic fallback routing
    - Recovery detection
    - Offline operation queue
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize fallback manager

        Args:
            config_path: Path to fallback configuration
        """
        if config_path is None:
            config_path = Path.home() / ".isaac" / "fallback.json"

        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Service status tracking
        self.services: Dict[str, ServiceStatus] = {}

        # Offline operation queue
        self.offline_queue: list = []

        # Load persisted state
        self._load_state()

        logger.info("Fallback manager initialized")

    def _load_state(self):
        """Load persisted service state"""
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)

            # Load offline queue
            self.offline_queue = data.get("offline_queue", [])

            logger.info(f"Loaded fallback state: {len(self.offline_queue)} queued operations")

        except Exception as e:
            logger.error(f"Failed to load fallback state: {e}")

    def _save_state(self):
        """Persist service state"""
        try:
            data = {"offline_queue": self.offline_queue, "last_updated": datetime.now().isoformat()}

            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save fallback state: {e}")

    def get_service(self, name: str) -> ServiceStatus:
        """Get or create service status tracker"""
        if name not in self.services:
            self.services[name] = ServiceStatus(name)
        return self.services[name]

    def call_with_fallback(
        self,
        service_name: str,
        primary_fn: Callable,
        fallback_fn: Optional[Callable] = None,
        queue_on_failure: bool = False,
    ) -> Dict[str, Any]:
        """
        Call service with automatic fallback

        Args:
            service_name: Service identifier
            primary_fn: Primary service function
            fallback_fn: Optional fallback function
            queue_on_failure: Queue operation for later retry

        Returns:
            Service response with fallback info
        """
        service = self.get_service(service_name)

        # Check if service should be attempted
        if not service.should_retry():
            logger.info(f"Service {service_name} unavailable, using fallback immediately")
            return self._execute_fallback(service_name, fallback_fn, queue_on_failure)

        # Attempt primary service
        try:
            result = primary_fn()
            service.record_success()

            return {"success": True, "result": result, "source": "primary", "service": service_name}

        except Exception as e:
            error_msg = str(e)
            service.record_failure(error_msg)

            logger.warning(f"Service {service_name} failed: {error_msg}")

            return self._execute_fallback(service_name, fallback_fn, queue_on_failure, error_msg)

    def _execute_fallback(
        self,
        service_name: str,
        fallback_fn: Optional[Callable],
        queue_on_failure: bool,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute fallback strategy"""

        # Try fallback function
        if fallback_fn:
            try:
                result = fallback_fn()
                return {
                    "success": True,
                    "result": result,
                    "source": "fallback",
                    "service": service_name,
                    "fallback_used": True,
                }
            except Exception as fb_error:
                logger.error(f"Fallback also failed for {service_name}: {fb_error}")

        # Queue for later if requested
        if queue_on_failure:
            self.queue_operation(
                service_name, {"timestamp": datetime.now().isoformat(), "error": error}
            )

        # Return failure
        return {
            "success": False,
            "service": service_name,
            "error": error or "Service unavailable",
            "fallback_used": fallback_fn is not None,
            "queued": queue_on_failure,
        }

    def queue_operation(self, operation_type: str, data: Dict[str, Any]):
        """Queue operation for later execution"""
        operation = {"type": operation_type, "data": data, "queued_at": datetime.now().isoformat()}

        self.offline_queue.append(operation)
        self._save_state()

        logger.info(f"Queued {operation_type} operation for later execution")

    def process_queue(self) -> Dict[str, Any]:
        """
        Process queued operations

        Returns:
            Processing statistics
        """
        if not self.offline_queue:
            return {"processed": 0, "succeeded": 0, "failed": 0, "remaining": 0}

        processed = 0
        succeeded = 0
        failed = 0
        remaining_queue = []

        logger.info(f"Processing {len(self.offline_queue)} queued operations")

        for operation in self.offline_queue:
            op_type = operation["type"]
            service = self.get_service(op_type)

            # Only retry if service appears available
            if service.should_retry():
                # TODO: Implement actual operation retry logic
                # For now, just keep in queue
                remaining_queue.append(operation)
                logger.debug(f"Kept {op_type} in queue (retry logic not implemented)")
            else:
                remaining_queue.append(operation)

            processed += 1

        self.offline_queue = remaining_queue
        self._save_state()

        return {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "remaining": len(remaining_queue),
        }

    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        return {
            "services": {name: svc.get_status() for name, svc in self.services.items()},
            "offline_queue": len(self.offline_queue),
        }

    def reset_service(self, service_name: str):
        """Reset service status (force availability check)"""
        if service_name in self.services:
            service = self.services[service_name]
            service.consecutive_failures = 0
            service.available = True
            logger.info(f"Reset service {service_name}")


# Global instance
_fallback_manager: Optional[FallbackManager] = None


def get_fallback_manager() -> FallbackManager:
    """Get or create global fallback manager instance"""
    global _fallback_manager

    if _fallback_manager is None:
        _fallback_manager = FallbackManager()

    return _fallback_manager


if __name__ == "__main__":
    # Test fallback manager
    logging.basicConfig(level=logging.DEBUG)

    manager = FallbackManager()

    print("=== Fallback Manager Test ===\n")

    # Test successful service call
    def success_fn():
        return "Success!"

    result = manager.call_with_fallback("test_service", success_fn)
    print(f"Successful call: {result}")

    # Test failing service with fallback
    def failing_fn():
        raise Exception("Service unavailable")

    def fallback_fn():
        return "Fallback result"

    result = manager.call_with_fallback("failing_service", failing_fn, fallback_fn)
    print(f"\nFailing call with fallback: {result}")

    # Test multiple failures to trigger unavailable
    for i in range(3):
        result = manager.call_with_fallback("unreliable_service", failing_fn, queue_on_failure=True)
        print(f"\nAttempt {i+1}: {result}")

    # Check status
    status = manager.get_all_status()
    print(f"\nService status:")
    for svc_name, svc_status in status["services"].items():
        print(
            f"  {svc_name}: available={svc_status['available']}, failures={svc_status['consecutive_failures']}"
        )

    print(f"\nQueued operations: {status['offline_queue']}")

    print(f"\n✓ Fallback state saved to: {manager.config_path}")
