#!/usr/bin/env python3
"""
Team Command Handler - Team collaboration and resource management
"""

import sys
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.team.command_impl import TeamCommand


def main():
    """Main entry point for team command"""
    command = TeamCommand()
    run_command(command)


if __name__ == "__main__":
    main()
