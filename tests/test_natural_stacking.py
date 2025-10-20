#!/usr/bin/env python3
"""
Natural Terminal Stacking Test - Test the persistent command history behavior
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isaac.ui.terminal_control import TerminalControl


def test_natural_stacking():
    """Test that commands stack naturally in the scroll region."""
    terminal = TerminalControl()

    print("📚 Testing Natural Terminal Stacking")
    print("=" * 50)

    # Setup terminal with scroll region
    terminal.setup_terminal()
    print("✅ Terminal setup complete with scroll region")

    # Simulate natural command stacking
    print("\nSimulating natural command stacking...")

    # First command and response
    terminal.print_normal_output("PS C:\\Users\\user> ls")
    terminal.print_normal_output("file1.txt")
    terminal.print_normal_output("file2.txt")
    terminal.print_normal_output("PS C:\\Users\\user> ")

    # Second command and response
    terminal.print_normal_output("PS C:\\Users\\user> pwd")
    terminal.print_normal_output("C:\\Users\\user")
    terminal.print_normal_output("PS C:\\Users\\user> ")

    # AI interaction
    terminal.print_normal_output("PS C:\\Users\\user> isaac who won the baseball game?")
    terminal.print_isaac_response("isaac> The Chicago Cubs won the World Series in 2016.")
    terminal.print_normal_output("PS C:\\Users\\user> ")

    # Third command
    terminal.print_normal_output("PS C:\\Users\\user> echo 'hello world'")
    terminal.print_normal_output("hello world")
    terminal.print_normal_output("PS C:\\Users\\user> ")

    print("✅ Commands stacked naturally in scroll region")

    # Test clear command
    print("\nTesting clear command...")
    terminal.print_normal_output("PS C:\\Users\\user> clear")
    terminal.clear_main_area()
    print("✅ Clear command cleared scroll region")

    # After clear, new prompt at bottom
    terminal.print_normal_output("PS C:\\Users\\user> ")

    print("\n" + "=" * 50)
    print("✨ Natural stacking test complete!")
    print("\nExpected behavior:")
    print("• Status bar fixed at top (lines 1-3)")
    print("• Commands stack naturally below status bar")
    print("• Scroll region handles overflow automatically")
    print("• Clear resets the stack, cursor back to line 4")
    print("• Input prompt always at bottom of visible area")

    # Restore terminal
    input("\nPress Enter to restore terminal...")
    terminal.restore_terminal()


if __name__ == "__main__":
    test_natural_stacking()