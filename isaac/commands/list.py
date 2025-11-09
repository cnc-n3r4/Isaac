"""
List Handler - Display command history and backups.

Handles:
- Listing command history with status symbols
- Listing available backups
- Displaying session information
- Formatted output
"""

from typing import List

from isaac.core.cli_command_router import CommandResult


class ListHandler:
    """
    Handle list command execution.

    Expected format:
        list history      - Show command history
        list backups      - Show available backups
        list              - Show recent history (default)
    """

    def __init__(self, session_manager):
        """
        Initialize handler with session manager.

        Args:
            session_manager: SessionManager for accessing history
        """
        self.session = session_manager

    def execute(self, args: List[str]) -> CommandResult:
        """
        Execute list command.

        Args:
            args: Command arguments (everything after 'list')

        Returns:
            CommandResult with formatted listing
        """
        # Determine what to list
        target = args[0].lower() if args else "history"

        if target == "history":
            return self._list_history()
        elif target == "backups":
            return self._list_backups()
        else:
            return CommandResult(
                success=False,
                message=f"Unknown list target: {target}",
                status_symbol="✗",
                suggestion="Usage: isaac list [history|backups]",
            )

    def _list_history(self) -> CommandResult:
        """
        List command history from session.

        Returns:
            CommandResult with formatted history
        """
        # Get command history from session
        # For now, return placeholder until SessionManager implements history storage

        history_lines = [
            "Command History:",
            "",
            "✓ cd /home [2025-10-19 14:30]",
            "✗ backup invalid-path [2025-10-19 14:31] - Path not found",
            "✓ backup documents to /mnt/external [2025-10-19 14:32]",
            "⊘ restore sensitive-data [2025-10-19 14:33] - Cancelled by user",
            "",
            "Tip: Commands logged to session for learning",
        ]

        return CommandResult(
            success=True, message="\n".join(history_lines), status_symbol="✓", suggestion=None
        )

    def _list_backups(self) -> CommandResult:
        """
        List available backups.

        Returns:
            CommandResult with formatted backup list
        """
        # Get backup list from session
        # For now, return placeholder until backup tracking implemented

        backup_lines = [
            "Available Backups:",
            "",
            "📁 documents (2025-10-19 14:00) → /mnt/external/documents",
            "📁 projects (2025-10-19 13:30) → /backup/projects",
            "📄 config.json (2025-10-19 12:00) → /backup/config.json",
            "",
            "Tip: Use 'isaac restore <name> from <backup_path>' to restore",
        ]

        return CommandResult(
            success=True, message="\n".join(backup_lines), status_symbol="✓", suggestion=None
        )
