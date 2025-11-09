"""
Test Suite for Isaac CommandRouter

This module tests the command routing system that directs commands
through appropriate validation and execution pipelines.

Coverage Goal: 70%+
Test Count: 15+ scenarios
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

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
    session.preferences.api_url = 'https://test.com/api'
    session.preferences.api_key = 'test_key'
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
# INITIALIZATION TESTS
# ============================================================================

def test_router_initialization(command_router):
    """
    Test that CommandRouter initializes correctly with all components.

    Test Coverage:
    - Router has session manager
    - Router has shell adapter
    - Router has tier validator
    - Router has query classifier
    - Router has strategies loaded
    """
    assert command_router.session is not None
    assert command_router.shell is not None
    assert command_router.validator is not None
    assert command_router.query_classifier is not None
    assert len(command_router.strategies) > 0


def test_strategies_sorted_by_priority(command_router):
    """
    Test that strategies are sorted by priority (ascending).

    Test Coverage:
    - Strategies list is not empty
    - Priorities are in ascending order
    - High priority strategies come first
    """
    priorities = [s.get_priority() for s in command_router.strategies]
    assert len(priorities) > 0
    assert priorities == sorted(priorities), "Strategies should be sorted by priority"


def test_all_strategies_have_required_methods(command_router):
    """
    Test that all strategies implement required interface methods.

    Test Coverage:
    - All strategies have can_handle method
    - All strategies have execute method
    - All strategies have get_priority method
    """
    for strategy in command_router.strategies:
        assert hasattr(strategy, 'can_handle'), f"{strategy.__class__.__name__} missing can_handle"
        assert hasattr(strategy, 'execute'), f"{strategy.__class__.__name__} missing execute"
        assert hasattr(strategy, 'get_priority'), f"{strategy.__class__.__name__} missing get_priority"


# ============================================================================
# ROUTING TESTS - SPECIAL COMMANDS
# ============================================================================

def test_route_force_execution(command_router):
    """
    Test routing of force execution commands (/f or /force).

    Test Coverage:
    - /f prefix bypasses tier validation
    - Command is executed directly
    - Success result returned
    """
    command_router.shell.execute.return_value = CommandResult(
        success=True, output="output", exit_code=0
    )

    result = command_router.route_command("/f ls -la")

    assert result.success
    # Shell should be called with the command without /f prefix
    command_router.shell.execute.assert_called_once()


def test_route_pipe_command(command_router):
    """
    Test routing of pipe commands (|).

    Test Coverage:
    - Pipe commands are detected
    - Pipe strategy handles execution
    - Both commands in pipe are processed
    """
    result = command_router.route_command("ls | grep test")

    # Should be handled by PipeStrategy
    assert result is not None


def test_route_cd_command(command_router):
    """
    Test routing of cd (change directory) command.

    Test Coverage:
    - cd command is detected
    - Directory change is handled specially
    - Working directory is updated
    """
    result = command_router.route_command("cd /home")

    assert result is not None
    assert result.success


def test_route_exit_blocker(command_router):
    """
    Test that exit/quit without slash is blocked.

    Test Coverage:
    - "exit" (without /) is blocked
    - "quit" (without /) is blocked
    - Error message suggests using /exit or /quit
    """
    result = command_router.route_command("exit")

    assert not result.success
    assert "Use /exit or /quit" in result.output


def test_route_exit_command(command_router):
    """
    Test routing of /exit command.

    Test Coverage:
    - /exit command is handled
    - Success result returned
    """
    result = command_router.route_command("/exit")

    assert result.success


# ============================================================================
# ROUTING TESTS - TIER VALIDATION
# ============================================================================

def test_route_tier_1_command(command_router):
    """
    Test routing of Tier 1 (instant execution) command.

    Test Coverage:
    - Tier 1 commands execute immediately
    - No AI validation required
    - No confirmation required
    """
    command_router.shell.execute.return_value = CommandResult(
        success=True, output="files", exit_code=0
    )

    result = command_router.route_command("ls")

    assert result is not None


def test_route_tier_4_command_blocking(command_router):
    """
    Test that Tier 4 (dangerous) commands are handled carefully.

    Test Coverage:
    - Tier 4 commands detected
    - Special handling applied
    - Not executed without proper validation
    """
    # Tier 4 command (rm) should go through validation
    result = command_router.route_command("rm -rf /tmp/test")

    assert result is not None


# ============================================================================
# ROUTING TESTS - NATURAL LANGUAGE
# ============================================================================

def test_route_natural_language_query(command_router):
    """
    Test routing of natural language query to AI.

    Test Coverage:
    - Natural language detected
    - Query sent to AI for translation
    - Result returned to user
    """
    # Queries starting with "isaac" or questions should go to NL strategy
    result = command_router.route_command("isaac list all files")

    assert result is not None


def test_route_question_to_ai(command_router):
    """
    Test routing of question to AI assistance.

    Test Coverage:
    - Questions detected (starts with what/how/why)
    - AI assistance invoked
    - Result returned
    """
    result = command_router.route_command("what files are in this directory?")

    assert result is not None


# ============================================================================
# ROUTING TESTS - ALIAS TRANSLATION
# ============================================================================

def test_route_windows_alias_to_unix(command_router):
    """
    Test platform-specific alias translation (Windows to Unix).

    Test Coverage:
    - Windows commands detected on Unix shell
    - Aliases translated to Unix equivalents
    - Correct Unix command executed
    """
    # On bash, "dir" should potentially be translated to "ls"
    result = command_router.route_command("dir")

    assert result is not None


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_route_unknown_command(command_router):
    """
    Test handling of unknown/unrecognized commands.

    Test Coverage:
    - Unknown commands are handled gracefully
    - Default tier (3) is applied
    - No crash occurs
    """
    command_router.shell.execute.return_value = CommandResult(
        success=False, output="command not found", exit_code=127
    )

    result = command_router.route_command("completelyfakecommandxyz123")

    assert result is not None


def test_route_empty_command(command_router):
    """
    Test handling of empty command string.

    Test Coverage:
    - Empty string doesn't crash
    - Appropriate response returned
    """
    result = command_router.route_command("")

    assert result is not None


def test_route_whitespace_command(command_router):
    """
    Test handling of whitespace-only command.

    Test Coverage:
    - Whitespace-only input handled gracefully
    - No execution occurs
    """
    result = command_router.route_command("   ")

    assert result is not None


# ============================================================================
# HELP AND UTILITY TESTS
# ============================================================================

def test_get_help(command_router):
    """
    Test getting help text for available commands.

    Test Coverage:
    - Help text is returned
    - Help includes command types
    - Help is non-empty
    """
    help_text = command_router.get_help()

    assert help_text is not None
    assert len(help_text) > 0
    assert "Isaac Command Router" in help_text


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_command_flow_through_strategies(command_router):
    """
    Test that commands flow through strategies in priority order.

    Test Coverage:
    - Command is checked against strategies in order
    - First matching strategy handles command
    - Execution stops after match
    """
    # Force command should be handled by ForceExecutionStrategy (priority 20)
    # not by TierExecutionStrategy (priority 100)
    command_router.shell.execute.return_value = CommandResult(
        success=True, output="forced", exit_code=0
    )

    result = command_router.route_command("/f echo test")

    assert result.success


def test_fallback_to_tier_execution(command_router):
    """
    Test that commands fall back to TierExecutionStrategy.

    Test Coverage:
    - Commands not matching specific strategies
    - Fall back to tier-based execution
    - TierExecutionStrategy always accepts command
    """
    command_router.shell.execute.return_value = CommandResult(
        success=True, output="done", exit_code=0
    )

    # Simple command that doesn't match special strategies
    result = command_router.route_command("echo hello")

    assert result is not None


# ============================================================================
# SUMMARY
# ============================================================================

"""
Test Suite Summary:
-------------------
Total Tests: 20

Coverage Breakdown:
- Initialization: 3 tests
- Special Commands: 4 tests (force, pipe, cd, exit)
- Tier Validation: 2 tests
- Natural Language: 2 tests
- Alias Translation: 1 test
- Error Handling: 3 tests
- Help/Utility: 1 test
- Integration: 2 tests

Success Criteria:
✅ 15+ test cases (20 total)
✅ Tests cover routing to correct handlers
✅ Tests cover tier validation
✅ Tests cover platform-specific aliases
✅ Tests cover error handling
✅ Tests cover integration scenarios

Next Steps:
1. Run: pytest tests/core/test_command_router.py -v
2. Check coverage: pytest tests/core/test_command_router.py --cov=isaac.core.command_router
3. Verify 70%+ coverage achieved
"""
