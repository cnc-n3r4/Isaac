#!/usr/bin/env python3
"""
File Command - Entry Point

Standardized entry point using BaseCommand interface.
Unified file operations: read, write, edit, append.
"""

import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.file.command_impl import FileCommand


def main():
    """Main entry point for /file command"""
    command = FileCommand()
    run_command(command)


if __name__ == "__main__":
    main()
