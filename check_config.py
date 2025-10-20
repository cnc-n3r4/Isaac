#!/usr/bin/env python3
"""
Check for Isaac config.json file
"""

import os
import json
from pathlib import Path

def check_isaac_config():
    """Check for and display Isaac config.json"""

    # Check the path the user specified
    config_path = Path("c:/Users/ndemi/.isaac/config.json")

    print(f"Checking for config at: {config_path}")
    print(f"Path exists: {config_path.exists()}")

    if config_path.exists():
        print(f"File size: {config_path.stat().st_size} bytes")

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            print("\nConfig contents:")
            print(json.dumps(config, indent=2))

            # Check for AI-related keys
            ai_keys = ['claude_api_key', 'claude_api_url', 'ai_enabled']
            print(f"\nAI-related keys found:")
            for key in ai_keys:
                if key in config:
                    if 'key' in key.lower():
                        print(f"  {key}: [REDACTED] (length: {len(str(config[key]))})")
                    else:
                        print(f"  {key}: {config[key]}")
                else:
                    print(f"  {key}: NOT FOUND")

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
        except Exception as e:
            print(f"Error reading file: {e}")
    else:
        print("Config file not found!")

        # Check if the directory exists
        config_dir = config_path.parent
        print(f"Config directory exists: {config_dir.exists()}")

        if config_dir.exists():
            print("Files in config directory:")
            for item in config_dir.iterdir():
                print(f"  {item.name} ({'dir' if item.is_dir() else 'file'})")

if __name__ == "__main__":
    check_isaac_config()