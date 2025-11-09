"""Plugin Security - Sandboxed plugin execution and security policies."""

import resource
import signal
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class SecurityPolicy:
    """Security policy for plugin execution."""

    # Resource limits
    max_memory_mb: int = 100  # Max memory in MB
    max_cpu_time: int = 5  # Max CPU time in seconds
    max_file_size_mb: int = 10  # Max file size in MB

    # Permissions
    allow_network: bool = False
    allow_subprocess: bool = False
    allow_file_write: bool = False
    allow_file_read: bool = True

    # Allowed paths
    allowed_read_paths: Set[str] = field(default_factory=set)
    allowed_write_paths: Set[str] = field(default_factory=set)

    # Blocked modules
    blocked_modules: Set[str] = field(default_factory=lambda: {
        "os.system",
        "subprocess",
        "socket",
        "http",
        "urllib",
        "requests",
    })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_memory_mb": self.max_memory_mb,
            "max_cpu_time": self.max_cpu_time,
            "max_file_size_mb": self.max_file_size_mb,
            "allow_network": self.allow_network,
            "allow_subprocess": self.allow_subprocess,
            "allow_file_write": self.allow_file_write,
            "allow_file_read": self.allow_file_read,
            "allowed_read_paths": list(self.allowed_read_paths),
            "allowed_write_paths": list(self.allowed_write_paths),
            "blocked_modules": list(self.blocked_modules),
        }


class PluginSandbox:
    """Sandbox for secure plugin execution."""

    def __init__(self, policy: Optional[SecurityPolicy] = None):
        """Initialize sandbox with security policy.

        Args:
            policy: Security policy (uses default if None)
        """
        self.policy = policy or SecurityPolicy()
        self._original_import = None

    def execute(
        self,
        func: Callable,
        *args,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Any:
        """Execute a function in a sandboxed environment.

        Args:
            func: Function to execute
            *args: Positional arguments
            timeout: Timeout in seconds (uses policy default if None)
            **kwargs: Keyword arguments

        Returns:
            Function return value

        Raises:
            TimeoutError: If execution exceeds timeout
            MemoryError: If execution exceeds memory limit
            PermissionError: If function violates security policy
        """
        timeout = timeout or self.policy.max_cpu_time

        # Set resource limits
        with self._resource_limits():
            # Set timeout
            with self._timeout(timeout):
                # Hook imports
                with self._import_guard():
                    # Hook file operations
                    with self._file_guard():
                        return func(*args, **kwargs)

    @contextmanager
    def _resource_limits(self):
        """Context manager for resource limits."""
        # Save original limits
        original_limits = {}

        try:
            # Set memory limit (if supported)
            if hasattr(resource, "RLIMIT_AS"):
                try:
                    original_limits["memory"] = resource.getrlimit(resource.RLIMIT_AS)
                    memory_bytes = self.policy.max_memory_mb * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
                except (ValueError, OSError):
                    # Can't set limit (e.g., in test environment or insufficient permissions)
                    pass

            # Set CPU time limit
            if hasattr(resource, "RLIMIT_CPU"):
                try:
                    original_limits["cpu"] = resource.getrlimit(resource.RLIMIT_CPU)
                    resource.setrlimit(
                        resource.RLIMIT_CPU,
                        (self.policy.max_cpu_time, self.policy.max_cpu_time)
                    )
                except (ValueError, OSError):
                    # Can't set limit
                    pass

            yield

        finally:
            # Restore original limits
            if "memory" in original_limits and hasattr(resource, "RLIMIT_AS"):
                try:
                    resource.setrlimit(resource.RLIMIT_AS, original_limits["memory"])
                except (ValueError, OSError):
                    pass
            if "cpu" in original_limits and hasattr(resource, "RLIMIT_CPU"):
                try:
                    resource.setrlimit(resource.RLIMIT_CPU, original_limits["cpu"])
                except (ValueError, OSError):
                    pass

    @contextmanager
    def _timeout(self, seconds: int):
        """Context manager for execution timeout."""

        def timeout_handler(signum, frame):
            raise TimeoutError(f"Plugin execution exceeded {seconds} seconds")

        # Only works on Unix-like systems
        if hasattr(signal, "SIGALRM"):
            # Save original handler
            original_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)

            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, original_handler)
        else:
            # No timeout on Windows
            yield

    @contextmanager
    def _import_guard(self):
        """Context manager to guard against dangerous imports."""
        import builtins

        # Handle __builtins__ which can be dict or module
        if isinstance(__builtins__, dict):
            original_import = __builtins__['__import__']
        else:
            original_import = __builtins__.__import__

        def guarded_import(name, *args, **kwargs):
            # Check if module is blocked
            if name in self.policy.blocked_modules:
                raise PermissionError(f"Import of module '{name}' is not allowed")

            # Check for network modules
            if not self.policy.allow_network:
                network_modules = {"socket", "http", "urllib", "requests", "aiohttp"}
                if name in network_modules or name.startswith(tuple(network_modules)):
                    raise PermissionError(f"Network access is not allowed")

            # Check for subprocess
            if not self.policy.allow_subprocess:
                if name == "subprocess" or name.startswith("subprocess."):
                    raise PermissionError(f"Subprocess execution is not allowed")

            return original_import(name, *args, **kwargs)

        # Use builtins module for consistency
        builtins.__import__ = guarded_import

        try:
            yield
        finally:
            builtins.__import__ = original_import

    @contextmanager
    def _file_guard(self):
        """Context manager to guard file operations."""
        original_open = open

        def guarded_open(file, mode="r", *args, **kwargs):
            file_path = str(file)

            # Check write permissions
            if "w" in mode or "a" in mode or "+" in mode:
                if not self.policy.allow_file_write:
                    raise PermissionError(f"File write is not allowed")

                # Check if path is in allowed write paths
                if self.policy.allowed_write_paths:
                    allowed = any(
                        file_path.startswith(path)
                        for path in self.policy.allowed_write_paths
                    )
                    if not allowed:
                        raise PermissionError(
                            f"Write access to '{file_path}' is not allowed"
                        )

            # Check read permissions
            if "r" in mode:
                if not self.policy.allow_file_read:
                    raise PermissionError(f"File read is not allowed")

                # Check if path is in allowed read paths
                if self.policy.allowed_read_paths:
                    allowed = any(
                        file_path.startswith(path)
                        for path in self.policy.allowed_read_paths
                    )
                    if not allowed:
                        raise PermissionError(
                            f"Read access to '{file_path}' is not allowed"
                        )

            return original_open(file, mode, *args, **kwargs)

        # Replace open
        import builtins
        builtins.open = guarded_open

        try:
            yield
        finally:
            builtins.open = original_open

    def validate_plugin_code(self, code: str) -> List[str]:
        """Validate plugin code for security issues.

        Args:
            code: Plugin code to validate

        Returns:
            List of security warnings
        """
        warnings = []

        # Check for dangerous imports
        dangerous_imports = [
            "os.system",
            "subprocess",
            "eval",
            "exec",
            "__import__",
            "compile",
        ]

        for dangerous in dangerous_imports:
            if dangerous in code:
                warnings.append(f"Potentially dangerous: {dangerous}")

        # Check for file operations
        if not self.policy.allow_file_write:
            file_writes = ["open(", "write(", "writelines("]
            for write_op in file_writes:
                if write_op in code:
                    warnings.append(f"File write operation detected: {write_op}")

        # Check for network operations
        if not self.policy.allow_network:
            network_ops = ["socket", "http", "urllib", "requests"]
            for net_op in network_ops:
                if net_op in code:
                    warnings.append(f"Network operation detected: {net_op}")

        return warnings


