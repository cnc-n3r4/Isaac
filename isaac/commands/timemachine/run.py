#!/usr/bin/env python3
"""
Time Machine Command Handler - Timeline navigation and snapshots
"""

import sys
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.timemachine.command_impl import TimeMachineCommand


def main():
    """Main entry point for time machine command"""
    command = TimeMachineCommand()
    run_command(command)


if __name__ == "__main__":
    main()
