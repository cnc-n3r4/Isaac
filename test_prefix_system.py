#!/usr/bin/env python3
"""Test script for command prefix system."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from isaac.ui.permanent_shell import PermanentShell

def test_prefix_detection():
    """Test the command prefix detection."""
    shell = PermanentShell()
    
    test_commands = [
        ('ls', ('', 'ls')),
        ('/help', ('/', 'help')),
        ('/status', ('/', 'status')),
        ('!list', ('!', 'list')),
        ('/togrok list', ('/', 'togrok list')),
        ('dir', ('', 'dir')),
        ('', ('', '')),
        ('/', ('/', '')),
        ('!', ('!', '')),
    ]
    
    print("Command Prefix Detection Test:")
    all_passed = True
    
    for cmd, expected in test_commands:
        result = shell._detect_command_prefix(cmd)
        if result == expected:
            print(f"✓ '{cmd}' -> {result}")
        else:
            print(f"✗ '{cmd}' -> {result} (expected {expected})")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success = test_prefix_detection()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")