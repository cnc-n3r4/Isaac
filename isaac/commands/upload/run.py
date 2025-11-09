#!/usr/bin/env python3
"""
Upload command for Isaac - Phase 1 Cloud Image Storage
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.upload.command_impl import UploadCommand


def main():
    """Main entry point for upload command"""
    command = UploadCommand()
    run_command(command)


if __name__ == "__main__":
    sys.exit(main() or 0)
