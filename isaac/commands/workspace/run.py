#!/usr/bin/env python3
"""
Workspace Command Handler - Manage isolated workspaces
"""

import sys
from pathlib import Path

from isaac.core.sandbox_enforcer import SandboxEnforcer


def main():
    """Main workspace command handler"""
    args = sys.argv[1:]

    if len(args) < 1:
        print("Usage: /workspace <subcommand> [name]")
        print("Subcommands: create, list, switch, delete")
        return 1

    subcommand = args[0].lower()

    # Initialize sandbox enforcer (will get session from environment)
    try:
        # For now, create a minimal session manager mock
        class MockSession:
            def get_config(self, key=None, default=None):
                # Load from config file
                config_path = Path.home() / '.isaac' / 'config.json'
                if config_path.exists():
                    import json
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    if key is None:
                        return config
                    return config.get(key, default)
                return default if key is not None else {}

        session = MockSession()
        enforcer = SandboxEnforcer(session)
    except Exception as e:
        print(f"Error initializing workspace manager: {e}")
        return 1

    if subcommand == "create":
        if len(args) < 2:
            print("Usage: /workspace create <name>")
            return 1
        name = args[1]
        try:
            result = enforcer.create_workspace(name)
            if result:
                print(f"✓ Created workspace '{name}'")
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
            result = enforcer.switch_workspace(name)
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
            print("Usage: /workspace delete <name>")
            return 1
        name = args[1]
        try:
            # Confirm deletion
            confirm = input(f"Are you sure you want to delete workspace '{name}'? (y/N): ")
            if confirm.lower() not in ['y', 'yes']:
                print("Workspace deletion cancelled.")
                return 0

            result = enforcer.delete_workspace(name)
            if result:
                print(f"✓ Deleted workspace '{name}'")
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