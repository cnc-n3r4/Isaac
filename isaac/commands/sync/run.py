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

def main():
    """Main entry point for sync command"""
    # Read payload from stdin
    payload = json.loads(sys.stdin.read())

    # Get session
    session = SessionManager()

    # Check for dry-run flag
    args = payload.get('args', [])
    dry_run = '--dry-run' in args

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