#!/usr/bin/env python3
"""
Status Command Handler - Plugin format
"""

import sys
import json


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


def main():
    """Main entry point for status command"""
    # Read payload from stdin
    payload = json.loads(sys.stdin.read())
    args_raw = payload.get("args", [])
    session = payload.get("session", {})

    # Parse flags from args
    flags, positional = parse_flags(args_raw)

    verbose = 'verbose' in flags or 'help' in flags

    if verbose:
        # Show detailed help
        output = get_detailed_help()
    else:
        # Show comprehensive status display
        output = get_comprehensive_status(session)

    # Return envelope
    print(json.dumps({
        "ok": True,
        "kind": "text",
        "stdout": output,
        "meta": {}
    }))


def get_comprehensive_status(session):
    """Return comprehensive status display"""
    # Import the shared status display utility
    try:
        # Try to import from the expected location
        import os
        isaac_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        import sys
        if isaac_root not in sys.path:
            sys.path.insert(0, isaac_root)
        
        from isaac.ui.status_display import StatusDisplay
        
        # Create a mock session object from the session dict
        class MockSession:
            def __init__(self, session_dict):
                self.config = session_dict.get('config', {})
                self.cloud = None  # Placeholder
                self.command_history = type('obj', (object,), {'commands': session_dict.get('command_history', [])})()
        
        mock_session = MockSession(session)
        status_display = StatusDisplay(mock_session)
        return status_display.get_comprehensive_status()
    except Exception:
        # Fallback to simple status if import fails
        return get_fallback_status(session)


def get_detailed_help():
    """Return detailed help for status command"""
    return """
ISAAC Status Command - Detailed Help

USAGE:
  /status                    # Show comprehensive system status
  /status --help            # Show this detailed help
  /status --verbose         # Legacy verbose mode

The status display shows:
• System version and network information
• AI model and workspace details  
• Inbox and message status
• Cloud sync information
• Session and connectivity status
• Command history count

All information is refreshed in real-time.
""".strip()


def get_fallback_status(session):
    """Fallback status display if StatusDisplay import fails"""
    machine_id = session.get('machine_id', 'unknown')[:6]
    return f"Session: {machine_id} | Status: Basic mode (StatusDisplay unavailable)"


if __name__ == "__main__":
    main()