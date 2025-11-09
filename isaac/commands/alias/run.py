#!/usr/bin/env python3
"""
Alias Command Handler - Manage Unix-to-PowerShell command aliases
"""

import sys
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.alias.command_impl import AliasCommand


def main():
    """Main entry point for alias command"""
    command = AliasCommand()
    run_command(command)


if __name__ == "__main__":
    main()
