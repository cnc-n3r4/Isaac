#!/usr/bin/env python3
"""
Whatis Command - One-line Command Description
"""

import sys
from pathlib import Path

# Add Isaac to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.whatis.command_impl import WhatisCommand


def main():
    """Main entry point"""
    command = WhatisCommand()
    run_command(command)


if __name__ == "__main__":
    main()
