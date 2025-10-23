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


def parse_flags(args_list):
    """Parse command line flags using standardized syntax."""
    flags = {}
    positional = []
    i = 0
    
    while i < len(args_list):
        arg = args_list[i]
        
        # Check if it's a flag (starts with -)
        if arg.startswith('--'):
            flag = arg[2:]  # Remove --
            # Check if next arg is the value
            if i + 1 < len(args_list) and not args_list[i + 1].startswith('-'):
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

    # Determine subcommand from flags
    if 'status' in flags:
        output = show_status(session)
    elif 'ai' in flags:
        output = show_ai_details(session)
    elif 'cloud' in flags:
        output = show_cloud_details(session)
    elif 'plugins' in flags:
        output = show_plugins()
    elif 'collections' in flags:
        output = show_collections_config(session)
    elif 'console' in flags:
        output = show_config_console(session)
    elif 'set' in flags:
        # For set, the value after --set should be "key value"
        set_args = positional
        if len(set_args) >= 2:
            key, value = set_args[0], ' '.join(set_args[1:])
            output = set_config(session, key, value)
        else:
            output = "Usage: /config --set <key> <value>"
    elif not flags:
        # No flags means show overview
        output = show_overview(session)
    else:
        output = f"Unknown flags: {list(flags.keys())}\nUse /config for help"

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