"""
Integration tests for AR/VR Preparation System

Tests all components working together.
"""

import unittest
import time
import os
import tempfile

from isaac.arvr.spatial_api import SpatialAPI, Vector3D, SpatialObject, SpatialWorkspace
from isaac.arvr.gesture_api import GestureAPI, GestureType, Gesture, HandType
from isaac.arvr.spatial_layouts import LayoutManager, LayoutType, Layout
from isaac.arvr.multimodal_input import MultimodalInputHandler, InputModality
from isaac.arvr.prototype_mode import PrototypeRenderer
from isaac.arvr.platform_adapter import PlatformAdapter, Platform
from isaac.commands.arvr.arvr_command import ARVRCommand


class TestSpatialAPI(unittest.TestCase):
    """Test spatial API functionality"""

    def setUp(self):
        self.api = SpatialAPI()

    def test_workspace_creation(self):
        """Test workspace creation"""
        workspace = self.api.create_workspace("test_workspace")
        self.assertIsNotNone(workspace)
        self.assertEqual(workspace.name, "test_workspace")
        self.assertEqual(self.api.active_workspace, "test_workspace")

    def test_object_creation(self):
        """Test spatial object creation"""
        self.api.create_workspace("test")
        obj = self.api.create_object("TestObject", Vector3D(1, 2, 3))
        self.assertIsNotNone(obj)
        self.assertEqual(obj.name, "TestObject")
        self.assertEqual(obj.transform.position.x, 1.0)

    def test_spatial_relationships(self):
        """Test spatial relationship calculations"""
        workspace = self.api.create_workspace("test")
        obj1 = self.api.create_object("Object1", Vector3D(0, 0, 0))
        obj2 = self.api.create_object("Object2", Vector3D(3, 4, 0))

        relationships = self.api.calculate_spatial_relationships(obj1.id, obj2.id)
        self.assertIsNotNone(relationships)
        self.assertEqual(relationships['distance'], 5.0)  # 3-4-5 triangle

    def test_workspace_persistence(self):
        """Test workspace save/load"""
        workspace = self.api.create_workspace("test")
        self.api.create_object("Object1", Vector3D(1, 2, 3))

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name

        try:
            workspace.save(filepath)
            loaded = SpatialWorkspace.load(filepath)
            self.assertEqual(loaded.name, "test")
            self.assertEqual(len(loaded.objects), 1)
        finally:
            os.unlink(filepath)


class TestGestureAPI(unittest.TestCase):
    """Test gesture recognition"""

    def setUp(self):
        self.api = GestureAPI()

    def test_gesture_simulation(self):
        """Test gesture simulation"""
        trajectory = [
            Vector3D(-1, 0, -1),
            Vector3D(0, 0, -1),
            Vector3D(1, 0, -1)
        ]

        gesture = self.api.simulate_gesture(
            GestureType.SWIPE,
            HandType.RIGHT,
            trajectory,
            duration=0.1
        )

        self.assertIsNotNone(gesture)
        self.assertEqual(gesture.type, GestureType.SWIPE)
        self.assertTrue(gesture.is_complete())

    def test_gesture_stats(self):
        """Test gesture statistics"""
        stats = self.api.get_gesture_stats()
        self.assertIn('total_gestures', stats)
        self.assertIn('average_confidence', stats)

    def test_custom_gesture(self):
        """Test custom gesture creation"""
        name = self.api.create_custom_gesture(
            "my_gesture",
            min_points=5,
            max_duration=2.0
        )
        self.assertEqual(name, "my_gesture")
        self.assertIn("my_gesture", self.api.recognizer.patterns)


class TestLayoutManager(unittest.TestCase):
    """Test spatial layout management"""

    def setUp(self):
        self.manager = LayoutManager()

    def test_circular_layout(self):
        """Test circular layout generation"""
        items = ["Item1", "Item2", "Item3", "Item4"]
        layout = self.manager.create_layout(
            "test_circular",
            LayoutType.CIRCULAR,
            items
        )

        self.assertEqual(len(layout.nodes), 4)
        self.assertEqual(layout.type, LayoutType.CIRCULAR)

    def test_grid_layout(self):
        """Test grid layout generation"""
        items = ["A", "B", "C", "D", "E", "F"]
        layout = self.manager.create_layout(
            "test_grid",
            LayoutType.GRID,
            items
        )

        self.assertEqual(len(layout.nodes), 6)
        self.assertEqual(layout.type, LayoutType.GRID)

    def test_layout_optimization(self):
        """Test layout optimization"""
        items = ["Item1", "Item2"]
        layout = self.manager.create_layout(
            "test_opt",
            LayoutType.CIRCULAR,
            items
        )

        # Force overlap
        layout.nodes[0].position = Vector3D(0, 0, 0)
        layout.nodes[1].position = Vector3D(0, 0, 0)

        optimized = self.manager.optimize_layout(layout)
        distance = layout.nodes[0].position.distance_to(layout.nodes[1].position)
        self.assertGreater(distance, 0.0)

    def test_layout_recommendation(self):
        """Test layout recommendation"""
        recommended = self.manager.get_recommended_layout(5, "general")
        self.assertIsInstance(recommended, LayoutType)

    def test_layout_persistence(self):
        """Test layout save/load"""
        items = ["A", "B", "C"]
        layout = self.manager.create_layout(
            "test_save",
            LayoutType.HEMISPHERE,
            items
        )

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name

        try:
            layout.save(filepath)
            loaded = Layout.load(filepath)
            self.assertEqual(loaded.name, "test_save")
            self.assertEqual(len(loaded.nodes), 3)
        finally:
            os.unlink(filepath)


