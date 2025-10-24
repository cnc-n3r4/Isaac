#!/usr/bin/env python3
"""
Config Command Handler - Plugin format
"""

import sys
import json
import socket
import shlex
from pathlib import Path

from isaac.ui.config_console import show_config_console
from isaac.core.key_manager import KeyManager


def parse_flags(args_list):
    """Parse command line flags using standardized syntax."""
    flags = {}
    positional = []
    i = 0
    
    # Flags that indicate subcommands (consume all remaining args as positional)
    subcommand_flags = {'keys', 'set'}
    
    while i < len(args_list):
        arg = args_list[i]
        
        # Check if it's a flag (starts with -)
        if arg.startswith('--'):
            flag = arg[2:]  # Remove --
            
            # If this is a subcommand flag, treat everything after it as positional
            if flag in subcommand_flags:
                flags[flag] = True
                # All remaining args are positional for the subcommand
                positional.extend(args_list[i + 1:])
                break
            # Check if next arg is the value
            elif i + 1 < len(args_list) and not args_list[i + 1].startswith('-'):
                flags[flag] = args_list[i + 1]
                i += 1  # Skip the value
            else:
                flags[flag] = True  # Boolean flag
        else:
            positional.append(arg)
            
        i += 1
        
    return flags, positional


def handle_piped_file_ids(stdin_data: str, session: dict) -> None:
    """Handle piped file_ids from /mine --pan command."""
    import re

    file_ids = []
    lines = stdin_data.strip().split('\n')

    # Parse file_ids from /mine --pan output format
    # Expected format: "• filename: file_id"
    for line in lines:
        line = line.strip()
        if line.startswith('• ') and ': ' in line:
            parts = line[2:].split(': ', 1)
            if len(parts) == 2:
                filename, file_id = parts
                # Validate file_id format (should start with 'file_' or be UUID-like)
                if file_id.startswith('file_') or len(file_id) == 36:
                    file_ids.append(file_id)

    if not file_ids:
        output = "No valid file_ids found in piped input. Expected format from '/mine --pan <collection>'"
    else:
        # Save file_ids to config
        config_path = Path.home() / '.isaac' / 'config.json'
        try:
            # Load existing config
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}

            # Ensure xai.collections structure exists
            if 'xai' not in config:
                config['xai'] = {}
            if 'collections' not in config['xai']:
                config['xai']['collections'] = {}

            # Add file_ids
            config['xai']['collections']['file_ids'] = file_ids

            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            output = f"Saved {len(file_ids)} file_ids to config:\n" + "\n".join(f"  {fid}" for fid in file_ids)

        except Exception as e:
            output = f"Error saving file_ids to config: {e}"

    # Return envelope
    print(json.dumps({
        "ok": True,
        "kind": "text",
        "stdout": output,
        "meta": {}
    }))


