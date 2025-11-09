#!/usr/bin/env python3
"""
Queue Command Handler - Plugin format
"""

import sys
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.queue.command_impl import QueueCommand


def main():
    """Main entry point for queue command"""
    command = QueueCommand()
    run_command(command)


if __name__ == "__main__":
    main()
