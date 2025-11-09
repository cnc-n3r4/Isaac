"""Tests for plugin manager."""

import unittest
import tempfile
import shutil
from pathlib import Path

from isaac.plugins.plugin_api import Plugin, PluginMetadata, PluginContext, PluginHook
from isaac.plugins.plugin_manager import PluginManager
from isaac.plugins.plugin_registry import PluginRegistry


class TestPluginForManager(Plugin):
    """Test plugin for manager tests."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test-manager-plugin",
            version="1.0.0",
            author="Test",
            description="Test plugin for manager",
            hooks=[PluginHook.STARTUP],
        )

    def initialize(self, context: PluginContext) -> None:
        self._context = context

    def shutdown(self) -> None:
        pass


class TestPluginManager(unittest.TestCase):
    """Test PluginManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugins_dir = Path(self.temp_dir) / "plugins"
        self.plugins_dir.mkdir()

        self.manager = PluginManager(
            plugins_dir=self.plugins_dir,
            enable_sandbox=False,  # Disable for testing
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_manager_creation(self):
        """Test creating plugin manager."""
        self.assertIsNotNone(self.manager)
        self.assertTrue(self.plugins_dir.exists())

    def test_list_installed_empty(self):
        """Test listing installed plugins when none installed."""
        plugins = self.manager.list_installed()
        self.assertEqual(len(plugins), 0)

    def test_list_enabled_empty(self):
        """Test listing enabled plugins when none enabled."""
        plugins = self.manager.list_enabled()
        self.assertEqual(len(plugins), 0)

    def test_get_plugin_not_found(self):
        """Test getting non-existent plugin."""
        plugin = self.manager.get_plugin("nonexistent")
        self.assertIsNone(plugin)

    def test_get_metadata_not_found(self):
        """Test getting metadata for non-existent plugin."""
        metadata = self.manager.get_metadata("nonexistent")
        self.assertIsNone(metadata)


class TestPluginManagerHooks(unittest.TestCase):
    """Test plugin manager hook system."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugins_dir = Path(self.temp_dir) / "plugins"
        self.plugins_dir.mkdir()

        self.manager = PluginManager(
            plugins_dir=self.plugins_dir,
            enable_sandbox=False,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_trigger_hook_no_handlers(self):
        """Test triggering hook with no handlers."""
        # Should not raise an error
        self.manager.trigger_hook(PluginHook.STARTUP)

    def test_trigger_hook_with_event_data(self):
        """Test triggering hook with event data."""
        # Should not raise an error
        self.manager.trigger_hook(
            PluginHook.BEFORE_COMMAND,
            event_data={"command": "test"},
        )


if __name__ == "__main__":
    unittest.main()
