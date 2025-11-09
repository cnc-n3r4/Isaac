"""
Help Unified Command - Standardized Implementation

Unified help system combining /help, /man, /apropos, /whatis functionality.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.commands.help_unified.run import UnifiedHelpCommand as UnifiedHelpCommandLegacy


class HelpUnifiedCommand(BaseCommand):
    """Unified help system"""

    def __init__(self):
        """Initialize help unified command"""
        self.legacy_command = UnifiedHelpCommandLegacy()

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute help unified command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with help output
        """
        try:
            # Execute legacy command (returns string output)
            result = self.legacy_command.run(args)

            return CommandResponse(
                success=True,
                data=result,
                metadata={}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "HELP_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="help_unified",
            description="Unified help system combining help, man, apropos, and whatis",
            usage="/help [command] [--search <keyword>] [--whatis <cmd>] [--man <topic>]",
            examples=[
                "/help                        # List all commands",
                "/help config                 # Show help for specific command",
                "/help --search file          # Search for commands about files",
                "/help --whatis read          # Show one-line description",
                "/help --man isaac            # Show detailed manual page",
                "/help --all                  # Show all commands including hidden"
            ],
            tier=1,  # Safe - read-only help information
            aliases=["help", "man", "apropos", "whatis"],
            category="system"
        )
