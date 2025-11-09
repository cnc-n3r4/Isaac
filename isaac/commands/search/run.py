#!/usr/bin/env python3
"""
Search Command - Entry Point

Standardized entry point using BaseCommand interface.
Universal search combining glob and grep with smart detection.
"""

import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.search.command_impl import SearchCommand


def main():
    """Main entry point for /search command"""
    command = SearchCommand()
    run_command(command)


if __name__ == "__main__":
    main()
