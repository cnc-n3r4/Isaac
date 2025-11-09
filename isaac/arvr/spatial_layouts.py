"""
Spatial Layouts for 3D Workspace Organization

Provides layout algorithms and templates for organizing UI elements,
code windows, and tools in 3D space for optimal VR/AR workflows.
"""

import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from isaac.arvr.spatial_api import SpatialObject, SpatialWorkspace, Vector3D


class LayoutType(Enum):
    """Predefined layout types"""

    CIRCULAR = "circular"  # Objects arranged in a circle
    GRID = "grid"  # 3D grid arrangement
    SPHERE = "sphere"  # Objects on sphere surface
    HEMISPHERE = "hemisphere"  # Objects on hemisphere (AR mode)
    LINEAR = "linear"  # Linear arrangement
    LAYERED = "layered"  # Stacked layers
    FOCUS_CONTEXT = "focus_context"  # Central focus with context around
    CUSTOM = "custom"


class LayoutAlignment(Enum):
    """Alignment options for layouts"""

    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    FRONT = "front"
    BACK = "back"


@dataclass
class LayoutConstraints:
    """Constraints for layout generation"""

    min_distance: float = 0.5  # meters
    max_distance: float = 3.0  # meters
    optimal_viewing_distance: float = 1.5  # meters
    field_of_view: float = 110.0  # degrees
    maintain_aspect_ratio: bool = True
    allow_overlap: bool = False
    face_center: bool = True  # Objects face the center


@dataclass
class LayoutNode:
    """Single node in a layout"""

    id: str
    name: str
    position: Vector3D
    size: Vector3D = field(default_factory=lambda: Vector3D(0.3, 0.3, 0.1))
    priority: int = 0  # Higher priority = closer to center
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_spatial_object(self) -> SpatialObject:
        """Convert to SpatialObject"""
        from isaac.arvr.spatial_api import Transform3D

        return SpatialObject(
            id=self.id,
            name=self.name,
            transform=Transform3D(position=self.position),
            metadata={**self.metadata, "size": self.size.to_dict()},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position.to_dict(),
            "size": self.size.to_dict(),
            "priority": self.priority,
            "metadata": self.metadata,
        }


@dataclass
class Layout:
    """Complete spatial layout"""

    name: str
    type: LayoutType
    nodes: List[LayoutNode] = field(default_factory=list)
    center: Vector3D = field(default_factory=Vector3D)
    constraints: LayoutConstraints = field(default_factory=LayoutConstraints)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: LayoutNode) -> None:
        """Add a node to the layout"""
        self.nodes.append(node)

    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the layout"""
        for i, node in enumerate(self.nodes):
            if node.id == node_id:
                self.nodes.pop(i)
                return True
        return False

    def get_node(self, node_id: str) -> Optional[LayoutNode]:
        """Get a node by ID"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def apply_to_workspace(self, workspace: SpatialWorkspace) -> None:
        """Apply layout to a spatial workspace"""
        for node in self.nodes:
            obj = node.to_spatial_object()
            workspace.add_object(obj)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "nodes": [node.to_dict() for node in self.nodes],
            "center": self.center.to_dict(),
            "constraints": {
                "min_distance": self.constraints.min_distance,
                "max_distance": self.constraints.max_distance,
                "optimal_viewing_distance": self.constraints.optimal_viewing_distance,
                "field_of_view": self.constraints.field_of_view,
                "maintain_aspect_ratio": self.constraints.maintain_aspect_ratio,
                "allow_overlap": self.constraints.allow_overlap,
                "face_center": self.constraints.face_center,
            },
            "metadata": self.metadata,
        }

    def save(self, filepath: str) -> None:
        """Save layout to JSON file"""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "Layout":
        """Load layout from JSON file"""
        with open(filepath, "r") as f:
            data = json.load(f)

        constraints = LayoutConstraints(**data["constraints"])
        layout = cls(
            name=data["name"],
            type=LayoutType(data["type"]),
            center=Vector3D.from_dict(data["center"]),
            constraints=constraints,
            metadata=data["metadata"],
        )

        for node_data in data["nodes"]:
            node = LayoutNode(
                id=node_data["id"],
                name=node_data["name"],
                position=Vector3D.from_dict(node_data["position"]),
                size=Vector3D.from_dict(node_data["size"]),
                priority=node_data["priority"],
                metadata=node_data["metadata"],
            )
            layout.add_node(node)

        return layout


