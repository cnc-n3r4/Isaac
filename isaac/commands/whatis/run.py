#!/usr/bin/env python3
"""
Whatis Command - One-line Command Description
"""

import sys
import json
from pathlib import Path

# Add Isaac to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.core.man_pages import get_generator


def main():
    """Main entry point"""
    # Read payload
    try:
        payload = json.loads(sys.stdin.read())
        args_dict = payload.get("args", {})
        command = args_dict.get("command", "")
    except (json.JSONDecodeError, KeyError):
        # Fallback to command line args
        command = sys.argv[1] if len(sys.argv) > 1 else ""

    if not command:
        print("Usage: /whatis <command>", file=sys.stderr)
        sys.exit(1)

    # Get one-line summary
    generator = get_generator()
    summary = generator.whatis(command)

    if summary:
        print(summary)
    else:
        print(f"{command}: nothing appropriate", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
