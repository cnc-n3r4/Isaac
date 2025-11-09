"""
Plugin Command - Standardized Implementation

Plugin system management for Isaac.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.commands.plugin.plugin_command import PluginCommand as PluginCommandLegacy


class PluginCommand(BaseCommand):
    """Plugin system management"""

    def __init__(self):
        """Initialize plugin command"""
        self.legacy_command = PluginCommandLegacy()

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute plugin command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with plugin operation results
        """
        try:
            # Execute legacy command (returns exit code)
            exit_code = self.legacy_command.execute(args)

            # Since legacy command prints directly, we return success/failure
            # based on exit code
            if exit_code == 0:
                return CommandResponse(
                    success=True,
                    data="",  # Output was already printed
                    metadata={"exit_code": exit_code}
                )
            else:
                return CommandResponse(
                    success=False,
                    error="Plugin command failed",
                    metadata={"exit_code": exit_code, "error_code": "PLUGIN_ERROR"}
                )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "PLUGIN_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="plugin",
            description="Plugin system management - install, manage, and develop plugins",
            usage="/plugin <subcommand> [options]",
            examples=[
                "/plugin list                    # List installed plugins",
                "/plugin install command-logger  # Install a plugin",
                "/plugin search git              # Search for plugins",
                "/plugin info <name>             # Show plugin details",
                "/plugin create my-plugin        # Create new plugin from template",
                "/plugin update --all            # Update all plugins"
            ],
            tier=3,  # AI validation - can install/execute arbitrary code
            aliases=["plugins"],
            category="system"
        )
