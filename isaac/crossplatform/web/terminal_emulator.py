"""
Terminal Emulator - ANSI terminal emulation for web
"""

import re
from typing import List


class TerminalEmulator:
    """
    Emulates ANSI terminal functionality for web browsers
    """

    # ANSI color codes
    COLORS = {
        "30": "black",
        "31": "red",
        "32": "green",
        "33": "yellow",
        "34": "blue",
        "35": "magenta",
        "36": "cyan",
        "37": "white",
        "90": "bright-black",
        "91": "bright-red",
        "92": "bright-green",
        "93": "bright-yellow",
        "94": "bright-blue",
        "95": "bright-magenta",
        "96": "bright-cyan",
        "97": "bright-white",
    }

    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
        self.buffer: List[str] = []
        self.cursor_x = 0
        self.cursor_y = 0

    def process_output(self, text: str) -> str:
        """
        Process terminal output and convert ANSI codes to HTML

        Args:
            text: Raw terminal output with ANSI codes

        Returns:
            HTML formatted output
        """
        # Replace ANSI escape codes with HTML spans
        html = self._convert_ansi_to_html(text)

        return html

    def _convert_ansi_to_html(self, text: str) -> str:
        """Convert ANSI escape codes to HTML"""
        # Pattern for ANSI escape codes
        ansi_pattern = re.compile(r"\033\[([0-9;]+)m")

        result = []
        last_end = 0
        current_styles = []

        for match in ansi_pattern.finditer(text):
            # Add text before this code
            if match.start() > last_end:
                result.append(text[last_end : match.start()])

            # Process the ANSI code
            codes = match.group(1).split(";")

            for code in codes:
                if code == "0":
                    # Reset all styles
                    if current_styles:
                        result.append("</span>" * len(current_styles))
                        current_styles = []
                elif code in self.COLORS:
                    # Color code
                    color = self.COLORS[code]
                    result.append(f'<span class="ansi-{color}">')
                    current_styles.append(color)
                elif code == "1":
                    # Bold
                    result.append('<span class="ansi-bold">')
                    current_styles.append("bold")
                elif code == "4":
                    # Underline
                    result.append('<span class="ansi-underline">')
                    current_styles.append("underline")

            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            result.append(text[last_end:])

        # Close any open spans
        if current_styles:
            result.append("</span>" * len(current_styles))

        return "".join(result)

    def get_css(self) -> str:
        """Get CSS for ANSI color support"""
        return """
.ansi-black { color: #000000; }
.ansi-red { color: #cd3131; }
.ansi-green { color: #0dbc79; }
.ansi-yellow { color: #e5e510; }
.ansi-blue { color: #2472c8; }
.ansi-magenta { color: #bc3fbc; }
.ansi-cyan { color: #11a8cd; }
.ansi-white { color: #e5e5e5; }
.ansi-bright-black { color: #666666; }
.ansi-bright-red { color: #f14c4c; }
.ansi-bright-green { color: #23d18b; }
.ansi-bright-yellow { color: #f5f543; }
.ansi-bright-blue { color: #3b8eea; }
.ansi-bright-magenta { color: #d670d6; }
.ansi-bright-cyan { color: #29b8db; }
.ansi-bright-white { color: #ffffff; }
.ansi-bold { font-weight: bold; }
.ansi-underline { text-decoration: underline; }
"""

    def wrap_text(self, text: str) -> List[str]:
        """Wrap text to terminal width"""
        lines = []
        current_line = ""

        for char in text:
            if char == "\n":
                lines.append(current_line)
                current_line = ""
            elif len(current_line) >= self.width:
                lines.append(current_line)
                current_line = char
            else:
                current_line += char

        if current_line:
            lines.append(current_line)

        return lines

    def clear(self):
        """Clear the terminal buffer"""
        self.buffer = []
        self.cursor_x = 0
        self.cursor_y = 0

    def write(self, text: str):
        """Write text to terminal buffer"""
        lines = self.wrap_text(text)

        for line in lines:
            if len(self.buffer) >= self.height:
                self.buffer.pop(0)

            self.buffer.append(line)

    def get_buffer(self) -> List[str]:
        """Get current terminal buffer"""
        return self.buffer.copy()
