"""
Update Command - Standardized Implementation

Intelligent package dependency updates with safety checks.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse


class UpdateCommand(BaseCommand):
    """Intelligent package dependency updates"""

    def __init__(self):
        """Initialize update command"""
        # Import here to avoid circular dependencies
        from isaac.core.session_manager import SessionManager
        self.session_manager = SessionManager()

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute update command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with update operation results
        """
        try:
            parser = FlagParser(args)

            # Parse arguments for legacy command
            legacy_args = {
                "manager": parser.get_flag("manager", "auto"),
                "packages": parser.get_flag("packages", ""),
                "dry_run": parser.has_flag("dry-run", ["n"]),
                "confirm": not parser.has_flag("yes", ["y"])  # Invert: yes means skip confirm
            }

            # Import and execute legacy command
            from isaac.commands.update.run import UpdateCommand as UpdateCommandLegacy
            legacy_cmd = UpdateCommandLegacy(self.session_manager)
            result = legacy_cmd.execute(legacy_args)

            # Convert result format to CommandResponse
            return CommandResponse(
                success=result["success"],
                data=result["output"],
                metadata={"exit_code": result["exit_code"]}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "UPDATE_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="update",
            description="Intelligent package dependency updates with safety checks",
            usage="/update [--manager <manager>] [--packages <packages>] [--dry-run] [--yes]",
            examples=[
                "/update                              # Update all outdated packages",
                "/update --manager pip                # Update only pip packages",
                "/update --packages numpy,pandas      # Update specific packages",
                "/update --dry-run                    # Show what would be updated",
                "/update --yes                        # Skip confirmation prompt"
            ],
            tier=3,  # AI validation - can install/update packages
            aliases=["upgrade"],
            category="system"
        )
