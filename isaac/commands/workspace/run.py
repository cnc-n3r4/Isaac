#!/usr/bin/env python3
"""
Workspace Command Handler - Manage isolated workspaces
"""

import sys
import json

from isaac.core.sandbox_enforcer import SandboxEnforcer


def parse_command_flags(args: list) -> dict:
    """Parse command arguments using standardized -/-- flag syntax.
    
    Supports:
    - --flag value
    - --flag=value  
    - -f value
    - -f=value
    - --flag (boolean flags)
    
    Returns dict with parsed flags and remaining positional args.
    """
    parsed = {}
    i = 0
    
    while i < len(args):
        arg = args[i]
        
        # Check if it's a flag (starts with -)
        if arg.startswith('--'):
            # Long flag like --flag or --flag=value
            if '=' in arg:
                flag, value = arg.split('=', 1)
                flag = flag[2:]  # Remove --
                parsed[flag] = value
            else:
                flag = arg[2:]  # Remove --
                # Check if next arg is the value
                if i + 1 < len(args) and not args[i + 1].startswith('-'):
                    parsed[flag] = args[i + 1]
                    i += 1  # Skip the value
                else:
                    parsed[flag] = True  # Boolean flag
                    
        elif arg.startswith('-') and len(arg) > 1:
            # Short flag like -f or -f=value
            if '=' in arg:
                flag, value = arg.split('=', 1)
                flag = flag[1:]  # Remove -
                parsed[flag] = value
            else:
                flag = arg[1:]  # Remove -
                # Check if next arg is the value
                if i + 1 < len(args) and not args[i + 1].startswith('-'):
                    parsed[flag] = args[i + 1]
                    i += 1  # Skip the value
                else:
                    parsed[flag] = True  # Boolean flag
        else:
            # Positional argument - ignore for now since workspace uses flags
            pass
                
        i += 1
        
    return parsed


def main():
    """Main workspace command handler"""
    # Read payload from stdin (like other commands)
    payload = json.loads(sys.stdin.read())
    command = payload.get("command", "")
    session_data = payload.get("session", {})

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

    # Parse command flags from the command string
    # Extract args from command (everything after /workspace)
    command = payload.get("command", "")
    if command.startswith("/workspace "):
        args_raw = command[11:].strip()  # Remove "/workspace "
        import shlex
        args_list = shlex.split(args_raw)
    else:
        args_list = []
    
    flags = parse_command_flags(args_list)

    # Handle flag-based arguments
    if flags.get('list'):
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

    elif flags.get('create'):
        name = flags['create']
        create_venv = flags.get('venv', False)
        create_collection = flags.get('collection', False)

        try:
            result = enforcer.create_workspace(name, create_venv, create_collection)
            if result:
                print(f"[OK] Created workspace '{name}'")
                if create_venv:
                    print(f"[OK] Created virtual environment in '{name}/.venv'")
                    print("  Run 'activate_venv.bat' to activate it")
                if create_collection:
                    print(f"[OK] Created xAI collection 'workspace-{name}'")
            else:
                print(f"[FAIL] Failed to create workspace '{name}'")
                return 1
        except Exception as e:
            print(f"Error creating workspace: {e}")
            return 1

    elif flags.get('switch'):
        name = flags['switch']
        try:
            result = enforcer.switch_workspace(name, session)
            if result:
                print(f"[OK] Switched to workspace '{name}'")
            else:
                print(f"[FAIL] Failed to switch to workspace '{name}'")
                return 1
        except Exception as e:
            print(f"Error switching workspace: {e}")
            return 1

    elif flags.get('delete'):
        name = flags['delete']
        preserve_collection = flags.get('preserve_collection', False)

        try:
            # Confirm deletion
            collection_msg = " (preserving collection)" if preserve_collection else " and its collection"
            confirm = input(f"Are you sure you want to delete workspace '{name}'{collection_msg}? (y/N): ")
            if confirm.lower() not in ['y', 'yes']:
                print("Workspace deletion cancelled.")
                return 0

            result = enforcer.delete_workspace(name, preserve_collection)
            if result:
                print(f"[OK] Deleted workspace '{name}'")
                if preserve_collection:
                    print("[OK] Collection preserved (use /mine --claim to access it)")
            else:
                print(f"[FAIL] Failed to delete workspace '{name}'")
                return 1
        except Exception as e:
            print(f"Error deleting workspace: {e}")
            return 1

    elif flags.get('add-collection'):
        name = flags['add-collection']
        try:
            result = enforcer.add_collection_to_workspace(name)
            if result:
                print(f"[OK] Added xAI collection to workspace '{name}'")
            else:
                print(f"[FAIL] Failed to add collection to workspace '{name}'")
                return 1
        except Exception as e:
            print(f"Error adding collection to workspace: {e}")
            return 1

    else:
        print("Usage: /workspace <--subcommand> [options]")
        print("Subcommands:")
        print("  --list                           List all workspaces")
        print("  --create <name>                  Create a new workspace")
        print("  --switch <name>                  Switch to workspace")
        print("  --delete <name>                  Delete workspace")
        print("  --add-collection <name>          Add xAI collection to existing workspace")
        print("Options:")
        print("  --venv                           Create virtual environment")
        print("  --collection                     Create xAI collection")
        print("  --preserve-collection            Preserve collection on delete")
        print("")
        print("Examples:")
        print("  /workspace --list")
        print("  /workspace --create myproject --venv --collection")
        print("  /workspace --add-collection myproject")
        print("  /workspace --switch myproject")
        print("  /workspace --delete oldproject")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
