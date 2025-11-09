"""
AR/VR Preparation Module

Provides infrastructure for spatial computing, gesture controls, and
future AR/VR platform integration.
"""

from isaac.arvr.gesture_api import Gesture, GestureAPI, GestureRecognizer
from isaac.arvr.multimodal_input import MultimodalInputHandler
from isaac.arvr.platform_adapter import Platform, PlatformAdapter
from isaac.arvr.prototype_mode import PrototypeRenderer
from isaac.arvr.spatial_api import SpatialAPI, SpatialObject, SpatialWorkspace, Vector3D
from isaac.arvr.spatial_layouts import Layout, LayoutManager, LayoutNode

__all__ = [
    "SpatialAPI",
    "Vector3D",
    "SpatialObject",
    "SpatialWorkspace",
    "GestureAPI",
    "Gesture",
    "GestureRecognizer",
    "LayoutManager",
    "Layout",
    "LayoutNode",
    "MultimodalInputHandler",
    "PrototypeRenderer",
    "PlatformAdapter",
    "Platform",
]
