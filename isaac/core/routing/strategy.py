"""
Base strategy class for command routing.

This module implements the Strategy pattern to break down the complex
CommandRouter.route_command method into smaller, manageable pieces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult


class CommandStrategy(ABC):
    """Base class for command routing strategies."""

    def __init__(self, session_mgr, shell):
        """
        Initialize strategy with session manager and shell adapter.

        Args:
            session_mgr: Session manager instance
            shell: Shell adapter instance
        """
        self.session = session_mgr
        self.shell = shell

    @abstractmethod
    def can_handle(self, input_text: str) -> bool:
        """
        Check if this strategy can handle the given command.

        Args:
            input_text: Raw user input

        Returns:
            True if this strategy can handle the command, False otherwise
        """
        pass

    @abstractmethod
    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """
        Execute the command using this strategy.

        Args:
            input_text: Raw user input
            context: Additional context (router instance, validators, etc.)

        Returns:
            CommandResult with execution results
        """
        pass

    @abstractmethod
    def get_help(self) -> str:
        """
        Get help text for this command type.

        Returns:
            Help text string
        """
        pass

    def get_priority(self) -> int:
        """
        Get execution priority for this strategy.
        Lower values = higher priority (executed first).

        Returns:
            Priority value (default: 100)
        """
        return 100
