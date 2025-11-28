"""Tests for plugin security."""

import unittest
import tempfile
import os

from isaac.plugins.plugin_security import (
    SecurityPolicy,
    PluginSandbox,
    PermissionManager,
    APIKeyManager,
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


class TestAPIKeyManager(unittest.TestCase):
    """Test APIKeyManager class."""

    def test_manager_creation(self):
        """Test creating API key manager."""
        manager = APIKeyManager()
        self.assertIsNotNone(manager)

    def test_register_key(self):
        """Test registering API key."""
        manager = APIKeyManager()

        manager.register_key("test-plugin", "openai", "sk-test123")
        manager.grant_service_access("test-plugin", "openai")

        key = manager.get_key("test-plugin", "openai")
        self.assertEqual(key, "sk-test123")

    def test_get_key_without_permission(self):
        """Test getting key without permission."""
        manager = APIKeyManager()

        manager.register_key("test-plugin", "openai", "sk-test123")
        # Don't grant access

        key = manager.get_key("test-plugin", "openai")
        self.assertIsNone(key)

    def test_grant_revoke_service_access(self):
        """Test granting and revoking service access."""
        manager = APIKeyManager()

        manager.grant_service_access("test-plugin", "openai")
        self.assertTrue(manager.has_service_access("test-plugin", "openai"))

        manager.revoke_service_access("test-plugin", "openai")
        self.assertFalse(manager.has_service_access("test-plugin", "openai"))

    def test_list_services(self):
        """Test listing services."""
        manager = APIKeyManager()

        manager.grant_service_access("test-plugin", "openai")
        manager.grant_service_access("test-plugin", "anthropic")

        services = manager.list_services("test-plugin")
        self.assertEqual(len(services), 2)
        self.assertIn("openai", services)
        self.assertIn("anthropic", services)

    def test_validate_key_format_openai(self):
        """Test OpenAI key format validation."""
        manager = APIKeyManager()

        self.assertTrue(manager.validate_key_format("openai", "sk-test123456789"))
        self.assertFalse(manager.validate_key_format("openai", "invalid"))

    def test_validate_key_format_anthropic(self):
        """Test Anthropic key format validation."""
        manager = APIKeyManager()

        self.assertTrue(manager.validate_key_format("anthropic", "sk-ant-test12345678901234567890"))
        self.assertFalse(manager.validate_key_format("anthropic", "invalid"))

    def test_secure_store_key(self):
        """Test secure key storage."""
        manager = APIKeyManager()

        success = manager.secure_store_key("test-plugin", "openai", "sk-test123456789")
        self.assertTrue(success)

        self.assertTrue(manager.has_service_access("test-plugin", "openai"))
        key = manager.get_key("test-plugin", "openai")
        self.assertEqual(key, "sk-test123456789")

    def test_secure_store_invalid_key(self):
        """Test secure storage rejects invalid keys."""
        manager = APIKeyManager()

        success = manager.secure_store_key("test-plugin", "openai", "invalid")
        self.assertFalse(success)

    def test_remove_key(self):
        """Test key removal."""
        manager = APIKeyManager()

        manager.register_key("test-plugin", "openai", "sk-test123")
        manager.grant_service_access("test-plugin", "openai")

        manager.remove_key("test-plugin", "openai")

        self.assertFalse(manager.has_service_access("test-plugin", "openai"))
        key = manager.get_key("test-plugin", "openai")
        self.assertIsNone(key)


if __name__ == "__main__":
    unittest.main()
