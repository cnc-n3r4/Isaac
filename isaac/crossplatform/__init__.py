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

__version__ = '5.5.0'

# Universal Bubbles
from .bubbles import UniversalBubble, PlatformAdapter, StateManager

# Cloud-Native Mode
from .cloud import CloudExecutor, CloudStorage, RemoteWorkspace

# API Layer
from .api import RestAPI, WebSocketAPI, WebhookManager, APIAuth

# Web Interface
from .web import WebServer, WebTerminal, TerminalEmulator

# Mobile Companion
from .mobile import MobileAPI, NotificationService, MobileAuth

# Offline Mode
from .offline import OfflineManager, SyncQueue, ConflictResolver, CacheManager

__all__ = [
    # Bubbles
    'UniversalBubble',
    'PlatformAdapter',
    'StateManager',

    # Cloud
    'CloudExecutor',
    'CloudStorage',
    'RemoteWorkspace',

    # API
    'RestAPI',
    'WebSocketAPI',
    'WebhookManager',
    'APIAuth',

    # Web
    'WebServer',
    'WebTerminal',
    'TerminalEmulator',

    # Mobile
    'MobileAPI',
    'NotificationService',
    'MobileAuth',

    # Offline
    'OfflineManager',
    'SyncQueue',
    'ConflictResolver',
    'CacheManager'
]
