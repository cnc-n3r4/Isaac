# isaac/commands/msg/run.py

"""
Message Queue Management Command - Plugin Entry Point

Provides interface for viewing and managing AI assistant notifications.
/msg command with support for filtering by type and acknowledging messages.
"""

import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from isaac.core.message_queue import MessageQueue, MessageType


def main():
    """Main entry point for msg command"""
    # Read payload from stdin (dispatcher sends args this way)
    import json
    import select
    
    # Check if stdin has data (running through dispatcher)
    # On Windows, select doesn't work with stdin, so use a different approach
    import os
    if os.name == 'nt':
        # Windows: try to read with timeout
        import msvcrt
        has_stdin = msvcrt.kbhit() or not sys.stdin.isatty()
    else:
        # Unix: use select
        has_stdin = select.select([sys.stdin], [], [], 0)[0]
    
    if has_stdin:
        # Running through dispatcher - read JSON payload
        try:
            payload = json.loads(sys.stdin.read())
            command = payload.get("command", "/msg")
            # Extract arguments from command (everything after "/msg")
            parts = command.split()
            if len(parts) > 1:
                args = parts[1:]
            else:
                args = []
        except (json.JSONDecodeError, KeyError):
            args = sys.argv[1:]
    else:
        # Running directly - use command line args
        args = sys.argv[1:]

    # Initialize message queue
    try:
        message_queue = MessageQueue()
    except Exception as e:
        print(f"Error initializing message queue: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse arguments
    show_system = False
    show_code = False
    show_all = False
    ack_id = None
    ack_all = False
    ack_type = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ['--sys', '-s']:
            show_system = True
        elif arg in ['--code', '-c']:
            show_code = True
        elif arg in ['--all', '-a']:
            show_all = True
        elif arg == '--ack' and i + 1 < len(args):
            try:
                ack_id = int(args[i + 1])
                i += 1
            except ValueError:
                print("Error: --ack requires a valid message ID", file=sys.stderr)
                sys.exit(1)
        elif arg == '--ack-all':
            ack_all = True
            if i + 1 < len(args) and args[i + 1] in ['--sys', '--code']:
                ack_type = MessageType.SYSTEM if args[i + 1] == '--sys' else MessageType.CODE
                i += 1
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
            print("Usage: /msg [--sys|--code|--all] [--ack ID|--ack-all]", file=sys.stderr)
            sys.exit(1)
        i += 1

    # Handle acknowledgments first
    if ack_id is not None:
        if message_queue.acknowledge_message(ack_id):
            print(f"✓ Message {ack_id} acknowledged")
        else:
            print(f"✗ Message {ack_id} not found or already acknowledged")
            sys.exit(1)

    if ack_all:
        count = message_queue.acknowledge_all(ack_type)
        if ack_type:
            type_name = ack_type.value
            print(f"✓ Acknowledged {count} {type_name} message(s)")
        else:
            print(f"✓ Acknowledged {count} message(s)")

    # Determine what to show
    if show_all or (not show_system and not show_code):
        # Show all messages (default behavior)
        messages = message_queue.get_messages(status='pending')
        _display_messages(messages, "All Messages")
    else:
        # Show specific types
        if show_system:
            system_msgs = message_queue.get_messages(
                message_type=MessageType.SYSTEM, status='pending'
            )
            _display_messages(system_msgs, "System Messages")

        if show_code:
            code_msgs = message_queue.get_messages(
                message_type=MessageType.CODE, status='pending'
            )
            _display_messages(code_msgs, "Code Messages")


def _display_messages(messages, title):
    """Display messages in a formatted way."""
    if not messages:
        print(f"\n{title}:")
        print("  No pending messages")
        return

    print(f"\n{title} ({len(messages)} pending):")
    print("-" * 60)

    for msg in messages:
        # Priority indicator (text-based for Windows compatibility)
        priority = msg['priority']
        if priority == 'urgent':
            pri_indicator = "[URGENT]"
        elif priority == 'high':
            pri_indicator = "[HIGH]"
        elif priority == 'normal':
            pri_indicator = "[NORMAL]"
        else:
            pri_indicator = "[LOW]"

        # Type indicator
        msg_type = msg['message_type']
        type_indicator = "!" if msg_type == 'system' else "¢"

        # Format message
        print(f"{pri_indicator} {type_indicator} [{msg['id']}] {msg['title']}")

        # Show content if present
        if msg['content']:
            # Truncate long content
            content = msg['content']
            if len(content) > 100:
                content = content[:97] + "..."
            print(f"    {content}")

        # Show metadata if present
        if msg['metadata']:
            metadata_items = []
            for key, value in msg['metadata'].items():
                if isinstance(value, (str, int, float, bool)):
                    metadata_items.append(f"{key}={value}")
            if metadata_items:
                print(f"    Metadata: {', '.join(metadata_items)}")

        print()


if __name__ == "__main__":
    main()