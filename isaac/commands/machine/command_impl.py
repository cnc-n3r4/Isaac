"""
Machine Command - Standardized Implementation

Machine registry and orchestration management.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse


class MachineCommand(BaseCommand):
    """Machine orchestration command"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute machine command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with machine output or error
        """
        parser = FlagParser(args)

        # Get action (first positional argument)
        action = parser.get_positional(0)

        if not action:
            return CommandResponse(
                success=False,
                error="Action required. Use: register, unregister, list, show, status, group, groups, discover, find",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        try:
            # Build args dict from parser
            args_dict = {
                "action": action,
                "machine_id": parser.get_flag("machine-id", aliases=["machine_id"]),
                "hostname": parser.get_flag("hostname"),
                "ip_address": parser.get_flag("ip-address", aliases=["ip_address"]),
                "port": parser.get_flag("port", default=8080),
                "tags": parser.get_flag("tags"),
                "group_name": parser.get_flag("group-name", aliases=["group_name"]),
                "group_members": parser.get_flag("group-members", aliases=["group_members"]),
                "filter_tags": parser.get_flag("filter-tags", aliases=["filter_tags"]),
                "min_cpu": int(parser.get_flag("min-cpu", default=0)),
                "min_memory": float(parser.get_flag("min-memory", default=0.0)),
            }

            # Import the original MachineCommand class
            from isaac.commands.machine.run import MachineCommand as OriginalMachineCommand

            original_command = OriginalMachineCommand()
            output = original_command.execute(args_dict)

            return CommandResponse(
                success=True,
                data=output,
                metadata={}
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
            name="machine",
            description="Machine registry and orchestration - register, manage, and discover machines",
            usage="/machine <action> [options]",
            examples=[
                "/machine register --hostname server1 --ip-address 192.168.1.100",
                "/machine list",
                "/machine show --machine-id abc123",
                "/machine find --filter-tags gpu,production --min-cpu 8",
                "/machine group --group-name gpu-cluster --group-members id1,id2",
                "/machine discover"
            ],
            tier=2,  # Needs validation - manages infrastructure
            aliases=["registry", "infra"],
            category="system"
        )
