#!/usr/bin/env python3
"""Test that help output matches mine command output."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_help_consistency():
    """Test that /help and /mine outputs are consistent."""
    from isaac.commands.help.run import get_overview_help
    from isaac.commands.mine.run import MineHandler
    from unittest.mock import Mock

    # Get help output
    help_output = get_overview_help(Mock())

    # Get mine command help
    mine_handler = MineHandler(Mock())
    mine_help = mine_handler.run(['--help'])

    print("=== /help output ===")
    print(help_output)
    print("\n=== /mine output ===")
    print(mine_help)

    # Check if mining commands are consistent
    if "Collections (xAI Mining):" in help_output and "--stake" in help_output:
        print("\n✅ Help output updated to match mining metaphor!")
    else:
        print("\n❌ Help output still shows old commands")

    if "--stake" in mine_help and "--claim" in mine_help:
        print("✅ Mine command uses mining metaphor")
    else:
        print("❌ Mine command doesn't use mining metaphor")

if __name__ == "__main__":
    test_help_consistency()