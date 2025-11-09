#!/usr/bin/env python3
"""
Pipeline Command Handler - Intelligent workflow automation
"""

import sys
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.pipeline.command_impl import PipelineCommand


def main():
    """Main entry point for pipeline command"""
    command = PipelineCommand()
    run_command(command)


if __name__ == "__main__":
    main()
