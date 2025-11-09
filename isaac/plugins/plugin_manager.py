"""Plugin Manager - Install, update, remove, and manage plugins."""

import importlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from isaac.plugins.plugin_api import (
    Plugin,
    PluginMetadata,
    PluginContext,
    PluginHook,
    PluginLoadError,
)
from isaac.plugins.plugin_registry import PluginRegistry
from isaac.plugins.plugin_security import PluginSandbox


class PluginManager:
    """Manages plugin lifecycle: install, load, enable, disable, remove."""

    def __init__(
        self,
        plugins_dir: Optional[Path] = None,
        registry: Optional[PluginRegistry] = None,
        enable_sandbox: bool = True,
    ):
        """Initialize the plugin manager.

        Args:
            plugins_dir: Directory where plugins are installed
            registry: Plugin registry for discovering plugins
            enable_sandbox: Whether to enable sandboxed execution
        """
        self.plugins_dir = plugins_dir or Path.home() / ".isaac" / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        self.registry = registry or PluginRegistry()
        self.enable_sandbox = enable_sandbox

        # Installed plugins
        self._plugins: Dict[str, Plugin] = {}
        self._metadata: Dict[str, PluginMetadata] = {}

        # Hook subscriptions
        self._hook_handlers: Dict[PluginHook, List[tuple[str, Plugin]]] = {}

        # Plugin state
        self._contexts: Dict[str, PluginContext] = {}

        # Sandbox
        self._sandbox: Optional[PluginSandbox] = None
        if enable_sandbox:
            self._sandbox = PluginSandbox()

        # Load installed plugins
        self._load_installed_plugins()

    def _load_installed_plugins(self) -> None:
        """Load all installed plugins from disk."""
        metadata_file = self.plugins_dir / "installed.json"
        if not metadata_file.exists():
            return

        try:
            with open(metadata_file) as f:
                data = json.load(f)

            for plugin_name, metadata_dict in data.items():
                metadata = PluginMetadata.from_dict(metadata_dict)
                self._metadata[plugin_name] = metadata

                # Load plugin if enabled
                if metadata.enabled:
                    try:
                        self._load_plugin(plugin_name)
                    except PluginLoadError as e:
                        print(f"Failed to load plugin {plugin_name}: {e}")

        except Exception as e:
            print(f"Failed to load installed plugins: {e}")

    def _save_installed_plugins(self) -> None:
        """Save installed plugins metadata to disk."""
        metadata_file = self.plugins_dir / "installed.json"

        data = {name: meta.to_dict() for name, meta in self._metadata.items()}

        with open(metadata_file, "w") as f:
            json.dump(data, f, indent=2)

    def _load_plugin(self, name: str) -> Plugin:
        """Load a plugin module and instantiate it.

        Args:
            name: Plugin name

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If plugin cannot be loaded
        """
        plugin_path = self.plugins_dir / name / "plugin.py"
        if not plugin_path.exists():
            raise PluginLoadError(f"Plugin file not found: {plugin_path}")

        # Load module
        spec = importlib.util.spec_from_file_location(f"isaac_plugin_{name}", plugin_path)
        if not spec or not spec.loader:
            raise PluginLoadError(f"Cannot load plugin module: {name}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[f"isaac_plugin_{name}"] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            raise PluginLoadError(f"Error executing plugin module: {e}")

        # Find Plugin subclass
        plugin_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Plugin)
                and attr is not Plugin
            ):
                plugin_class = attr
                break

        if not plugin_class:
            raise PluginLoadError(f"No Plugin subclass found in {name}")

        # Instantiate plugin
        try:
            plugin = plugin_class()
        except Exception as e:
            raise PluginLoadError(f"Error instantiating plugin: {e}")

        # Verify metadata matches
        if plugin.metadata.name != name:
            raise PluginLoadError(
                f"Plugin name mismatch: expected {name}, got {plugin.metadata.name}"
            )

        return plugin

    def install(self, name: str, force: bool = False) -> bool:
        """Install a plugin from the registry.

        Args:
            name: Plugin name
            force: Force reinstall if already installed

        Returns:
            True if installation successful
        """
        # Check if already installed
        if name in self._metadata and not force:
            print(f"Plugin {name} is already installed. Use --force to reinstall.")
            return False

        # Get plugin from registry
        entry = self.registry.get(name)
        if not entry:
            print(f"Plugin {name} not found in registry")
            return False

        # Create plugin directory
        plugin_dir = self.plugins_dir / name
        if plugin_dir.exists() and force:
            shutil.rmtree(plugin_dir)
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # Download plugin
        plugin_file = plugin_dir / "plugin.py"
        success = self.registry.download_plugin(name, plugin_file)

        if not success:
            shutil.rmtree(plugin_dir)
            print(f"Failed to download plugin {name}")
            return False

        # Update metadata
        entry.metadata.install_date = datetime.now()
        entry.metadata.enabled = True
        self._metadata[name] = entry.metadata

        # Save metadata
        self._save_installed_plugins()

        # Load and initialize plugin
        try:
            plugin = self._load_plugin(name)
            context = self._create_context(name)
            plugin.initialize(context)

            self._plugins[name] = plugin
            self._contexts[name] = context

            # Register hooks
            self._register_plugin_hooks(name, plugin)

            print(f"Successfully installed plugin: {name}")
            return True

        except PluginLoadError as e:
            print(f"Failed to load plugin after installation: {e}")
            # Clean up
            shutil.rmtree(plugin_dir)
            del self._metadata[name]
            self._save_installed_plugins()
            return False

    def uninstall(self, name: str) -> bool:
        """Uninstall a plugin.

        Args:
            name: Plugin name

        Returns:
            True if uninstallation successful
        """
        if name not in self._metadata:
            print(f"Plugin {name} is not installed")
            return False

        # Shutdown plugin if loaded
        if name in self._plugins:
            try:
                self._plugins[name].shutdown()
            except Exception as e:
                print(f"Error during plugin shutdown: {e}")

            # Unregister hooks
            self._unregister_plugin_hooks(name)

            del self._plugins[name]
            del self._contexts[name]

        # Remove from disk
        plugin_dir = self.plugins_dir / name
        if plugin_dir.exists():
            shutil.rmtree(plugin_dir)

        # Remove metadata
        del self._metadata[name]
        self._save_installed_plugins()

        print(f"Successfully uninstalled plugin: {name}")
        return True

    def enable(self, name: str) -> bool:
        """Enable a plugin.

        Args:
            name: Plugin name

        Returns:
            True if plugin was enabled
        """
        if name not in self._metadata:
            print(f"Plugin {name} is not installed")
            return False

        if name in self._plugins:
            print(f"Plugin {name} is already enabled")
            return True

        # Load and initialize plugin
        try:
            plugin = self._load_plugin(name)
            context = self._create_context(name)
            plugin.initialize(context)

            self._plugins[name] = plugin
            self._contexts[name] = context

            # Register hooks
            self._register_plugin_hooks(name, plugin)

            # Update metadata
            self._metadata[name].enabled = True
            self._save_installed_plugins()

            print(f"Successfully enabled plugin: {name}")
            return True

        except PluginLoadError as e:
            print(f"Failed to enable plugin: {e}")
            return False

    def disable(self, name: str) -> bool:
        """Disable a plugin.

        Args:
            name: Plugin name

        Returns:
            True if plugin was disabled
        """
        if name not in self._metadata:
            print(f"Plugin {name} is not installed")
            return False

        if name not in self._plugins:
            print(f"Plugin {name} is already disabled")
            return True

        # Shutdown plugin
        try:
            self._plugins[name].shutdown()
        except Exception as e:
            print(f"Error during plugin shutdown: {e}")

        # Unregister hooks
        self._unregister_plugin_hooks(name)

        del self._plugins[name]
        del self._contexts[name]

        # Update metadata
        self._metadata[name].enabled = False
        self._save_installed_plugins()

        print(f"Successfully disabled plugin: {name}")
        return True

    def list_installed(self) -> List[PluginMetadata]:
        """List all installed plugins.

        Returns:
            List of installed plugin metadata
        """
        return list(self._metadata.values())

    def list_enabled(self) -> List[PluginMetadata]:
        """List enabled plugins.

        Returns:
            List of enabled plugin metadata
        """
        return [meta for meta in self._metadata.values() if meta.enabled]

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a loaded plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None
        """
        return self._plugins.get(name)

    def get_metadata(self, name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata.

        Args:
            name: Plugin name

        Returns:
            Plugin metadata or None
        """
        return self._metadata.get(name)

    def _create_context(self, name: str) -> PluginContext:
        """Create a plugin context.

        Args:
            name: Plugin name

        Returns:
            Plugin context
        """
        metadata = self._metadata[name]

        return PluginContext(
            session_id="default",  # TODO: Get from session manager
            workspace_path=str(Path.cwd()),
            config={
                "permissions": metadata.permissions,
                "plugin_name": name,
            },
            state={},
            event_data={},
            apis={},
        )

    def _register_plugin_hooks(self, name: str, plugin: Plugin) -> None:
        """Register all hooks for a plugin.

        Args:
            name: Plugin name
            plugin: Plugin instance
        """
        for hook in plugin.get_all_hooks():
            if hook not in self._hook_handlers:
                self._hook_handlers[hook] = []
            self._hook_handlers[hook].append((name, plugin))

    def _unregister_plugin_hooks(self, name: str) -> None:
        """Unregister all hooks for a plugin.

        Args:
            name: Plugin name
        """
        for hook in list(self._hook_handlers.keys()):
            self._hook_handlers[hook] = [
                (n, p) for n, p in self._hook_handlers[hook] if n != name
            ]
            if not self._hook_handlers[hook]:
                del self._hook_handlers[hook]

    def trigger_hook(self, hook: PluginHook, event_data: Optional[Dict[str, Any]] = None) -> None:
        """Trigger a hook and call all registered handlers.

        Args:
            hook: Hook to trigger
            event_data: Optional event data to pass to handlers
        """
        if hook not in self._hook_handlers:
            return

        for name, plugin in self._hook_handlers[hook]:
            try:
                # Update context with event data
                if name in self._contexts and event_data:
                    self._contexts[name].event_data = event_data

                # Call all handlers for this hook
                for handler in plugin.get_hooks(hook):
                    if self.enable_sandbox and self._sandbox:
                        self._sandbox.execute(handler)
                    else:
                        handler()

            except Exception as e:
                print(f"Error in plugin {name} hook {hook.value}: {e}")

    def update(self, name: str) -> bool:
        """Update a plugin to the latest version.

        Args:
            name: Plugin name

        Returns:
            True if update successful
        """
        if name not in self._metadata:
            print(f"Plugin {name} is not installed")
            return False

        # Get latest version from registry
        entry = self.registry.get(name)
        if not entry:
            print(f"Plugin {name} not found in registry")
            return False

        current_version = self._metadata[name].version
        if entry.metadata.version == current_version:
            print(f"Plugin {name} is already at the latest version ({current_version})")
            return True

        print(f"Updating {name} from {current_version} to {entry.metadata.version}")

        # Disable plugin
        was_enabled = name in self._plugins
        if was_enabled:
            self.disable(name)

        # Reinstall
        success = self.install(name, force=True)

        # Re-enable if it was enabled
        if success and was_enabled:
            self.enable(name)

        return success

    def update_all(self) -> Dict[str, bool]:
        """Update all installed plugins.

        Returns:
            Dictionary mapping plugin names to update success status
        """
        results = {}
        for name in list(self._metadata.keys()):
            results[name] = self.update(name)
        return results
