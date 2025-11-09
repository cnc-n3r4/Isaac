#!/usr/bin/env python3
"""
Plugin Command Handler - Plugin system management
"""

import sys
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.plugin.command_impl import PluginCommand


def main():
    """Main entry point for plugin command"""
    command = PluginCommand()
    run_command(command)


if __name__ == "__main__":
    main()
