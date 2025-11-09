#!/usr/bin/env python3
"""
Apropos Command - Search Manual Pages
"""

import sys
from pathlib import Path

# Add Isaac to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.apropos.command_impl import AproposCommand


def main():
    """Main entry point"""
    command = AproposCommand()
    run_command(command)


if __name__ == "__main__":
    main()
