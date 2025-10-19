# Implementation: Terminal UI

## Goal
Create terminal control system: splash screen, header display, prompt handler, and ANSI control.

**Time Estimate:** 40 minutes

**Dependencies:**
- 03_impl_data_files.md (splash_art.txt)
- 06_impl_core_logic_part2.md (SessionManager)

---

## File 1: terminal_control.py

**Path:** `isaac/ui/terminal_control.py`

**Purpose:** ANSI escape codes for terminal control (cursor, colors, scroll regions).

**Complete Implementation:**

```python
"""
Terminal control with ANSI escape codes.
Supports cursor movement, colors, and scroll region locking.
"""

import platform
import shutil


class TerminalControl:
    """ANSI escape code wrapper for terminal control."""
    
    def __init__(self):
        """Initialize terminal control, enable ANSI on Windows."""
        self.is_windows = platform.system() == 'Windows'
        
        if self.is_windows:
            self._enable_ansi_windows()
    
    def _enable_ansi_windows(self):
        """Enable ANSI escape codes on Windows 10+."""
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Enable VT100 mode
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            # If fails, colorama will handle it
            pass
    
    def clear_screen(self):
        """Clear entire screen."""
        print('\033[2J', end='', flush=True)
    
    def move_cursor(self, row: int, col: int):
        """
        Move cursor to position (1-indexed).
        
        Args:
            row: Row number (1 = top)
            col: Column number (1 = left)
        """
        print(f'\033[{row};{col}H', end='', flush=True)
    
    def set_scroll_region(self, top: int, bottom: int):
        """
        Set scrollable region, locks lines outside region.
        
        Args:
            top: Top line of scroll region (1-indexed)
            bottom: Bottom line of scroll region (1-indexed)
        """
        print(f'\033[{top};{bottom}r', end='', flush=True)
    
    def reset_scroll_region(self):
        """Reset to full-screen scrolling."""
        print('\033[r', end='', flush=True)
    
    def hide_cursor(self):
        """Hide cursor."""
        print('\033[?25l', end='', flush=True)
    
    def show_cursor(self):
        """Show cursor."""
        print('\033[?25h', end='', flush=True)
    
    def save_cursor_position(self):
        """Save current cursor position."""
        print('\033[s', end='', flush=True)
    
    def restore_cursor_position(self):
        """Restore saved cursor position."""
        print('\033[u', end='', flush=True)
    
    def get_terminal_size(self) -> tuple:
        """
        Get terminal dimensions.
        
        Returns:
            tuple: (columns, lines)
        """
        size = shutil.get_terminal_size()
        return (size.columns, size.lines)
```

---

## File 2: splash_screen.py

**Path:** `isaac/ui/splash_screen.py`

**Purpose:** Display 5.5 second startup splash (WarGames theme).

**Complete Implementation:**

```python
"""
Splash screen display for Isaac startup.
WarGames-inspired 5.5 second sequence (non-skippable).
"""

import time
from pathlib import Path


def show_splash():
    """
    Display forced 5.5 second splash screen.
    
    Sequence:
    1. "would you like to play... a game?" (1s)
    2. Pause (0.5s)
    3. "nah!!" (1s)
    4. ASCII art + acronym (3s)
    """
    # Line 1: WarGames reference
    print("would you like to play... a game?")
    time.sleep(1.0)
    
    # Pause
    time.sleep(0.5)
    
    # Line 2: Response (centered-ish)
    print("                  nah!!")
    time.sleep(1.0)
    
    # ASCII art
    art_file = Path(__file__).parent.parent / 'data' / 'splash_art.txt'
    if art_file.exists():
        ascii_art = art_file.read_text()
        print(ascii_art)
    else:
        # Fallback if file missing
        print("\n   ISAAC 2.0\n")
    
    time.sleep(3.0)
    
    # Clear screen after splash
    print('\033[2J', end='', flush=True)
```

---

## File 3: header_display.py

**Path:** `isaac/ui/header_display.py`

**Purpose:** Render and update locked header (top 3 lines).

**Complete Implementation:**