class TestMultimodalInput(unittest.TestCase):
    """Test multimodal input handling"""

    def setUp(self):
        self.handler = MultimodalInputHandler()

    def test_voice_input(self):
        """Test voice input processing"""
        inp = self.handler.process_voice_input("move this", confidence=0.95)
        self.assertEqual(inp.modality, InputModality.VOICE)
        self.assertIsNotNone(inp.voice_command)
        self.assertEqual(inp.voice_command.text, "move this")

    def test_gesture_input(self):
        """Test gesture input processing"""
        gesture = Gesture(
            type=GestureType.GRAB,
            hand=HandType.RIGHT,
            start_time=time.time(),
            end_time=time.time()
        )

        inp = self.handler.process_gesture_input(gesture)
        self.assertEqual(inp.modality, InputModality.GESTURE)
        self.assertIsNotNone(inp.gesture)

    def test_combined_input(self):
        """Test combined voice+gesture input"""
        gesture = Gesture(
            type=GestureType.POINT,
            hand=HandType.RIGHT,
            start_time=time.time(),
            end_time=time.time()
        )

        inp = self.handler.process_combined_input(
            voice_text="delete this",
            gesture=gesture,
            gaze_target="object_1"
        )

        self.assertEqual(inp.modality, InputModality.COMBINED)
        self.assertTrue(inp.is_combined())
        self.assertIsNotNone(inp.voice_command)
        self.assertIsNotNone(inp.gesture)

    def test_pattern_matching(self):
        """Test multimodal pattern matching"""
        patterns_before = len(self.handler.patterns)
        self.assertGreater(patterns_before, 0)

    def test_multimodal_stats(self):
        """Test statistics collection"""
        # Generate some inputs
        self.handler.process_voice_input("test")
        stats = self.handler.get_statistics()
        self.assertGreater(stats['total_inputs'], 0)


class TestPrototypeRenderer(unittest.TestCase):
    """Test prototype rendering"""

    def setUp(self):
        self.renderer = PrototypeRenderer(width=60, height=20)

    def test_workspace_rendering(self):
        """Test workspace rendering"""
        workspace = self.renderer.create_demo_scene()
        output = self.renderer.render_workspace(workspace)

        self.assertIsInstance(output, str)
        self.assertIn("Workspace:", output)
        self.assertGreater(len(output), 100)

    def test_layout_rendering(self):
        """Test layout rendering"""
        from isaac.arvr.spatial_layouts import Layout, LayoutType, LayoutNode

        layout = Layout(
            name="test",
            type=LayoutType.CIRCULAR,
            center=Vector3D(0, 0, -2)
        )

        for i in range(3):
            node = LayoutNode(
                id=f"node_{i}",
                name=f"Item{i}",
                position=Vector3D(i, 0, -2)
            )
            layout.add_node(node)

        output = self.renderer.render_layout(layout)
        self.assertIsInstance(output, str)
        self.assertIn("Layout:", output)

    def test_gesture_rendering(self):
        """Test gesture rendering"""
        from isaac.arvr.gesture_api import GesturePoint

        gesture = Gesture(
            type=GestureType.SWIPE,
            hand=HandType.RIGHT,
            start_time=time.time() - 1,
            end_time=time.time()
        )

        for i in range(5):
            point = GesturePoint(
                position=Vector3D(i * 0.5, 0, -1),
                timestamp=time.time()
            )
            gesture.points.append(point)

        output = self.renderer.render_gesture(gesture)
        self.assertIsInstance(output, str)
        self.assertIn("Gesture:", output)


