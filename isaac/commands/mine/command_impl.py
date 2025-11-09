"""
Mine Command - Standardized Implementation

xAI Collections manager for personal file history and collection search.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse


class MineCommand(BaseCommand):
    """xAI Collections manager - search and manage personal file collections"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute mine command.

        Args:
            args: Command arguments
            context: Optional execution context with session data

        Returns:
            CommandResponse with mine operation results
        """
        try:
            # Import MineHandler (it has all the logic)
            from isaac.commands.mine.run import MineHandler

            # Get session data from context if available
            if context and "session" in context:
                session_data = context["session"]
            else:
                # Try to get session manager
                try:
                    from isaac.core.session_manager import SessionManager
                    session_manager = SessionManager()
                    session_data = session_manager
                except Exception:
                    # Fallback to empty config
                    session_data = {"config": {}}

            # Create handler
            handler = MineHandler(session_data)

            # Execute command
            result = handler.handle_command(args, "/mine")

            return CommandResponse(
                success=True,
                data=result,
                metadata={"operation": "mine"}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "EXECUTION_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="mine",
            description="xAI Collections manager - search and manage personal file collections",
            usage="/mine [--create|--use|--delete|--upload|--search|--list|--info] <args>",
            examples=[
                "/mine --create mydocs  # Create collection",
                "/mine --use mydocs  # Switch to collection",
                "/mine --upload file.txt  # Upload file",
                "/mine --search \"query\"  # Search collection",
                "/mine --list  # List all collections",
                "/mine --info  # Show active collection details"
            ],
            tier=3,  # AI validation needed - interacts with external API
            aliases=["collection", "xai"],
            category="ai"
        )
