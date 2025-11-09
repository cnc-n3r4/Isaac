#!/usr/bin/env python3
"""
Helper script to migrate commands to standardized schema

Usage: python migrate_command.py <command_name>
"""

import sys
from pathlib import Path


def create_simple_command_impl(cmd_name: str, description: str, category: str = "general", tier: int = 2):
    """Create a simple command_impl.py template"""
    return f'''"""
{cmd_name.capitalize()} Command - Standardized Implementation

{description}
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse


class {cmd_name.capitalize()}Command(BaseCommand):
    """{description}"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute {cmd_name} command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with result or error
        """
        parser = FlagParser(args)

        try:
            # TODO: Implement command logic

            return CommandResponse(
                success=True,
                data="Command executed successfully",
                metadata={{}}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={{"error_code": "EXECUTION_ERROR"}}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="{cmd_name}",
            description="{description}",
            usage="/{cmd_name} [options]",
            examples=[
                "/{cmd_name}",
            ],
            tier={tier},
            aliases=[],
            category="{category}"
        )
'''


def create_run_py(cmd_name: str):
    """Create standardized run.py"""
    class_name = cmd_name.capitalize() + "Command"
    return f'''"""
{cmd_name.capitalize()} Command - Entry Point

Standardized entry point using BaseCommand interface.
"""

import sys
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.{cmd_name}.command_impl import {class_name}


def main():
    """Main entry point for /{cmd_name} command"""
    command = {class_name}()
    run_command(command)


if __name__ == "__main__":
    main()
'''


def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate_command.py <command_name>")
        sys.exit(1)

    cmd_name = sys.argv[1]
    cmd_dir = Path(f"isaac/commands/{cmd_name}")

    if not cmd_dir.exists():
        print(f"Error: Command directory {cmd_dir} does not exist")
        sys.exit(1)

    # Check if already migrated
    if (cmd_dir / "command_impl.py").exists():
        print(f"✓ Command {cmd_name} already migrated")
        sys.exit(0)

    # Get description (placeholder)
    description = f"{cmd_name.capitalize()} command functionality"

    # Create command_impl.py
    impl_path = cmd_dir / "command_impl.py"
    impl_content = create_simple_command_impl(cmd_name, description)
    impl_path.write_text(impl_content)
    print(f"✓ Created {impl_path}")

    # Backup original run.py
    run_py_path = cmd_dir / "run.py"
    if run_py_path.exists():
        backup_path = cmd_dir / "run.py.bak"
        backup_path.write_text(run_py_path.read_text())
        print(f"✓ Backed up original to {backup_path}")

    # Create new run.py
    run_content = create_run_py(cmd_name)
    run_py_path.write_text(run_content)
    print(f"✓ Created {run_py_path}")

    print(f"\n✅ Command {cmd_name} migrated! Now review and implement the logic in command_impl.py")


if __name__ == "__main__":
    main()
