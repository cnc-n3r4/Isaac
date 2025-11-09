"""Integration tests for plugin system."""

import unittest
import tempfile
import shutil
from pathlib import Path

from isaac.plugins import (
    Plugin,
    PluginMetadata,
    PluginContext,
    PluginHook,
    PluginManager,
    PluginRegistry,
)
from isaac.plugins.plugin_devkit import PluginDevKit


class IntegrationTestPlugin(Plugin):
    """Test plugin for integration tests."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="integration-test",
            version="1.0.0",
            author="Test",
            description="Integration test plugin",
            hooks=[PluginHook.STARTUP],
        )

    def initialize(self, context: PluginContext) -> None:
        self._context = context
        self.startup_called = False
        self.register_hook(PluginHook.STARTUP, self.on_startup)

    def shutdown(self) -> None:
        pass

    def on_startup(self) -> None:
        self.startup_called = True


class TestPluginSystemIntegration(unittest.TestCase):
    """Test complete plugin system integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugins_dir = Path(self.temp_dir) / "plugins"
        self.plugins_dir.mkdir()

        self.manager = PluginManager(
            plugins_dir=self.plugins_dir,
            enable_sandbox=False,
        )

        self.registry = PluginRegistry(
            cache_dir=Path(self.temp_dir) / "cache"
        )

        self.devkit = PluginDevKit(
            workspace_dir=Path(self.temp_dir) / "workspace"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_plugin_lifecycle(self):
        """Test complete plugin lifecycle."""
        # This test verifies the basic manager functionality
        # In a real scenario, we would:
        # 1. Create plugin with devkit
        # 2. Validate it
        # 3. Install it via manager
        # 4. Enable it
        # 5. Trigger hooks
        # 6. Disable it
        # 7. Uninstall it

        # For now, just verify manager is working
        plugins = self.manager.list_installed()
        self.assertEqual(len(plugins), 0)

    def test_devkit_plugin_creation(self):
        """Test creating plugin with devkit."""
        plugin_dir = self.devkit.create_plugin(
            name="test-plugin",
            author="Test Author",
            description="Test plugin",
            hooks=["STARTUP"],
        )

        self.assertTrue(plugin_dir.exists())
        self.assertTrue((plugin_dir / "plugin.py").exists())
        self.assertTrue((plugin_dir / "manifest.json").exists())
        self.assertTrue((plugin_dir / "README.md").exists())

    def test_devkit_plugin_validation(self):
        """Test validating plugin."""
        plugin_dir = self.devkit.create_plugin(
            name="test-plugin",
            author="Test",
            description="Test",
        )

        result = self.devkit.validate_plugin(plugin_dir)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_devkit_validation_missing_files(self):
        """Test validation with missing files."""
        # Create empty directory
        empty_dir = Path(self.temp_dir) / "empty"
        empty_dir.mkdir()

        result = self.devkit.validate_plugin(empty_dir)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)

    def test_registry_search(self):
        """Test registry search functionality."""
        # Update registry (will be empty for test)
        self.registry.update()

        # Search should not crash even with empty registry
        results = self.registry.search(query="test")
        self.assertIsInstance(results, list)

    def test_registry_featured_plugins(self):
        """Test getting featured plugins."""
        self.registry.update()

        # Should not crash even with empty registry
        featured = self.registry.list_featured()
        self.assertIsInstance(featured, list)


class TestPluginHookSystem(unittest.TestCase):
    """Test plugin hook system."""

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

    def test_hook_triggering(self):
        """Test triggering hooks."""
        # This test would verify hook triggering
        # In a real scenario, we would load a plugin and trigger its hooks

        # For now, just verify manager hook system
        self.manager.trigger_hook(PluginHook.STARTUP)

        # Should not raise any errors


if __name__ == "__main__":
    unittest.main()
