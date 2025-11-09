"""
Debug Command Runner - Execute debug analysis commands
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.debug.command_impl import DebugCommand


def main():
    """Main entry point for debug command"""
    command = DebugCommand()
    run_command(command)


if __name__ == "__main__":
    main()
