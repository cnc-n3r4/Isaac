"""
3D API Design for Spatial Computing

Provides core primitives for working in 3D space, including vectors,
objects, transformations, and spatial relationships.
"""

import json
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class CoordinateSystem(Enum):
    """Coordinate system types for spatial computing"""
    WORLD = "world"  # Global coordinate system
    LOCAL = "local"  # Object-relative coordinates
    SCREEN = "screen"  # 2D screen projection
    HEAD = "head"  # Head-relative (VR/AR headset)
    HAND = "hand"  # Hand-relative (controllers)


@dataclass
class Vector3D:
    """3D vector with common operations"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def magnitude(self) -> float:
        """Calculate vector magnitude"""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> 'Vector3D':
        """Return normalized vector"""
        mag = self.magnitude()
        if mag == 0:
            return Vector3D(0, 0, 0)
        return Vector3D(self.x/mag, self.y/mag, self.z/mag)

    def dot(self, other: 'Vector3D') -> float:
        """Dot product with another vector"""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vector3D') -> 'Vector3D':
        """Cross product with another vector"""
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def distance_to(self, other: 'Vector3D') -> float:
        """Calculate distance to another point"""
        return math.sqrt(
            (self.x - other.x)**2 +
            (self.y - other.y)**2 +
            (self.z - other.z)**2
        )

    def __add__(self, other: 'Vector3D') -> 'Vector3D':
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3D') -> 'Vector3D':
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> 'Vector3D':
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def to_dict(self) -> Dict[str, float]:
        return {'x': self.x, 'y': self.y, 'z': self.z}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'Vector3D':
        return cls(data['x'], data['y'], data['z'])


@dataclass
class Quaternion:
    """Quaternion for 3D rotations"""
    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def normalize(self) -> 'Quaternion':
        """Return normalized quaternion"""
        mag = math.sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)
        if mag == 0:
            return Quaternion(1, 0, 0, 0)
        return Quaternion(self.w/mag, self.x/mag, self.y/mag, self.z/mag)

    def to_euler(self) -> Tuple[float, float, float]:
        """Convert to Euler angles (pitch, yaw, roll)"""
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (self.w * self.x + self.y * self.z)
        cosr_cosp = 1 - 2 * (self.x**2 + self.y**2)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2 * (self.w * self.y - self.z * self.x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2 * (self.w * self.z + self.x * self.y)
        cosy_cosp = 1 - 2 * (self.y**2 + self.z**2)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return (pitch, yaw, roll)

    @classmethod
    def from_euler(cls, pitch: float, yaw: float, roll: float) -> 'Quaternion':
        """Create quaternion from Euler angles"""
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        return cls(
            w=cr * cp * cy + sr * sp * sy,
            x=sr * cp * cy - cr * sp * sy,
            y=cr * sp * cy + sr * cp * sy,
            z=cr * cp * sy - sr * sp * cy
        )

    def to_dict(self) -> Dict[str, float]:
        return {'w': self.w, 'x': self.x, 'y': self.y, 'z': self.z}


@dataclass
class Transform3D:
    """Complete 3D transformation (position, rotation, scale)"""
    position: Vector3D = field(default_factory=Vector3D)
    rotation: Quaternion = field(default_factory=Quaternion)
    scale: Vector3D = field(default_factory=lambda: Vector3D(1, 1, 1))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'position': self.position.to_dict(),
            'rotation': self.rotation.to_dict(),
            'scale': self.scale.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transform3D':
        return cls(
            position=Vector3D.from_dict(data['position']),
            rotation=Quaternion(**data['rotation']),
            scale=Vector3D.from_dict(data['scale'])
        )


@dataclass
class SpatialObject:
    """Base class for objects in 3D space"""
    id: str
    name: str
    transform: Transform3D = field(default_factory=Transform3D)
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    visible: bool = True
    interactive: bool = True

    def get_world_position(self, workspace: 'SpatialWorkspace') -> Vector3D:
        """Get position in world coordinates"""
        if self.parent is None:
            return self.transform.position

        parent_obj = workspace.get_object(self.parent)
        if parent_obj:
            parent_pos = parent_obj.get_world_position(workspace)
            return parent_pos + self.transform.position

        return self.transform.position

    def distance_to(self, other: 'SpatialObject', workspace: 'SpatialWorkspace') -> float:
        """Calculate distance to another object"""
        pos1 = self.get_world_position(workspace)
        pos2 = other.get_world_position(workspace)
        return pos1.distance_to(pos2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'transform': self.transform.to_dict(),
            'parent': self.parent,
            'children': self.children,
            'metadata': self.metadata,
            'visible': self.visible,
            'interactive': self.interactive
        }


class SpatialWorkspace:
    """Manages a 3D workspace with objects and spatial relationships"""

    def __init__(self, name: str = "default"):
        self.name = name
        self.objects: Dict[str, SpatialObject] = {}
        self.coordinate_system = CoordinateSystem.WORLD
        self.origin = Vector3D(0, 0, 0)

    def add_object(self, obj: SpatialObject) -> None:
        """Add object to workspace"""
        self.objects[obj.id] = obj

        # Update parent's children list
        if obj.parent and obj.parent in self.objects:
            parent = self.objects[obj.parent]
            if obj.id not in parent.children:
                parent.children.append(obj.id)

    def remove_object(self, obj_id: str) -> None:
        """Remove object from workspace"""
        if obj_id not in self.objects:
            return

        obj = self.objects[obj_id]

        # Remove from parent's children
        if obj.parent and obj.parent in self.objects:
            parent = self.objects[obj.parent]
            if obj_id in parent.children:
                parent.children.remove(obj_id)

        # Recursively remove children
        for child_id in obj.children[:]:
            self.remove_object(child_id)

        del self.objects[obj_id]

    def get_object(self, obj_id: str) -> Optional[SpatialObject]:
        """Get object by ID"""
        return self.objects.get(obj_id)

    def find_objects_near(self, position: Vector3D, radius: float) -> List[SpatialObject]:
        """Find all objects within radius of position"""
        nearby = []
        for obj in self.objects.values():
            world_pos = obj.get_world_position(self)
            if position.distance_to(world_pos) <= radius:
                nearby.append(obj)
        return nearby

    def find_objects_by_name(self, name: str) -> List[SpatialObject]:
        """Find objects by name (supports partial matching)"""
        return [obj for obj in self.objects.values() if name.lower() in obj.name.lower()]

    def get_hierarchy(self) -> Dict[str, Any]:
        """Get object hierarchy as tree"""
        roots = [obj for obj in self.objects.values() if obj.parent is None]

        def build_tree(obj: SpatialObject) -> Dict[str, Any]:
            return {
                'id': obj.id,
                'name': obj.name,
                'children': [build_tree(self.objects[child_id])
                           for child_id in obj.children if child_id in self.objects]
            }

        return {
            'workspace': self.name,
            'roots': [build_tree(obj) for obj in roots]
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize workspace to dictionary"""
        return {
            'name': self.name,
            'coordinate_system': self.coordinate_system.value,
            'origin': self.origin.to_dict(),
            'objects': {obj_id: obj.to_dict() for obj_id, obj in self.objects.items()}
        }

    def save(self, filepath: str) -> None:
        """Save workspace to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'SpatialWorkspace':
        """Load workspace from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        workspace = cls(data['name'])
        workspace.coordinate_system = CoordinateSystem(data['coordinate_system'])
        workspace.origin = Vector3D.from_dict(data['origin'])

        # Load objects
        for obj_id, obj_data in data['objects'].items():
            obj = SpatialObject(
                id=obj_data['id'],
                name=obj_data['name'],
                transform=Transform3D.from_dict(obj_data['transform']),
                parent=obj_data['parent'],
                children=obj_data['children'],
                metadata=obj_data['metadata'],
                visible=obj_data['visible'],
                interactive=obj_data['interactive']
            )
            workspace.objects[obj_id] = obj

        return workspace


