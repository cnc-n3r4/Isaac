# isaac/runtime/security_enforcer.py

import os
import signal
import subprocess
import threading
import time
from typing import Dict, List, Optional, Tuple


class SecurityEnforcer:
    """Enforces security boundaries and resource limits for command execution"""

    def __init__(self):
        self.active_processes = {}  # pid → process info

    def enforce_timeout(self, process: subprocess.Popen, timeout_ms: int) -> bool:
        """Kill process if it exceeds timeout. Returns True if killed."""
        timeout_sec = timeout_ms / 1000.0

        def timeout_handler():
            time.sleep(timeout_sec)
            if process.poll() is None:  # Still running
                try:
                    if os.name == "nt":  # Windows
                        process.terminate()
                        time.sleep(0.1)
                        if process.poll() is None:
                            process.kill()
                    else:  # Unix-like
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        time.sleep(0.1)
                        if process.poll() is None:
                            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except Exception:
                    pass  # Process may have already exited

        timer = threading.Thread(target=timeout_handler, daemon=True)
        timer.start()

        try:
            process.wait(timeout=timeout_sec + 0.5)  # Wait a bit longer than timeout
            return False  # Process completed normally
        except subprocess.TimeoutExpired:
            return True  # Process was killed due to timeout

    def cap_stdout(self, output: str, max_kib: int) -> Tuple[str, bool]:
        """Truncate output if it exceeds limit. Returns (output, truncated)"""
        max_bytes = max_kib * 1024
        if len(output.encode("utf-8")) <= max_bytes:
            return output, False

        # Truncate to fit within limit
        truncated = output.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
        return truncated, True

    def check_allowlist(self, manifest: Dict, platform: str) -> bool:
        """Verify binary is in platform allowlist"""
        # For now, allow all - implement platform-specific allowlists later
        # This would check manifest.runtime.interpreter against allowed binaries
        return True

    def sanitize_env(self, env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Clean environment variables for security"""
        if env is None:
            env = os.environ.copy()

        # Remove potentially dangerous variables
        dangerous_vars = [
            "LD_PRELOAD",
            "LD_LIBRARY_PATH",  # Linux
            "DYLD_LIBRARY_PATH",
            "DYLD_INSERT_LIBRARIES",  # macOS
            "PATH",  # Could be manipulated
        ]

        sanitized = {}
        for key, value in env.items():
            if key not in dangerous_vars:
                sanitized[key] = value

        # Ensure minimal PATH
        if "PATH" not in sanitized:
            sanitized["PATH"] = os.environ.get("PATH", "")

        return sanitized

    def redact_patterns(self, text: str, patterns: List[str]) -> str:
        """Apply redaction patterns to output"""
        import re

        redacted = text
        for pattern in patterns:
            try:
                redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.IGNORECASE)
            except re.error:
                # Invalid regex pattern, skip
                continue

        return redacted

    def validate_resources(self, manifest: Dict) -> Tuple[bool, str]:
        """Validate resource limits in manifest"""
        resources = manifest.get("security", {}).get("resources", {})

        timeout_ms = resources.get("timeout_ms", 5000)
        max_stdout_kib = resources.get("max_stdout_kib", 64)

        if timeout_ms < 100:
            return False, "timeout_ms must be at least 100ms"

        if max_stdout_kib < 1:
            return False, "max_stdout_kib must be at least 1"

        return True, ""
