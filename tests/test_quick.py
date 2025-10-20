#!/usr/bin/env python3
"""
Quick test of clear and scrolling behavior
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from isaac.ui.terminal_control import TerminalControl

def test_basic():
    terminal = TerminalControl()

    print("Setting up terminal...")
    terminal.setup_terminal()

    print("Adding test output...")
    for i in range(5):
        terminal.print_normal_output(f"Test line {i+1}")

    print("Testing clear...")
    terminal.clear_main_area()

    print("Clear complete. Status bar should remain.")

if __name__ == "__main__":
    test_basic()