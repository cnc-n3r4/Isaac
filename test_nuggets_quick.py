#!/usr/bin/env python3
"""Quick test of nuggets functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isaac.commands.mine.run import MineHandler
from unittest.mock import Mock

def test_nuggets():
    """Test nuggets functionality."""
    print("Testing nuggets functionality...")

    # Create handler with mock session manager
    handler = MineHandler(Mock())

    # Test empty nuggets list
    handler.session_manager.get_config.return_value = {}
    result = handler._list_nuggets()
    print("Empty nuggets result:", result[:100] + "...")

    # Test nugget name creation
    name = handler._create_nugget_name("test file (2023).mp3", [])
    print("Created nugget name:", name)

    # Test uniqueness
    name2 = handler._create_nugget_name("test file (2023).mp3", ["test_file__2023_"])
    print("Created unique nugget name:", name2)

    print("Nuggets functionality test completed!")

if __name__ == "__main__":
    test_nuggets()