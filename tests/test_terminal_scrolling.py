#!/usr/bin/env python3
"""
Terminal Scrolling Test - Test traditional terminal scrolling with status bar
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isaac.ui.terminal_control import TerminalControl


def test_terminal_scrolling():
    """Test traditional terminal scrolling with status bar redraw."""
    terminal = TerminalControl()

    print("📜 Testing Traditional Terminal Scrolling")
    print("=" * 50)

    # Setup terminal
    terminal.setup_terminal()
    print("✅ Terminal setup complete")

    # Simulate a command execution cycle
    print("\nSimulating command execution with scrolling...")

    # First command
    terminal.print_normal_output("PS C:\\Users\\user> echo 'First command output'")
    terminal.print_normal_output("First command output")
    terminal.print_normal_output("PS C:\\Users\\user> ")

    # Redraw status bar (as would happen after command)
    terminal._draw_status_bar()
    print("✅ Status bar redrawn after first command")

    # Second command with more output
    terminal.print_normal_output("PS C:\\Users\\user> ls -la")
    for i in range(15):  # Generate output that should scroll
        terminal.print_normal_output(f"file{i}.txt    2023-10-19 10:{i:02d}    {i*100} bytes")
    terminal.print_normal_output("PS C:\\Users\\user> ")

    # Redraw status bar
    terminal._draw_status_bar()
    print("✅ Status bar redrawn after second command")

    # Third command
    terminal.print_normal_output("PS C:\\Users\\user> pwd")
    terminal.print_normal_output("C:\\Users\\user")
    terminal.print_normal_output("PS C:\\Users\\user> ")

    # Redraw status bar
    terminal._draw_status_bar()
    print("✅ Status bar redrawn after third command")

    print("\n" + "=" * 50)
    print("✨ Terminal scrolling test complete!")
    print("\nExpected behavior:")
    print("• Status bar appears at top initially")
    print("• Commands execute and output scrolls naturally")
    print("• Status bar gets redrawn after each command")
    print("• Scrolling works like traditional terminal")

    # Restore terminal
    input("\nPress Enter to restore terminal...")
    terminal.restore_terminal()


if __name__ == "__main__":
    test_terminal_scrolling()