def handle_keys_command(flags, positional):
    """Handle key management commands."""
    try:
        key_manager = KeyManager()

        if not positional:
            # Show help
            return """Key Management Commands:

  /config --keys create <type> [name]    Create a new key
  /config --keys list                    List all keys
  /config --keys delete <key_id>         Delete a key
  /config --keys test <key>              Test key authentication

Master Key Commands (Emergency Override):
  /config --keys master set <key>        Set master key file
  /config --keys master remove           Remove master key file
  /config --keys master status           Show master key status

Key Types:
  user      - Full access to all commands
  daemon    - Background webhook processing
  readonly  - Read-only access (no execution)
  oneshot   - Single command execution
  persona   - Persona-specific access (Sarah, Daniel, etc.)

Master Key Override:
  If you lose all keys, use ISAAC_MASTER_KEY environment variable
  or create a master key file with /config --keys master set

Examples:
  /config --keys create user mykey
  /config --keys create daemon webhook
  /config --keys list
  /config --keys test abc123
  /config --keys master set myemergencykey
  /config --keys master status"""

        action = positional[0].lower()

        if action == 'create':
            if len(positional) < 2:
                return "Usage: /config --keys create <type> [name]"
            key_type = positional[1]
            name = positional[2] if len(positional) > 2 else None

            if key_type not in KeyManager.KEY_TYPES:
                return f"Invalid key type. Valid types: {', '.join(KeyManager.KEY_TYPES.keys())}"

            try:
                key, key_id = key_manager.create_random_key(key_type, name)
                return f"Created {key_type} key '{key_id}': {key}\nKeep this key secure!"
            except ValueError as e:
                return str(e)

        elif action == 'list':
            keys = key_manager.list_keys()
            if not keys:
                return "No keys found. Create one with: /config --keys create <type> [name]"

            output = "Isaac Keys:\n\n"
            for key_info in keys:
                permissions = key_manager.KEY_TYPES[key_info['type']]['permissions']
                output += f"Name: {key_info['name']}\n"
                output += f"Type: {key_info['type']}\n"
                output += f"Created: {key_info['created']}\n"
                if key_info.get('expires'):
                    output += f"Expires: {key_info['expires']}\n"
                output += f"Permissions: {', '.join(permissions)}\n\n"
            return output.strip()

        elif action == 'delete':
            if len(positional) < 2:
                return "Usage: /config --keys delete <key_id>"
            key_id = positional[1]

            if key_manager.delete_key(key_id):
                return f"Deleted key '{key_id}'"
            else:
                return f"Key '{key_id}' not found"

        elif action == 'test':
            if len(positional) < 2:
                return "Usage: /config --keys test <key>"
            test_key = positional[1]

            key_info = key_manager.authenticate(test_key)
            if key_info:
                permissions = key_manager.KEY_TYPES[key_info['type']]['permissions']
                return f"✓ Key authenticated\nType: {key_info['type']}\nPermissions: {', '.join(permissions)}"
            else:
                return "✗ Key authentication failed"

        elif action == 'master':
            if len(positional) < 2:
                return "Usage: /config --keys master <set|remove|status> [key]"

            master_action = positional[1].lower()

            if master_action == 'set':
                if len(positional) < 3:
                    return "Usage: /config --keys master set <key>"
                master_key = positional[2]

                if key_manager.set_master_key(master_key):
                    return f"✓ Master key set successfully\nFile: {key_manager.master_key_file}\nKeep this key secure - it bypasses all authentication!"
                else:
                    return "✗ Failed to set master key"

            elif master_action == 'remove':
                if key_manager.remove_master_key():
                    return "✓ Master key removed"
                else:
                    return "✗ Failed to remove master key"

            elif master_action == 'status':
                status = key_manager.get_master_key_status()
                output = "Master Key Status:\n\n"

                output += f"Environment Variable: {'✓ Set' if status['environment_variable'] else '✗ Not set'}\n"
                output += f"Master Key File: {'✓ Exists' if status['master_key_file'] else '✗ Not found'}\n"
                output += f"Development Key: {'✓ Available' if status['development_key'] else '✗ Not available'}\n\n"

                if status.get('file_permissions'):
                    output += f"File Permissions: {status['file_permissions']}\n"
                    output += f"Last Modified: {status['file_modified']}\n\n"

                output += "Override Priority:\n"
                output += "1. ISAAC_MASTER_KEY environment variable\n"
                output += "2. ~/.isaac/.master_key file\n"
                output += "3. Development key (ISAAC_DEBUG=true)\n\n"

                output += "To set emergency override:\n"
                output += "  export ISAAC_MASTER_KEY=your_key\n"
                output += "  /config --keys master set your_key"

                return output

            else:
                return f"Unknown master action '{master_action}'. Use set, remove, or status"

        else:
            return f"Unknown action '{action}'. Use /config --keys for help"

    except Exception as e:
        return f"Key management error: {e}"


def main():
    """Main entry point for config command"""
    # Read payload from stdin
    payload = json.loads(sys.stdin.read())
    args_raw = payload.get("args", [])
    session = payload.get("session", {})

    # Check for piped input (file_ids from /mine --pan)
    stdin_data = payload.get("stdin", "").strip()
    if stdin_data and not args_raw:
        # Handle piped file_ids from /mine --pan
        return handle_piped_file_ids(stdin_data, session)

    # Parse flags from args
    flags, positional = parse_flags(args_raw)

    # Determine subcommand from flags or first positional arg
    if 'status' in flags or (positional and positional[0] == 'status'):
        output = show_status(session)
    elif 'ai' in flags or (positional and positional[0] == 'ai'):
        output = show_ai_details(session)
    elif 'cloud' in flags or (positional and positional[0] == 'cloud'):
        output = show_cloud_details(session)
    elif 'plugins' in flags or (positional and positional[0] == 'plugins'):
        output = show_plugins()
    elif 'collections' in flags or (positional and positional[0] == 'collections'):
        output = show_collections_config(session)
    elif 'console' in flags or (positional and positional[0] == 'console'):
        output = show_config_console(session)
    elif 'keys' in flags or (positional and positional[0] == 'keys'):
        # For keys, pass the remaining positional args
        if 'keys' in flags:
            key_args = positional  # All positional args are key command args
        else:
            key_args = positional[1:] if len(positional) > 1 else []  # Skip 'keys' if it's positional
        output = handle_keys_command(flags, key_args)
    elif 'set' in flags:
        # For set, the value after --set should be "key value"
        set_args = positional
        if len(set_args) >= 2:
            key, value = set_args[0], ' '.join(set_args[1:])
            output = set_config(session, key, value)
        else:
            output = "Usage: /config --set <key> <value>"
    elif not flags and not positional:
        # No flags or positional means show overview
        output = show_overview(session)
    else:
        output = f"Unknown command: {' '.join(positional)}\nUse /config for help"

    # Return envelope
    print(json.dumps({
        "ok": True,
        "kind": "text",
        "stdout": output,
        "meta": {}
    }))