```python
"""
Header display for Isaac.
Locks top 3 lines showing shell, session info, and status.
"""

from isaac.ui.terminal_control import TerminalControl


class HeaderDisplay:
    """Manage locked header display (top 3 lines)."""
    
    def __init__(self, session_mgr, shell_adapter):
        """
        Initialize header display.
        
        Args:
            session_mgr: SessionManager instance
            shell_adapter: Shell adapter instance
        """
        self.session = session_mgr
        self.shell = shell_adapter
        self.term = TerminalControl()
    
    def render_locked_header(self):
        """
        Render locked header and set scroll region.
        
        Layout:
        Line 1: Shell version | Machine name
        Line 2: Session info (command count)
        Line 3: Status indicators [✓✓ ONLINE | SYNCED]
        Line 4: Separator ━━━━━━━━━━━━━━━━━
        Lines 5+: Scroll region (interaction area)
        """
        self.term.clear_screen()
        self.term.move_cursor(1, 1)
        
        # Line 1: Shell + Machine
        shell_name = self.shell.name
        machine_name = self.session.machine_id
        print(f"{shell_name} | {machine_name}")
        
        # Line 2: Session info
        cmd_count = self.session.get_command_count()
        print(f"Session loaded ({cmd_count} commands)")
        
        # Line 3: Status
        status = self._get_status_indicator()
        separator_line = "─" * 40
        print(f"{status} {separator_line}")
        
        # Line 4: Heavy separator
        cols, _ = self.term.get_terminal_size()
        separator = "━" * cols
        print(separator)
        
        # Set scroll region (lines 5 to end)
        _, lines = self.term.get_terminal_size()
        self.term.set_scroll_region(5, lines)
        
        # Move cursor to scroll region
        self.term.move_cursor(5, 1)
        print("isaac> Ready.")
        self.term.show_cursor()
    
    def update_status(self):
        """
        Update status line (Line 3) without scrolling.
        Call this after command execution to refresh sync status.
        """
        self.term.save_cursor_position()
        self.term.move_cursor(3, 1)
        
        status = self._get_status_indicator()
        separator_line = "─" * 40
        print(f"\r{status} {separator_line}", end='', flush=True)
        
        self.term.restore_cursor_position()
    
    def _get_status_indicator(self) -> str:
        """
        Get status indicator string.
        
        Returns:
            str: Status like "[✓✓ ONLINE | SYNCED]"
        """
        # MVP: Offline mode (no cloud sync yet)
        return "[OFFLINE]"
        
        # Phase 2: Dynamic status based on cloud sync
        # ai_online = self._check_ai_online()
        # synced = self.session.cloud.is_synced() if self.session.cloud else False
        # 
        # if ai_online and synced:
        #     return "[✓✓ ONLINE | SYNCED]"
        # elif ai_online and not synced:
        #     return "[✓~ ONLINE | SYNCING]"
        # elif not ai_online and synced:
        #     return "[✗✓ OFFLINE | SYNCED]"
        # else:
        #     return "[✗✗ OFFLINE | NOT SYNCED]"
```

---

## File 4: prompt_handler.py

**Path:** `isaac/ui/prompt_handler.py`

**Purpose:** Main input loop with command execution.

**Complete Implementation:**

```python
"""
Prompt handler for Isaac interactive loop.
Handles user input, command routing, and output display.
"""

import sys
from isaac.core.command_router import CommandRouter


class PromptHandler:
    """Handle interactive prompt loop."""
    
    def __init__(self, session_mgr, shell_adapter, header):
        """
        Initialize prompt handler.
        
        Args:
            session_mgr: SessionManager instance
            shell_adapter: Shell adapter instance
            header: HeaderDisplay instance
        """
        self.session = session_mgr
        self.shell = shell_adapter
        self.header = header
        self.router = CommandRouter(session_mgr, shell_adapter)
    
    def run_interactive_loop(self):
        """
        Main input loop.
        
        Handles:
        - User input
        - Command routing
        - Output display
        - History logging
        - Header updates
        """
        while True:
            try:
                # Get user input
                user_input = input("user> ").strip()
                
                # Handle empty input
                if not user_input:
                    continue
                
                # Handle exit commands
                if user_input.lower() in ['exit', 'quit']:
                    print("Isaac > Goodbye!")
                    break
                
                # Route command
                result = self.router.route_command(user_input)
                
                # Display output
                if result.output:
                    print(result.output)
                
                # Log command to history (if it was a shell command, not AI query)
                if not user_input.lower().startswith('isaac '):
                    self.session.add_command(user_input, result)
                
                # Update header status
                self.header.update_status()
                
            except KeyboardInterrupt:
                print("\nIsaac > Use 'exit' to quit.")
            except EOFError:
                print("\nIsaac > Goodbye!")
                break
            except Exception as e:
                print(f"Isaac > Error: {str(e)}")
```

