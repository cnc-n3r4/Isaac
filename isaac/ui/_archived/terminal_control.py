"""
Terminal Control - Traditional terminal interface for Isaac
Provides a clean, traditional terminal experience with status bar
"""

import os
import sys
import time
import datetime
import threading
import re
from typing import Optional
from pathlib import Path

try:
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
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Regex for stripping ANSI escape codes
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')


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
        # Calculate max visible output lines: terminal height - header(5) - prompt(1) - separator(1) - bottom(1) - spacing(1)
        self.max_visible_output_lines = max(1, self.terminal_height - 9)
        
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

    def _draw_status_bar(self):
        """Draw the full Unicode box-drawn header and frame with exact spacing."""
        # Hide cursor and move to top-left
        print("\033[?25l\033[1;1H", end="", flush=True)

        # Ensure minimum width
        total_width = max(self.terminal_width, 80)
        inner_width = total_width - 2  # account for side borders

        # Compute column widths:
        # - 5 columns in header rows
        # - Final 3 status columns have capped widths
        #   per-col: min 6, max 10; total status inner width capped [18, 30]
        status_inner_max = 30
        status_inner_min = 26

        # Start with desired status area ~28% of inner width
        desired_status = int(inner_width * 0.28)
        status_inner = max(status_inner_min, min(status_inner_max, desired_status))

        # Split status area evenly into 3 columns within per-col caps
        per_col = max(6, min(10, status_inner // 3))
        # Recompute status_inner from per_col to keep symmetry
        status_inner = per_col * 3

        # Header has 4 connectors between 5 columns
        connectors = 4
        remaining = max(0, inner_width - connectors - status_inner)

        # Split remaining between col1/col2; let col1 ~60%, col2 ~40%
        w1 = int(remaining * 0.6)
        w2 = remaining - w1
        w3 = per_col
        w4 = per_col
        w5 = per_col

        # Helper to build top/bottom header lines
        def header_top_line():
            return (
                "┌" +
                ("─" * w1) + "╥" +
                ("─" * w2) + "╥" +
                ("─" * w3) + "╥" +
                ("─" * w4) + "╥" +
                ("─" * w5) +
                "┐"
            )

        def header_sep_line():
            return (
                "╞" +
                ("═" * w1) + "╩" +
                ("═" * w2) + "╩" +
                ("═" * w3) + "╩" +
                ("═" * w4) + "╩" +
                ("═" * w5) +
                "╡"
            )

        # Print top header border
        print(header_top_line(), end="", flush=True)
        # Move to next line
        print("\033[2;1H", end="", flush=True)

        # Build header content lines
        machine_name = os.getenv('COMPUTERNAME', 'machine')
        ip_address = self._get_ip_address()

        # Content for three lines
        left1 = f"ISAAC v{self.version}".ljust(w1)
        center1 = f"SID:{self.session_id}".ljust(w2)
        right1a = f" #{self.cloud_status}".ljust(w3)
        right1b = f" #{self.ai_status}".ljust(w4)
        right1c = f" #{self.vpn_status}".ljust(w5)

        left2 = f"{self.user_name}@{machine_name}".ljust(w1)
        last_cmd = self.last_command
        if len(last_cmd) > w2 - 8:
            last_cmd = last_cmd[: max(0, w2 - 11)] + "..."
        center2 = f"Last:'{last_cmd}'".ljust(w2)
        right2a = f" #hist".ljust(w3)
        right2b = f" #Log".ljust(w4)
        right2c = f" {self.validation_level}".ljust(w5)

        wd_label = self.working_directory.as_posix()
        if len(wd_label) > w1 - 4:
            wd_label = wd_label[: max(0, w1 - 7)] + "..."
        left3 = f"PWD:{wd_label}".ljust(w1)
        center3 = f"IP:{ip_address}".ljust(w2)
        right3a = f" #{self.cpu_usage}%".ljust(w3)
        right3b = f" #{self.network_status}".ljust(w4)
        right3c = f" Wrap:{self.wrap_width}".ljust(w5)

        # Helper to print a header row with separators
        def print_header_row(l, c, r1, r2, r3, row_idx):
            line = (
                "│" + l[:w1] + "║" + c[:w2] + "║" + r1[:w3] + "║" + r2[:w4] + "║" + r3[:w5] + "│"
            )
            print(f"\033[{row_idx};1H" + line, end="", flush=True)

        # Three header rows
        print_header_row(left1, center1, right1a, right1b, right1c, 2)
        print_header_row(left2, center2, right2a, right2b, right2c, 3)
        print_header_row(left3, center3, right3a, right3b, right3c, 4)

        # Header separator (heavy)
        print(f"\033[5;1H" + header_sep_line(), end="", flush=True)

        # Save computed widths for later body rendering
        self._frame_cached = {
            'total_width': total_width,
            'inner_width': inner_width,
            'w1': w1, 'w2': w2, 'w3': w3, 'w4': w4, 'w5': w5
        }

        # Position cursor for body start (line 6)
        print(f"\033[6;1H", end="", flush=True)

    def _update_cloud_status(self):
        """Update cloud service status (lightweight, no network in tests)."""
        try:
            # Placeholder logic; real impl would ping backend
            self.cloud_status = "OK"
        except Exception:
            self.cloud_status = "ERR"

    def _update_ai_status(self):
        """Update AI service status (x.ai) with optional network check."""
        if not HAS_REQUESTS:
            # Keep neutral state when requests isn't available
            self.ai_status = "UNK"
            return
        try:
            import requests  # type: ignore
            resp = requests.get("https://status.x.ai/feed.xml", timeout=5)
            if resp.status_code != 200:
                self.ai_status = "OFF"
                return
            # Minimal parse without strict XML reliance
            text = resp.text.lower()
            if "operational" in text or "all systems" in text:
                self.ai_status = "OK"
            elif "degraded" in text:
                self.ai_status = "DEG"
            else:
                self.ai_status = "UNK"
        except Exception:
            self.ai_status = "OFF"

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
                try:
                    import psutil  # type: ignore
                    self.cpu_usage = f"{psutil.cpu_percent(interval=0.1):.0f}"
                except Exception:
                    self.cpu_usage = "--"
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
        # Use ANSI escape codes instead of os.system for better control
        print("\033[2J\033[H", end="", flush=True)  # Clear screen and move cursor to home

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

    def _monitor_statuses(self):
        """Background thread to periodically update all service statuses."""
        while True:
            try:
                self._update_cloud_status()
                self._update_ai_status()
                self._update_vpn_status()
                self._update_system_stats()
                self.mark_header_dirty()
            except Exception:
                pass
            time.sleep(10)

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
            # Yellow prompt for user
            return f"\033[33m$.>\033[0m "
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
        
        # Wrap text to fit inside frame with gutter: inner_width - 1 for gutter
        # inner_width = terminal_width - 2 (for borders), so max text = terminal_width - 3
        max_text_width = self.wrap_width - 3  # -2 for borders, -1 for gutter
        wrapped_lines = self._wrap_text(text, max_text_width)
        
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
        # Retrieve cached frame widths (fallback if not set)
        frame = getattr(self, '_frame_cached', None)
        if not frame:
            self._draw_status_bar()
            frame = self._frame_cached

        frame['total_width']
        inner_width = frame['inner_width']
        
        # DEBUG: Print actual widths (will appear in terminal)
        # print(f"\033[30;1HDEBUG: total_width={total_width}, inner_width={inner_width}", end="", flush=True)

        # Body geometry
        body_start = self.status_lines + 1  # Line 6
        # Lines available for body including prompt, separator, output, bottom border
        max_rows = self.terminal_height

        # 1) Prompt line (with borders)
        prompt_line = body_start
        prompt_inside = f"$> _"
        # Pad to exactly inner_width
        prompt_content = prompt_inside.ljust(inner_width)[:inner_width]
        prompt_line_str = "│" + prompt_content + "│"
        print(f"\033[{prompt_line};1H" + prompt_line_str, end="", flush=True)
        sys.stdout.flush()

        # 2) Prompt separator (heavy full-width)
        sep_line_idx = prompt_line + 1
        sep_line = "╞" + ("═" * inner_width) + "╡"
        print(f"\033[{sep_line_idx};1H" + sep_line, end="", flush=True)
        sys.stdout.flush()

        # 3) Output area starts two lines below header (line 8)
        output_start = sep_line_idx + 1
        output_end = max_rows - 1  # Reserve last row for bottom border

        # Shade gutter column index (second to last char inside frame)
        gutter_char = "░"

        # Compute max visible output lines between output_start and output_end-1 (inclusive)
        self.max_visible_output_lines = max(0, (output_end - output_start))

        # Calculate visible slice based on scroll offset
        total_lines = len(self.current_output)
        start_idx = max(0, total_lines - self.max_visible_output_lines - self.output_scroll_offset)
        end_idx = min(total_lines, start_idx + self.max_visible_output_lines)
        visible_lines = self.current_output[start_idx:end_idx] if total_lines > 0 else []

        # Draw output lines within frame
        for i in range(self.max_visible_output_lines):
            row = output_start + i
            if row >= output_end:
                break
            if i < len(visible_lines):
                content = visible_lines[i]
            else:
                content = ""

            # Strip ANSI codes to measure visible width properly
            visible_content = ANSI_ESCAPE.sub('', content)
            
            # Reserve 1 char for gutter at the right edge
            max_text_width = inner_width - 1
            
            # Truncate visible content if needed, keeping original with ANSI codes if it fits
            if len(visible_content) <= max_text_width:
                text = content  # Keep ANSI codes
            else:
                # Content too long, truncate the visible part (strips ANSI codes)
                text = visible_content[:max_text_width]
            
            # Determine gutter indicator arrows
            is_top_row = (i == 0)
            is_bottom_row = (i == len(visible_lines) - 1) or (i == self.max_visible_output_lines - 1)
            show_up = start_idx > 0
            show_down = end_idx < total_lines
            gutter = gutter_char
            if is_top_row and show_up:
                gutter = "+"
            elif is_bottom_row and show_down:
                gutter = "-"

            # Build inside: pad visible width to exactly inner_width-1, then add gutter
            visible_text = ANSI_ESCAPE.sub('', text)
            padding_needed = max_text_width - len(visible_text)
            text_padded = text + (' ' * padding_needed)
            inside = text_padded + gutter
            print(f"\033[{row};1H│" + inside + "│", end="", flush=True)

        # 4) Bottom border of the frame
        bottom_line = "└" + ("─" * inner_width) + "┘"
        print(f"\033[{self.terminal_height};1H" + bottom_line, end="", flush=True)
        sys.stdout.flush()

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
        """Wrap text to specified width, accounting for ANSI escape codes."""
        lines = []
        for line in text.split('\n'):
            # Strip ANSI codes to measure visible width
            visible_line = ANSI_ESCAPE.sub('', line)
            
            if len(visible_line) <= width:
                # Line fits, keep it as-is with ANSI codes
                if line.strip():
                    lines.append(line)
            else:
                # Line is too long, need to wrap
                # For simplicity, strip ANSI codes when wrapping
                # (More complex: preserve ANSI codes across wrapped lines)
                while len(visible_line) > width:
                    lines.append(visible_line[:width])
                    visible_line = visible_line[width:]
                if visible_line.strip():
                    lines.append(visible_line)
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