#!/usr/bin/env python3
"""
Pair Command Handler - Collaborative pair programming with AI
"""

import sys
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.pair.command_impl import PairCommand


def main():
    """Main entry point for pair command"""
    command = PairCommand()
    run_command(command)


if __name__ == "__main__":
    main()
