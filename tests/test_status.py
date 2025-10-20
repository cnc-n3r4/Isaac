#!/usr/bin/env python3
"""
Simple Status Bar Test - Test status bar initialization
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isaac.ui.terminal_control import TerminalControl


def test_status_bar():
    """Test status bar functionality."""
    terminal = TerminalControl()

    print("Testing status bar initialization...")

    # Setup terminal
    terminal.setup_terminal()
    print("✅ Terminal setup complete")

    # Test status updates
    terminal.update_status(tier="2 (Auto-correct)")
    print("✅ Status update successful")

    # Test prompt generation
    prompt = terminal.get_prompt_string()
    print(f"✅ Prompt generated: {prompt}")

    # Restore terminal
    terminal.restore_terminal()
    print("✅ Terminal restored")

    print("🎉 All status bar tests passed!")


if __name__ == "__main__":
    test_status_bar()