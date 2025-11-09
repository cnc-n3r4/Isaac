"""
Write Command - Entry Point

Standardized entry point using BaseCommand interface.
"""

import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.write.command_impl import WriteCommand


def main():
    """Main entry point for /write command"""
    command = WriteCommand()
    run_command(command)


if __name__ == "__main__":
    main()
