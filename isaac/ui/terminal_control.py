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

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class TerminalControl:
    """Controls terminal display in traditional style."""

    def __init__(self, session_manager=None):
        """Initialize terminal control."""
        self.session_manager = session_manager
        # Get actual terminal size instead of hardcoding
        self._update_terminal_size()
        self.status_lines = 5  # Top 5 lines for header (borders + 3 content)
        self.working_directory = Path.cwd()
        self.current_tier = "1 (Safe)"
        self.connection_status = "Online"
        self.session_id = self._generate_session_id()
        
        # New header status fields
        self.version = "3.4.2"  # Will be set from package version
        self.user_name = os.getenv('USERNAME', 'user')
        self.system_state = "READY"
        self.current_mode = "EXEC"
        self.cloud_status = "OK"
        self.ai_status = "OK" 
        self.vpn_status = "ON"
        self.history_count = 0
        self.log_enabled = True
        self.validation_level = "T2"
        self.last_command = ""
        self.last_command_status = ""
        self.cpu_usage = "--"
        self.network_status = "OK"
        self.wrap_width = self.terminal_width  # Use actual terminal width
        
        # Body content management
        self.command_prompt = "> "
        self.current_output = []
        self.log_entries = []
        self.max_log_entries = 10
        
        # Scrolling support
        self.output_scroll_offset = 0  # How many lines to scroll back
        self.max_visible_output_lines = 0  # Calculated based on terminal size
        
        # Config mode state
        self.config_mode = False
        self.config_cursor = 0
        self.config_items = [
            {"type": "checkbox", "label": "Enable auto-validate (T>2)", "value": True, "key": "auto_validate"},
            {"type": "checkbox", "label": "Show CPU in header", "value": False, "key": "show_cpu"},
            {"type": "text", "label": "Cloud storage:", "value": "GoDaddy", "key": "cloud_provider"},
            {"type": "text", "label": "AI provider:", "value": "gpt-x", "key": "ai_provider"},
            {"type": "text", "label": "Workspace root:", "value": "~/projects", "key": "workspace_root"},
            {"type": "text", "label": "VPN required:", "value": "Yes/No", "key": "vpn_required"},
        ]
        
        # x.ai status tracking
        self.xai_status = "Loading..."
        self.status_thread = None
        
        # Screen update tracking
        self.header_dirty = False
        self.body_dirty = False
        self.last_header_hash = ""
        
        self._start_status_monitor()

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

    def _start_status_monitor(self):
        """Start background thread to monitor all service statuses."""
        self.status_thread = threading.Thread(
            target=self._monitor_statuses, 
            daemon=True
        )
        self.status_thread.start()

    def _monitor_statuses(self):
        """Background thread to periodically update all service statuses."""
        while True:
            try:
                self._update_cloud_status()
                self._update_ai_status() 
                self._update_vpn_status()
                self._update_system_stats()
                
                # Mark header as dirty to trigger redraw
                self.mark_header_dirty()
                
            except Exception as e:
                # Don't crash the thread on errors
                pass
            
            time.sleep(10)  # Update every 10 seconds

    def _update_cloud_status(self):
        """Update cloud service status."""
        try:
            # For now, simulate cloud status check
            # In real implementation, this would ping GoDaddy API or similar
            self.cloud_status = "OK"
        except Exception:
            self.cloud_status = "ERR"

    def _update_ai_status(self):
        """Update AI service status (x.ai)."""
        if not HAS_REQUESTS:
            self.ai_status = "No requests"
            return
            
        try:
            response = requests.get("https://status.x.ai/feed.xml", timeout=5)
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
                    # Map to simple status
                    if "operational" in status_text.lower():
                        self.ai_status = "OK"
                    elif "degraded" in status_text.lower():
                        self.ai_status = "DEG"
                    else:
                        self.ai_status = "UNK"
                else:
                    self.ai_status = "UNK"
            else:
                self.ai_status = "UNK"
                
        except requests.exceptions.RequestException:
            self.ai_status = "OFF"
        except Exception:
            self.ai_status = "ERR"

    def _update_vpn_status(self):
        """Update VPN status."""
        try:
            # For now, simulate VPN status check
            # In real implementation, this would check VPN connection
            self.vpn_status = "ON"
        except Exception:
            self.vpn_status = "OFF"

    def _update_system_stats(self):
        """Update system statistics like CPU and network."""
        try:
            # Update CPU usage (simplified)
            if HAS_PSUTIL:
                import psutil
                self.cpu_usage = f"{psutil.cpu_percent(interval=0.1):.0f}"
            else:
                self.cpu_usage = "--"
        except Exception:
            self.cpu_usage = "--"

    def setup_terminal(self):
        """Set up the terminal for Isaac experience."""
        # Don't force terminal size - use whatever the user has
        self._update_terminal_size()
        self._clear_screen()
        self._setup_scroll_region()
        
        # Initial full draw
        self._draw_status_bar()
        self.draw_body()
        self._position_cursor_for_input()
        
        # Mark as clean for future updates
        self.header_dirty = False
        self.body_dirty = False
        self.last_header_hash = self._calculate_header_hash()

    def _update_terminal_size(self):
        """Get current terminal dimensions."""
        try:
            import shutil
            size = shutil.get_terminal_size()
            self.terminal_width = size.columns
            self.terminal_height = size.lines
            # Update wrap width to match terminal width
            self.wrap_width = self.terminal_width
        except Exception:
            # Fallback to reasonable defaults if terminal size detection fails
            self.terminal_width = 80
            self.terminal_height = 25
            self.wrap_width = 80

    def _clear_screen(self):
        """Clear the entire screen."""
        os.system('cls')

    def _setup_scroll_region(self):
        """Set up scroll region for the main terminal area."""
        # Set scroll region from line 6 (after header) to bottom of terminal
        scroll_start = self.status_lines + 1  # Line 6
        scroll_end = self.terminal_height     # Bottom of terminal
        if scroll_end > scroll_start:
            print(f"\033[{scroll_start};{scroll_end}r", end="", flush=True)

    def _get_ip_address(self) -> str:
        """Get the local IP address."""
        try:
            import socket
            # Get the local IP by connecting to a dummy address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Connect to Google DNS
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _position_cursor_for_input(self):
        """Position cursor at the start of the scroll region for input."""
        scroll_start = self.status_lines + 1  # Line 6
        # For Windows, position at start of scroll region
        print(f"\033[{scroll_start};1H", end="", flush=True)

    def _draw_status_bar(self):
        """Draw the 3-line header in the new format."""
        # Move cursor to top
        print("\033[1;1H", end="", flush=True)

        # Draw top border
        border = "+" + "-" * (self.terminal_width - 2) + "+"
        self._print_header_line(border, 0, color_code="1;37;44")  # Blue background

        # Line 1: ISAAC vX.Y.Z | SID:xxxx     | [cloud] [AI] [VPN]
        left1 = f"ISAAC v{self.version}"
        center1 = f"SID:{self.session_id}"
        right1 = f"[{self.cloud_status}] [{self.ai_status}] [{self.vpn_status}]"
        self._print_header_line_3col(left1, center1, right1, "", 1)

        # Line 2: <user>@<machine> | Last:'x' | Hist:### [log] [Tier]
        machine_name = os.getenv('COMPUTERNAME', 'machine')
        left2 = f"{self.user_name}@{machine_name}"
        center2 = f"Last:'{self.last_command[:10]}{'...' if len(self.last_command) > 10 else ''}'"
        right2 = f"Hist:{self.history_count:3d} [{'on' if self.log_enabled else 'off'}] [{self.validation_level}]"
        self._print_header_line_3col(left2, center2, right2, "", 2)

        # Line 3: PWD:<cwd> | IP:<ip>         | [CPU] [Net] Wrap:80
        ip_address = self._get_ip_address()
        left3 = f"PWD:{self.working_directory.name[:20]}{'...' if len(self.working_directory.name) > 20 else ''}"
        center3 = f"IP:{ip_address}"
        right3 = f"[{self.cpu_usage}%] [{self.network_status}] Wrap:{self.wrap_width}"
        self._print_header_line_3col(left3, center3, right3, "", 3)

        # Draw bottom border
        self._print_header_line(border, 4, color_code="1;37;44")  # Blue background

        # Position cursor below header (line 6)
        print(f"\033[6;1H", end="", flush=True)

    def _print_status_line(self, text: str, line_num: int):
        """Print a status line with background color."""
        # Cyan blue background, white text for status lines
        padded_text = text.ljust(self.terminal_width)
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
        # Windows - use ANSI colors (modern Windows terminals support them)
        print(f"\033[{line_num + 1};1H\033[1;37;46m{padded_text}\033[0m", flush=True)

    def _print_header_line(self, text: str, line_num: int, color_code: str = "1;37;44"):
        """Print a header line with specified color."""
        padded_text = text.ljust(self.terminal_width)
        print(f"\033[{line_num + 1};1H\033[{color_code}m{padded_text}\033[0m", flush=True)

    def _print_header_line_3col(self, left: str, center: str, right: str, status: str, line_num: int):
        """Print a header line with 3 proportional columns."""
        # Calculate proportional column widths based on terminal width
        # Left: 40%, Center: 35%, Right: 25%
        total_width = self.terminal_width
        left_width = int(total_width * 0.40)
        center_width = int(total_width * 0.35)
        right_width = total_width - left_width - center_width  # Remaining space
        
        # Ensure minimum widths
        left_width = max(left_width, 20)
        center_width = max(center_width, 15)
        right_width = max(right_width, 10)
        
        # Adjust if we exceed total width
        total_calculated = left_width + center_width + right_width
        if total_calculated > total_width:
            # Reduce proportionally
            scale = total_width / total_calculated
            left_width = int(left_width * scale)
            center_width = int(center_width * scale)
            right_width = total_width - left_width - center_width

        # Format columns
        left_padded = left.ljust(left_width)[:left_width]
        center_padded = center.ljust(center_width)[:center_width]
        right_padded = right.ljust(right_width)[:right_width]

        line = f"{left_padded}{center_padded}{right_padded}"[:total_width]
        line = line.ljust(total_width)

        print(f"\033[{line_num + 1};1H\033[1;37;44m{line}\033[0m", flush=True)

    @property
    def is_windows(self) -> bool:
        """Always return True since this is Windows-only."""
        return True

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

    def scroll_output_up(self, lines: int = 1):
        """Scroll output up (show older content)."""
        max_scroll = max(0, len(self.current_output) - self.max_visible_output_lines)
        self.output_scroll_offset = min(max_scroll, self.output_scroll_offset + lines)
        self.mark_body_dirty()
        self.update_screen()

    def scroll_output_down(self, lines: int = 1):
        """Scroll output down (show newer content)."""
        self.output_scroll_offset = max(0, self.output_scroll_offset - lines)
        self.mark_body_dirty()
        self.update_screen()

    def scroll_to_top(self):
        """Scroll to the top of the output."""
        max_scroll = max(0, len(self.current_output) - self.max_visible_output_lines)
        self.output_scroll_offset = max_scroll
        self.mark_body_dirty()
        self.update_screen()

    def scroll_to_bottom(self):
        """Scroll to the bottom of the output (latest content)."""
        self.output_scroll_offset = 0
        self.mark_body_dirty()
        self.update_screen()

    def add_output(self, text: str):
        """Add text to the output area."""
        # Strip the text to remove any trailing newlines
        text = text.rstrip('\n\r')
        
        # Wrap text to terminal width
        wrapped_lines = self._wrap_text(text, self.wrap_width - 2)  # -2 for margin
        
        self.current_output.extend(wrapped_lines)
        
        # Auto-scroll to show latest output
        self.output_scroll_offset = 0
        
        # Keep only recent output (but allow scrolling back)
        max_output_lines = self.terminal_height - self.status_lines - 8  # Leave room for prompt and logs
        if len(self.current_output) > max_output_lines * 2:  # Keep 2x the visible amount for scrolling
            # Remove oldest lines but keep enough for scrolling
            excess = len(self.current_output) - (max_output_lines * 2)
            self.current_output = self.current_output[excess:]
            # Adjust scroll offset if we removed lines
            if self.output_scroll_offset > excess:
                self.output_scroll_offset -= excess
            else:
                self.output_scroll_offset = 0

    def add_log_entry(self, entry_type: str, tier: str, message: str):
        """Add an entry to the chronological log."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"{timestamp} {tier} {entry_type}: {message}"
        
        self.log_entries.append(log_entry)
        
        # Keep only recent log entries
        if len(self.log_entries) > self.max_log_entries:
            self.log_entries.pop(0)

    def draw_body(self):
        """Draw the body area (output/logs or config panel)."""
        if self.config_mode:
            self.draw_config_body()
        else:
            self.draw_normal_body()

    def draw_normal_body(self):
        """Draw the normal body area (output/logs)."""
        # Clear body area (lines 6+)
        body_start = self.status_lines + 1  # Line 6
        body_height = self.terminal_height - body_start
        
        for line in range(body_start, self.terminal_height + 1):
            print(f"\033[{line};1H\033[K", end="", flush=True)
        
        # Calculate how many output lines we can show
        self.max_visible_output_lines = self.terminal_height - self.status_lines - 8  # Leave room for prompt and logs
        
        # Draw prompt (line 6)
        prompt_line = body_start
        prompt_text = f"{self.command_prompt}_"
        print(f"\033[{prompt_line};1H{prompt_text}", end="", flush=True)
        
        # Draw output section (starting line 8)
        output_start = body_start + 2  # Line 8
        if self.current_output:
            # Calculate which lines to show based on scroll offset
            total_lines = len(self.current_output)
            start_idx = max(0, total_lines - self.max_visible_output_lines - self.output_scroll_offset)
            end_idx = min(total_lines, start_idx + self.max_visible_output_lines)
            
            visible_lines = self.current_output[start_idx:end_idx]
            
            for i, line in enumerate(visible_lines):
                output_line = output_start + i
                if output_line <= self.terminal_height - 6:  # Leave room for logs (6 lines)
                    print(f"\033[{output_line};1H{line}", end="", flush=True)
            
            # Show scroll indicator if there's more content
            if start_idx > 0 or end_idx < total_lines:
                indicator_line = output_start + len(visible_lines)
                if indicator_line <= self.terminal_height - 6:
                    if start_idx > 0 and end_idx < total_lines:
                        indicator = f"[↑↓ More content available, {total_lines} total lines]"
                    elif start_idx > 0:
                        indicator = f"[↑ More content above, {total_lines} total lines]"
                    else:
                        indicator = f"[↓ More content below, {total_lines} total lines]"
                    print(f"\033[{indicator_line};1H{indicator}", end="", flush=True)
        
        # Draw log section (bottom area)
        log_start = output_start + self.max_visible_output_lines + 2  # Start logs after output area
        if log_start + self.max_log_entries <= self.terminal_height:  # Only if there's space
            for i, entry in enumerate(self.log_entries[-self.max_log_entries:]):
                log_line = log_start + i
                if log_line <= self.terminal_height:
                    print(f"\033[{log_line};1H{entry}", end="", flush=True)

    def enter_config_mode(self):
        """Enter configuration mode."""
        # Load current config values
        if self.session_manager:
            config = self.session_manager.get_config()
            for item in self.config_items:
                key = item['key']
                if key in config:
                    item['value'] = config[key]
        
        self.config_mode = True
        self.config_cursor = 0
        self.mark_body_dirty()
        self.update_screen()

    def exit_config_mode(self, save: bool = True):
        """Exit configuration mode."""
        if save:
            self._save_config()
        self.config_mode = False
        self.mark_body_dirty()
        self.update_screen()

    def _save_config(self):
        """Save configuration changes."""
        if not self.session_manager:
            return
            
        # Update config with current values
        config = self.session_manager.get_config()
        for item in self.config_items:
            key = item['key']
            value = item['value']
            config[key] = value
            
        # Save the updated config
        try:
            import json
            config_file = Path.home() / '.isaac' / 'config.json'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass  # Silently fail for now

    def navigate_config(self, direction: str):
        """Navigate config menu (tab/up/down)."""
        if direction == "next":
            self.config_cursor = (self.config_cursor + 1) % len(self.config_items)
        elif direction == "prev":
            self.config_cursor = (self.config_cursor - 1) % len(self.config_items)
        self.mark_body_dirty()

    def toggle_config_item(self):
        """Toggle checkbox or edit text field."""
        item = self.config_items[self.config_cursor]
        if item["type"] == "checkbox":
            item["value"] = not item["value"]
        # For text fields, would enter edit mode
        self.mark_body_dirty()

    def draw_config_body(self):
        """Draw the configuration panel body."""
        # Clear body area
        body_start = self.status_lines + 1
        for line in range(body_start, self.terminal_height):
            print(f"\033[{line};1H\033[K", end="", flush=True)
        
        # Draw config items
        for i, item in enumerate(self.config_items):
            line_num = body_start + i
            if line_num >= self.terminal_height - 2:  # Leave room for help
                break
                
            cursor = ">" if i == self.config_cursor else " "
            
            if item["type"] == "checkbox":
                check = "[x]" if item["value"] else "[ ]"
                text = f"{cursor} {check} {item['label']}"
            else:  # text field
                text = f"{cursor} {item['label']} [{item['value']}]"
            
            print(f"\033[{line_num};1H{text}", end="", flush=True)
        
        # Draw help text
        help_line = self.terminal_height - 1
        help_text = "Tab: move   Space: toggle   Enter: save   Esc: cancel"
        print(f"\033[{help_line};1H{help_text}", end="", flush=True)

    def _calculate_header_hash(self) -> str:
        """Calculate a hash of current header state to detect changes."""
        import hashlib
        header_state = f"{self.version}{self.session_id}{self.system_state}{self.current_mode}{self.cloud_status}{self.ai_status}{self.vpn_status}{self.history_count}{self.log_enabled}{self.validation_level}{self.last_command}{self.last_command_status}{self.cpu_usage}{self.network_status}{self.wrap_width}{self.working_directory}"
        return hashlib.md5(header_state.encode()).hexdigest()

    def update_screen(self):
        """Efficiently update the screen, only redrawing changed parts."""
        current_hash = self._calculate_header_hash()
        
        # Update header if it changed
        if self.header_dirty or current_hash != self.last_header_hash:
            self._draw_status_bar()
            self.last_header_hash = current_hash
            self.header_dirty = False
        
        # Update body if needed
        if self.body_dirty:
            self.draw_body()
            self.body_dirty = False

    def mark_header_dirty(self):
        """Mark header as needing redraw."""
        self.header_dirty = True

    def mark_body_dirty(self):
        """Mark body as needing redraw."""
        self.body_dirty = True

    def _wrap_text(self, text: str, width: int) -> list:
        """Wrap text to specified width."""
        lines = []
        for line in text.split('\n'):
            while len(line) > width:
                lines.append(line[:width])
                line = line[width:]
            # Only append if line has non-whitespace content
            if line.strip():  # This filters out blank and whitespace-only lines
                lines.append(line)
        return lines

    def restore_terminal(self):
        """Restore terminal to normal state."""
        # Windows - clear screen and show cursor
        os.system('cls')
        print("\033[?25h", end="", flush=True)

    def get_terminal_size(self):
        """Get current terminal dimensions as (width, height)."""
        self._update_terminal_size()
        return self.terminal_width, self.terminal_height