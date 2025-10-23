#!/usr/bin/env python3
"""
Sync Command Handler - Plugin format
"""

import sys
import json
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.core.session_manager import SessionManager


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
    """Main entry point for sync command"""
    # Read payload from stdin
    payload = json.loads(sys.stdin.read())
    args_raw = payload.get("args", [])
    
    # Parse flags from args
    flags, positional = parse_flags(args_raw)

    # Get session
    session = SessionManager()

    # Check for dry-run flag
    dry_run = 'dry-run' in flags

    # Trigger sync
    if dry_run:
        # Show what would be synced
        pending = session.queue.dequeue_pending(limit=100)
        output = []
        output.append(f"Dry run: {len(pending)} commands would be synced")
        output.append("")

        for cmd in pending:
            output.append(f"#{cmd['id']}: {cmd['command_text'][:60]}...")
            output.append(f"  Type: {cmd['command_type']} | Queued: {cmd['queued_at']}")
            if cmd['target_device']:
                output.append(f"  Target: {cmd['target_device']}")
            output.append("")
    else:
        # Force sync
        success = session.force_sync()
        if success:
            output = ["Sync completed successfully"]
        else:
            output = ["Sync failed - check connection and try again"]

    # Return envelope
    print(json.dumps({
        "ok": True,
        "kind": "text",
        "stdout": "\n".join(output),
        "meta": {}
    }))


if __name__ == "__main__":
    main()