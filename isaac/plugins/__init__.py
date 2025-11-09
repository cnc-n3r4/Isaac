"""Isaac Plugin System.

This module provides the plugin architecture for Isaac.
"""

from isaac.plugins.plugin_api import (
    Plugin,
    PluginMetadata,
    PluginContext,
    PluginHook,
    PluginError,
    PluginLoadError,
    PluginSecurityError,
)
from isaac.plugins.plugin_manager import PluginManager
from isaac.plugins.plugin_registry import PluginRegistry

__all__ = [
    "Plugin",
    "PluginMetadata",
    "PluginContext",
    "PluginHook",
    "PluginError",
    "PluginLoadError",
    "PluginSecurityError",
    "PluginManager",
    "PluginRegistry",
]
