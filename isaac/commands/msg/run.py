#!/usr/bin/env python3
"""
Msg Command - Entry Point

Standardized entry point using BaseCommand interface.
Message queue management for AI notifications.
"""

import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.msg.command_impl import MsgCommand


def main():
    """Main entry point for /msg command"""
    command = MsgCommand()
    run_command(command)


if __name__ == "__main__":
    main()