class SpatialAPI:
    """High-level API for spatial computing operations"""

    def __init__(self):
        self.workspaces: Dict[str, SpatialWorkspace] = {}
        self.active_workspace: Optional[str] = None

    def create_workspace(self, name: str) -> SpatialWorkspace:
        """Create a new spatial workspace"""
        workspace = SpatialWorkspace(name)
        self.workspaces[name] = workspace
        if self.active_workspace is None:
            self.active_workspace = name
        return workspace

    def get_workspace(self, name: Optional[str] = None) -> Optional[SpatialWorkspace]:
        """Get workspace by name, or active workspace if name is None"""
        if name is None:
            name = self.active_workspace
        return self.workspaces.get(name) if name else None

    def set_active_workspace(self, name: str) -> bool:
        """Set the active workspace"""
        if name in self.workspaces:
            self.active_workspace = name
            return True
        return False

    def create_object(
        self,
        name: str,
        position: Optional[Vector3D] = None,
        workspace: Optional[str] = None
    ) -> Optional[SpatialObject]:
        """Create a new spatial object"""
        ws = self.get_workspace(workspace)
        if ws is None:
            return None

        import uuid
        obj = SpatialObject(
            id=str(uuid.uuid4()),
            name=name,
            transform=Transform3D(position=position or Vector3D())
        )
        ws.add_object(obj)
        return obj

    def calculate_spatial_relationships(
        self,
        obj1_id: str,
        obj2_id: str,
        workspace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate spatial relationships between two objects"""
        ws = self.get_workspace(workspace)
        if ws is None:
            return {}

        obj1 = ws.get_object(obj1_id)
        obj2 = ws.get_object(obj2_id)

        if not obj1 or not obj2:
            return {}

        pos1 = obj1.get_world_position(ws)
        pos2 = obj2.get_world_position(ws)

        direction = pos2 - pos1
        distance = pos1.distance_to(pos2)

        return {
            'distance': distance,
            'direction': direction.to_dict(),
            'obj1_position': pos1.to_dict(),
            'obj2_position': pos2.to_dict()
        }