class PermissionManager:
    """Manage plugin permissions."""

    # Standard permission types
    PERMISSION_FILE_READ = "file:read"
    PERMISSION_FILE_WRITE = "file:write"
    PERMISSION_NETWORK = "network"
    PERMISSION_SUBPROCESS = "subprocess"
    PERMISSION_SYSTEM = "system"

    def __init__(self):
        """Initialize permission manager."""
        self._granted_permissions: Dict[str, Set[str]] = {}

    def grant(self, plugin_name: str, permission: str) -> None:
        """Grant a permission to a plugin.

        Args:
            plugin_name: Plugin name
            permission: Permission to grant
        """
        if plugin_name not in self._granted_permissions:
            self._granted_permissions[plugin_name] = set()
        self._granted_permissions[plugin_name].add(permission)

    def revoke(self, plugin_name: str, permission: str) -> None:
        """Revoke a permission from a plugin.

        Args:
            plugin_name: Plugin name
            permission: Permission to revoke
        """
        if plugin_name in self._granted_permissions:
            self._granted_permissions[plugin_name].discard(permission)

    def has_permission(self, plugin_name: str, permission: str) -> bool:
        """Check if plugin has a permission.

        Args:
            plugin_name: Plugin name
            permission: Permission to check

        Returns:
            True if plugin has permission
        """
        return permission in self._granted_permissions.get(plugin_name, set())

    def get_permissions(self, plugin_name: str) -> Set[str]:
        """Get all permissions for a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            Set of permissions
        """
        return self._granted_permissions.get(plugin_name, set()).copy()

    def create_policy(self, plugin_name: str) -> SecurityPolicy:
        """Create a security policy based on granted permissions.

        Args:
            plugin_name: Plugin name

        Returns:
            Security policy
        """
        permissions = self.get_permissions(plugin_name)

        return SecurityPolicy(
            allow_network=self.PERMISSION_NETWORK in permissions,
            allow_subprocess=self.PERMISSION_SUBPROCESS in permissions,
            allow_file_write=self.PERMISSION_FILE_WRITE in permissions,
            allow_file_read=self.PERMISSION_FILE_READ in permissions,
        )
