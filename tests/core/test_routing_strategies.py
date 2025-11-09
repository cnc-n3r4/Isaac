"""
Tests for command routing strategies.
"""

import pytest
from unittest.mock import Mock, MagicMock

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.cd_strategy import CdStrategy
from isaac.core.routing.exit_blocker_strategy import ExitBlockerStrategy
from isaac.core.routing.exit_quit_strategy import ExitQuitStrategy
from isaac.core.routing.force_execution_strategy import ForceExecutionStrategy
from isaac.core.routing.pipe_strategy import PipeStrategy
from isaac.core.routing.task_mode_strategy import TaskModeStrategy


class TestPipeStrategy:
    """Tests for PipeStrategy."""

    @pytest.fixture
    def strategy(self):
        session = Mock()
        shell = Mock()
        return PipeStrategy(session, shell)

    def test_can_handle_pipe_command(self, strategy):
        assert strategy.can_handle("ls | grep pattern")
        assert strategy.can_handle("cat file.txt | wc -l")

    def test_cannot_handle_quoted_pipe(self, strategy):
        assert not strategy.can_handle('echo "test | data"')
        assert not strategy.can_handle("echo 'test | data'")

    def test_cannot_handle_no_pipe(self, strategy):
        assert not strategy.can_handle("ls -la")
        assert not strategy.can_handle("echo hello")

    def test_priority(self, strategy):
        assert strategy.get_priority() == 10


class TestCdStrategy:
    """Tests for CdStrategy."""

    @pytest.fixture
    def strategy(self):
        session = Mock()
        shell = Mock()
        return CdStrategy(session, shell)

    def test_can_handle_cd_command(self, strategy):
        assert strategy.can_handle("cd /home")
        assert strategy.can_handle("cd ..")
        assert strategy.can_handle("cd")

    def test_cannot_handle_other_commands(self, strategy):
        assert not strategy.can_handle("ls")
        assert not strategy.can_handle("pwd")

    def test_execute_cd_to_home(self, strategy):
        result = strategy.execute("cd", {})
        assert result.success
        # Should change to home directory

    def test_priority(self, strategy):
        assert strategy.get_priority() == 15


class TestForceExecutionStrategy:
    """Tests for ForceExecutionStrategy."""

    @pytest.fixture
    def strategy(self):
        session = Mock()
        shell = Mock()
        shell.execute = Mock(return_value=CommandResult(success=True, output="done", exit_code=0))
        return ForceExecutionStrategy(session, shell)

    def test_can_handle_force_prefix(self, strategy):
        assert strategy.can_handle("/f ls")
        assert strategy.can_handle("/force ls")

    def test_cannot_handle_other_commands(self, strategy):
        assert not strategy.can_handle("ls")
        assert not strategy.can_handle("/help")

    def test_execute_strips_force_prefix(self, strategy):
        result = strategy.execute("/f ls -la", {})
        strategy.shell.execute.assert_called_once_with("ls -la")

    def test_priority(self, strategy):
        assert strategy.get_priority() == 20


class TestExitQuitStrategy:
    """Tests for ExitQuitStrategy."""

    @pytest.fixture
    def strategy(self):
        session = Mock()
        shell = Mock()
        return ExitQuitStrategy(session, shell)

    def test_can_handle_exit_quit_clear(self, strategy):
        assert strategy.can_handle("/exit")
        assert strategy.can_handle("/quit")
        assert strategy.can_handle("/clear")

    def test_cannot_handle_other_commands(self, strategy):
        assert not strategy.can_handle("exit")
        assert not strategy.can_handle("/help")

    def test_execute_returns_success(self, strategy):
        result = strategy.execute("/exit", {})
        assert result.success

    def test_priority(self, strategy):
        assert strategy.get_priority() == 25


class TestExitBlockerStrategy:
    """Tests for ExitBlockerStrategy."""

    @pytest.fixture
    def strategy(self):
        session = Mock()
        shell = Mock()
        return ExitBlockerStrategy(session, shell)

    def test_can_handle_exit_quit_without_slash(self, strategy):
        assert strategy.can_handle("exit")
        assert strategy.can_handle("quit")

    def test_cannot_handle_other_commands(self, strategy):
        assert not strategy.can_handle("/exit")
        assert not strategy.can_handle("ls")

    def test_execute_returns_error(self, strategy):
        result = strategy.execute("exit", {})
        assert not result.success
        assert "Use /exit or /quit" in result.output

    def test_priority(self, strategy):
        assert strategy.get_priority() == 40


class TestTaskModeStrategy:
    """Tests for TaskModeStrategy."""

    @pytest.fixture
    def strategy(self):
        session = Mock()
        shell = Mock()
        return TaskModeStrategy(session, shell)

    def test_can_handle_task_mode(self, strategy):
        assert strategy.can_handle("isaac task: do something")
        assert strategy.can_handle("Isaac Task: another task")

    def test_cannot_handle_other_commands(self, strategy):
        assert not strategy.can_handle("isaac hello")
        assert not strategy.can_handle("ls")

    def test_priority(self, strategy):
        assert strategy.get_priority() == 45


class TestCommandRouterIntegration:
    """Integration tests for the refactored CommandRouter."""

    @pytest.fixture
    def router(self):
        from isaac.core.command_router import CommandRouter

        session = Mock()
        session.preferences = Mock()
        shell = Mock()
        shell.name = "bash"
        shell.execute = Mock(return_value=CommandResult(success=True, output="test", exit_code=0))

        # Mock the dispatcher and its methods
        router = CommandRouter(session, shell)
        return router

    def test_router_has_strategies(self, router):
        """Test that router initializes with strategies."""
        assert len(router.strategies) > 0

    def test_strategies_sorted_by_priority(self, router):
        """Test that strategies are sorted by priority."""
        priorities = [s.get_priority() for s in router.strategies]
        assert priorities == sorted(priorities)

    def test_route_force_command(self, router):
        """Test routing a force command."""
        result = router.route_command("/f ls")
        assert result.success

    def test_route_exit_blocker(self, router):
        """Test that exit without / is blocked."""
        result = router.route_command("exit")
        assert not result.success
        assert "Use /exit or /quit" in result.output

    def test_get_help(self, router):
        """Test getting help from router."""
        help_text = router.get_help()
        assert "Isaac Command Router" in help_text
        assert len(help_text) > 0
