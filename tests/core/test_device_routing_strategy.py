"""
Test Suite for Isaac DeviceRoutingStrategy

This module tests the DeviceRoutingStrategy implementation that handles
!device routing commands for multi-device execution.

Coverage Goal: 80%+
Test Count: 8+ scenarios
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
# DEVICE ROUTING STRATEGY TESTS
# ============================================================================

def test_device_routing_strategy_can_handle_device_commands(command_router):
    """
    Test that DeviceRoutingStrategy can handle !device commands.

    Test Coverage:
    - !device commands are recognized
    - Non-device commands are not handled by DeviceRoutingStrategy
    """
    # Should handle !device commands
    def check_handle(command):
        return any(strategy.can_handle(command) for strategy in command_router.strategies)

    assert check_handle("!laptop ls")
    assert check_handle("!server:round_robin /status")
    assert check_handle("!group1 pwd")

    # Should not handle non-device commands
    assert not any(strategy.can_handle("ls") for strategy in command_router.strategies if hasattr(strategy, 'can_handle') and strategy.__class__.__name__ == 'DeviceRoutingStrategy')
    assert not any(strategy.can_handle("/config") for strategy in command_router.strategies if hasattr(strategy, 'can_handle') and strategy.__class__.__name__ == 'DeviceRoutingStrategy')


def test_device_routing_strategy_priority(command_router):
    """
    Test that DeviceRoutingStrategy has correct priority.

    Test Coverage:
    - DeviceRoutingStrategy priority is 40
    - Priority is within expected range
    """
    device_strategy = next((s for s in command_router.strategies if s.__class__.__name__ == 'DeviceRoutingStrategy'), None)
    assert device_strategy is not None
    assert device_strategy.get_priority() == 40


def test_device_routing_simple_command(command_router):
    """
    Test !device command with simple routing.

    Test Coverage:
    - !device command is handled
    - Placeholder implementation works
    - Success result returned
    """
    result = command_router.route_command("!laptop ls -la")

    assert result.success
    assert "Executed locally:" in result.output or "Command queued for" in result.output
    assert "laptop" in result.output
    assert "ls -la" in result.output


def test_device_routing_with_strategy(command_router):
    """
    Test !device:strategy command with load balancing strategy.

    Test Coverage:
    - !device:strategy syntax is parsed
    - Strategy parameter is recognized
    - Command is routed appropriately
    """
    result = command_router.route_command("!server:round_robin /status")

    assert result.success
    assert "server" in result.output
    assert "/status" in result.output


def test_device_routing_group_command(command_router):
    """
    Test !group command for group execution.

    Test Coverage:
    - Group routing is handled
    - Multiple device execution is acknowledged
    """
    result = command_router.route_command("!webservers uptime")

    assert result.success
    assert "Load balancing across group" in result.output
    assert "webservers" in result.output
    assert "uptime" in result.output


def test_device_routing_missing_command(command_router):
    """
    Test !device without command.

    Test Coverage:
    - Malformed !device commands are rejected
    - Error message provided
    - Usage instructions given
    """
    result = command_router.route_command("!laptop")

    assert not result.success
    assert "Usage:" in result.output
    assert "!device_alias" in result.output


def test_device_routing_empty_device(command_router):
    """
    Test ! command without device name.

    Test Coverage:
    - Empty device specifications are handled
    - Error message provided
    """
    result = command_router.route_command("! ls")

    assert not result.success
    assert "Usage:" in result.output


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_device_routing_strategy_in_router_strategies(command_router):
    """
    Test that DeviceRoutingStrategy is properly included in router strategies.

    Test Coverage:
    - DeviceRoutingStrategy is loaded in strategies list
    - Strategies are sorted by priority
    - DeviceRoutingStrategy has required methods
    """
    device_strategy = next((s for s in command_router.strategies if s.__class__.__name__ == 'DeviceRoutingStrategy'), None)
    assert device_strategy is not None

    # Check required methods
    assert hasattr(device_strategy, 'can_handle')
    assert hasattr(device_strategy, 'execute')
    assert hasattr(device_strategy, 'get_priority')
    assert hasattr(device_strategy, 'get_help')

    # Check help text
    help_text = device_strategy.get_help()
    assert "device" in help_text.lower()
    assert "routing" in help_text.lower()


def test_device_routing_priority_ordering(command_router):
    """
    Test that DeviceRoutingStrategy has correct position in priority ordering.

    Test Coverage:
    - DeviceRoutingStrategy comes after ConfigStrategy (35)
    - DeviceRoutingStrategy comes before MetaCommandStrategy (50)
    - Overall priority ordering is maintained
    """
    strategies = command_router.strategies
    priorities = [s.get_priority() for s in strategies]
    
    # Find positions
    config_pos = next(i for i, s in enumerate(strategies) if s.__class__.__name__ == 'ConfigStrategy')
    device_pos = next(i for i, s in enumerate(strategies) if s.__class__.__name__ == 'DeviceRoutingStrategy')
    meta_pos = next(i for i, s in enumerate(strategies) if s.__class__.__name__ == 'MetaCommandStrategy')
    
    assert config_pos < device_pos  # Config (35) before Device (40)
    assert device_pos < meta_pos    # Device (40) before Meta (50)


# ============================================================================
# SUMMARY
# ============================================================================

"""
Test Suite Summary:
-------------------
Total Tests: 9

Coverage Breakdown:
- Basic handling: 2 tests (can_handle, priority)
- Command execution: 4 tests (simple, strategy, group, malformed)
- Error handling: 2 tests (missing command, empty device)
- Integration: 1 test (strategy inclusion and ordering)

Success Criteria:
? Tests cover !device command parsing
? Tests verify strategy parameter handling
? Tests confirm proper error handling
? Tests validate priority ordering
? Tests check integration with router

Next Steps:
1. Run: pytest tests/core/test_device_routing_strategy.py -v
2. Check coverage: pytest tests/core/test_device_routing_strategy.py --cov=isaac.core.routing.device_routing_strategy
3. Verify 80%+ coverage achieved
"""