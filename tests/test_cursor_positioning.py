#!/usr/bin/env python3
"""
Cursor Positioning Test - Verify cursor starts at line 4 and clear works correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isaac.ui.terminal_control import TerminalControl


def test_cursor_positioning():
    """Test that cursor positioning works correctly."""
    terminal = TerminalControl()

    print("🎯 Testing Cursor Positioning")
    print("=" * 40)

    # Setup terminal
    terminal.setup_terminal()
    print("✅ Terminal setup complete")

    # Check initial cursor position should be at line 4
    expected_start_line = terminal.status_lines + 1  # Should be 4
    print(f"Expected cursor start line: {expected_start_line}")
    print(f"Terminal height: {terminal.terminal_height}")

    # Simulate some commands stacking
    print("\nSimulating command stacking...")
    terminal.print_normal_output("PS C:\\Users\\user> ls")
    terminal.print_normal_output("file1.txt")
    terminal.print_normal_output("file2.txt")
    terminal.print_normal_output("PS C:\\Users\\user> pwd")
    terminal.print_normal_output("C:\\Users\\user")
    terminal.print_normal_output("PS C:\\Users\\user> ")

    # Test clear command
    print("\nTesting clear command...")
    terminal.print_normal_output("PS C:\\Users\\user> clear")
    terminal.clear_main_area()
    print("✅ Clear command executed - should position cursor at line 4")

    # After clear, next input should start at line 4
    terminal.print_normal_output("PS C:\\Users\\user> ")

    print("\n" + "=" * 40)
    print("✨ Cursor positioning test complete!")
    print("\nExpected behavior:")
    print("• Initial input cursor at line 4 (after status bar)")
    print("• Commands stack naturally below line 4")
    print("• Clear command clears from line 4 down")
    print("• After clear, cursor back at line 4")

    # Restore terminal
    input("\nPress Enter to restore terminal...")
    terminal.restore_terminal()


if __name__ == "__main__":
    test_cursor_positioning()