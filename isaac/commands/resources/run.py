#!/usr/bin/env python3
"""
Resources Command - Resource optimization and monitoring
"""

import sys
from pathlib import Path

# Add the isaac package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.commands.resources.resources_command import ResourcesCommand


def main():
    """Main entry point for resources command."""
    command = ResourcesCommand()

    # Get arguments from command line (space-separated string)
    args = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""

    # Execute command
    try:
        result = command.execute(args)

        # Print output
        print(result)

        # Exit with success
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
