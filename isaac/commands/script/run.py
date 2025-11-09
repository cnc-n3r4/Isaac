"""
Script Command Runner - Natural Language Shell Scripting
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.script.command_impl import ScriptCommand


def main():
    """Main entry point for script command"""
    command = ScriptCommand()
    run_command(command)


if __name__ == "__main__":
    main()
