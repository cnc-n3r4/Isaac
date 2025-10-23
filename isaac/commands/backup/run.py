#!/usr/bin/env python3
"""
Backup Command Handler - Plugin format
"""

import sys
import json


def parse_flags(args_list):
    """Parse command line flags using standardized syntax."""
    flags = {}
    positional = []
    i = 0
    
    while i < len(args_list):
        arg = args_list[i]
        
        # Check if it's a flag (starts with -)
        if arg.startswith('--'):
            flag = arg[2:]  # Remove --
            # Check if next arg is the value
            if i + 1 < len(args_list) and not args_list[i + 1].startswith('-'):
                flags[flag] = args_list[i + 1]
                i += 1  # Skip the value
            else:
                flags[flag] = True  # Boolean flag
        else:
            positional.append(arg)
            
        i += 1
        
    return flags, positional


def main():
    """Main entry point for backup command"""
    # Read payload from stdin
    payload = json.loads(sys.stdin.read())
    args_raw = payload.get("args", [])
    
    # Parse flags from args
    flags, positional = parse_flags(args_raw)

    target = flags.get('target', 'all')

    # Simulate backup operation
    output = f"=== Backup Operation ===\n\n"
    output += f"Target: {target}\n"
    output += "Status: ✓ Backup completed successfully\n"
    output += "Files backed up: 5\n"
    output += "Total size: 2.3 MB\n"
    output += "Destination: ~/.isaac/backups/\n"

    # Return envelope
    print(json.dumps({
        "ok": True,
        "kind": "text",
        "stdout": output,
        "meta": {}
    }))


if __name__ == "__main__":
    main()