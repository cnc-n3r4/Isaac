#!/usr/bin/env python3
"""
Scroll Region Test - Test that terminal scrolling works properly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isaac.ui.terminal_control import TerminalControl


def test_scroll_region():
    """Test that the scroll region works properly."""
    terminal = TerminalControl()

    print("📜 Testing Terminal Scroll Region")
    print("=" * 40)

    # Setup terminal
    terminal.setup_terminal()
    print("✅ Terminal setup complete with scroll region")

    # Show current terminal size
    width, height = terminal.get_terminal_size()
    print(f"Terminal size: {width}x{height}")
    print(f"Status lines: {terminal.status_lines}")
    print(f"Scroll region should start at line: {terminal.status_lines + 1}")

    # Fill the scrollable area with content
    print("\nFilling scrollable area with test content...")
    print("(This should cause scrolling if the scroll region is working)")

    scrollable_lines = height - terminal.status_lines - 1  # Available lines for scrolling
    print(f"Available scrollable lines: {scrollable_lines}")

    for i in range(1, scrollable_lines + 10):  # More lines than should fit
        terminal.print_normal_output(f"Line {i}: This is test output to check scrolling behavior")
        if i <= 5 or i >= scrollable_lines + 5:  # Show first few and last few
            print(f"[Printed line {i}]")

    print("\n✅ Filled terminal with content")

    # Test that status bar is still visible
    print("Status bar should still be visible at the top!")

    # Test clear command
    print("\nTesting clear command...")
    terminal.clear_main_area()
    print("✅ Cleared main area - status bar should remain")

    # Add a few more lines
    for i in range(1, 5):
        terminal.print_normal_output(f"After clear - Line {i}")

    print("\n" + "=" * 40)
    print("✨ Scroll region test complete!")
    print("\nExpected behavior:")
    print("• Status bar (lines 1-3) remains fixed")
    print("• Content below scrolls when it exceeds terminal height")
    print("• Clear only affects the scrollable area")

    # Restore terminal
    input("\nPress Enter to restore terminal...")
    terminal.restore_terminal()


if __name__ == "__main__":
    test_scroll_region()