class LayoutAlgorithm:
    """Base class for layout algorithms"""

    def __init__(self, constraints: Optional[LayoutConstraints] = None):
        self.constraints = constraints or LayoutConstraints()

    def generate(self, items: List[str], center: Vector3D) -> List[LayoutNode]:
        """Generate layout for items"""
        raise NotImplementedError


class CircularLayout(LayoutAlgorithm):
    """Arrange items in a circle around center"""

    def generate(self, items: List[str], center: Vector3D) -> List[LayoutNode]:
        nodes = []
        radius = self.constraints.optimal_viewing_distance
        angle_step = 2 * math.pi / len(items)

        for i, item in enumerate(items):
            angle = i * angle_step
            x = center.x + radius * math.cos(angle)
            y = center.y
            z = center.z + radius * math.sin(angle)

            node = LayoutNode(id=f"node_{i}", name=item, position=Vector3D(x, y, z))
            nodes.append(node)

        return nodes


class GridLayout(LayoutAlgorithm):
    """Arrange items in a 3D grid"""

    def __init__(
        self,
        constraints: Optional[LayoutConstraints] = None,
        grid_size: Tuple[int, int, int] = (3, 3, 1),
    ):
        super().__init__(constraints)
        self.grid_size = grid_size

    def generate(self, items: List[str], center: Vector3D) -> List[LayoutNode]:
        nodes = []
        spacing = self.constraints.min_distance * 1.5

        cols, rows, layers = self.grid_size
        x_start = center.x - (cols - 1) * spacing / 2
        y_start = center.y - (rows - 1) * spacing / 2
        z_start = center.z - (layers - 1) * spacing / 2

        idx = 0
        for layer in range(layers):
            for row in range(rows):
                for col in range(cols):
                    if idx >= len(items):
                        break

                    x = x_start + col * spacing
                    y = y_start + row * spacing
                    z = z_start + layer * spacing

                    node = LayoutNode(id=f"node_{idx}", name=items[idx], position=Vector3D(x, y, z))
                    nodes.append(node)
                    idx += 1

        return nodes


class SphereLayout(LayoutAlgorithm):
    """Arrange items on sphere surface"""

    def generate(self, items: List[str], center: Vector3D) -> List[LayoutNode]:
        nodes = []
        radius = self.constraints.optimal_viewing_distance
        count = len(items)

        # Fibonacci sphere algorithm for even distribution
        golden_ratio = (1 + math.sqrt(5)) / 2
        angle_increment = 2 * math.pi * golden_ratio

        for i, item in enumerate(items):
            t = i / count
            inclination = math.acos(1 - 2 * t)
            azimuth = angle_increment * i

            x = center.x + radius * math.sin(inclination) * math.cos(azimuth)
            y = center.y + radius * math.sin(inclination) * math.sin(azimuth)
            z = center.z + radius * math.cos(inclination)

            node = LayoutNode(id=f"node_{i}", name=item, position=Vector3D(x, y, z))
            nodes.append(node)

        return nodes


class HemisphereLayout(LayoutAlgorithm):
    """Arrange items on hemisphere (ideal for AR)"""

    def generate(self, items: List[str], center: Vector3D) -> List[LayoutNode]:
        nodes = []
        radius = self.constraints.optimal_viewing_distance
        count = len(items)

        golden_ratio = (1 + math.sqrt(5)) / 2
        angle_increment = 2 * math.pi * golden_ratio

        for i, item in enumerate(items):
            t = i / count
            # Only use upper hemisphere (y >= 0)
            inclination = math.acos(1 - t)  # 0 to pi/2
            azimuth = angle_increment * i

            x = center.x + radius * math.sin(inclination) * math.cos(azimuth)
            y = center.y + radius * math.cos(inclination)  # Always positive
            z = center.z + radius * math.sin(inclination) * math.sin(azimuth)

            node = LayoutNode(id=f"node_{i}", name=item, position=Vector3D(x, y, z))
            nodes.append(node)

        return nodes


