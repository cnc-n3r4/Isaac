"""
Queue Command - Standardized Implementation

Command queue management for cross-device execution.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.core.session_manager import SessionManager


class QueueCommand(BaseCommand):
    """Command queue management"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute queue command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with queue status
        """
        try:
            # Get session
            session = SessionManager()

            # Get queue status
            status = session.get_queue_status()
            pending = session.queue.dequeue_pending(limit=50)

            # Format output
            output = []
            output.append(f"Queue Status: {status['pending']} pending, {status['failed']} failed")
            output.append("")

            if not pending:
                output.append("No commands queued")
            else:
                for cmd in pending:
                    output.append(f"#{cmd['id']}: {cmd['command_text'][:60]}...")
                    output.append(f"  Type: {cmd['command_type']} | Queued: {cmd['queued_at']}")
                    if cmd["target_device"]:
                        output.append(f"  Target: {cmd['target_device']}")
                    output.append("")

            return CommandResponse(
                success=True,
                data="\n".join(output),
                metadata={
                    "pending_count": status['pending'],
                    "failed_count": status['failed']
                }
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "QUEUE_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="queue",
            description="Command queue management for cross-device execution",
            usage="/queue",
            examples=[
                "/queue    # Show all queued commands"
            ],
            tier=1,  # Safe - read-only status
            aliases=["q", "cmd-queue"],
            category="system"
        )
