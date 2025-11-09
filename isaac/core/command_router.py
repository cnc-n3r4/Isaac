"""
CommandRouter - Routes commands through safety tiers and AI processing
SAFETY-CRITICAL: Ensures all commands go through appropriate validation

REFACTORED: Now uses Strategy pattern for cleaner, more maintainable code.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from isaac.adapters.base_adapter import CommandResult
from isaac.ai.query_classifier import QueryClassifier
from isaac.core.routing.agentic_mode_strategy import AgenticModeStrategy
from isaac.core.routing.cd_strategy import CdStrategy
from isaac.core.routing.config_strategy import ConfigStrategy
from isaac.core.routing.device_routing_strategy import DeviceRoutingStrategy
from isaac.core.routing.exit_blocker_strategy import ExitBlockerStrategy
from isaac.core.routing.exit_quit_strategy import ExitQuitStrategy
from isaac.core.routing.force_execution_strategy import ForceExecutionStrategy
from isaac.core.routing.meta_command_strategy import MetaCommandStrategy
from isaac.core.routing.natural_language_strategy import NaturalLanguageStrategy
from isaac.core.routing.pipe_strategy import PipeStrategy
from isaac.core.routing.strategy import CommandStrategy
from isaac.core.routing.task_mode_strategy import TaskModeStrategy
from isaac.core.routing.tier_execution_strategy import TierExecutionStrategy
from isaac.core.routing.unix_alias_strategy import UnixAliasStrategy
from isaac.core.tier_validator import TierValidator
from isaac.runtime import CommandDispatcher


class CommandRouter:
    """Routes commands through tier validation and AI processing using Strategy pattern."""

    def __init__(self, session_mgr: Any, shell: Any) -> None:
        """Initialize with session manager and shell adapter."""
        self.session = session_mgr
        self.shell = shell
        self.validator = TierValidator(self.session.preferences)
        self.query_classifier = QueryClassifier()

        # Initialize the plugin dispatcher
        self.dispatcher = CommandDispatcher(session_mgr)
        self.dispatcher.load_commands(
            [Path(__file__).parent.parent / "commands", Path.home() / ".isaac" / "commands"]
        )

        # Initialize all command strategies
        self.strategies: List[CommandStrategy] = self._initialize_strategies()

        # Sort strategies by priority (lower = higher priority)
        self.strategies.sort(key=lambda s: s.get_priority())

    def _initialize_strategies(self) -> List[CommandStrategy]:
        """Initialize and return all command strategies."""
        return [
            # High priority strategies (10-30)
            PipeStrategy(self.session, self.shell),
            CdStrategy(self.session, self.shell),
            ForceExecutionStrategy(self.session, self.shell),
            ExitQuitStrategy(self.session, self.shell),
            ConfigStrategy(self.session, self.shell),
            DeviceRoutingStrategy(self.session, self.shell),
            ExitBlockerStrategy(self.session, self.shell),
            TaskModeStrategy(self.session, self.shell),
            AgenticModeStrategy(self.session, self.shell),
            # Medium priority strategies (50-60)
            MetaCommandStrategy(self.session, self.shell),
            NaturalLanguageStrategy(self.session, self.shell),
            UnixAliasStrategy(self.session, self.shell),
            # Low priority - default strategy (100)
            TierExecutionStrategy(self.session, self.shell),
        ]

    def route_command(self, input_text: str) -> CommandResult:
        """
        Route command through appropriate processing pipeline using strategies.

        Args:
            input_text: Raw user input

        Returns:
            CommandResult with execution results
        """
        # Build context for strategies
        context = {
            "router": self,
            "validator": self.validator,
            "query_classifier": self.query_classifier,
            "dispatcher": self.dispatcher,
        }

        # Try each strategy in priority order
        for strategy in self.strategies:
            if strategy.can_handle(input_text):
                return strategy.execute(input_text, context)

        # Should never reach here (TierExecutionStrategy always returns True)
        return CommandResult(
            success=False, output="Isaac > No strategy could handle command", exit_code=-1
        )

    def get_help(self) -> str:
        """Get help text for all available command types."""
        help_lines = ["Isaac Command Router - Available command types:\n"]
        for strategy in self.strategies:
            help_text = strategy.get_help()
            if help_text:
                help_lines.append(f"  • {help_text}")
        return "\n".join(help_lines)
