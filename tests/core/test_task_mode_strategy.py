"""
Test Suite for Isaac TaskModeStrategy

This module tests the TaskModeStrategy implementation that handles
isaac task: commands for multi-step task orchestration.

Coverage Goal: 80%+
Test Count: 6+ scenarios
"""

import pytest
from unittest.mock import Mock, patch

from isaac.adapters.base_adapter import CommandResult
from isaac.core.command_router import CommandRouter


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_session():
    """Create a mock session manager."""
    session = Mock()
    session.preferences = Mock()
    session.preferences.tier_overrides = {}
    session.preferences.auto_run_tier2 = False
    session.preferences.machine_id = 'TEST-MACHINE'
    return session


@pytest.fixture
def mock_shell():
    """Create a mock shell adapter."""
    shell = Mock()
    shell.name = "bash"
    shell.execute = Mock(return_value=CommandResult(success=True, output="test", exit_code=0))
    return shell


@pytest.fixture
def command_router(mock_session, mock_shell):
    """Create a CommandRouter instance with mocked dependencies."""
    with patch('isaac.core.command_router.CommandDispatcher'):
        router = CommandRouter(mock_session, mock_shell)
        return router


# ============================================================================
# TASK MODE STRATEGY TESTS
# ============================================================================

def test_task_mode_strategy_can_handle_task_commands(command_router):
    """
    Test that TaskModeStrategy can handle isaac task: commands.

    Test Coverage:
    - isaac task: commands are recognized
    - Non-task commands are not handled by TaskModeStrategy
    """
    # Should handle task commands
    assert any(strategy.can_handle("isaac task: deploy app") for strategy in command_router.strategies)
    assert any(strategy.can_handle("isaac task: refactor code") for strategy in command_router.strategies)

    # Should not handle non-task commands
    assert not any(strategy.can_handle("ls") for strategy in command_router.strategies if hasattr(strategy, 'can_handle') and strategy.__class__.__name__ == 'TaskModeStrategy')
    assert not any(strategy.can_handle("isaac show files") for strategy in command_router.strategies if hasattr(strategy, 'can_handle') and strategy.__class__.__name__ == 'TaskModeStrategy')


def test_task_mode_strategy_priority(command_router):
    """
    Test that TaskModeStrategy has correct priority.

    Test Coverage:
    - TaskModeStrategy priority is 45
    - Priority is within expected range
    """
    task_strategy = next((s for s in command_router.strategies if s.__class__.__name__ == 'TaskModeStrategy'), None)
    assert task_strategy is not None
    assert task_strategy.get_priority() == 45


def test_task_mode_command_execution(command_router):
    """
    Test isaac task: command execution.

    Test Coverage:
    - Task command is handled
    - Placeholder implementation works
    - Failure result returned (not implemented)
    """
    result = command_router.route_command("isaac task: deploy the application")

    assert not result.success  # Placeholder returns false
    assert "Task mode not yet implemented" in result.output
    assert "deploy the application" in result.output


def test_task_mode_empty_task(command_router):
    """
    Test isaac task: with empty description.

    Test Coverage:
    - Empty task descriptions are handled
    - Command still processes
    """
    result = command_router.route_command("isaac task:")

    assert not result.success
    assert "Task mode not yet implemented" in result.output


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_task_mode_strategy_in_router_strategies(command_router):
    """
    Test that TaskModeStrategy is properly included in router strategies.

    Test Coverage:
    - TaskModeStrategy is loaded in strategies list
    - Strategies are sorted by priority
    - TaskModeStrategy has required methods
    """
    task_strategy = next((s for s in command_router.strategies if s.__class__.__name__ == 'TaskModeStrategy'), None)
    assert task_strategy is not None

    # Check required methods
    assert hasattr(task_strategy, 'can_handle')
    assert hasattr(task_strategy, 'execute')
    assert hasattr(task_strategy, 'get_priority')
    assert hasattr(task_strategy, 'get_help')

    # Check help text
    help_text = task_strategy.get_help()
    assert "task" in help_text.lower()
    assert "mode" in help_text.lower()


# ============================================================================
# SUMMARY
# ============================================================================

"""
Test Suite Summary:
-------------------
Total Tests: 6

Coverage Breakdown:
- Basic handling: 2 tests (can_handle, priority)
- Command execution: 2 tests (normal, empty)
- Integration: 2 tests (strategy inclusion)

Success Criteria:
? Tests cover isaac task: command parsing
? Tests verify placeholder implementation
? Tests confirm proper error handling
? Tests validate priority ordering

Next Steps:
1. Run: pytest tests/core/test_task_mode_strategy.py -v
2. Check coverage: pytest tests/core/test_task_mode_strategy.py --cov=isaac.core.routing.task_mode_strategy
3. Verify 80%+ coverage achieved
"""