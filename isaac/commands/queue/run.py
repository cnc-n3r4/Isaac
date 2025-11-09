#!/usr/bin/env python3
"""
Queue Command Handler - Plugin format
"""

import json
import sys
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.core.session_manager import SessionManager


def main():
    """Main entry point for queue command"""
    # Read payload from stdin
    json.loads(sys.stdin.read())

    # Get session
    session = SessionManager()

    # Get queue status
    status = session.get_queue_status()
    pending = session.queue.dequeue_pending(limit=50)

    # Format output
    output = []
    output.append(f"Queue Status: {status['pending']} pending, {status['failed']} failed")
    output.append("")

    if not pending:
        output.append("No commands queued")
    else:
        for cmd in pending:
            output.append(f"#{cmd['id']}: {cmd['command_text'][:60]}...")
            output.append(f"  Type: {cmd['command_type']} | Queued: {cmd['queued_at']}")
            if cmd["target_device"]:
                output.append(f"  Target: {cmd['target_device']}")
            output.append("")

    # Return envelope
    print(json.dumps({"ok": True, "kind": "text", "stdout": "\n".join(output), "meta": {}}))


if __name__ == "__main__":
    main()
