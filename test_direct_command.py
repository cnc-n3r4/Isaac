#!/usr/bin/env python3
"""Test direct command execution."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Test the new direct command functionality
if __name__ == "__main__":
    # Simulate command line args
    test_args = ["/help"]  # Test with a simple command

    # Import and test the function
    from isaac.__main__ import execute_direct_command

    print("Testing direct command execution...")
    try:
        execute_direct_command(test_args)
        print("Direct command execution test passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()