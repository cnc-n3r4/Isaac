#!/usr/bin/env python3
"""
Pipeline Command - Intelligent workflow automation
"""

import sys
from pathlib import Path

# Add the isaac package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.commands.pipeline.pipeline_command import PipelineCommand


def main():
    """Main entry point for pipeline command."""
    command = PipelineCommand()

    # Get arguments from command line
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    # Execute command
    result = command.execute(args)

    # Print output
    print(result['output'])

    # Exit with appropriate code
    sys.exit(result['exit_code'])


if __name__ == "__main__":
    main()