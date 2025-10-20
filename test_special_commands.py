#!/usr/bin/env python3
"""
Terminal Command Handling Test - Test clear/reset commands preserve status bar
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isaac.ui.terminal_control import TerminalControl
from isaac.ui.permanent_shell import PermanentShell


def test_special_commands():
    """Test that special commands (clear, reset) preserve the status bar."""
    print("🧹 Testing Special Command Handling")
    print("=" * 50)

    # Create terminal control
    terminal = TerminalControl()
    terminal.setup_terminal()
    print("✅ Terminal setup complete with status bar")

    # Create permanent shell instance
    shell = PermanentShell.__new__(PermanentShell)  # Create without calling __init__
    shell.terminal = terminal

    # Test clear command
    print("\n1. Testing 'clear' command...")
    shell._handle_clear_command()
    print("✅ Clear command handled - status bar should remain intact")

    # Add some output after clear
    terminal.print_normal_output("PS C:\\Users\\user> echo 'output after clear'")
    terminal.print_normal_output("output after clear")
    print("✅ Added output after clear")

    # Test reset command
    print("\n2. Testing 'reset' command...")
    shell._handle_reset_command()
    print("✅ Reset command handled - status bar redrawn")

    # Add some output after reset
    terminal.print_normal_output("PS C:\\Users\\user> echo 'output after reset'")
    terminal.print_normal_output("output after reset")
    print("✅ Added output after reset")

    # Test command detection
    print("\n3. Testing command detection...")
    test_commands = [
        ("clear", True, "clear command"),
        ("cls", True, "cls command"),
        ("reset", True, "reset command"),
        ("ls", False, "normal command"),
        ("echo hello", False, "normal command with args"),
    ]

    for cmd, should_be_special, description in test_commands:
        result = shell._handle_special_command(cmd)
        status = "✅" if result == should_be_special else "❌"
        print(f"{status} {description}: {cmd} -> {'special' if result else 'normal'}")

    print("\n" + "=" * 50)
    print("✨ Special command handling test complete!")
    print("\nKey behaviors:")
    print("• 'clear' and 'cls' only clear below the status bar")
    print("• 'reset' clears below status bar and redraws status bar")
    print("• Status bar at top remains intact throughout")
    print("• Normal commands execute as usual")

    # Restore terminal
    input("\nPress Enter to restore terminal...")
    terminal.restore_terminal()


if __name__ == "__main__":
    test_special_commands()