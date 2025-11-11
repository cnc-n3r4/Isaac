"""
Integration Test: Complete Agentic Workflow
Test the full pipeline from user input to agentic execution with UI feedback
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from isaac.core.command_router import CommandRouter
from isaac.core.agentic_orchestrator import AgenticOrchestrator
from isaac.ui.streaming_display import StreamingDisplay, DisplayMode
from isaac.ui.progress_indicator import ProgressIndicator
from isaac.adapters.base_adapter import CommandResult


class TestCompleteAgenticWorkflow:
    """Test complete agentic workflow integration"""

    @patch('isaac.core.agentic_orchestrator.AIRouter')
    @patch('isaac.core.agentic_orchestrator.ToolRegistry')
    @patch('isaac.core.agentic_orchestrator.StreamingExecutor')
    def test_agentic_mode_routing(self, mock_executor, mock_registry, mock_ai_router):
        """Test that agentic mode is properly routed through command router"""
        # Mock session manager
        mock_session = Mock()
        mock_session.get_recent_commands.return_value = []
        mock_session.config = {"current_directory": ".", "project_root": None}

        # Mock shell adapter
        mock_shell = Mock()
        mock_shell.name = "PowerShell"

        # Create command router
        router = CommandRouter(mock_session, mock_shell)

        # Mock the orchestrator's sync method
        with patch.object(AgenticOrchestrator, 'execute_agentic_task_sync') as mock_sync:
            mock_sync.return_value = CommandResult(
                success=True,
                output="Agentic task completed successfully",
                exit_code=0
            )

            # Test agentic mode routing
            result = router.route_command("isaac agent: analyze this codebase")

            # Verify routing worked
            assert result.success == True
            assert "Agentic task completed successfully" in result.output
            mock_sync.assert_called_once_with("analyze this codebase")

    @patch('isaac.core.agentic_orchestrator.AIRouter')
    @patch('isaac.core.agentic_orchestrator.ToolRegistry')
    @patch('isaac.core.agentic_orchestrator.StreamingExecutor')
    def test_ui_integration_during_execution(self, mock_executor, mock_registry, mock_ai_router):
        """Test that UI components are properly updated during agentic execution"""
        # Mock session manager
        mock_session = Mock()
        mock_session.get_recent_commands.return_value = []
        mock_session.config = {"current_directory": ".", "project_root": None}

        # Create UI components
        display = StreamingDisplay()
        progress = ProgressIndicator()

        # Track UI events
        display_events = []
        display.add_event_listener(lambda e: display_events.append(e))

        # Create orchestrator with UI
        orchestrator = AgenticOrchestrator(
            session_mgr=mock_session,
            streaming_display=display,
            progress_indicator=progress
        )

        # Mock async execution with realistic events
        async def mock_execute(*args, **kwargs):
            yield {"type": "task_start", "user_input": "test query"}
            yield {"type": "ai_selected", "ai_provider": "claude"}
            yield {"type": "tool_start", "tool_name": "read_file", "tool_args": {"file_path": "test.py"}}
            yield {"type": "tool_result", "tool_name": "read_file", "success": True, "output": "file content"}
            yield {"type": "task_complete", "result": "success"}

        orchestrator.execute_agentic_task = mock_execute

        # Execute sync wrapper
        result = orchestrator.execute_agentic_task_sync("test query")

        # Verify result
        assert result.success == True
        assert "Tool output: file content" in result.output

        # Verify UI was updated
        assert display.current_mode == DisplayMode.IDLE  # Should be reset after completion
        assert progress.current_progress == 1.0  # Should be completed

        # Check that UI events were emitted
        event_types = [e.event_type for e in display_events]
        assert "mode_change" in event_types
        assert "status_message" in event_types

    def test_agentic_mode_detection(self):
        """Test that agentic mode commands are properly detected"""
        # Mock session and shell
        mock_session = Mock()
        mock_shell = Mock()
        mock_shell.name = "PowerShell"

        router = CommandRouter(mock_session, mock_shell)

        # Test various agentic mode prefixes
        assert router.route_command("isaac agent: do something").success == False  # Should fail due to mocking
        assert router.route_command("isaac agentic: analyze code").success == False

        # Test that regular commands still work
        with patch.object(router, '_handle_meta_command') as mock_meta:
            mock_meta.return_value = CommandResult(success=True, output="meta result", exit_code=0)
            result = router.route_command("/help")
            mock_meta.assert_called_once_with("/help")

    @patch('isaac.core.agentic_orchestrator.AIRouter')
    @patch('isaac.core.agentic_orchestrator.ToolRegistry')
    @patch('isaac.core.agentic_orchestrator.StreamingExecutor')
    def test_error_handling_in_agentic_mode(self, mock_executor, mock_registry, mock_ai_router):
        """Test error handling in agentic execution"""
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

        # Mock async execution that raises an error
        async def mock_execute_error(*args, **kwargs):
            yield {"type": "task_start", "user_input": "test query"}
            raise Exception("Test error in agentic execution")

        orchestrator.execute_agentic_task = mock_execute_error

        # Execute and verify error handling
        result = orchestrator.execute_agentic_task_sync("test query")

        # Should return error result
        assert result.success == False
        assert "Agentic task failed" in result.output
        assert "Test error in agentic execution" in result.output

        # UI should reflect error state
        assert display.current_mode == DisplayMode.ERROR
        assert not progress.is_active

    def test_ui_component_lifecycle(self):
        """Test that UI components properly manage their lifecycle"""
        display = StreamingDisplay()
        progress = ProgressIndicator()

        # Initial state
        assert display.current_mode == DisplayMode.IDLE
        assert not progress.is_active

        # Start operations
        display.update_mode(DisplayMode.THINKING, "Starting")
        progress.start("Working")

        assert display.current_mode == DisplayMode.THINKING
        assert progress.is_active
        assert progress.current_progress == 0.0

        # Update progress
        progress.update(0.5, "Halfway")
        assert progress.current_progress == 0.5

        # Complete operations
        display.update_mode(DisplayMode.IDLE, "Done")
        progress.complete("Finished")

        assert display.current_mode == DisplayMode.IDLE
        assert not progress.is_active
        assert progress.current_progress == 1.0

        # Reset
        display.reset()
        assert display.current_mode == DisplayMode.IDLE
        assert len(display.status_messages) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])