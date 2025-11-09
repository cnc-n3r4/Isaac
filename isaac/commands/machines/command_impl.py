"""
Machines Command - Standardized Implementation

Multi-machine orchestration status and management.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse


class MachinesCommand(BaseCommand):
    """Multi-machine orchestration status command"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute machines command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with orchestration status or error
        """
        parser = FlagParser(args)

        # Get action (first positional argument, defaults to status)
        action = parser.get_positional(0, default="status")
        target = parser.get_positional(1)
        verbose = parser.get_flag("verbose", default=False)

        # Build payload for original command
        payload = {
            "args": {
                "action": action,
                "target": target,
                "verbose": verbose,
                "ip": parser.get_flag("ip"),
                "port": parser.get_flag("port"),
                "tags": parser.get_flag("tags")
            },
            "session": {}
        }

        try:
            # Import and call original command functions
            from isaac.commands.machines import run

            # Map actions to functions
            if action == "status":
                output = run.get_orchestration_status(verbose)
            elif action == "list":
                output = run.list_machines(verbose)
            elif action == "groups":
                output = run.list_groups(verbose)
            elif action == "load":
                output = run.show_load_distribution(verbose)
            elif action == "register":
                output = run.register_machine(target, payload["args"])
            elif action == "unregister":
                output = run.unregister_machine(target)
            else:
                output = f"Unknown action: {action}"

            return CommandResponse(
                success=True,
                data=output,
                metadata={"action": action}
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
            name="machines",
            description="Multi-machine orchestration status - view and manage distributed infrastructure",
            usage="/machines [action] [target] [--verbose]",
            examples=[
                "/machines",
                "/machines status --verbose",
                "/machines list",
                "/machines groups --verbose",
                "/machines load",
                "/machines register server1 --ip 192.168.1.100"
            ],
            tier=1,  # Safe - read-only status display
            aliases=["orchestration", "cluster"],
            category="system"
        )
