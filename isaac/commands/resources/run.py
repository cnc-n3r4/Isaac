#!/usr/bin/env python3
"""
Resources Command Handler - Resource optimization and monitoring
"""

import sys
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.resources.command_impl import ResourcesCommand


def main():
    """Main entry point for resources command"""
    command = ResourcesCommand()
    run_command(command)


if __name__ == "__main__":
    main()
