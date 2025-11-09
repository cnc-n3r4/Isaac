"""
Universal Bubbles - Cross-Platform Workspace State

Enables workspace state capture and restoration across different operating systems
without modification. Bubbles created on Windows function identically on macOS and Linux.
"""

from .platform_adapter import PlatformAdapter
from .state_manager import StateManager
from .universal_bubble import UniversalBubble

__all__ = ["UniversalBubble", "PlatformAdapter", "StateManager"]
