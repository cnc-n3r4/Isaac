"""
Header Display - Isaac's status header
Shows session info, tier status, and system indicators
"""

from datetime import datetime
from typing import Optional
from isaac.ui.terminal_control import TerminalControl
from isaac.models.preferences import Preferences


class HeaderDisplay:
    """Display Isaac's status header in the locked top area."""

    def __init__(self, terminal: TerminalControl, preferences: Preferences):
        """Initialize header display."""
        self.terminal = terminal
        self.preferences = preferences
        self.session_start = datetime.now()
        self.current_tier = 1  # Default safe tier
        self.cloud_status = "offline"  # offline, syncing, synced
        self.shell_type = "unknown"

    def update_header(self, tier: Optional[int] = None, cloud_status: Optional[str] = None,
                     shell_type: Optional[str] = None) -> None:
        """Update and display the header information.

        Args:
            tier: Current command tier (1-4)
            cloud_status: Cloud sync status
            shell_type: Current shell type (powershell/bash)
        """
        if tier is not None:
            self.current_tier = tier
        if cloud_status is not None:
            self.cloud_status = cloud_status
        if shell_type is not None:
            self.shell_type = shell_type

        self._draw_header()

    def _draw_header(self) -> None:
        """Draw the complete header in the locked area."""
        # Get terminal dimensions
        width, height = self.terminal.get_terminal_size()

        # Header spans full width, 4 lines high now
        header_lines = self._build_header_lines(width)

        # Print header lines in locked area (top 4 lines)
        for i, line in enumerate(header_lines):
            self.terminal.print_at(0, i, line)

    def _build_header_lines(self, width: int) -> list[str]:
        """Build the three header lines.

        Args:
            width: Terminal width

        Returns:
            List of three header line strings
        """
        # Line 1: Title and session time
        session_time = self._format_session_time()
        title = "Isaac 2.0 - AI Shell Assistant"
        line1 = f"{title} | Session: {session_time}"

        # Line 2: Status indicators
        tier_indicator = self._get_tier_indicator()
        cloud_indicator = self._get_cloud_indicator()
        shell_indicator = f"Shell: {self.shell_type}"

        # Center the indicators
        status_line = f"{tier_indicator} | {cloud_indicator} | {shell_indicator}"
        line2 = status_line.center(width)

        # Line 3: Command history header
        line3 = "Command History".center(width)

        # Line 4: Separator
        line4 = "─" * width

        return [line1, line2, line3, line4]

    def _format_session_time(self) -> str:
        """Format session elapsed time."""
        elapsed = datetime.now() - self.session_start
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def _get_tier_indicator(self) -> str:
        """Get tier safety indicator."""
        tier_names = {
            1: "SAFE",
            2: "CAUTION",
            3: "DANGER",
            4: "LOCKDOWN"
        }

        tier_colors = {
            1: "[GREEN]",
            2: "[YELLOW]",
            3: "[RED]",
            4: "[RED]"
        }

        name = tier_names.get(self.current_tier, "UNKNOWN")
        color = tier_colors.get(self.current_tier, "[WHITE]")

        return f"Tier {self.current_tier}: {color}{name}[RESET]"

    def _get_cloud_indicator(self) -> str:
        """Get cloud sync status indicator."""
        status_indicators = {
            "offline": "[RED]● Offline[RESET]",
            "syncing": "[YELLOW]● Syncing[RESET]",
            "synced": "[GREEN]● Synced[RESET]"
        }

        return status_indicators.get(self.cloud_status, "[GRAY]● Unknown[RESET]")