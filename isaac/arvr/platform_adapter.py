"""
Platform Adapter for AR/VR Systems

Provides extensible architecture for integrating with different AR/VR platforms
(Oculus/Meta Quest, HTC Vive, Apple Vision Pro, HoloLens, etc.)
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from isaac.arvr.multimodal_input import MultimodalInput
from isaac.arvr.spatial_api import SpatialWorkspace, Transform3D, Vector3D


class Platform(Enum):
    """Supported AR/VR platforms"""

    GENERIC = "generic"
    OCULUS_QUEST = "oculus_quest"
    META_QUEST = "meta_quest"
    VIVE = "htc_vive"
    APPLE_VISION_PRO = "apple_vision_pro"
    HOLOLENS = "microsoft_hololens"
    PICO = "pico"
    VALVE_INDEX = "valve_index"
    WEBXR = "webxr"
    TERMINAL = "terminal"  # 2D terminal mode


class InputCapability(Enum):
    """Input capabilities of platforms"""

    HAND_TRACKING = "hand_tracking"
    CONTROLLER = "controller"
    EYE_TRACKING = "eye_tracking"
    VOICE = "voice"
    GESTURE = "gesture"
    PASSTHROUGH = "passthrough"  # AR passthrough
    SPATIAL_AUDIO = "spatial_audio"


class DisplayMode(Enum):
    """Display modes"""

    VR_IMMERSIVE = "vr_immersive"  # Full VR
    AR_PASSTHROUGH = "ar_passthrough"  # AR with camera passthrough
    AR_TRANSPARENT = "ar_transparent"  # AR with transparent displays
    MIXED_REALITY = "mixed_reality"  # MR with spatial mapping
    DESKTOP = "desktop"  # 2D desktop mode


@dataclass
class PlatformCapabilities:
    """Capabilities of a platform"""

    platform: Platform
    display_mode: DisplayMode
    input_capabilities: List[InputCapability]
    max_fov: float = 110.0  # degrees
    tracking_volume: Vector3D = field(default_factory=lambda: Vector3D(3, 3, 3))  # meters
    refresh_rate: int = 90  # Hz
    supports_6dof: bool = True  # 6 degrees of freedom
    supports_hand_tracking: bool = False
    supports_eye_tracking: bool = False
    supports_spatial_audio: bool = True
    max_concurrent_apps: int = 10
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "display_mode": self.display_mode.value,
            "input_capabilities": [cap.value for cap in self.input_capabilities],
            "max_fov": self.max_fov,
            "tracking_volume": self.tracking_volume.to_dict(),
            "refresh_rate": self.refresh_rate,
            "supports_6dof": self.supports_6dof,
            "supports_hand_tracking": self.supports_hand_tracking,
            "supports_eye_tracking": self.supports_eye_tracking,
            "supports_spatial_audio": self.supports_spatial_audio,
            "max_concurrent_apps": self.max_concurrent_apps,
            "metadata": self.metadata,
        }


@dataclass
class DeviceState:
    """Current state of the AR/VR device"""

    head_transform: Transform3D
    left_hand_transform: Optional[Transform3D] = None
    right_hand_transform: Optional[Transform3D] = None
    eye_gaze_direction: Optional[Vector3D] = None
    is_connected: bool = True
    battery_level: Optional[float] = None  # 0.0 to 1.0
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PlatformInterface(ABC):
    """Abstract interface for AR/VR platforms"""

    def __init__(self, capabilities: PlatformCapabilities):
        self.capabilities = capabilities
        self.is_initialized = False
        self.device_state: Optional[DeviceState] = None

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the platform connection"""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the platform connection"""

    @abstractmethod
    def update(self) -> DeviceState:
        """Update and return current device state"""

    @abstractmethod
    def render_workspace(self, workspace: SpatialWorkspace) -> None:
        """Render workspace to the device"""

    @abstractmethod
    def process_input(self) -> List[MultimodalInput]:
        """Process and return input events"""

    @abstractmethod
    def enable_passthrough(self, enabled: bool) -> bool:
        """Enable/disable AR passthrough (if supported)"""

    def get_capabilities(self) -> PlatformCapabilities:
        """Get platform capabilities"""
        return self.capabilities

    def is_capability_supported(self, capability: InputCapability) -> bool:
        """Check if capability is supported"""
        return capability in self.capabilities.input_capabilities


class GenericPlatform(PlatformInterface):
    """Generic platform implementation for testing"""

    def __init__(self):
        capabilities = PlatformCapabilities(
            platform=Platform.GENERIC,
            display_mode=DisplayMode.VR_IMMERSIVE,
            input_capabilities=[
                InputCapability.CONTROLLER,
                InputCapability.GESTURE,
                InputCapability.VOICE,
            ],
        )
        super().__init__(capabilities)

    def initialize(self) -> bool:
        self.is_initialized = True
        self.device_state = DeviceState(head_transform=Transform3D(position=Vector3D(0, 1.7, 0)))
        return True

    def shutdown(self) -> None:
        self.is_initialized = False

    def update(self) -> DeviceState:
        if not self.device_state:
            self.device_state = DeviceState(
                head_transform=Transform3D(position=Vector3D(0, 1.7, 0))
            )
        return self.device_state

    def render_workspace(self, workspace: SpatialWorkspace) -> None:
        # Generic rendering (no-op for now)
        pass

    def process_input(self) -> List[MultimodalInput]:
        # Generic input processing
        return []

    def enable_passthrough(self, enabled: bool) -> bool:
        return False  # Not supported in generic


class TerminalPlatform(PlatformInterface):
    """Terminal-based platform for 2D testing"""

    def __init__(self):
        capabilities = PlatformCapabilities(
            platform=Platform.TERMINAL,
            display_mode=DisplayMode.DESKTOP,
            input_capabilities=[InputCapability.VOICE, InputCapability.GESTURE],
            supports_6dof=False,
        )
        super().__init__(capabilities)
        self.renderer = None

    def initialize(self) -> bool:
        from isaac.arvr.prototype_mode import PrototypeRenderer

        self.renderer = PrototypeRenderer()
        self.is_initialized = True
        self.device_state = DeviceState(head_transform=Transform3D(position=Vector3D(0, 0, 5)))
        return True

    def shutdown(self) -> None:
        self.is_initialized = False
        self.renderer = None

    def update(self) -> DeviceState:
        return self.device_state

    def render_workspace(self, workspace: SpatialWorkspace) -> None:
        if self.renderer:
            output = self.renderer.render_workspace(workspace)
            self.renderer.render_and_display(output)

    def process_input(self) -> List[MultimodalInput]:
        # Terminal input would be handled via command interface
        return []

    def enable_passthrough(self, enabled: bool) -> bool:
        return False  # Not applicable for terminal


class WebXRPlatform(PlatformInterface):
    """WebXR platform adapter for web-based AR/VR"""

    def __init__(self):
        capabilities = PlatformCapabilities(
            platform=Platform.WEBXR,
            display_mode=DisplayMode.VR_IMMERSIVE,
            input_capabilities=[
                InputCapability.CONTROLLER,
                InputCapability.HAND_TRACKING,
                InputCapability.VOICE,
            ],
            supports_hand_tracking=True,
        )
        super().__init__(capabilities)

    def initialize(self) -> bool:
        # WebXR initialization would happen in browser
        self.is_initialized = True
        self.device_state = DeviceState(head_transform=Transform3D(position=Vector3D(0, 1.7, 0)))
        return True

    def shutdown(self) -> None:
        self.is_initialized = False

    def update(self) -> DeviceState:
        return self.device_state

    def render_workspace(self, workspace: SpatialWorkspace) -> None:
        # Rendering would be handled by WebXR API
        pass

    def process_input(self) -> List[MultimodalInput]:
        # Input would come from WebXR events
        return []

    def enable_passthrough(self, enabled: bool) -> bool:
        # WebXR supports passthrough
        return True


class PlatformAdapter:
    """Main adapter for managing different AR/VR platforms"""

    def __init__(self):
        self.current_platform: Optional[PlatformInterface] = None
        self.available_platforms: Dict[Platform, type] = {
            Platform.GENERIC: GenericPlatform,
            Platform.TERMINAL: TerminalPlatform,
            Platform.WEBXR: WebXRPlatform,
        }
        self.event_handlers: Dict[str, List[Callable]] = {}

    def register_platform(self, platform: Platform, platform_class: type) -> None:
        """Register a custom platform implementation"""
        self.available_platforms[platform] = platform_class

    def initialize_platform(self, platform: Platform) -> bool:
        """Initialize a specific platform"""
        if platform not in self.available_platforms:
            raise ValueError(f"Platform {platform.value} not available")

        platform_class = self.available_platforms[platform]
        self.current_platform = platform_class()

        success = self.current_platform.initialize()
        if success:
            self._trigger_event("platform_initialized", {"platform": platform})

        return success

    def shutdown_platform(self) -> None:
        """Shutdown current platform"""
        if self.current_platform:
            self.current_platform.shutdown()
            self._trigger_event("platform_shutdown", {})
            self.current_platform = None

    def get_current_platform(self) -> Optional[PlatformInterface]:
        """Get current active platform"""
        return self.current_platform

    def get_device_state(self) -> Optional[DeviceState]:
        """Get current device state"""
        if self.current_platform:
            return self.current_platform.update()
        return None

    def render_workspace(self, workspace: SpatialWorkspace) -> None:
        """Render workspace on current platform"""
        if self.current_platform:
            self.current_platform.render_workspace(workspace)

    def process_input(self) -> List[MultimodalInput]:
        """Process input from current platform"""
        if self.current_platform:
            return self.current_platform.process_input()
        return []

    def get_capabilities(self) -> Optional[PlatformCapabilities]:
        """Get capabilities of current platform"""
        if self.current_platform:
            return self.current_platform.get_capabilities()
        return None

    def is_capability_supported(self, capability: InputCapability) -> bool:
        """Check if capability is supported on current platform"""
        if self.current_platform:
            return self.current_platform.is_capability_supported(capability)
        return False

    def get_available_platforms(self) -> List[Platform]:
        """Get list of available platforms"""
        return list(self.available_platforms.keys())

    def auto_detect_platform(self) -> Optional[Platform]:
        """Auto-detect best available platform"""
        # Try to detect available platforms
        # For now, just return terminal as default
        return Platform.TERMINAL

    def on_event(self, event_name: str, handler: Callable) -> None:
        """Register event handler"""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)

    def _trigger_event(self, event_name: str, data: Dict[str, Any]) -> None:
        """Trigger event handlers"""
        handlers = self.event_handlers.get(event_name, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"Error in event handler: {e}")

    def save_configuration(self, filepath: str) -> None:
        """Save current configuration"""
        config = {
            "current_platform": (
                self.current_platform.capabilities.platform.value if self.current_platform else None
            ),
            "capabilities": (
                self.current_platform.capabilities.to_dict() if self.current_platform else None
            ),
        }

        with open(filepath, "w") as f:
            json.dump(config, f, indent=2)

    def create_platform_report(self) -> Dict[str, Any]:
        """Create comprehensive platform report"""
        report = {
            "available_platforms": [p.value for p in self.get_available_platforms()],
            "current_platform": None,
            "capabilities": None,
            "device_state": None,
        }

        if self.current_platform:
            caps = self.current_platform.get_capabilities()
            state = self.current_platform.update()

            report["current_platform"] = caps.platform.value
            report["capabilities"] = caps.to_dict()
            report["device_state"] = {
                "is_connected": state.is_connected,
                "battery_level": state.battery_level,
                "head_position": state.head_transform.position.to_dict(),
            }

        return report


# Platform factory for easy platform creation
def create_platform(platform_type: Platform) -> PlatformInterface:
    """Factory function to create platform instances"""
    platforms = {
        Platform.GENERIC: GenericPlatform,
        Platform.TERMINAL: TerminalPlatform,
        Platform.WEBXR: WebXRPlatform,
    }

    platform_class = platforms.get(platform_type)
    if not platform_class:
        raise ValueError(f"Unknown platform type: {platform_type}")

    return platform_class()
