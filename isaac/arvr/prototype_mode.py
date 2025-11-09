"""
Prototype Mode for AR/VR Testing in 2D Terminal

Provides ASCII-based visualization and testing of spatial layouts,
gestures, and multimodal interactions in a standard terminal.
"""

import math
import os
from dataclasses import dataclass
from typing import List, Tuple

from isaac.arvr.gesture_api import Gesture
from isaac.arvr.multimodal_input import MultimodalInput
from isaac.arvr.spatial_api import SpatialObject, SpatialWorkspace, Vector3D
from isaac.arvr.spatial_layouts import Layout, LayoutNode


@dataclass
class Camera:
    """Virtual camera for 2D projection"""

    position: Vector3D
    target: Vector3D
    fov: float = 60.0  # degrees

    def project_to_2d(
        self, point: Vector3D, screen_width: int, screen_height: int
    ) -> Tuple[int, int]:
        """Project 3D point to 2D screen coordinates"""
        # Simple orthographic projection for now
        # Transform to camera space
        dx = point.x - self.position.x
        dy = point.y - self.position.y
        point.z - self.position.z

        # Project to screen
        scale = 20.0  # Adjust for terminal size
        x = int(screen_width / 2 + dx * scale)
        y = int(screen_height / 2 - dy * scale)

        return (x, y)