class FocusContextLayout(LayoutAlgorithm):
    """Central focus item with context items around it"""

    def generate(self, items: List[str], center: Vector3D) -> List[LayoutNode]:
        if not items:
            return []

        nodes = []

        # Central focus item
        focus_node = LayoutNode(
            id="focus_0",
            name=items[0],
            position=center,
            priority=10,
            size=Vector3D(0.5, 0.5, 0.1),  # Larger focus item
        )
        nodes.append(focus_node)

        # Context items in circle around focus
        if len(items) > 1:
            context_items = items[1:]
            radius = self.constraints.optimal_viewing_distance * 0.7
            angle_step = 2 * math.pi / len(context_items)

            for i, item in enumerate(context_items):
                angle = i * angle_step
                x = center.x + radius * math.cos(angle)
                y = center.y - 0.3  # Slightly below focus
                z = center.z + radius * math.sin(angle)

                node = LayoutNode(
                    id=f"context_{i}",
                    name=item,
                    position=Vector3D(x, y, z),
                    priority=1,
                    size=Vector3D(0.25, 0.25, 0.05),  # Smaller context items
                )
                nodes.append(node)

        return nodes


class LayoutManager:
    """Manages spatial layouts"""

    def __init__(self):
        self.layouts: Dict[str, Layout] = {}
        self.algorithms: Dict[LayoutType, LayoutAlgorithm] = {
            LayoutType.CIRCULAR: CircularLayout(),
            LayoutType.GRID: GridLayout(),
            LayoutType.SPHERE: SphereLayout(),
            LayoutType.HEMISPHERE: HemisphereLayout(),
            LayoutType.FOCUS_CONTEXT: FocusContextLayout(),
        }

    def create_layout(
        self,
        name: str,
        layout_type: LayoutType,
        items: List[str],
        center: Optional[Vector3D] = None,
        constraints: Optional[LayoutConstraints] = None,
    ) -> Layout:
        """Create a new layout"""
        center = center or Vector3D(0, 1.5, -2)  # Default viewing position
        constraints = constraints or LayoutConstraints()

        algorithm = self.algorithms.get(layout_type)
        if not algorithm:
            raise ValueError(f"Unknown layout type: {layout_type}")

        algorithm.constraints = constraints
        nodes = algorithm.generate(items, center)

        layout = Layout(
            name=name, type=layout_type, nodes=nodes, center=center, constraints=constraints
        )

        self.layouts[name] = layout
        return layout

    def get_layout(self, name: str) -> Optional[Layout]:
        """Get layout by name"""
        return self.layouts.get(name)

    def register_algorithm(self, layout_type: LayoutType, algorithm: LayoutAlgorithm) -> None:
        """Register custom layout algorithm"""
        self.algorithms[layout_type] = algorithm

    def optimize_layout(self, layout: Layout) -> Layout:
        """Optimize layout to prevent overlaps and improve visibility"""
        # Simple optimization: push overlapping nodes apart
        changed = True
        iterations = 0
        max_iterations = 100

        while changed and iterations < max_iterations:
            changed = False
            iterations += 1

            for i, node1 in enumerate(layout.nodes):
                for node2 in layout.nodes[i + 1 :]:
                    dist = node1.position.distance_to(node2.position)
                    min_dist = layout.constraints.min_distance

                    if dist < min_dist:
                        # Push nodes apart
                        if dist == 0.0:
                            # Special case: nodes at exact same position
                            # Move them in opposite directions along x-axis
                            offset = Vector3D(min_dist / 2, 0, 0)
                        else:
                            direction = (node2.position - node1.position).normalize()
                            offset = direction * ((min_dist - dist) / 2)

                        node1.position = node1.position - offset
                        node2.position = node2.position + offset
                        changed = True

        return layout

    def get_recommended_layout(self, item_count: int, context: str = "general") -> LayoutType:
        """Recommend layout type based on item count and context"""
        if item_count <= 1:
            return LayoutType.FOCUS_CONTEXT

        if context == "ar":
            # AR prefers hemisphere (ground plane visible)
            return LayoutType.HEMISPHERE

        if item_count <= 8:
            # Small number: circular is intuitive
            return LayoutType.CIRCULAR

        if item_count <= 20:
            # Medium number: grid works well
            return LayoutType.GRID

        # Large number: sphere or hemisphere
        return LayoutType.SPHERE if context == "vr" else LayoutType.HEMISPHERE

    def save_layout(self, name: str, filepath: str) -> bool:
        """Save layout to file"""
        layout = self.get_layout(name)
        if layout:
            layout.save(filepath)
            return True
        return False

    def load_layout(self, filepath: str) -> Layout:
        """Load layout from file"""
        layout = Layout.load(filepath)
        self.layouts[layout.name] = layout
        return layout
