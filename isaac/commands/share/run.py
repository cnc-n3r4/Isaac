#!/usr/bin/env python3
"""
Share command for Isaac - Phase 1 Cloud Image Storage
Generate shareable links for uploaded images.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.share.command_impl import ShareCommand


def main():
    """Main entry point for share command"""
    command = ShareCommand()
    run_command(command)


if __name__ == "__main__":
    sys.exit(main() or 0)
