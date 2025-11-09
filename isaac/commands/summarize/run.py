#!/usr/bin/env python3
"""
Summarize Command Handler - AI-powered content summarization
"""

import sys
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.summarize.command_impl import SummarizeCommand


def main():
    """Main entry point for summarize command"""
    command = SummarizeCommand()
    run_command(command)


if __name__ == "__main__":
    main()
