#!/usr/bin/env python3
"""
Clear Command Test - Test that clear/cls commands preserve the status bar
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isaac.ui.terminal_control import TerminalControl


def test_clear_command():
    """Test that clear commands work correctly with status bar."""
    terminal = TerminalControl()

    print("🧹 Testing Clear Command Handling")
    print("=" * 40)

    # Setup terminal
    terminal.setup_terminal()
    print("✅ Terminal setup complete with status bar")

    # Simulate some output
    terminal.print_normal_output("PS C:\\Users\\user> echo 'some output'")
    terminal.print_normal_output("some output")
    terminal.print_normal_output("PS C:\\Users\\user> ls")
    terminal.print_normal_output("file1.txt")
    terminal.print_normal_output("file2.txt")
    print("✅ Added some test output")

    # Test clear command handling
    print("\nTesting clear command...")
    terminal.print_normal_output("PS C:\\Users\\user> clear")

    # This should clear only below the status bar
    terminal.clear_main_area()
    print("✅ Clear command executed - status bar should remain intact")

    # Add some output after clear
    terminal.print_normal_output("PS C:\\Users\\user> echo 'after clear'")
    terminal.print_normal_output("after clear")
    print("✅ Added output after clear")

    print("\n" + "=" * 40)
    print("✨ Clear command test complete!")
    print("The status bar at the top should have remained visible throughout.")

    # Restore terminal
    input("\nPress Enter to restore terminal...")
    terminal.restore_terminal()


if __name__ == "__main__":
    test_clear_command()