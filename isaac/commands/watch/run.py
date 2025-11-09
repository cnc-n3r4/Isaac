#!/usr/bin/env python3
"""
Watch Command Handler - File watching and monitoring
"""

import sys
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.watch.command_impl import WatchCommand


def main():
    """Main entry point for watch command"""
    command = WatchCommand()
    run_command(command)


if __name__ == "__main__":
    main()