class TestPlatformAdapter(unittest.TestCase):
    """Test platform adapter"""

    def setUp(self):
        self.adapter = PlatformAdapter()

    def test_platform_list(self):
        """Test available platforms list"""
        platforms = self.adapter.get_available_platforms()
        self.assertGreater(len(platforms), 0)
        self.assertIn(Platform.TERMINAL, platforms)

    def test_platform_initialization(self):
        """Test platform initialization"""
        success = self.adapter.initialize_platform(Platform.TERMINAL)
        self.assertTrue(success)
        self.assertIsNotNone(self.adapter.get_current_platform())

    def test_platform_capabilities(self):
        """Test platform capabilities"""
        self.adapter.initialize_platform(Platform.TERMINAL)
        caps = self.adapter.get_capabilities()
        self.assertIsNotNone(caps)
        self.assertEqual(caps.platform, Platform.TERMINAL)

    def test_device_state(self):
        """Test device state retrieval"""
        self.adapter.initialize_platform(Platform.TERMINAL)
        state = self.adapter.get_device_state()
        self.assertIsNotNone(state)
        self.assertTrue(state.is_connected)

    def test_platform_report(self):
        """Test platform report generation"""
        self.adapter.initialize_platform(Platform.TERMINAL)
        report = self.adapter.create_platform_report()
        self.assertIn('current_platform', report)
        self.assertIn('capabilities', report)

    def tearDown(self):
        """Cleanup"""
        if self.adapter.get_current_platform():
            self.adapter.shutdown_platform()


class TestARVRCommand(unittest.TestCase):
    """Test command interface"""

    def setUp(self):
        self.command = ARVRCommand()

    def test_help_command(self):
        """Test help command"""
        output = self.command.execute(['help'])
        self.assertIn('AR/VR', output)
        self.assertIn('workspace', output)

    def test_workspace_commands(self):
        """Test workspace commands"""
        # Create workspace
        output = self.command.execute(['workspace', 'create', 'test'])
        self.assertIn('Created', output)

        # List workspaces
        output = self.command.execute(['workspace', 'list'])
        self.assertIn('test', output)

    def test_layout_commands(self):
        """Test layout commands"""
        # Create layout
        output = self.command.execute(['layout', 'create', 'test', 'circular', 'A,B,C'])
        self.assertIn('Created', output)

        # List layouts
        output = self.command.execute(['layout', 'list'])
        self.assertIn('test', output)

    def test_gesture_commands(self):
        """Test gesture commands"""
        # List gestures
        output = self.command.execute(['gesture', 'list'])
        self.assertIn('gesture types', output.lower())

        # Stats
        output = self.command.execute(['gesture', 'stats'])
        self.assertIn('Statistics', output)

    def test_platform_commands(self):
        """Test platform commands"""
        # List platforms
        output = self.command.execute(['platform', 'list'])
        self.assertIn('terminal', output.lower())

        # Initialize
        output = self.command.execute(['platform', 'init', 'terminal'])
        self.assertIn('Initialized', output)

        # Status
        output = self.command.execute(['platform', 'status'])
        self.assertIn('Platform', output)

    def test_status_command(self):
        """Test overall status command"""
        output = self.command.execute(['status'])
        self.assertIn('Status', output)
        self.assertIn('Workspaces', output)


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests"""

    def test_complete_workflow(self):
        """Test complete AR/VR workflow"""
        # 1. Create spatial API and workspace
        spatial_api = SpatialAPI()
        workspace = spatial_api.create_workspace("demo")
        self.assertIsNotNone(workspace)

        # 2. Add objects
        obj1 = spatial_api.create_object("Terminal", Vector3D(0, 0, -1))
        obj2 = spatial_api.create_object("Editor", Vector3D(1, 0, -1))
        self.assertEqual(len(workspace.objects), 2)

        # 3. Create layout
        layout_mgr = LayoutManager()
        layout = layout_mgr.create_layout(
            "demo_layout",
            LayoutType.CIRCULAR,
            ["Terminal", "Editor", "Browser"]
        )
        self.assertEqual(len(layout.nodes), 3)

        # 4. Initialize platform
        platform_adapter = PlatformAdapter()
        success = platform_adapter.initialize_platform(Platform.TERMINAL)
        self.assertTrue(success)

        # 5. Simulate gesture
        gesture_api = GestureAPI()
        trajectory = [Vector3D(-1, 0, -1), Vector3D(1, 0, -1)]
        gesture = gesture_api.simulate_gesture(
            GestureType.SWIPE,
            HandType.RIGHT,
            trajectory,
            duration=0.1
        )
        self.assertIsNotNone(gesture)

        # 6. Process multimodal input
        multimodal = MultimodalInputHandler()
        inp = multimodal.process_combined_input(
            voice_text="select window",
            gesture=gesture
        )
        self.assertTrue(inp.is_combined())

        # 7. Render scene
        renderer = PrototypeRenderer()
        output = renderer.render_workspace(workspace)
        self.assertIsInstance(output, str)

        # Cleanup
        platform_adapter.shutdown_platform()


if __name__ == '__main__':
    unittest.main()