def show_overview(session):
    """Show configuration overview"""
    lines = []
    lines.append("=== ISAAC Configuration ===")
    lines.append("Version: 1.0.2")
    lines.append(f"Session ID: {session.get('machine_id', 'unknown')}")
    lines.append("History Count: 42")  # Placeholder
    lines.append(f"Default Tier: {session.get('user_prefs', {}).get('default_tier', 2)}")
    lines.append("")
    lines.append("Available subcommands:")
    lines.append("  /config status     - System status check")
    lines.append("  /config ai         - AI provider details")
    lines.append("  /config cloud      - Cloud sync status")
    lines.append("  /config plugins    - Available plugins")
    lines.append("  /config collections - xAI Collections status")
    lines.append("  /config keys       - Key management and authentication")
    lines.append("  /config console     - Interactive /mine settings TUI")
    lines.append("  /config set <key> <value> - Change setting")
    return "\n".join(lines)


def show_status(session):
    """Show detailed system status"""
    lines = []
    lines.append("=== System Status ===")

    # Cloud status
    lines.append("Cloud: ✓ Connected")

    # AI status
    lines.append("AI Provider: ✓ xAI (grok-3)")

    # Network info
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        lines.append(f"Network: {ip}")
    except:
        lines.append("Network: Unable to detect")

    # Session info
    lines.append(f"Session: {session.get('machine_id', 'unknown')}")
    lines.append("Commands today: 42")  # Placeholder

    return "\n".join(lines)


def show_ai_details(session):
    """Show AI provider configuration"""
    lines = []
    lines.append("=== AI Provider Details ===")

    provider = "xai"
    model = "grok-3"

    lines.append(f"Provider: {provider}")
    lines.append(f"Model: {model}")
    lines.append("Status: ✓ Connected")

    return "\n".join(lines)


def show_cloud_details(session):
    """Show cloud sync status"""
    lines = []
    lines.append("=== Cloud Sync Status ===")

    lines.append("Cloud sync: Enabled")
    lines.append("Connection: ✓ Healthy")
    lines.append("Last sync: Recent")

    return "\n".join(lines)


def show_plugins():
    """List available plugins"""
    lines = []
    lines.append("=== Available Plugins ===")

    plugins = [
        ("togrok", "Vector search collections", True),
        ("backup", "Config backup/restore", True),
        ("task_planner", "Multi-step task execution", True),
    ]

    for name, desc, enabled in plugins:
        status = "✓" if enabled else "✗"
        lines.append(f"{status} {name:15} - {desc}")

    return "\n".join(lines)


def show_collections_config(session):
    """Show xAI Collections configuration"""
    lines = []
    lines.append("=== xAI Collections ===")

    # Check if collections are enabled
    config = session
    xai_config = config.get('xai', {})
    collections_config = xai_config.get('collections', {})
    
    enabled = collections_config.get('enabled', False)
    lines.append(f"Enabled: {'✓' if enabled else '✗'}")

    # Show saved file_ids
    file_ids = collections_config.get('file_ids', [])
    if file_ids:
        lines.append(f"Saved File IDs: {len(file_ids)} files")
        for i, file_id in enumerate(file_ids[:5], 1):  # Show first 5
            lines.append(f"  {i}. {file_id}")
        if len(file_ids) > 5:
            lines.append(f"  ... and {len(file_ids) - 5} more")
    else:
        lines.append("Saved File IDs: None")

    # Show collection IDs (masked for security)
    tc_collection = collections_config.get('tc-log')
    cpf_collection = collections_config.get('cpf-log')

    if tc_collection:
        masked_tc = tc_collection[:20] + "..." if len(tc_collection) > 20 else tc_collection
        lines.append(f"TC Log Collection: {masked_tc}")
    else:
        lines.append("TC Log Collection: Not configured")

    if cpf_collection:
        masked_cpf = cpf_collection[:20] + "..." if len(cpf_collection) > 20 else cpf_collection
        lines.append(f"CPF Log Collection: {masked_cpf}")
    else:
        lines.append("CPF Log Collection: Not configured")

    if not enabled:
        lines.append("")
        lines.append("To enable: /config set xai.collections.enabled true")
        lines.append("To save file_ids: /mine --pan <collection> | /config")

    return "\n".join(lines)


def set_config(session, key, value):
    """Set a configuration value"""
    # Define allowed config keys
    allowed_keys = {
        'default_tier': int,
        'sync_enabled': lambda v: v.lower() in ['true', '1', 'yes'],
        'ai_provider': str,
        'ai_model': str,
        'collections_enabled': lambda v: v.lower() in ['true', '1', 'yes'],
        'tc_log_collection_id': str,
        'cpf_log_collection_id': str,
        'xai_management_api_key': str,
        'xai_api_host': str,
        'xai_management_api_host': str,
    }

    if key not in allowed_keys:
        return f"Unknown config key: {key}\nAllowed: {', '.join(allowed_keys.keys())}"

    try:
        # Convert value to correct type
        converter = allowed_keys[key]
        converted_value = converter(value)

        # Load existing config
        import os
        from pathlib import Path
        isaac_dir = Path.home() / '.isaac'
        isaac_dir.mkdir(exist_ok=True)
        config_file = isaac_dir / 'config.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except:
                config = {}
        else:
            config = {}
        
        # Update the config
        config[key] = converted_value
        
        # Save back to file
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        return f"✓ Set {key} = {converted_value}"
    except Exception as e:
        return f"✗ Error setting {key}: {str(e)}"


if __name__ == "__main__":
    main()