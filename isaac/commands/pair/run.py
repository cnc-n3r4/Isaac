#!/usr/bin/env python3
"""
Pair Command Runner
Executes the collaborative pair programming command
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from isaac.commands.pair.pair_command import PairCommand


def main():
    """Main entry point."""
    try:
        command = PairCommand()
        result = command.execute(sys.argv[1:])

        print(result["output"])

        # Cleanup
        command.cleanup()

        if not result["success"]:
            sys.exit(result["exit_code"])

    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
