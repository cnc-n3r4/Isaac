"""
AR/VR Command Interface

Provides command-line interface for AR/VR preparation features.
"""

import json
from typing import Dict, Any, List

from isaac.arvr.spatial_api import SpatialAPI, Vector3D, SpatialWorkspace
from isaac.arvr.gesture_api import GestureAPI, GestureType
from isaac.arvr.spatial_layouts import LayoutManager, LayoutType, LayoutConstraints
from isaac.arvr.multimodal_input import MultimodalInputHandler
from isaac.arvr.prototype_mode import PrototypeRenderer
from isaac.arvr.platform_adapter import PlatformAdapter, Platform
from isaac.arvr.gesture_api import HandType


class ARVRCommand:
    """Main AR/VR command handler"""

    def __init__(self):
        self.spatial_api = SpatialAPI()
        self.gesture_api = GestureAPI()
        self.layout_manager = LayoutManager()
        self.multimodal_handler = MultimodalInputHandler()
        self.renderer = PrototypeRenderer()
        self.platform_adapter = PlatformAdapter()

    def execute(self, args: List[str]) -> str:
        """Execute AR/VR command"""
        if not args:
            return self._show_help()

        subcommand = args[0]
        subargs = args[1:]

        commands = {
            'workspace': self._cmd_workspace,
            'layout': self._cmd_layout,
            'gesture': self._cmd_gesture,
            'multimodal': self._cmd_multimodal,
            'platform': self._cmd_platform,
            'demo': self._cmd_demo,
            'status': self._cmd_status,
            'help': lambda _: self._show_help(),
        }

        handler = commands.get(subcommand)
        if handler:
            try:
                return handler(subargs)
            except Exception as e:
                return f"Error: {str(e)}"
        else:
            return f"Unknown subcommand: {subcommand}\n\n{self._show_help()}"

    def _cmd_workspace(self, args: List[str]) -> str:
        """Workspace management commands"""
        if not args:
            return self._workspace_list()

        action = args[0]

        if action == 'create':
            name = args[1] if len(args) > 1 else "default"
            workspace = self.spatial_api.create_workspace(name)
            return f"Created workspace: {name}"

        elif action == 'list':
            return self._workspace_list()

        elif action == 'show':
            name = args[1] if len(args) > 1 else None
            workspace = self.spatial_api.get_workspace(name)
            if workspace:
                output = self.renderer.render_workspace(workspace)
                return output
            return "No workspace found"

        elif action == 'add-object':
            name = args[1] if len(args) > 1 else "Object"
            x = float(args[2]) if len(args) > 2 else 0.0
            y = float(args[3]) if len(args) > 3 else 0.0
            z = float(args[4]) if len(args) > 4 else 0.0

            obj = self.spatial_api.create_object(name, Vector3D(x, y, z))
            if obj:
                return f"Added object '{name}' at ({x}, {y}, {z})"
            return "Failed to add object"

        elif action == 'save':
            name = args[1] if len(args) > 1 else None
            filepath = args[2] if len(args) > 2 else f"workspace_{name}.json"
            workspace = self.spatial_api.get_workspace(name)
            if workspace:
                workspace.save(filepath)
                return f"Saved workspace to {filepath}"
            return "No workspace found"

        return "Usage: arvr workspace [create|list|show|add-object|save] [args...]"

    def _workspace_list(self) -> str:
        """List all workspaces"""
        workspaces = self.spatial_api.workspaces
        if not workspaces:
            return "No workspaces created"

        output = ["Workspaces:"]
        for name, workspace in workspaces.items():
            active = " (active)" if name == self.spatial_api.active_workspace else ""
            output.append(f"  - {name}: {len(workspace.objects)} objects{active}")

        return "\n".join(output)

    def _cmd_layout(self, args: List[str]) -> str:
        """Layout management commands"""
        if not args:
            return self._layout_list()

        action = args[0]

        if action == 'create':
            name = args[1] if len(args) > 1 else "layout"
            layout_type = args[2] if len(args) > 2 else "circular"
            items_str = args[3] if len(args) > 3 else "Item1,Item2,Item3"

            items = [item.strip() for item in items_str.split(',')]

            try:
                ltype = LayoutType[layout_type.upper()]
            except KeyError:
                return f"Invalid layout type. Use: {', '.join(t.value for t in LayoutType)}"

            layout = self.layout_manager.create_layout(name, ltype, items)
            return f"Created {layout_type} layout '{name}' with {len(items)} items"

        elif action == 'list':
            return self._layout_list()

        elif action == 'show':
            name = args[1] if len(args) > 1 else None
            layout = self.layout_manager.get_layout(name)
            if layout:
                output = self.renderer.render_layout(layout)
                return output
            return "Layout not found"

        elif action == 'optimize':
            name = args[1] if len(args) > 1 else None
            layout = self.layout_manager.get_layout(name)
            if layout:
                optimized = self.layout_manager.optimize_layout(layout)
                return f"Optimized layout '{name}'"
            return "Layout not found"

        elif action == 'recommend':
            count = int(args[1]) if len(args) > 1 else 5
            context = args[2] if len(args) > 2 else "general"
            recommended = self.layout_manager.get_recommended_layout(count, context)
            return f"Recommended layout for {count} items ({context}): {recommended.value}"

        return "Usage: arvr layout [create|list|show|optimize|recommend] [args...]"

    def _layout_list(self) -> str:
        """List all layouts"""
        layouts = self.layout_manager.layouts
        if not layouts:
            return "No layouts created"

        output = ["Layouts:"]
        for name, layout in layouts.items():
            output.append(f"  - {name}: {layout.type.value}, {len(layout.nodes)} nodes")

        return "\n".join(output)

    def _cmd_gesture(self, args: List[str]) -> str:
        """Gesture-related commands"""
        if not args:
            return self._gesture_stats()

        action = args[0]

        if action == 'simulate':
            gesture_type = args[1] if len(args) > 1 else "swipe"
            try:
                gtype = GestureType[gesture_type.upper()]
            except KeyError:
                return f"Invalid gesture type. Use: {', '.join(t.value for t in GestureType)}"

            # Create simple trajectory
            trajectory = [
                Vector3D(-1, 0, -1),
                Vector3D(0, 0, -1),
                Vector3D(1, 0, -1)
            ]

            gesture = self.gesture_api.simulate_gesture(
                gtype, HandType.RIGHT, trajectory, duration=0.5
            )

            if gesture:
                output = self.renderer.render_gesture(gesture)
                return output
            return "Failed to simulate gesture"

        elif action == 'stats':
            return self._gesture_stats()

        elif action == 'list':
            output = ["Available gesture types:"]
            for gtype in GestureType:
                output.append(f"  - {gtype.value}")
            return "\n".join(output)

        return "Usage: arvr gesture [simulate|stats|list] [args...]"

    def _gesture_stats(self) -> str:
        """Get gesture statistics"""
        stats = self.gesture_api.get_gesture_stats()
        output = ["Gesture Statistics:"]
        output.append(f"  Total gestures: {stats['total_gestures']}")
        output.append(f"  Average confidence: {stats['average_confidence']:.2f}")
        output.append(f"  Active gestures: {stats['active_gestures']}")

        if stats['type_counts']:
            output.append("\n  Gestures by type:")
            for gtype, count in stats['type_counts'].items():
                output.append(f"    {gtype}: {count}")

        return "\n".join(output)

    def _cmd_multimodal(self, args: List[str]) -> str:
        """Multimodal input commands"""
        if not args:
            return self._multimodal_stats()

        action = args[0]

        if action == 'simulate':
            voice = args[1] if len(args) > 1 else "move this"
            gesture = args[2] if len(args) > 2 else "grab"

            try:
                gtype = GestureType[gesture.upper()]
            except KeyError:
                return f"Invalid gesture type"

            inputs = self.multimodal_handler.simulate_interaction(
                voice, gtype, gaze_target="object_1"
            )

            output = ["Simulated multimodal interaction:"]
            for inp in inputs:
                rendered = self.renderer.render_multimodal_input(inp)
                output.append(rendered)
                output.append("-" * 60)

            return "\n".join(output)

        elif action == 'stats':
            return self._multimodal_stats()

        elif action == 'patterns':
            patterns = self.multimodal_handler.patterns
            output = ["Registered multimodal patterns:"]
            for name, pattern in patterns.items():
                output.append(f"  - {name}:")
                output.append(f"      Modalities: {[m.value for m in pattern.required_modalities]}")
                output.append(f"      Voice keywords: {pattern.voice_keywords}")
                output.append(f"      Gestures: {[g.value for g in pattern.gesture_types]}")

            return "\n".join(output)

        return "Usage: arvr multimodal [simulate|stats|patterns] [args...]"

    def _multimodal_stats(self) -> str:
        """Get multimodal input statistics"""
        stats = self.multimodal_handler.get_statistics()
        output = ["Multimodal Input Statistics:"]
        output.append(f"  Total inputs: {stats['total_inputs']}")
        output.append(f"  Combined inputs: {stats.get('combined_inputs', 0)}")
        output.append(f"  Pattern matches: {stats.get('pattern_matches', 0)}")
        output.append(f"  Patterns registered: {stats.get('patterns_registered', 0)}")

        if 'modality_counts' in stats:
            output.append("\n  Inputs by modality:")
            for modality, count in stats['modality_counts'].items():
                output.append(f"    {modality}: {count}")

        return "\n".join(output)

    def _cmd_platform(self, args: List[str]) -> str:
        """Platform adapter commands"""
        if not args:
            return self._platform_status()

        action = args[0]

        if action == 'list':
            platforms = self.platform_adapter.get_available_platforms()
            output = ["Available platforms:"]
            for platform in platforms:
                output.append(f"  - {platform.value}")
            return "\n".join(output)

        elif action == 'init':
            platform_name = args[1] if len(args) > 1 else "terminal"
            try:
                platform = Platform[platform_name.upper()]
            except KeyError:
                return f"Invalid platform. Use: {', '.join(p.value for p in Platform)}"

            success = self.platform_adapter.initialize_platform(platform)
            if success:
                return f"Initialized platform: {platform.value}"
            return f"Failed to initialize platform: {platform.value}"

        elif action == 'status':
            return self._platform_status()

        elif action == 'report':
            report = self.platform_adapter.create_platform_report()
            return json.dumps(report, indent=2)

        return "Usage: arvr platform [list|init|status|report] [args...]"

    def _platform_status(self) -> str:
        """Get platform status"""
        platform = self.platform_adapter.get_current_platform()

        if not platform:
            return "No platform initialized"

        caps = platform.get_capabilities()
        state = platform.update()

        output = ["Platform Status:"]
        output.append(f"  Platform: {caps.platform.value}")
        output.append(f"  Display mode: {caps.display_mode.value}")
        output.append(f"  Initialized: {platform.is_initialized}")
        output.append(f"  Connected: {state.is_connected}")
        output.append(f"\n  Capabilities:")
        output.append(f"    6DOF: {caps.supports_6dof}")
        output.append(f"    Hand tracking: {caps.supports_hand_tracking}")
        output.append(f"    Eye tracking: {caps.supports_eye_tracking}")
        output.append(f"    Spatial audio: {caps.supports_spatial_audio}")
        output.append(f"    FOV: {caps.max_fov}°")
        output.append(f"    Refresh rate: {caps.refresh_rate} Hz")

        return "\n".join(output)

    def _cmd_demo(self, args: List[str]) -> str:
        """Run interactive demo"""
        demo_type = args[0] if args else "all"

        if demo_type == "workspace":
            workspace = self.renderer.create_demo_scene()
            return self.renderer.render_workspace(workspace)

        elif demo_type == "layout":
            return self.renderer._demo_layout()

        elif demo_type == "gesture":
            return self.renderer._demo_gesture()

        elif demo_type == "interactive":
            self.renderer.interactive_demo()
            return "Interactive demo completed"

        else:
            # Show all demos
            output = []
            output.append("=== Demo: Workspace ===")
            workspace = self.renderer.create_demo_scene()
            output.append(self.renderer.render_workspace(workspace))
            output.append("\n=== Demo: Layout ===")
            output.append(self.renderer._demo_layout())
            output.append("\n=== Demo: Gesture ===")
            output.append(self.renderer._demo_gesture())

            return "\n".join(output)

    def _cmd_status(self, args: List[str]) -> str:
        """Show overall AR/VR system status"""
        output = ["AR/VR System Status:"]
        output.append("")

        # Workspaces
        workspaces = len(self.spatial_api.workspaces)
        output.append(f"Workspaces: {workspaces}")

        # Layouts
        layouts = len(self.layout_manager.layouts)
        output.append(f"Layouts: {layouts}")

        # Gestures
        gesture_stats = self.gesture_api.get_gesture_stats()
        output.append(f"Gestures tracked: {gesture_stats['total_gestures']}")

        # Multimodal
        multimodal_stats = self.multimodal_handler.get_statistics()
        output.append(f"Multimodal inputs: {multimodal_stats['total_inputs']}")

        # Platform
        platform = self.platform_adapter.get_current_platform()
        if platform:
            output.append(f"Active platform: {platform.get_capabilities().platform.value}")
        else:
            output.append("Active platform: None")

        output.append("")
        output.append("Use 'arvr help' for available commands")

        return "\n".join(output)

    def _show_help(self) -> str:
        """Show help message"""
        return """
AR/VR Preparation System

Usage: /arvr <subcommand> [args...]

Subcommands:
  workspace    Manage 3D spatial workspaces
    create <name>                   Create new workspace
    list                            List all workspaces
    show [name]                     Visualize workspace
    add-object <name> <x> <y> <z>  Add object to workspace
    save <name> <filepath>          Save workspace to file

  layout       Manage spatial layouts
    create <name> <type> <items>    Create layout (items: comma-separated)
    list                            List all layouts
    show <name>                     Visualize layout
    optimize <name>                 Optimize layout spacing
    recommend <count> <context>     Get layout recommendation

  gesture      Work with gestures
    simulate <type>                 Simulate gesture
    stats                           Show gesture statistics
    list                            List available gesture types

  multimodal   Multimodal input handling
    simulate <voice> <gesture>      Simulate combined input
    stats                           Show input statistics
    patterns                        List registered patterns

  platform     Platform management
    list                            List available platforms
    init <platform>                 Initialize platform
    status                          Show platform status
    report                          Generate platform report

  demo         Run demonstrations
    workspace                       Demo workspace visualization
    layout                          Demo layout systems
    gesture                         Demo gesture recognition
    interactive                     Run interactive demo
    all                             Show all demos

  status       Show overall system status
  help         Show this help message

Examples:
  /arvr workspace create my_workspace
  /arvr layout create my_layout circular Terminal,Editor,Browser
  /arvr gesture simulate swipe
  /arvr platform init terminal
  /arvr demo interactive
"""


def run_command(args: List[str]) -> str:
    """Entry point for the AR/VR command"""
    command = ARVRCommand()
    return command.execute(args)