class PrototypeRenderer:
    """Renders 3D scenes in 2D terminal"""

    def __init__(self, width: int = 80, height: int = 30):
        self.width = width
        self.height = height
        self.camera = Camera(position=Vector3D(0, 0, 5), target=Vector3D(0, 0, 0))
        self.buffer: List[List[str]] = []
        self._clear_buffer()

    def _clear_buffer(self) -> None:
        """Clear the rendering buffer"""
        self.buffer = [[" " for _ in range(self.width)] for _ in range(self.height)]

    def _set_pixel(self, x: int, y: int, char: str) -> None:
        """Set a character in the buffer"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = char

    def _draw_text(self, x: int, y: int, text: str) -> None:
        """Draw text at position"""
        for i, char in enumerate(text):
            self._set_pixel(x + i, y, char)

    def _draw_box(self, x: int, y: int, width: int, height: int, char: str = "#") -> None:
        """Draw a box outline"""
        # Top and bottom
        for i in range(width):
            self._set_pixel(x + i, y, char)
            self._set_pixel(x + i, y + height - 1, char)

        # Sides
        for i in range(height):
            self._set_pixel(x, y + i, char)
            self._set_pixel(x + width - 1, y + i, char)

    def _draw_line(self, x1: int, y1: int, x2: int, y2: int, char: str = "-") -> None:
        """Draw a line using Bresenham's algorithm"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            self._set_pixel(x1, y1, char)

            if x1 == x2 and y1 == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def render_workspace(self, workspace: SpatialWorkspace) -> str:
        """Render a spatial workspace to ASCII"""
        self._clear_buffer()

        # Draw border
        self._draw_box(0, 0, self.width, self.height, "█")

        # Draw title
        title = f"Workspace: {workspace.name}"
        self._draw_text(2, 1, title)

        # Draw coordinate system indicator
        self._draw_text(2, 2, f"Objects: {len(workspace.objects)}")

        # Render objects
        for obj in workspace.objects.values():
            if obj.visible:
                self._render_object(obj, workspace)

        # Draw legend
        legend_y = self.height - 3
        self._draw_text(2, legend_y, "Legend: [O]=Object  [*]=Center  [+]=Focus")

        return self._buffer_to_string()

    def _render_object(self, obj: SpatialObject, workspace: SpatialWorkspace) -> None:
        """Render a single object"""
        world_pos = obj.get_world_position(workspace)
        x, y = self.camera.project_to_2d(world_pos, self.width, self.height)

        # Draw object representation
        if obj.metadata.get("is_focus", False):
            self._set_pixel(x, y, "+")
        else:
            self._set_pixel(x, y, "O")

        # Draw label if space allows
        if y + 1 < self.height - 1:
            label = obj.name[:10]  # Truncate long names
            self._draw_text(x - len(label) // 2, y + 1, label)

    def render_layout(self, layout: Layout) -> str:
        """Render a spatial layout to ASCII"""
        self._clear_buffer()

        # Draw border
        self._draw_box(0, 0, self.width, self.height, "█")

        # Draw title
        title = f"Layout: {layout.name} ({layout.type.value})"
        self._draw_text(2, 1, title)

        # Draw center
        cx, cy = self.camera.project_to_2d(layout.center, self.width, self.height)
        self._set_pixel(cx, cy, "*")

        # Render nodes
        for node in layout.nodes:
            self._render_layout_node(node, layout)

        # Draw legend
        legend_y = self.height - 3
        self._draw_text(2, legend_y, f"Nodes: {len(layout.nodes)}")

        return self._buffer_to_string()

    def _render_layout_node(self, node: LayoutNode, layout: Layout) -> None:
        """Render a layout node"""
        x, y = self.camera.project_to_2d(node.position, self.width, self.height)

        # Draw node
        if node.priority > 5:
            self._set_pixel(x, y, "+")  # High priority
        else:
            self._set_pixel(x, y, "o")

        # Draw label
        label = node.name[:8]
        self._draw_text(x - len(label) // 2, y + 1, label)

        # Draw line to center if not too far
        cx, cy = self.camera.project_to_2d(layout.center, self.width, self.height)
        distance = abs(x - cx) + abs(y - cy)
        if distance < 20:  # Only draw lines for nearby nodes
            self._draw_line(cx, cy, x, y, ".")

    def render_gesture(self, gesture: Gesture) -> str:
        """Render a gesture trajectory to ASCII"""
        self._clear_buffer()

        # Draw border
        self._draw_box(0, 0, self.width, self.height, "█")

        # Draw title
        title = f"Gesture: {gesture.type.value} ({gesture.hand.value})"
        self._draw_text(2, 1, title)

        # Draw info
        self._draw_text(2, 2, f"Points: {len(gesture.points)}")
        self._draw_text(2, 3, f"Duration: {gesture.duration():.2f}s")
        self._draw_text(2, 4, f"Confidence: {gesture.confidence:.2f}")

        # Draw trajectory
        if len(gesture.points) > 1:
            for i in range(len(gesture.points) - 1):
                p1 = gesture.points[i].position
                p2 = gesture.points[i + 1].position

                x1, y1 = self.camera.project_to_2d(p1, self.width, self.height)
                x2, y2 = self.camera.project_to_2d(p2, self.width, self.height)

                self._draw_line(x1, y1, x2, y2, "*")

            # Mark start and end
            start = gesture.points[0].position
            end = gesture.points[-1].position

            sx, sy = self.camera.project_to_2d(start, self.width, self.height)
            ex, ey = self.camera.project_to_2d(end, self.width, self.height)

            self._set_pixel(sx, sy, "S")
            self._set_pixel(ex, ey, "E")

        return self._buffer_to_string()

    def render_multimodal_input(self, multimodal_input: MultimodalInput) -> str:
        """Render multimodal input visualization"""
        self._clear_buffer()

        # Draw border
        self._draw_box(0, 0, self.width, self.height, "█")

        # Draw title
        title = f"Multimodal Input: {multimodal_input.modality.value}"
        self._draw_text(2, 1, title)

        line = 3

        # Voice command
        if multimodal_input.voice_command:
            self._draw_text(2, line, "Voice: " + multimodal_input.voice_command.text)
            line += 1
            self._draw_text(
                2, line, f"  Confidence: {multimodal_input.voice_command.confidence:.2f}"
            )
            line += 2

        # Gesture
        if multimodal_input.gesture:
            gesture = multimodal_input.gesture
            self._draw_text(2, line, f"Gesture: {gesture.type.value}")
            line += 1
            self._draw_text(2, line, f"  Hand: {gesture.hand.value}")
            line += 1
            self._draw_text(2, line, f"  Confidence: {gesture.confidence:.2f}")
            line += 2

        # Gaze target
        if multimodal_input.gaze_target:
            self._draw_text(2, line, f"Gaze: {multimodal_input.gaze_target}")
            line += 2

        # Intent
        intent = multimodal_input.get_intent()
        self._draw_text(2, line, f"Intent: {intent}")

        return self._buffer_to_string()

    def render_scene_overview(
        self,
        workspace: SpatialWorkspace,
        active_gestures: List[Gesture],
        recent_inputs: List[MultimodalInput],
    ) -> str:
        """Render complete scene with all elements"""
        self._clear_buffer()

        # Draw border
        self._draw_box(0, 0, self.width, self.height, "█")

        # Title
        self._draw_text(2, 1, "AR/VR Prototype Scene Overview")

        # Workspace section
        self._draw_text(2, 3, f"Workspace: {workspace.name}")
        self._draw_text(2, 4, f"  Objects: {len(workspace.objects)}")

        # Gestures section
        y = 6
        self._draw_text(2, y, f"Active Gestures: {len(active_gestures)}")
        for i, gesture in enumerate(active_gestures[:3]):  # Show up to 3
            y += 1
            self._draw_text(4, y, f"{i+1}. {gesture.type.value} ({gesture.hand.value})")

        # Inputs section
        y += 2
        self._draw_text(2, y, f"Recent Inputs: {len(recent_inputs)}")
        for i, inp in enumerate(recent_inputs[-3:]):  # Show last 3
            y += 1
            self._draw_text(4, y, f"{i+1}. {inp.modality.value}: {inp.get_intent()}")

        # Visualize workspace (simplified)
        y = self.height // 2
        self.width // 2

        for obj in list(workspace.objects.values())[:5]:  # Show up to 5 objects
            world_pos = obj.get_world_position(workspace)
            x, y_pos = self.camera.project_to_2d(world_pos, self.width, self.height)
            self._set_pixel(x, y_pos, "O")

        return self._buffer_to_string()

    def _buffer_to_string(self) -> str:
        """Convert buffer to string"""
        return "\n".join("".join(row) for row in self.buffer)

    def clear_screen(self) -> None:
        """Clear the terminal screen"""
        os.system("clear" if os.name != "nt" else "cls")

    def render_and_display(self, content: str) -> None:
        """Clear screen and display rendered content"""
        self.clear_screen()
        print(content)

    def create_demo_scene(self) -> SpatialWorkspace:
        """Create a demo scene for testing"""
        from isaac.arvr.spatial_api import Transform3D

        workspace = SpatialWorkspace("demo_scene")

        # Create some objects
        positions = [
            Vector3D(0, 0, 0),  # Center
            Vector3D(1, 0, -1),  # Front right
            Vector3D(-1, 0, -1),  # Front left
            Vector3D(0, 1, -1),  # Top
            Vector3D(0, -1, -1),  # Bottom
        ]

        names = ["Center", "Terminal", "Editor", "Browser", "Debugger"]

        for i, (name, pos) in enumerate(zip(names, positions)):
            obj = SpatialObject(id=f"demo_{i}", name=name, transform=Transform3D(position=pos))
            workspace.add_object(obj)

        return workspace

    def interactive_demo(self) -> None:
        """Run an interactive demo of the prototype renderer"""
        workspace = self.create_demo_scene()

        self.clear_screen()
        print("AR/VR Prototype Mode - Interactive Demo")
        print("=" * 60)
        print("\nPress Enter to cycle through visualizations...")
        print("Type 'quit' to exit\n")

        demos = [
            ("Workspace View", lambda: self.render_workspace(workspace)),
            ("Demo Layout", lambda: self._demo_layout()),
            ("Demo Gesture", lambda: self._demo_gesture()),
        ]

        idx = 0
        while True:
            name, renderer = demos[idx % len(demos)]

            print(f"\n--- {name} ---")
            print(renderer())

            user_input = input("\nPress Enter for next, or 'quit' to exit: ").strip().lower()
            if user_input == "quit":
                break

            idx += 1

    def _demo_layout(self) -> str:
        """Create demo layout"""
        from isaac.arvr.spatial_layouts import Layout, LayoutNode, LayoutType

        layout = Layout(name="demo_layout", type=LayoutType.CIRCULAR, center=Vector3D(0, 0, -2))

        # Add nodes in a circle
        import math

        radius = 1.5
        for i in range(6):
            angle = i * (2 * math.pi / 6)
            x = radius * math.cos(angle)
            z = -2 + radius * math.sin(angle)

            node = LayoutNode(
                id=f"node_{i}",
                name=f"Window{i+1}",
                position=Vector3D(x, 0, z),
                priority=5 if i == 0 else 1,
            )
            layout.add_node(node)

        return self.render_layout(layout)

    def _demo_gesture(self) -> str:
        """Create demo gesture"""
        import time

        from isaac.arvr.gesture_api import Gesture, GesturePoint, GestureType, HandType

        gesture = Gesture(
            type=GestureType.SWIPE,
            hand=HandType.RIGHT,
            start_time=time.time() - 1.0,
            end_time=time.time(),
            confidence=0.95,
        )

        # Create swipe trajectory
        for i in range(10):
            t = i / 9.0
            x = -1.0 + 2.0 * t  # Swipe from left to right
            y = 0.2 * math.sin(t * math.pi)  # Slight curve

            point = GesturePoint(position=Vector3D(x, y, -1), timestamp=time.time() - 1.0 + t)
            gesture.points.append(point)

        return self.render_gesture(gesture)
