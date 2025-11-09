"""Tests for plugin security."""

import unittest
import tempfile
import os

from isaac.plugins.plugin_security import (
    SecurityPolicy,
    PluginSandbox,
    PermissionManager,
)


class TestSecurityPolicy(unittest.TestCase):
    """Test SecurityPolicy class."""

    def test_default_policy(self):
        """Test default security policy."""
        policy = SecurityPolicy()

        self.assertEqual(policy.max_memory_mb, 100)
        self.assertEqual(policy.max_cpu_time, 5)
        self.assertFalse(policy.allow_network)
        self.assertFalse(policy.allow_subprocess)
        self.assertFalse(policy.allow_file_write)
        self.assertTrue(policy.allow_file_read)

    def test_custom_policy(self):
        """Test custom security policy."""
        policy = SecurityPolicy(
            max_memory_mb=200,
            allow_network=True,
            allow_file_write=True,
        )

        self.assertEqual(policy.max_memory_mb, 200)
        self.assertTrue(policy.allow_network)
        self.assertTrue(policy.allow_file_write)

    def test_policy_to_dict(self):
        """Test converting policy to dictionary."""
        policy = SecurityPolicy(max_memory_mb=150)
        data = policy.to_dict()

        self.assertEqual(data["max_memory_mb"], 150)
        self.assertFalse(data["allow_network"])
        self.assertTrue(data["allow_file_read"])


class TestPluginSandbox(unittest.TestCase):
    """Test PluginSandbox class."""

    def test_sandbox_creation(self):
        """Test creating sandbox."""
        sandbox = PluginSandbox()
        self.assertIsNotNone(sandbox)

    def test_sandbox_with_policy(self):
        """Test creating sandbox with custom policy."""
        policy = SecurityPolicy(max_memory_mb=200)
        sandbox = PluginSandbox(policy=policy)

        self.assertEqual(sandbox.policy.max_memory_mb, 200)

    def test_execute_simple_function(self):
        """Test executing simple function in sandbox."""
        sandbox = PluginSandbox()

        def test_func():
            return 42

        result = sandbox.execute(test_func)
        self.assertEqual(result, 42)

    def test_execute_with_args(self):
        """Test executing function with arguments."""
        sandbox = PluginSandbox()

        def test_func(a, b):
            return a + b

        result = sandbox.execute(test_func, 10, 20)
        self.assertEqual(result, 30)

    def test_execute_with_kwargs(self):
        """Test executing function with keyword arguments."""
        sandbox = PluginSandbox()

        def test_func(a=0, b=0):
            return a * b

        result = sandbox.execute(test_func, a=5, b=6)
        self.assertEqual(result, 30)

    def test_validate_plugin_code_safe(self):
        """Test validating safe plugin code."""
        sandbox = PluginSandbox()

        code = """
def my_function():
    x = 1 + 2
    return x
"""

        warnings = sandbox.validate_plugin_code(code)
        # Safe code should have no warnings
        self.assertEqual(len(warnings), 0)

    def test_validate_plugin_code_dangerous(self):
        """Test validating dangerous plugin code."""
        sandbox = PluginSandbox()

        code = """
import os
os.system('rm -rf /')
"""

        warnings = sandbox.validate_plugin_code(code)
        # Should detect os.system
        self.assertGreater(len(warnings), 0)
        self.assertTrue(any("os.system" in w for w in warnings))


class TestPermissionManager(unittest.TestCase):
    """Test PermissionManager class."""

    def test_manager_creation(self):
        """Test creating permission manager."""
        manager = PermissionManager()
        self.assertIsNotNone(manager)

    def test_grant_permission(self):
        """Test granting permission."""
        manager = PermissionManager()

        manager.grant("test-plugin", PermissionManager.PERMISSION_FILE_READ)
        self.assertTrue(
            manager.has_permission("test-plugin", PermissionManager.PERMISSION_FILE_READ)
        )

    def test_revoke_permission(self):
        """Test revoking permission."""
        manager = PermissionManager()

        manager.grant("test-plugin", PermissionManager.PERMISSION_FILE_READ)
        manager.revoke("test-plugin", PermissionManager.PERMISSION_FILE_READ)

        self.assertFalse(
            manager.has_permission("test-plugin", PermissionManager.PERMISSION_FILE_READ)
        )

    def test_has_permission_false(self):
        """Test checking permission that was not granted."""
        manager = PermissionManager()

        self.assertFalse(
            manager.has_permission("test-plugin", PermissionManager.PERMISSION_NETWORK)
        )

    def test_get_permissions(self):
        """Test getting all permissions for a plugin."""
        manager = PermissionManager()

        manager.grant("test-plugin", PermissionManager.PERMISSION_FILE_READ)
        manager.grant("test-plugin", PermissionManager.PERMISSION_FILE_WRITE)

        permissions = manager.get_permissions("test-plugin")
        self.assertEqual(len(permissions), 2)
        self.assertIn(PermissionManager.PERMISSION_FILE_READ, permissions)
        self.assertIn(PermissionManager.PERMISSION_FILE_WRITE, permissions)

    def test_create_policy(self):
        """Test creating security policy from permissions."""
        manager = PermissionManager()

        manager.grant("test-plugin", PermissionManager.PERMISSION_FILE_WRITE)
        manager.grant("test-plugin", PermissionManager.PERMISSION_NETWORK)

        policy = manager.create_policy("test-plugin")

        self.assertTrue(policy.allow_file_write)
        self.assertTrue(policy.allow_network)
        self.assertFalse(policy.allow_subprocess)


if __name__ == "__main__":
    unittest.main()
