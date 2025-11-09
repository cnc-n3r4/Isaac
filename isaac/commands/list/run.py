#!/usr/bin/env python3
"""
List Command - Entry Point

Standardized entry point using BaseCommand interface.
"""

import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.list.command_impl import ListCommand


def main():
    """Main entry point for /list command"""
    command = ListCommand()
    run_command(command)


if __name__ == "__main__":
    main()
