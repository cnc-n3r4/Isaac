"""
Test UI Integration
Test streaming display and progress indicators with agentic orchestrator
"""

import pytest
from unittest.mock import Mock, patch
from isaac.ui.streaming_display import StreamingDisplay, DisplayMode, DisplayEvent
from isaac.ui.progress_indicator import ProgressIndicator, ProgressStyle, MultiProgressTracker
from isaac.core.agentic_orchestrator import AgenticOrchestrator


class TestStreamingDisplay:
    """Test streaming display functionality"""

    def test_display_initialization(self):
        """Test display initializes correctly"""
        display = StreamingDisplay()
        assert display.current_mode == DisplayMode.IDLE
        assert len(display.active_tools) == 0
        assert len(display.status_messages) == 0

    def test_mode_updates(self):
        """Test mode changes and event emission"""
        display = StreamingDisplay()
        events_received = []

        def event_listener(event: DisplayEvent):
            events_received.append(event)

        display.add_event_listener(event_listener)

        # Test mode change (also emits status message)
        display.update_mode(DisplayMode.THINKING, "Processing...")
        assert display.current_mode == DisplayMode.THINKING
        assert len(events_received) == 2  # mode_change + status_message
        assert events_received[0].event_type == "mode_change"
        assert events_received[0].metadata["mode"] == "thinking"

    def test_status_messages(self):
        """Test status message handling"""
        display = StreamingDisplay()
        events_received = []

        display.add_event_listener(lambda e: events_received.append(e))

        # Add messages
        display.add_status_message("Starting task", "info")
        display.add_status_message("Task failed", "error")
        display.add_status_message("Task completed", "success")

        assert len(display.status_messages) == 3
        assert "Starting task" in display.status_messages[0]
        assert "❌" in display.status_messages[1]  # Error prefix
        assert "✅" in display.status_messages[2]  # Success prefix

        # Check events
        status_events = [e for e in events_received if e.event_type == "status_message"]
        assert len(status_events) == 3

    def test_tool_execution_tracking(self):
        """Test tool execution lifecycle"""
        display = StreamingDisplay()
        events_received = []

        display.add_event_listener(lambda e: events_received.append(e))

        # Start tool execution
        execution_id = display.start_tool_execution("test_tool", {"arg1": "value1"})
        assert execution_id in display.active_tools
        assert display.active_tools[execution_id]["tool_name"] == "test_tool"
        assert display.current_mode == DisplayMode.EXECUTING

        # Update progress
        display.update_tool_progress(execution_id, 0.5, "Halfway done")
        assert display.active_tools[execution_id]["progress"] == 0.5

        # Complete tool
        result = {"success": True, "output": "Tool completed"}
        display.complete_tool_execution(execution_id, result)
        
        # Tool should still be active immediately after completion
        assert execution_id in display.active_tools
        
        # Wait a bit for cleanup (in real usage, this happens asynchronously)
        import time
        time.sleep(6)  # Wait longer than the 5-second cleanup delay
        
        # Now it should be cleaned up
        assert execution_id not in display.active_tools

        # Check events
        tool_events = [e for e in events_received if "tool" in e.event_type]
        assert len(tool_events) >= 2  # start and complete


class TestProgressIndicator:
    """Test progress indicator functionality"""

    def test_progress_initialization(self):
        """Test progress indicator initializes correctly"""
        indicator = ProgressIndicator(ProgressStyle.BAR)
        assert indicator.current_progress == 0.0
        assert not indicator.is_active

    def test_bar_display(self):
        """Test progress bar display"""
        indicator = ProgressIndicator(ProgressStyle.BAR, width=10)

        # Test 0% - need to start first
        indicator.start("Starting")
        indicator.update(0.0, "Starting")
        display = indicator.get_display_text()
        assert "[░░░░░░░░░░]" in display
        assert "0.0%" in display

        # Test 50%
        indicator.update(0.5, "Halfway")
        display = indicator.get_display_text()
        assert "[█████░░░░░]" in display
        assert "50.0%" in display

        # Test 100%
        indicator.complete("Done")
        display = indicator.get_display_text()
        assert "[██████████]" in display
        assert "100.0%" in display

    def test_dots_display(self):
        """Test dots progress display"""
        indicator = ProgressIndicator(ProgressStyle.DOTS, width=5)

        indicator.start("Starting")
        indicator.update(0.0, "Starting")
        display = indicator.get_display_text()
        assert "○○○○○ 0/5" in display

        indicator.update(0.6, "Progressing")  # 3 out of 5
        display = indicator.get_display_text()
        assert "●●●○○ 3/5" in display

    def test_spinner_display(self):
        """Test spinner animation"""
        indicator = ProgressIndicator(ProgressStyle.SPINNER)

        indicator.start("Processing")
        display = indicator.get_display_text()
        assert any(char in display for char in ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])

    def test_multi_progress_tracker(self):
        """Test multi-progress tracking"""
        tracker = MultiProgressTracker()

        # Create indicators
        ind1 = tracker.create_indicator("task1")
        ind2 = tracker.create_indicator("task2")

        # Update progress
        ind1.update(0.5, "Task 1 halfway")
        ind2.update(0.8, "Task 2 almost done")

        # Check overall progress
        overall = tracker.get_overall_progress()
        assert overall == 0.65  # Average of 0.5 and 0.8

        # Check display text
        displays = tracker.get_all_display_text()
        assert len(displays) == 2
        assert any("task1" in display for display in displays)
        assert any("task2" in display for display in displays)


class TestAgenticOrchestratorIntegration:
    """Test agentic orchestrator with UI components"""

    @patch('isaac.core.agentic_orchestrator.AIRouter')
    @patch('isaac.core.agentic_orchestrator.ToolRegistry')
    @patch('isaac.core.agentic_orchestrator.StreamingExecutor')
    def test_orchestrator_with_ui(self, mock_executor, mock_registry, mock_ai_router):
        """Test orchestrator initialization with UI components"""
        # Mock session manager
        mock_session = Mock()
        mock_session.get_recent_commands.return_value = []
        mock_session.config = {"current_directory": ".", "project_root": None}

        # Create UI components
        display = StreamingDisplay()
        progress = ProgressIndicator()

        # Create orchestrator
        orchestrator = AgenticOrchestrator(
            session_mgr=mock_session,
            streaming_display=display,
            progress_indicator=progress
        )

        # Verify UI components are set
        assert orchestrator.streaming_display == display
        assert orchestrator.progress_indicator == progress

    @patch('isaac.core.agentic_orchestrator.AIRouter')
    @patch('isaac.core.agentic_orchestrator.ToolRegistry')
    @patch('isaac.core.agentic_orchestrator.StreamingExecutor')
    def test_sync_execution_wrapper(self, mock_executor, mock_registry, mock_ai_router):
        """Test synchronous execution wrapper"""
        # Mock session manager
        mock_session = Mock()
        mock_session.get_recent_commands.return_value = []
        mock_session.config = {"current_directory": ".", "project_root": None}

        # Mock async execution
        async def mock_execute(*args, **kwargs):
            yield {"type": "task_start", "user_input": "test"}
            yield {"type": "task_complete", "result": "success"}

        # Create orchestrator
        orchestrator = AgenticOrchestrator(session_mgr=mock_session)
        orchestrator.execute_agentic_task = mock_execute

        # Test sync wrapper
        result = orchestrator.execute_agentic_task_sync("test query")

        # Verify result structure
        assert hasattr(result, 'success')
        assert hasattr(result, 'output')
        assert hasattr(result, 'exit_code')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])