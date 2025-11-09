"""
Sync Command - Standardized Implementation

Cloud synchronization for command queue and session data.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.core.session_manager import SessionManager


class SyncCommand(BaseCommand):
    """Cloud synchronization for command queue"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute sync command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with sync operation results
        """
        try:
            parser = FlagParser(args)

            # Get session
            session = SessionManager()

            # Check for dry-run flag
            dry_run = parser.has_flag("dry-run")

            if dry_run:
                # Show what would be synced
                pending = session.queue.dequeue_pending(limit=100)
                output = []
                output.append(f"Dry run: {len(pending)} commands would be synced")
                output.append("")

                for cmd in pending:
                    output.append(f"#{cmd['id']}: {cmd['command_text'][:60]}...")
                    output.append(f"  Type: {cmd['command_type']} | Queued: {cmd['queued_at']}")
                    if cmd["target_device"]:
                        output.append(f"  Target: {cmd['target_device']}")
                    output.append("")

                result = "\n".join(output)
            else:
                # Force sync
                success = session.force_sync()
                if success:
                    result = "Sync completed successfully"
                else:
                    result = "Sync failed - check connection and try again"

            return CommandResponse(
                success=True,
                data=result,
                metadata={"dry_run": dry_run}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "SYNC_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="sync",
            description="Cloud synchronization for command queue and session data",
            usage="/sync [--dry-run]",
            examples=[
                "/sync              # Sync queued commands to cloud",
                "/sync --dry-run    # Show what would be synced without syncing"
            ],
            tier=2,  # Needs validation - network operation
            aliases=["synchronize"],
            category="system"
        )
