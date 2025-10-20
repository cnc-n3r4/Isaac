"""
Terminal Control - Traditional terminal interface for Isaac
Provides a clean, traditional terminal experience with status bar
"""

import os
import sys
import time
import datetime
import threading
import xml.etree.ElementTree as ET
from typing import Optional, Tuple
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import colorama
    colorama.init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False


class TerminalControl:
    """Controls terminal display in traditional style."""

    def __init__(self):
        """Initialize terminal control."""
        self.terminal_width = 80
        self.terminal_height = 24
        self.status_lines = 3  # Top 3 lines for status
        self.working_directory = Path.cwd()
        self.current_tier = "1 (Safe)"
        self.connection_status = "Online"
        self.session_id = self._generate_session_id()
        self.is_windows = os.name == 'nt'
        
        # x.ai status tracking
        self.xai_status = "Loading..."
        self.xai_status_thread = None
        self._start_xai_status_monitor()

    def _generate_session_id(self) -> str:
        """Generate a short unique session identifier."""
        import hashlib
        import secrets

        # Create a unique string from timestamp and random bytes
        timestamp = str(int(datetime.datetime.now().timestamp()))
        random_bytes = secrets.token_bytes(4)  # 8 hex chars

        # Hash and take first 6 hex chars for a short ID
        unique_string = f"{timestamp}{random_bytes.hex()}"
        session_hash = hashlib.md5(unique_string.encode()).hexdigest()[:6]

        return f"i{session_hash}"

    def _start_xai_status_monitor(self):
        """Start background thread to monitor x.ai status."""
        if not HAS_REQUESTS:
            self.xai_status = "No requests lib"
            return
            
        self.xai_status_thread = threading.Thread(
            target=self._monitor_xai_status, 
            daemon=True
        )
        self.xai_status_thread.start()

    def _monitor_xai_status(self):
        """Background thread to periodically fetch x.ai status."""
        while True:
            try:
                self._fetch_xai_status()
            except Exception as e:
                self.xai_status = f"Error: {str(e)[:15]}"
            time.sleep(300)  # Update every 5 minutes

    def _fetch_xai_status(self):
        """Fetch current status from x.ai RSS feed."""
        try:
            response = requests.get("https://status.x.ai/feed.xml", timeout=10)
            response.raise_for_status()
            
            # Parse RSS feed
            root = ET.fromstring(response.content)
            
            # Find the most recent item
            items = root.findall(".//item")
            if items:
                latest_item = items[0]
                title = latest_item.find("title")
                if title is not None and title.text:
                    # Extract status from title (typically "All Systems Operational" or similar)
                    status_text = title.text.strip()
                    # Truncate if too long for status bar
                    if len(status_text) > 20:
                        status_text = status_text[:17] + "..."
                    self.xai_status = status_text
                else:
                    self.xai_status = "No status found"
            else:
                self.xai_status = "No items"
                
        except requests.exceptions.RequestException as e:
            self.xai_status = f"Net error: {str(e)[:10]}"
        except ET.ParseError:
            self.xai_status = "Parse error"
        except Exception as e:
            self.xai_status = f"Error: {str(e)[:10]}"

    def setup_terminal(self):
        """Set up the terminal for traditional Isaac experience."""
        self._update_terminal_size()
        self._clear_screen()
        self._setup_scroll_region()
        self._draw_status_bar()
        self._position_cursor_for_input()

    def _update_terminal_size(self):
        """Get current terminal dimensions."""
        try:
            if self.is_windows:
                import shutil
                size = shutil.get_terminal_size()
                self.terminal_width = size.columns
                self.terminal_height = size.lines
            else:
                import shutil
                size = shutil.get_terminal_size()
                self.terminal_width = size.columns
                self.terminal_height = size.lines
        except:
            # Default fallback
            self.terminal_width = 80
            self.terminal_height = 24

    def _clear_screen(self):
        """Clear the entire screen."""
        if self.is_windows:
            os.system('cls')
        else:
            print("\033[2J\033[H", end="", flush=True)

    def _setup_scroll_region(self):
        """Set up scroll region for the main terminal area."""
        # Set scroll region from line 4 (after status bar) to bottom of terminal
        scroll_start = self.status_lines + 1  # Line 4
        scroll_end = self.terminal_height     # Bottom of terminal
        if scroll_end > scroll_start:
            print(f"\033[{scroll_start};{scroll_end}r", end="", flush=True)

    def _position_cursor_for_input(self):
        """Position cursor at the start of the scroll region for input."""
        scroll_start = self.status_lines + 1  # Line 4
        if not self.is_windows:
            # Move cursor to start of scroll region (line 4)
            print(f"\033[{scroll_start};1H", end="", flush=True)
        else:
            # For Windows, position at start of scroll region
            print(f"\033[{scroll_start};1H", end="", flush=True)

    def _draw_status_bar(self):
        """Draw the 3-line status bar at the top."""
        # Move cursor to top
        if not self.is_windows:
            print("\033[H", end="", flush=True)
        else:
            print("\033[1;1H", end="", flush=True)

        # Line 1: Session info (left) and x.ai status (right)
        session_line = f"Isaac Session: {self.session_id}"
        xai_status_line = f"x.ai: {self.xai_status}"
        self._print_status_line_dual(session_line, xai_status_line, 0)

        # Line 2: Current tier and status
        tier_line = f"Tier: {self.current_tier} | Status: Active"
        self._print_status_line(tier_line, 1)

        # Line 3: Connection and shell info with current directory
        shell_info = f"Shell: {self._get_shell_type()} | Dir: {self.working_directory} | Online: {self.connection_status}"
        self._print_status_line(shell_info, 2)

        # Position cursor below status bar
        if not self.is_windows:
            print(f"\033[{self.status_lines + 1};1H", end="", flush=True)
        else:
            print(f"\033[{self.status_lines + 1};1H", end="", flush=True)

    def _print_status_line(self, text: str, line_num: int):
        """Print a status line with background color."""
        # Cyan blue background, white text for status lines
        padded_text = text.ljust(self.terminal_width)
        if not self.is_windows:
            print(f"\033[{line_num + 1};1H\033[1;37;46m{padded_text}\033[0m", end="", flush=True)
        else:
            # Windows - use ANSI colors (modern Windows terminals support them)
            print(f"\033[{line_num + 1};1H\033[1;37;46m{padded_text}\033[0m", flush=True)

    def _print_status_line_dual(self, left_text: str, right_text: str, line_num: int):
        """Print a status line with left and right aligned text."""
        # Calculate available space for text
        total_width = self.terminal_width
        left_width = len(left_text)
        right_width = len(right_text)
        
        # If combined text is too long, truncate right text first
        if left_width + right_width + 3 > total_width:  # +3 for " | "
            available_for_right = total_width - left_width - 3
            if available_for_right > 0:
                right_text = right_text[:available_for_right]
                right_width = len(right_text)
            else:
                right_text = ""
                right_width = 0
        
        # Create the combined line
        if right_text:
            combined_text = f"{left_text} | {right_text}"
        else:
            combined_text = left_text
            
        # Pad to full width
        padded_text = combined_text.ljust(total_width)
        
        # Print with colors
        if not self.is_windows:
            print(f"\033[{line_num + 1};1H\033[1;37;46m{padded_text}\033[0m", end="", flush=True)
        else:
            # Windows - use ANSI colors (modern Windows terminals support them)
            print(f"\033[{line_num + 1};1H\033[1;37;46m{padded_text}\033[0m", flush=True)

    def _get_shell_type(self) -> str:
        """Get current shell type."""
        if self.is_windows:
            return "PowerShell"
        else:
            return "Bash"

    def update_status(self, tier: Optional[str] = None, status: Optional[str] = None,
                     connection: Optional[str] = None):
        """Update status bar information."""
        if tier:
            self.current_tier = tier
        if connection:
            self.connection_status = connection
        self._draw_status_bar()

    def get_main_area_start(self) -> int:
        """Get the line number where main terminal area starts."""
        return self.status_lines + 1

    def clear_main_area(self):
        """Clear everything below the status bar."""
        scroll_start = self.status_lines + 1  # Line 4

        if not self.is_windows:
            # Clear from status bar down to end of scroll region
            for line in range(scroll_start, self.terminal_height + 1):
                print(f"\033[{line};1H\033[K", end="", flush=True)

            # Position cursor at start of cleared area (line 4)
            print(f"\033[{scroll_start};1H", end="", flush=True)
        else:
            # Windows - clear entire screen and redraw status bar
            os.system('cls')
            self._draw_status_bar()
            # Position cursor at start of scroll region (line 4)
            print(f"\033[{scroll_start};1H", end="", flush=True)

    def print_normal_output(self, text: str):
        """Print text as normal terminal output (no special formatting)."""
        print(text, flush=True)

    def print_isaac_response(self, response: str):
        """Print Isaac response as if it's normal terminal output."""
        print(response, flush=True)

    def get_prompt_string(self) -> str:
        """Get the current prompt string for the terminal."""
        if HAS_COLORAMA:
            # Green text on black background for entire prompt
            return f"\033[40;32m$.\033[0m\033[32m>\033[0m "
        else:
            # Fallback without colors
            return "$.> "

    def update_working_directory(self, new_path: str):
        """Update the current working directory display."""
        self.working_directory = Path(new_path)

    def get_terminal_size(self) -> Tuple[int, int]:
        """Get current terminal size."""
        return (self.terminal_width, self.terminal_height)

    def restore_terminal(self):
        """Restore terminal to normal state."""
        if not self.is_windows:
            # Clear status lines
            for line in range(1, self.status_lines + 1):
                print(f"\033[{line};1H\033[K", end="", flush=True)
            # Reset scroll region
            print("\033[r", end="", flush=True)
            # Show cursor
            print("\033[?25h", end="", flush=True)