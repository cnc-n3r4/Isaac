"""Plugin API - Base classes and interfaces for Isaac plugins."""

import abc
import enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime


class PluginError(Exception):
    """Base exception for plugin errors."""


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""


class PluginSecurityError(PluginError):
    """Raised when a plugin violates security constraints."""


class PluginHook(enum.Enum):
    """Available plugin hooks."""

    # Lifecycle hooks
    STARTUP = "startup"
    SHUTDOWN = "shutdown"

    # Command hooks
    BEFORE_COMMAND = "before_command"
    AFTER_COMMAND = "after_command"
    COMMAND_ERROR = "command_error"

    # File hooks
    FILE_CHANGED = "file_changed"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"

    # AI hooks
    BEFORE_AI_QUERY = "before_ai_query"
    AFTER_AI_RESPONSE = "after_ai_response"

    # Debug hooks
    DEBUG_START = "debug_start"
    DEBUG_COMPLETE = "debug_complete"

    # Pipeline hooks
    PIPELINE_START = "pipeline_start"
    PIPELINE_COMPLETE = "pipeline_complete"

    # Memory hooks
    MEMORY_SAVE = "memory_save"
    MEMORY_LOAD = "memory_load"

    # Custom hooks
    CUSTOM = "custom"


@dataclass
class PluginMetadata:
    """Plugin metadata and configuration."""

    # Required fields
    name: str
    version: str
    author: str
    description: str

    # Optional fields
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # Dependencies
    requires_isaac_version: Optional[str] = None
    requires_python_version: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    # Capabilities
    hooks: List[PluginHook] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)

    # Installation info
    install_date: Optional[datetime] = None
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "homepage": self.homepage,
            "repository": self.repository,
            "license": self.license,
            "tags": self.tags,
            "requires_isaac_version": self.requires_isaac_version,
            "requires_python_version": self.requires_python_version,
            "dependencies": self.dependencies,
            "hooks": [h.value for h in self.hooks],
            "commands": self.commands,
            "permissions": self.permissions,
            "install_date": self.install_date.isoformat() if self.install_date else None,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginMetadata":
        """Create metadata from dictionary."""
        # Convert hooks from strings to enum
        hooks = [PluginHook(h) for h in data.get("hooks", [])]

        # Parse install date
        install_date = None
        if data.get("install_date"):
            install_date = datetime.fromisoformat(data["install_date"])

        return cls(
            name=data["name"],
            version=data["version"],
            author=data["author"],
            description=data["description"],
            homepage=data.get("homepage"),
            repository=data.get("repository"),
            license=data.get("license"),
            tags=data.get("tags", []),
            requires_isaac_version=data.get("requires_isaac_version"),
            requires_python_version=data.get("requires_python_version"),
            dependencies=data.get("dependencies", []),
            hooks=hooks,
            commands=data.get("commands", []),
            permissions=data.get("permissions", []),
            install_date=install_date,
            enabled=data.get("enabled", True),
        )


@dataclass
class PluginContext:
    """Context provided to plugins during execution."""

    # Session information
    session_id: str
    workspace_path: str

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # State storage (plugin can store data here)
    state: Dict[str, Any] = field(default_factory=dict)

    # Event data (for hook executions)
    event_data: Dict[str, Any] = field(default_factory=dict)

    # Available APIs
    apis: Dict[str, Any] = field(default_factory=dict)

    def get_api(self, name: str) -> Optional[Any]:
        """Get an API by name."""
        return self.apis.get(name)

    def has_permission(self, permission: str) -> bool:
        """Check if plugin has a specific permission."""
        return permission in self.config.get("permissions", [])


class Plugin(abc.ABC):
    """Base class for all Isaac plugins.

    Plugin developers should subclass this and implement:
    - metadata property
    - initialize() method
    - shutdown() method (optional)
    - Hook handlers for desired hooks
    """

    def __init__(self):
        """Initialize the plugin."""
        self._context: Optional[PluginContext] = None
        self._hooks: Dict[PluginHook, List[Callable]] = {}
        self._enabled = True

    @property
    @abc.abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        This must be implemented by all plugins.
        """

    @abc.abstractmethod
    def initialize(self, context: PluginContext) -> None:
        """Initialize the plugin with context.

        This is called when the plugin is loaded.

        Args:
            context: Plugin context with configuration and APIs
        """

    def shutdown(self) -> None:
        """Clean up plugin resources.

        This is called when the plugin is being unloaded.
        Optional to implement.
        """

    def register_hook(self, hook: PluginHook, handler: Callable) -> None:
        """Register a handler for a hook.

        Args:
            hook: The hook to register for
            handler: The function to call when hook fires
        """
        if hook not in self._hooks:
            self._hooks[hook] = []
        self._hooks[hook].append(handler)

    def get_hooks(self, hook: PluginHook) -> List[Callable]:
        """Get all handlers for a specific hook.

        Args:
            hook: The hook to get handlers for

        Returns:
            List of handler functions
        """
        return self._hooks.get(hook, [])

    def get_all_hooks(self) -> Set[PluginHook]:
        """Get all hooks this plugin has registered handlers for.

        Returns:
            Set of registered hooks
        """
        return set(self._hooks.keys())

    def enable(self) -> None:
        """Enable the plugin."""
        self._enabled = True

    def disable(self) -> None:
        """Disable the plugin."""
        self._enabled = False

    @property
    def enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._enabled

    @property
    def context(self) -> Optional[PluginContext]:
        """Get the plugin context."""
        return self._context

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a value from plugin state.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        if self._context:
            return self._context.state.get(key, default)
        return default

    def set_state(self, key: str, value: Any) -> None:
        """Set a value in plugin state.

        Args:
            key: State key
            value: State value
        """
        if self._context:
            self._context.state[key] = value

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Config key
            default: Default value if key not found

        Returns:
            Config value or default
        """
        if self._context:
            return self._context.config.get(key, default)
        return default