---

## Verification Steps

### 1. Test Terminal Control
```python
from isaac.ui.terminal_control import TerminalControl

term = TerminalControl()

# Test clear screen
term.clear_screen()
print("Screen cleared")

# Test cursor movement
term.move_cursor(5, 10)
print("At (5, 10)")

# Test terminal size
cols, lines = term.get_terminal_size()
print(f"Terminal: {cols} cols x {lines} lines")

# Test scroll region
term.set_scroll_region(5, 20)
print("Scroll region set (5-20)")
term.reset_scroll_region()
print("Scroll region reset")
```

### 2. Test Splash Screen
```python
from isaac.ui.splash_screen import show_splash

# This will display for 5.5 seconds
show_splash()

# Screen should clear after splash
print("Splash complete")
```

### 3. Test Header Display
```python
from isaac.ui.header_display import HeaderDisplay
from isaac.core.session_manager import SessionManager
from isaac.adapters.shell_detector import detect_shell

# Initialize dependencies
config = {}
shell = detect_shell()
session = SessionManager(config, shell)
session.load_from_local()

# Render header
header = HeaderDisplay(session, shell)
header.render_locked_header()

# Header should be visible, scroll region active
# Try typing - text should appear below header
```

### 4. Test Prompt Handler (Manual)
```python
from isaac.ui.prompt_handler import PromptHandler
from isaac.ui.header_display import HeaderDisplay
from isaac.core.session_manager import SessionManager
from isaac.adapters.shell_detector import detect_shell

# Full initialization
config = {}
shell = detect_shell()
session = SessionManager(config, shell)
session.load_from_local()

header = HeaderDisplay(session, shell)
header.render_locked_header()

prompt = PromptHandler(session, shell, header)
prompt.run_interactive_loop()

# Should show:
# user> _
# Type 'ls' → executes
# Type 'exit' → quits
```

---

## Common Pitfalls

⚠️ **ANSI codes not working on Windows**
- **Symptom:** Weird characters instead of colors/formatting
- **Fix:** Ensure colorama installed, or Windows 10+ with ANSI enabled

⚠️ **Header scrolls away**
- **Symptom:** Header disappears after output
- **Fix:** Ensure set_scroll_region() called AFTER printing header

⚠️ **Splash art file not found**
- **Symptom:** Fallback "ISAAC 2.0" shows instead of ASCII art
- **Fix:** Verify splash_art.txt exists in isaac/data/

⚠️ **Cursor position wrong**
- **Symptom:** Text appears in wrong place
- **Fix:** Always flush output with `flush=True` after ANSI codes

⚠️ **Terminal size detection fails**
- **Symptom:** `OSError` on get_terminal_size()
- **Fix:** Default to (80, 24) if shutil.get_terminal_size() fails

---

## Success Signals

✅ TerminalControl initializes without errors  
✅ ANSI codes work on both Windows and Linux  
✅ Splash screen displays for 5.5 seconds  
✅ ASCII art loads from file  
✅ Header displays with 3 lines  
✅ Scroll region locks (header doesn't scroll)  
✅ Prompt accepts input  
✅ Commands execute and display output  
✅ exit/quit commands work  
✅ Header status updates after commands  
✅ Ready for next step (Main Entry Point)

---

**Next Step:** 08_impl_main_entry.md (Create __main__.py to wire everything together)

---

**END OF TERMINAL UI IMPLEMENTATION**
