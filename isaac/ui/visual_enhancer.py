"""
Visual Enhancer - Syntax highlighting and color-coded output for Isaac
Provides beautiful terminal output with colors, formatting, and visual feedback
"""

import re
from enum import Enum
from typing import List, Tuple


class Color(Enum):
    """ANSI color codes for terminal output."""

    # Basic colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Special
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    REVERSE = "\033[7m"


class VisualEnhancer:
    """Enhance terminal output with colors, formatting, and visual effects."""

    def __init__(self):
        """Initialize visual enhancer."""
        self.color_enabled = True
        self.theme = "default"

        # Syntax highlighting patterns
        self.syntax_patterns = {
            "command": re.compile(r"^(\$|\w+>)\s*(\w+)"),
            "path": re.compile(r"(/[\w./-]+|[\w./-]+\.[\w]+|~\w*|./[\w./-]+)"),
            "option": re.compile(r"(-\w|--[\w-]+)"),
            "string": re.compile(r"'[^']*'|" + r'"[^"]*"'),
            "number": re.compile(r"\b\d+\b"),
            "error": re.compile(r"(error|Error|ERROR|failed|Failed|FAILED)"),
            "success": re.compile(r"(success|Success|SUCCESS|ok|OK|done|Done|DONE)"),
            "warning": re.compile(r"(warning|Warning|WARNING|caution|Caution|CAUTION)"),
        }

    def enable_colors(self, enabled: bool = True):
        """Enable or disable color output."""
        self.color_enabled = enabled

    def set_theme(self, theme: str):
        """Set color theme."""
        self.theme = theme

    def colorize_text(self, text: str, color: Color) -> str:
        """Apply color to text."""
        if not self.color_enabled:
            return text
        return f"{color.value}{text}{Color.RESET.value}"

    def highlight_syntax(self, text: str) -> str:
        """Apply syntax highlighting to text."""
        if not self.color_enabled:
            return text

        highlighted = text

        # Apply highlighting in order of priority
        highlights = [
            ("error", Color.BRIGHT_RED),
            ("warning", Color.BRIGHT_YELLOW),
            ("success", Color.BRIGHT_GREEN),
            ("command", Color.BRIGHT_BLUE),
            ("path", Color.CYAN),
            ("option", Color.YELLOW),
            ("string", Color.GREEN),
            ("number", Color.MAGENTA),
        ]

        for pattern_name, color in highlights:
            pattern = self.syntax_patterns[pattern_name]
            highlighted = pattern.sub(lambda m: self.colorize_text(m.group(0), color), highlighted)

        return highlighted

    def format_command_output(self, command: str, output: str, success: bool) -> str:
        """Format command execution results with visual enhancements."""
        lines = []

        # Command header
        status_icon = "✓" if success else "✗"
        status_color = Color.BRIGHT_GREEN if success else Color.BRIGHT_RED

        command_line = (
            f"{self.colorize_text(status_icon, status_color)} {self.highlight_syntax(command)}"
        )
        lines.append(command_line)

        # Output with syntax highlighting
        if output.strip():
            for line in output.split("\n"):
                if line.strip():
                    highlighted_line = self.highlight_syntax(line)
                    lines.append(f"  {highlighted_line}")
                else:
                    lines.append("")

        return "\n".join(lines)

    def format_prompt(self, prompt_type: str, text: str = "") -> str:
        """Format different types of prompts."""
        if not self.color_enabled:
            return f"{prompt_type}> {text}"

        prompts = {
            "isaac": (Color.BRIGHT_CYAN, "isaac"),
            "user": (Color.BRIGHT_YELLOW, "user"),
            "system": (Color.BRIGHT_MAGENTA, "system"),
            "error": (Color.BRIGHT_RED, "error"),
        }

        color, prefix = prompts.get(prompt_type, (Color.WHITE, prompt_type))
        return f"{self.colorize_text(prefix, color)}> {text}"

    def format_status_bar(self, items: List[Tuple[str, str]]) -> str:
        """Format status bar with multiple items."""
        if not self.color_enabled:
            return " | ".join(f"{label}: {value}" for label, value in items)

        formatted_items = []
        for label, value in items:
            colored_label = self.colorize_text(label, Color.CYAN)
            colored_value = self.colorize_text(value, Color.WHITE)
            formatted_items.append(f"{colored_label}: {colored_value}")

        return " | ".join(formatted_items)

    def format_progress_bar(self, current: int, total: int, width: int = 20) -> str:
        """Create a visual progress bar."""
        if not self.color_enabled:
            return f"[{current}/{total}]"

        percentage = current / total if total > 0 else 0
        filled = int(width * percentage)
        bar = "█" * filled + "░" * (width - filled)

        percent_text = f"{percentage:.1%}"
        return f"{self.colorize_text(bar, Color.BRIGHT_GREEN)} {self.colorize_text(percent_text, Color.CYAN)}"

    def format_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Format data as a nice table."""
        if not rows:
            return ""

        # Calculate column widths
        all_rows = [headers] + rows
        col_widths = []
        for i in range(len(headers)):
            col_widths.append(max(len(str(row[i])) for row in all_rows))

        lines = []

        # Header
        header_line = "  ".join(
            self.colorize_text(str(headers[i]).ljust(col_widths[i]), Color.BRIGHT_BLUE)
            for i in range(len(headers))
        )
        lines.append(header_line)

        # Separator
        separator = "──".join("─" * width for width in col_widths)
        lines.append(self.colorize_text(separator, Color.DIM))

        # Data rows
        for row in rows:
            row_line = "  ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
            lines.append(row_line)

        return "\n".join(lines)

    def format_welcome_message(self) -> str:
        """Create a beautiful welcome message."""
        if not self.color_enabled:
            return "Welcome to Isaac 2.0 - AI Shell Assistant"

        lines = [
            "",
            self.colorize_text("╔══════════════════════════════════════╗", Color.CYAN),
            self.colorize_text("║                                      ║", Color.CYAN),
            self.colorize_text("║     ", Color.CYAN)
            + self.colorize_text("Isaac 2.0", Color.BRIGHT_YELLOW)
            + self.colorize_text(" - AI Shell Assistant", Color.CYAN)
            + self.colorize_text("     ║", Color.CYAN),
            self.colorize_text("║                                      ║", Color.CYAN),
            self.colorize_text("╚══════════════════════════════════════╝", Color.CYAN),
            "",
            self.colorize_text("🚀 Ready for intelligent command execution", Color.BRIGHT_GREEN),
            self.colorize_text("⚡ Tab completion and history navigation", Color.BRIGHT_CYAN),
            self.colorize_text("🛡️  5-tier safety system active", Color.BRIGHT_YELLOW),
            "",
        ]

        return "\n".join(lines)
