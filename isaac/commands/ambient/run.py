#!/usr/bin/env python3
"""
Ambient Command Runner
Executes the ambient intelligence command
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from isaac.commands.ambient.ambient_command import AmbientCommand


def main():
    """Main entry point."""
    try:
        command = AmbientCommand()
        result = command.execute(sys.argv[1:])

        print(result['output'])

        if not result['success']:
            sys.exit(result['exit_code'])

    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()