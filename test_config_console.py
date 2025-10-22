#!/usr/bin/env python3
"""
Test script for config console
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock session manager
class MockSessionManager:
    def __init__(self):
        self.config = type('Config', (), {'machine_id': 'test'})()
        self.preferences = type('Prefs', (), {'data': {}})()

# Test the config console
from isaac.ui.config_console import show_config_console

session = MockSessionManager()
result = show_config_console(session)
print(f"Result: {result}")