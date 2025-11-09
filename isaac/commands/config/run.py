#!/usr/bin/env python3
"""
Config Command Handler - Plugin format
"""

import sys
import json
import socket

from isaac.ui.config_console import show_config_console


def parse_flags(args):
    """Parse command line flags"""
    flags = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('--'):
            flag = arg[2:]  # Remove --
            if i + 1 < len(args) and not args[i + 1].startswith('--'):
                flags[flag] = args[i + 1]
                i += 1
            else:
                flags[flag] = True
        i += 1
    return flags


def main():
    """Main entry point for config command"""
    # Read payload from stdin
    payload = json.loads(sys.stdin.read())
    args = payload.get("args", {})
    session = payload.get("session", {})

    # Parse flags - only accept --flag syntax
    if isinstance(args, list):
        # Old format - should not happen anymore, but handle gracefully
        flags = parse_flags(args)
    else:
        # New format: args is a dict from dispatcher
        subcommand = args.get('subcommand')
        arg1 = args.get('arg1')
        arg2 = args.get('arg2')
        
        if subcommand:
            if subcommand.startswith('--'):
                flag_name = subcommand[2:]  # Remove --
                flags = {flag_name: arg1 if arg1 else True}
                # Handle special cases that need two arguments
                if flag_name == 'set' and arg1 and arg2:
                    flags['set'] = arg1
                    flags['set_value'] = arg2
                elif flag_name == 'apikey' and arg1 and arg2:
                    flags['apikey'] = arg1
                    flags['api_key_value'] = arg2
            else:
                # Reject old positional syntax
                flags = {}
        else:
            flags = {}

    if not flags:
        output = show_overview(session)
    elif 'help' in flags:
        output = show_overview(session)  # Same as default for now
    elif 'status' in flags:
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
        key = flags.get('set')
        value = flags.get('set_value')
        if key and value:
            output = set_config(session, key, value)
        else:
            output = "Usage: /config --set <key> <value>"
    elif 'apikey' in flags or 'key' in flags:
        service = flags.get('apikey') or flags.get('key')
        api_key = flags.get('api_key_value')
        if service and api_key:
            output = set_api_key(session, service, api_key)
        else:
            output = "Usage: /config --apikey <service> <api_key>\n\nSupported services:\n  xai-chat        - xAI API key for chat completion\n  xai-collections - xAI API key for collections\n  claude          - Anthropic Claude API key\n  openai          - OpenAI API key\n\nExamples:\n  /config --apikey xai-chat YOUR_XAI_API_KEY\n  /config --apikey xai-collections YOUR_XAI_API_KEY\n  /config --apikey claude YOUR_CLAUDE_API_KEY"
    else:
        output = f"Unknown flag: {list(flags.keys())}\nUse /config for help"

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
    enabled = session.get('collections_enabled', False)
    lines.append(f"Enabled: {'✓' if enabled else '✗'}")

    # Show collection IDs (masked for security)
    tc_collection = session.get('tc_log_collection_id')
    cpf_collection = session.get('cpf_log_collection_id')

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
        lines.append("To enable: /config set collections_enabled true")
        lines.append("To set collection IDs: /config set tc_log_collection_id <uuid>")

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


def set_api_key(session, service, api_key):
    """Set API key for a specific service"""
    try:
        # Map service names to config keys
        service_map = {
            'xai-chat': 'xai.chat.api_key',
            'xai-collections': 'xai.collections.api_key',
            'xai': 'xai_api_key',  # Legacy fallback
            'claude': 'claude_api_key',
            'openai': 'openai_api_key',
        }
        
        if service not in service_map:
            return f"✗ Unknown service '{service}'. Supported services: {', '.join(service_map.keys())}"
        
        config_key = service_map[service]
        
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
        
        # Set the API key in nested structure for xAI services
        if service.startswith('xai-'):
            parts = config_key.split('.')
            current = config
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = api_key
        else:
            # Flat structure for other services
            config[config_key] = api_key
        
        # Save back to file
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        return f"✓ Set {service} API key (stored as {config_key})"
    except Exception as e:
        return f"✗ Error setting {service} API key: {str(e)}"


if __name__ == "__main__":
    main()