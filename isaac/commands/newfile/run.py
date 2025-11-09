#!/usr/bin/env python3
"""
Newfile Command - Entry Point

Standardized entry point using BaseCommand interface.
Create files with templates and proper path handling.
"""

import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.newfile.command_impl import NewfileCommand


def main():
    """Main entry point for /newfile command"""
    command = NewfileCommand()
    run_command(command)


if __name__ == "__main__":
    main()
