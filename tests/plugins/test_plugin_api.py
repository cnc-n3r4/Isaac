"""Tests for plugin API."""

import unittest
from datetime import datetime

from isaac.plugins.plugin_api import (
    Plugin,
    PluginMetadata,
    PluginContext,
    PluginHook,
    PluginError,
)


class TestPlugin(Plugin):
    """Test plugin implementation."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            author="Test Author",
            description="Test plugin",
            hooks=[PluginHook.STARTUP, PluginHook.BEFORE_COMMAND],
        )

    def initialize(self, context: PluginContext) -> None:
        self._context = context
        self.initialized = True

    def shutdown(self) -> None:
        self.shutdown_called = True


class TestPluginMetadata(unittest.TestCase):
    """Test PluginMetadata class."""

    def test_metadata_creation(self):
        """Test creating plugin metadata."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Author",
            description="Description",
        )

        self.assertEqual(metadata.name, "test")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.author, "Author")
        self.assertEqual(metadata.description, "Description")

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Author",
            description="Description",
            tags=["tag1", "tag2"],
        )

        data = metadata.to_dict()
        self.assertEqual(data["name"], "test")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["tags"], ["tag1", "tag2"])

    def test_metadata_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "name": "test",
            "version": "1.0.0",
            "author": "Author",
            "description": "Description",
            "tags": ["tag1"],
            "hooks": ["startup"],
        }

        metadata = PluginMetadata.from_dict(data)
        self.assertEqual(metadata.name, "test")
        self.assertEqual(len(metadata.hooks), 1)
        self.assertEqual(metadata.hooks[0], PluginHook.STARTUP)


class TestPluginContext(unittest.TestCase):
    """Test PluginContext class."""

    def test_context_creation(self):
        """Test creating plugin context."""
        context = PluginContext(
            session_id="test-session",
            workspace_path="/tmp",
        )

        self.assertEqual(context.session_id, "test-session")
        self.assertEqual(context.workspace_path, "/tmp")

    def test_context_state(self):
        """Test context state management."""
        context = PluginContext(
            session_id="test",
            workspace_path="/tmp",
        )

        context.state["key"] = "value"
        self.assertEqual(context.state["key"], "value")

    def test_context_apis(self):
        """Test context API access."""
        context = PluginContext(
            session_id="test",
            workspace_path="/tmp",
            apis={"test_api": "api_instance"},
        )

        self.assertEqual(context.get_api("test_api"), "api_instance")
        self.assertIsNone(context.get_api("missing"))


class TestPluginBase(unittest.TestCase):
    """Test Plugin base class."""

    def test_plugin_instantiation(self):
        """Test creating a plugin instance."""
        plugin = TestPlugin()
        self.assertIsNotNone(plugin)

    def test_plugin_metadata(self):
        """Test plugin metadata property."""
        plugin = TestPlugin()
        metadata = plugin.metadata

        self.assertEqual(metadata.name, "test-plugin")
        self.assertEqual(metadata.version, "1.0.0")

    def test_plugin_initialization(self):
        """Test plugin initialization."""
        plugin = TestPlugin()
        context = PluginContext(
            session_id="test",
            workspace_path="/tmp",
        )

        plugin.initialize(context)
        self.assertTrue(plugin.initialized)
        self.assertEqual(plugin.context, context)

    def test_plugin_shutdown(self):
        """Test plugin shutdown."""
        plugin = TestPlugin()
        context = PluginContext(
            session_id="test",
            workspace_path="/tmp",
        )

        plugin.initialize(context)
        plugin.shutdown()
        self.assertTrue(plugin.shutdown_called)

    def test_hook_registration(self):
        """Test hook registration."""
        plugin = TestPlugin()

        def handler():
            pass

        plugin.register_hook(PluginHook.STARTUP, handler)
        handlers = plugin.get_hooks(PluginHook.STARTUP)

        self.assertEqual(len(handlers), 1)
        self.assertEqual(handlers[0], handler)

    def test_get_all_hooks(self):
        """Test getting all registered hooks."""
        plugin = TestPlugin()

        def handler():
            pass

        plugin.register_hook(PluginHook.STARTUP, handler)
        plugin.register_hook(PluginHook.SHUTDOWN, handler)

        hooks = plugin.get_all_hooks()
        self.assertEqual(len(hooks), 2)
        self.assertIn(PluginHook.STARTUP, hooks)
        self.assertIn(PluginHook.SHUTDOWN, hooks)

    def test_enable_disable(self):
        """Test enabling and disabling plugin."""
        plugin = TestPlugin()

        self.assertTrue(plugin.enabled)

        plugin.disable()
        self.assertFalse(plugin.enabled)

        plugin.enable()
        self.assertTrue(plugin.enabled)

    def test_state_management(self):
        """Test plugin state management."""
        plugin = TestPlugin()
        context = PluginContext(
            session_id="test",
            workspace_path="/tmp",
        )

        plugin.initialize(context)

        plugin.set_state("key", "value")
        self.assertEqual(plugin.get_state("key"), "value")
        self.assertIsNone(plugin.get_state("missing"))
        self.assertEqual(plugin.get_state("missing", "default"), "default")

    def test_config_access(self):
        """Test plugin configuration access."""
        plugin = TestPlugin()
        context = PluginContext(
            session_id="test",
            workspace_path="/tmp",
            config={"setting": "value"},
        )

        plugin.initialize(context)

        self.assertEqual(plugin.get_config("setting"), "value")
        self.assertIsNone(plugin.get_config("missing"))
        self.assertEqual(plugin.get_config("missing", "default"), "default")


if __name__ == "__main__":
    unittest.main()
