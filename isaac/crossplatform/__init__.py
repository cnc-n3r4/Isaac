"""
Isaac Cross-Platform Module - Phase 5.5

Enables Isaac to operate seamlessly across multiple platforms and deployment contexts.

Components:
- Universal Bubbles: Cross-platform workspace state capture and restoration
- Cloud-Native Mode: Full operation within cloud infrastructure
- RESTful API: Programmatic access to all Isaac functionality
- Web Interface: Browser-based terminal and workspace access
- Mobile API: iOS and Android companion app backend
- Offline Mode: Local-first data synchronization
"""

__version__ = "5.5.0"

# API Layer
from .api import APIAuth, RestAPI, WebhookManager, WebSocketAPI

# Universal Bubbles
from .bubbles import PlatformAdapter, StateManager, UniversalBubble

# Cloud-Native Mode
from .cloud import CloudExecutor, CloudStorage, RemoteWorkspace

# Mobile Companion
from .mobile import MobileAPI, MobileAuth, NotificationService

# Offline Mode
from .offline import CacheManager, ConflictResolver, OfflineManager, SyncQueue

# Web Interface
from .web import TerminalEmulator, WebServer, WebTerminal

__all__ = [
    # Bubbles
    "UniversalBubble",
    "PlatformAdapter",
    "StateManager",
    # Cloud
    "CloudExecutor",
    "CloudStorage",
    "RemoteWorkspace",
    # API
    "RestAPI",
    "WebSocketAPI",
    "WebhookManager",
    "APIAuth",
    # Web
    "WebServer",
    "WebTerminal",
    "TerminalEmulator",
    # Mobile
    "MobileAPI",
    "NotificationService",
    "MobileAuth",
    # Offline
    "OfflineManager",
    "SyncQueue",
    "ConflictResolver",
    "CacheManager",
]
