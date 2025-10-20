#!/usr/bin/env python3
"""
Status Bar Demo - Show the 3-line status bar functionality
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isaac.ui.terminal_control import TerminalControl


def demo_status_bar():
    """Demonstrate the status bar functionality."""
    terminal = TerminalControl()

    print("📊 Isaac Status Bar Demo")
    print("=" * 40)

    # Setup terminal (this will show the status bar)
    terminal.setup_terminal()

    print("✅ Status bar initialized!")
    print("Look at the top 3 lines of your terminal - they should show:")
    print("1. Session info")
    print("2. Current tier and status")
    print("3. Connection and shell info")
    print()
    print("The status bar will update as you use Isaac...")

    # Simulate status updates
    time.sleep(1)
    terminal.update_status(tier="2 (Auto-correct)")
    print("✅ Updated tier to 2 (Auto-correct)")

    time.sleep(1)
    terminal.update_status(connection="Offline")
    print("✅ Updated connection to Offline")

    time.sleep(1)
    terminal.update_status(tier="3 (Validate)", connection="Online")
    print("✅ Updated tier to 3 (Validate) and connection to Online")

    print()
    print("Everything below the status bar looks like normal terminal output!")
    print("PS C:\\Users\\user> ls")
    print("directory contents here...")

    # Restore terminal
    input("\nPress Enter to restore terminal...")
    terminal.restore_terminal()

    print("✨ Status bar demo complete!")


if __name__ == "__main__":
    demo_status_bar()