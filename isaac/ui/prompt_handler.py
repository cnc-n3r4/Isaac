"""
Prompt Handler - Isaac's command prompt interface
Manages isaac> user> interaction and command input
"""

import sys
from typing import Optional, Tuple
from isaac.ui.terminal_control import TerminalControl
from isaac.ui.advanced_input import AdvancedInputHandler
from isaac.ui.visual_enhancer import VisualEnhancer
from isaac.core.tier_validator import TierValidator

try:
    import colorama
    colorama.init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False


class PromptHandler:
    """Handle Isaac's command prompt interface."""

    def __init__(self, terminal: TerminalControl, tier_validator: TierValidator):
        """Initialize prompt handler."""
        self.terminal = terminal
        self.tier_validator = tier_validator
        self.input_area_start = terminal.get_input_area_start()
        self.output_area_start = terminal.get_scroll_region_start()
        self.current_output_line = self.output_area_start

        # Advanced input features
        self.advanced_input = AdvancedInputHandler(tier_validator)

        # Visual enhancements
        self.visual = VisualEnhancer()

    def show_prompt(self) -> Tuple[str, float]:
        """Display the prompt and get user input with advanced features.

        Returns:
            Tuple of (command, tier) where tier is the safety classification
        """
        # Use advanced input handler for enhanced features
        command, display_text = self.advanced_input.get_input_with_advanced_features()

        # Classify command tier
        tier = self.tier_validator.get_tier(command)

        return command, tier

    def show_user_prompt(self, command: str, tier: float) -> None:
        """Show the user> prompt with command and tier info.

        Args:
            command: The command to display
            tier: The safety tier classification
        """
        width, height = self.terminal.get_terminal_size()

        # Position for user prompt (next line in input area)
        user_y = self.input_area_start + 1
        self.terminal.move_cursor(0, user_y)

        # Show user> prompt with command
        tier_indicator = self._get_tier_indicator(tier)
        if HAS_COLORAMA:
            # Yellow background (U.) with white text for user prompt
            user_prompt = f"\033[43;37mU.\033[0m\033[33m>\033[0m {tier_indicator} {command}"
        else:
            # Fallback without colors
            user_prompt = f"U.> {tier_indicator} {command}"
        print(user_prompt, flush=True)

    def show_confirmation_prompt(self, command: str, tier: float) -> bool:
        """Show confirmation prompt for high-tier commands.

        Args:
            command: Command requiring confirmation
            tier: Safety tier

        Returns:
            True if user confirms, False otherwise
        """
        width, height = self.terminal.get_terminal_size()

        # Position for confirmation in input area
        confirm_y = self.input_area_start + 2  # Still within input area
        self.terminal.move_cursor(0, confirm_y)

        tier_names = {3.0: "DANGER", 4.0: "LOCKDOWN"}
        tier_name = tier_names.get(tier, "UNKNOWN")

        confirm_msg = f"⚠️  {tier_name} command detected. Execute? (yes/no): "
        print(confirm_msg, end="", flush=True)

        try:
            response = input().strip().lower()
            return response in ["yes", "y"]
        except (EOFError, KeyboardInterrupt):
            return False

    def show_command_output(self, output: str, success: bool, command: str = "") -> None:
        """Display command execution results in scrolling output area with visual enhancements.

        Args:
            output: Command output text
            success: Whether command succeeded
            command: The command that was executed (for better formatting)
        """
        width, height = self.terminal.get_terminal_size()

        # Check if we need to scroll
        formatted_output = self.visual.format_command_output(command, output, success)
        output_lines = formatted_output.count('\n') + 1

        if self.current_output_line + output_lines >= height:
            self._scroll_output_area()

        # Position for output in scrolling area
        self.terminal.move_cursor(0, self.current_output_line)

        # Display formatted output
        lines = formatted_output.split('\n')
        for i, line in enumerate(lines):
            if self.current_output_line + i < height:
                self.terminal.move_cursor(0, self.current_output_line + i)
                # Truncate line if too long
                if len(line) > width - 1:
                    line = line[:width - 4] + "..."
                print(line, flush=True)

        self.current_output_line += len(lines)

    def _scroll_output_area(self) -> None:
        """Scroll the output area up by one line."""
        width, height = self.terminal.get_terminal_size()

        # Move all lines up by one, starting from output_area_start + 1
        for y in range(self.output_area_start, height - 1):
            self.terminal.move_cursor(0, y)
            # This is a simplified scroll - in a real implementation we'd copy line content
            print(" " * width, end="", flush=True)

        # Reset current output line to just below the last visible output
        self.current_output_line = height - 2

    def clear_prompt_area(self) -> None:
        """Clear only the input area, preserving output."""
        width, height = self.terminal.get_terminal_size()

        # Clear only the input area (bottom lines), not the output area
        input_start = self.input_area_start
        for y in range(input_start, height):
            self.terminal.move_cursor(0, y)
            print(" " * width, end="", flush=True)

        # Reset input area with prompt
        self.terminal.move_cursor(0, input_start)
        print("isaac> ", end="", flush=True)

    def _get_tier_indicator(self, tier: float) -> str:
        """Get tier indicator symbol."""
        indicators = {
            1.0: "🟢",  # Green circle
            2.0: "🟡",  # Yellow circle
            2.5: "🟠",  # Orange circle
            3.0: "🟠",  # Orange circle
            4.0: "🔴"   # Red circle
        }
        return indicators.get(tier, "⚪")  # White circle for unknown