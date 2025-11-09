"""
AR/VR Preparation Module

Provides infrastructure for spatial computing, gesture controls, and
future AR/VR platform integration.
"""

from isaac.arvr.spatial_api import SpatialAPI, Vector3D, SpatialObject, SpatialWorkspace
from isaac.arvr.gesture_api import GestureAPI, Gesture, GestureRecognizer
from isaac.arvr.spatial_layouts import LayoutManager, Layout, LayoutNode
from isaac.arvr.multimodal_input import MultimodalInputHandler
from isaac.arvr.prototype_mode import PrototypeRenderer
from isaac.arvr.platform_adapter import PlatformAdapter, Platform

__all__ = [
    'SpatialAPI',
    'Vector3D',
    'SpatialObject',
    'SpatialWorkspace',
    'GestureAPI',
    'Gesture',
    'GestureRecognizer',
    'LayoutManager',
    'Layout',
    'LayoutNode',
    'MultimodalInputHandler',
    'PrototypeRenderer',
    'PlatformAdapter',
    'Platform',
]
