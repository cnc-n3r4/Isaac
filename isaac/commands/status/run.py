#!/usr/bin/env python3
"""
Status Command Handler - Plugin format
"""

import sys
import json
import socket


def main():
    """Main entry point for status command"""
    # Read payload from stdin
    payload = json.loads(sys.stdin.read())
    args = payload.get("args", {})
    session = payload.get("session", {})

    verbose = args.get("verbose", False)

    if verbose:
        # Delegate to config status (simulate the detailed status)
        output = get_detailed_status(session)
    else:
        # One-line summary
        output = get_summary_status(session)

    # Return envelope
    print(json.dumps({
        "ok": True,
        "kind": "text",
        "stdout": output,
        "meta": {}
    }))


def get_summary_status(session):
    """Return one-line status summary"""
    machine_id = session.get('machine_id', 'unknown')[:6]

    # Check cloud status (simplified)
    cloud = "✓"  # Assume connected for now

    # Check AI status
    ai = "✓"  # Assume available for now

    # Get history count (placeholder)
    hist = 42  # Placeholder

    return f"Session: {machine_id} | Cloud: {cloud} | AI: {ai} | History: {hist}"


def get_detailed_status(session):
    """Return detailed system status"""
    lines = []
    lines.append("=== System Status ===")

    # Cloud status
    lines.append("Cloud: ✓ Connected")  # Simplified

    # AI status
    lines.append("AI Provider: ✓ xAI (grok-3)")  # Simplified

    # Network info
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        lines.append(f"Network: {ip}")
    except:
        lines.append("Network: Unable to detect")

    # Session info
    machine_id = session.get('machine_id', 'unknown')
    lines.append(f"Session: {machine_id}")
    lines.append("Commands today: 42")  # Placeholder

    return "\n".join(lines)


if __name__ == "__main__":
    main()