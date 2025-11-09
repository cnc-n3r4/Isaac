"""
Command Template - Copy this to create new commands

This template provides a standardized structure for implementing new Isaac commands.
Follow this pattern to ensure consistency with the command schema standardization.

USAGE:
1. Copy this file to isaac/commands/<your_command>/command_impl.py
2. Replace YourCommand with your command class name
3. Implement execute() method with your command logic
4. Update get_manifest() with your command's metadata
5. Create isaac/commands/<your_command>/run.py using the entry point pattern
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse


class YourCommand(BaseCommand):
    """Brief description of what your command does"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute your command.

        Args:
            args: Command arguments from command line
            context: Optional execution context containing:
                - piped_input: Data piped from previous command
                - piped_kind: Type of piped data (text, json, etc.)
                - session: Session information (if available)
                - config: Configuration data (if available)

        Returns:
            CommandResponse with success/failure and data/error
        """
        # Parse arguments using FlagParser
        parser = FlagParser(args)

        # Get positional arguments (e.g., file path, query, etc.)
        arg1 = parser.get_positional(0)
        arg2 = parser.get_positional(1)

        # Get flags (e.g., --output, --verbose, -i)
        flag1 = parser.get_flag('flag-name', default=False)
        flag2 = parser.get_flag('another-flag', default='default_value', aliases=['a'])

        # Check for piped input (if your command accepts piped data)
        piped_input = None
        if context and "piped_input" in context:
            piped_input = context["piped_input"]

        # Validate required arguments
        if not arg1:
            return CommandResponse(
                success=False,
                error="Required argument missing. Usage: /yourcommand <arg1>",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        # Execute your command logic
        try:
            # Your implementation here
            result = self._do_work(arg1, arg2, flag1, flag2, piped_input)

            # Return success response
            return CommandResponse(
                success=True,
                data=result,
                metadata={
                    "arg1": arg1,
                    "flag1": flag1,
                    # Add any additional metadata
                }
            )

        except ValueError as e:
            # Handle specific exceptions
            return CommandResponse(
                success=False,
                error=f"Invalid input: {e}",
                metadata={"error_code": "INVALID_INPUT"}
            )

        except Exception as e:
            # Handle unexpected errors
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "EXECUTION_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """
        Get command metadata.

        Returns:
            CommandManifest with command information
        """
        return CommandManifest(
            name="yourcommand",
            description="Brief one-line description of your command",
            usage="/yourcommand <arg1> [arg2] [--flag] [--another-flag VALUE]",
            examples=[
                "/yourcommand example1",
                "/yourcommand example2 --flag",
                "/yourcommand data --another-flag value",
                "cat data.txt | /yourcommand"
            ],
            tier=2,  # 1=safe, 2=needs validation, 3=AI validation, 4=dangerous
            aliases=["yc", "your-alias"],  # Optional short aliases
            category="general"  # general, file, ai, system, etc.
        )

    def _do_work(
        self,
        arg1: str,
        arg2: Optional[str],
        flag1: bool,
        flag2: str,
        piped_input: Optional[str]
    ) -> str:
        """
        Internal helper method for command logic.

        Separate your business logic into helper methods for better organization
        and testability.

        Args:
            arg1: First argument
            arg2: Second argument (optional)
            flag1: Boolean flag
            flag2: String flag value
            piped_input: Data piped from previous command

        Returns:
            Result string
        """
        # Your implementation here
        result = f"Processing {arg1}"

        if arg2:
            result += f" with {arg2}"

        if flag1:
            result += " (flag enabled)"

        if piped_input:
            result += f"\nPiped input: {piped_input[:100]}..."

        return result


# ============================================================================
# ENTRY POINT FILE (isaac/commands/yourcommand/run.py)
# ============================================================================
# Copy the following code to isaac/commands/yourcommand/run.py:

"""
YourCommand - Entry Point

Standardized entry point using BaseCommand interface.
"""

import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.yourcommand.command_impl import YourCommand


def main():
    \"\"\"Main entry point for /yourcommand\"\"\"
    command = YourCommand()
    run_command(command)


if __name__ == "__main__":
    main()

# ============================================================================
# END OF ENTRY POINT FILE
# ============================================================================


# TESTING YOUR COMMAND:
# =====================
# 1. Standalone mode:
#    python isaac/commands/yourcommand/run.py arg1 --flag
#
# 2. Through dispatcher:
#    echo '{"command": "/yourcommand arg1", "manifest": {}}' | python isaac/commands/yourcommand/run.py
#
# 3. With piped input:
#    echo '{"kind": "text", "content": "data", "meta": {"command": "/yourcommand"}}' | python isaac/commands/yourcommand/run.py


# CHECKLIST:
# ==========
# [ ] Implemented execute() method
# [ ] Implemented get_manifest() method
# [ ] Added proper error handling
# [ ] Validated required arguments
# [ ] Added helpful examples
# [ ] Created run.py entry point
# [ ] Tested standalone mode
# [ ] Tested with dispatcher
# [ ] Tested with piped input (if applicable)
# [ ] Added to command registry (if needed)
# [ ] Documented in migration guide
