#!/usr/bin/env python3
"""
Tasks Command - Entry Point

Standardized entry point using BaseCommand interface.
View and manage background task execution.
"""

import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.tasks.command_impl import TasksCommand


def main():
    """Main entry point for /tasks command"""
    command = TasksCommand()
    run_command(command)


if __name__ == "__main__":
    main()
