#!/usr/bin/env python3
"""
Learn Command Runner
Executes the self-improving learning system command
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from isaac.commands.base import run_command
from isaac.commands.learn.command_impl import LearnCommand


def main():
    """Main entry point."""
    command = LearnCommand()
    run_command(command)


if __name__ == "__main__":
    main()
