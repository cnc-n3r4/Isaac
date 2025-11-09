#!/usr/bin/env python3
"""
Restore Command - Entry Point

Standardized entry point using BaseCommand interface.
"""

import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.restore.command_impl import RestoreCommand


def main():
    """Main entry point for /restore command"""
    command = RestoreCommand()
    run_command(command)


if __name__ == "__main__":
    main()
