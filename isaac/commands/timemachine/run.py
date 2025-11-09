#!/usr/bin/env python3
"""
Time Machine Command - Timeline navigation and snapshots
"""

import sys
from pathlib import Path

# Add the isaac package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.commands.timemachine.timemachine_command import TimeMachineCommand


def main():
    """Main entry point for time machine command."""
    command = TimeMachineCommand()

    # Get arguments from command line
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    # Execute command
    result = command.execute(args)

    # Print output
    print(result["output"])

    # Exit with appropriate code
    sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
