"""
AR/VR Command - Entry Point

Standardized entry point using BaseCommand interface.
"""

import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.arvr.command_impl import ARVRCommand


def main():
    """Main entry point for /arvr command"""
    command = ARVRCommand()
    run_command(command)


if __name__ == "__main__":
    main()
