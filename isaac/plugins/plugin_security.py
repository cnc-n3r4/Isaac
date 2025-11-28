"""Plugin Security - Sandboxed plugin execution and security policies."""

import platform
import signal
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

# resource module is Unix-only
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False
    # Provide stub for Windows
    class resource:
        """Stub for Unix resource module on Windows"""
        RLIMIT_AS = 0
        RLIMIT_CPU = 1
        RLIMIT_FSIZE = 2
        
        @staticmethod
        def setrlimit(limit_type, limits):
            pass  # No-op on Windows
        
        @staticmethod
        def getrlimit(limit_type):
            return (-1, -1)  # Unlimited on Windows


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
    blocked_modules: Set[str] = field(
        default_factory=lambda: {
            "os.system",
            "subprocess",
            "socket",
            "http",
            "urllib",
            "requests",
        }
    )

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

    def execute(self, func: Callable, *args, timeout: Optional[int] = None, **kwargs) -> Any:
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
                        resource.RLIMIT_CPU, (self.policy.max_cpu_time, self.policy.max_cpu_time)
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
            original_import = __builtins__["__import__"]
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
                        file_path.startswith(path) for path in self.policy.allowed_write_paths
                    )
                    if not allowed:
                        raise PermissionError(f"Write access to '{file_path}' is not allowed")

            # Check read permissions
            if "r" in mode:
                if not self.policy.allow_file_read:
                    raise PermissionError(f"File read is not allowed")

                # Check if path is in allowed read paths
                if self.policy.allowed_read_paths:
                    allowed = any(
                        file_path.startswith(path) for path in self.policy.allowed_read_paths
                    )
                    if not allowed:
                        raise PermissionError(f"Read access to '{file_path}' is not allowed")

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


class APIKeyManager:
    """Manage API keys for plugins with security validation."""

    def __init__(self):
        """Initialize API key manager."""
        self._api_keys: Dict[str, Dict[str, str]] = {}  # plugin_name -> {service: key}
        self._key_permissions: Dict[str, Set[str]] = {}  # plugin_name -> allowed_services

    def register_key(self, plugin_name: str, service: str, api_key: str) -> None:
        """Register an API key for a plugin and service.

        Args:
            plugin_name: Plugin name
            service: API service name (e.g., 'openai', 'anthropic')
            api_key: API key to store
        """
        if plugin_name not in self._api_keys:
            self._api_keys[plugin_name] = {}
        self._api_keys[plugin_name][service] = api_key

    def grant_service_access(self, plugin_name: str, service: str) -> None:
        """Grant access to a specific API service.

        Args:
            plugin_name: Plugin name
            service: API service name
        """
        if plugin_name not in self._key_permissions:
            self._key_permissions[plugin_name] = set()
        self._key_permissions[plugin_name].add(service)

    def revoke_service_access(self, plugin_name: str, service: str) -> None:
        """Revoke access to a specific API service.

        Args:
            plugin_name: Plugin name
            service: API service name
        """
        if plugin_name in self._key_permissions:
            self._key_permissions[plugin_name].discard(service)

    def get_key(self, plugin_name: str, service: str) -> Optional[str]:
        """Get API key for a plugin and service.

        Args:
            plugin_name: Plugin name
            service: API service name

        Returns:
            API key if available and permitted, None otherwise
        """
        # Check if plugin has permission for this service
        if plugin_name not in self._key_permissions:
            return None
        if service not in self._key_permissions[plugin_name]:
            return None

        # Return key if it exists
        plugin_keys = self._api_keys.get(plugin_name, {})
        return plugin_keys.get(service)

    def has_service_access(self, plugin_name: str, service: str) -> bool:
        """Check if plugin has access to a service.

        Args:
            plugin_name: Plugin name
            service: API service name

        Returns:
            True if access is granted
        """
        return service in self._key_permissions.get(plugin_name, set())

    def list_services(self, plugin_name: str) -> Set[str]:
        """List all services a plugin has access to.

        Args:
            plugin_name: Plugin name

        Returns:
            Set of service names
        """
        return self._key_permissions.get(plugin_name, set()).copy()

    def validate_key_format(self, service: str, api_key: str) -> bool:
        """Validate API key format for a service.

        Args:
            service: API service name
            api_key: API key to validate

        Returns:
            True if key format is valid
        """
        # Basic validation patterns (can be extended)
        patterns = {
            'openai': lambda k: k.startswith('sk-') and len(k) > 20,
            'anthropic': lambda k: k.startswith('sk-ant-') and len(k) > 30,
            'xai': lambda k: len(k) > 10,  # XAI keys vary
            'claude': lambda k: k.startswith('sk-ant-') and len(k) > 30,
        }

        validator = patterns.get(service.lower())
        if validator:
            return validator(api_key)
        return len(api_key) > 10  # Default validation

    def secure_store_key(self, plugin_name: str, service: str, api_key: str) -> bool:
        """Securely store an API key with validation.

        Args:
            plugin_name: Plugin name
            service: API service name
            api_key: API key to store

        Returns:
            True if key was stored successfully
        """
        if not self.validate_key_format(service, api_key):
            return False

        self.register_key(plugin_name, service, api_key)
        self.grant_service_access(plugin_name, service)
        return True

    def remove_key(self, plugin_name: str, service: str) -> None:
        """Remove an API key and revoke access.

        Args:
            plugin_name: Plugin name
            service: API service name
        """
        if plugin_name in self._api_keys:
            self._api_keys[plugin_name].pop(service, None)
        self.revoke_service_access(plugin_name, service)
