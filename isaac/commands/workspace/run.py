#!/usr/bin/env python3
"""
Workspace Command Handler - Manage isolated workspaces
"""

import sys
import json
from pathlib import Path

from isaac.core.sandbox_enforcer import SandboxEnforcer


def main():
    """Main workspace command handler"""
    # Read payload from stdin (like other commands)
    payload = json.loads(sys.stdin.read())
    args = payload.get("args", [])
    session_data = payload.get("session", {})

    if len(args) < 1:
        print("Usage: /workspace <subcommand> [name]")
        print("Subcommands: create, list, switch, delete")
        return 1

    subcommand = args[0].lower()

    # Initialize sandbox enforcer with session data
    try:
        # Create a mock session from the session data
        class MockSession:
            def __init__(self, session_dict):
                self.config = session_dict.get('config', {})

            def get_config(self):
                """Return the full config dict (no parameters)"""
                return self.config

        session = MockSession(session_data)
        enforcer = SandboxEnforcer(session)
    except Exception as e:
        print(f"Error initializing workspace manager: {e}")
        return 1

    if subcommand == "create":
        if len(args) < 2:
            print("Usage: /workspace create <name> [--venv] [--collection]")
            return 1
        name = args[1]

        # Check for flags
        create_venv = '--venv' in args
        create_collection = '--collection' in args

        try:
            result = enforcer.create_workspace(name, create_venv, create_collection)
            if result:
                print(f"✓ Created workspace '{name}'")
                if create_venv:
                    print(f"✓ Created virtual environment in '{name}/.venv'")
                    print("  Run 'activate_venv.bat' to activate it")
                if create_collection:
                    print(f"✓ Created xAI collection 'workspace-{name}'")
            else:
                print(f"✗ Failed to create workspace '{name}'")
                return 1
        except Exception as e:
            print(f"Error creating workspace: {e}")
            return 1

    elif subcommand == "list":
        try:
            workspaces = enforcer.list_workspaces()
            if workspaces:
                print("Available workspaces:")
                for ws in workspaces:
                    print(f"  - {ws}")
            else:
                print("No workspaces found.")
        except Exception as e:
            print(f"Error listing workspaces: {e}")
            return 1

    elif subcommand == "switch":
        if len(args) < 2:
            print("Usage: /workspace switch <name>")
            return 1
        name = args[1]
        try:
            result = enforcer.switch_workspace(name, session)
            if result:
                print(f"✓ Switched to workspace '{name}'")
            else:
                print(f"✗ Failed to switch to workspace '{name}'")
                return 1
        except Exception as e:
            print(f"Error switching workspace: {e}")
            return 1

    elif subcommand == "delete":
        if len(args) < 2:
            print("Usage: /workspace delete <name> [--preserve-collection]")
            return 1
        name = args[1]

        # Check for preserve collection flag
        preserve_collection = '--preserve-collection' in args

        try:
            # Confirm deletion
            collection_msg = " (preserving collection)" if preserve_collection else " and its collection"
            confirm = input(f"Are you sure you want to delete workspace '{name}'{collection_msg}? (y/N): ")
            if confirm.lower() not in ['y', 'yes']:
                print("Workspace deletion cancelled.")
                return 0

            result = enforcer.delete_workspace(name, preserve_collection)
            if result:
                print(f"✓ Deleted workspace '{name}'")
                if preserve_collection:
                    print("✓ Collection preserved (use /mine --claim to access it)")
            else:
                print(f"✗ Failed to delete workspace '{name}'")
                return 1
        except Exception as e:
            print(f"Error deleting workspace: {e}")
            return 1

    else:
        print(f"Unknown subcommand: {subcommand}")
        print("Available subcommands: create, list, switch, delete")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
