#!/usr/bin/env python3
"""
Check config.json contents
"""

import os

def check_config_contents():
    """Check the actual contents of config.json"""

    config_path = r"c:\Users\ndemi\.isaac\config.json"

    print(f"Reading config file: {config_path}")

    try:
        with open(config_path, 'r') as f:
            content = f.read()

        print(f"File size: {len(content)} characters")
        print("Raw content:")
        print(repr(content))
        print()
        print("Content (first 200 chars):")
        print(content[:200])

        # Check if it's empty or whitespace
        if not content.strip():
            print("ERROR: File is empty or contains only whitespace!")
            return

        # Try to parse as JSON
        import json
        try:
            config = json.loads(content)
            print("JSON parsing successful!")
            print(f"Keys found: {list(config.keys())}")
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")

    except FileNotFoundError:
        print("File not found!")
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    check_config_contents()