#!/usr/bin/env python3
"""
Apropos Command - Search Manual Pages
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
        keyword = args_dict.get("keyword", "")
    except (json.JSONDecodeError, KeyError):
        # Fallback to command line args
        keyword = sys.argv[1] if len(sys.argv) > 1 else ""

    if not keyword:
        print("Usage: /apropos <keyword>", file=sys.stderr)
        sys.exit(1)

    # Search for commands
    generator = get_generator()
    results = generator.search(keyword)

    if not results:
        print(f"No matches found for: {keyword}")
        return

    # Display results
    print(f"Commands matching '{keyword}':")
    print("━" * 70)
    print()

    for result in results:
        trigger = result['trigger']
        version = result['version']
        summary = result['summary']

        # Truncate long summaries
        if len(summary) > 50:
            summary = summary[:47] + "..."

        print(f"{trigger:<20} ({version})  - {summary}")

    print()
    print(f"Found {len(results)} match(es)")
    print(f"Use '/man <command>' for detailed information")


if __name__ == '__main__':
    main()
