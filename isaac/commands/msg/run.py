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

    # Check if stdin has data (running through dispatcher)
    # On Windows, select doesn't work with stdin, so use a different approach
    import os
    import select

    if os.name == "nt":
        # Windows: try to read with timeout
        import msvcrt

        has_stdin = msvcrt.kbhit() or not sys.stdin.isatty()
    else:
        # Unix: use select
        has_stdin = select.select([sys.stdin], [], [], 0)[0]

    parsed_args = {}
    manual_args = []

    if has_stdin:
        # Running through dispatcher - read JSON payload
        try:
            payload = json.loads(sys.stdin.read())
            command = payload.get("command", "/msg")
            parsed_args = payload.get("args", {})

            # If no parsed args, fall back to extracting from command string
            if not parsed_args:
                parts = command.split()
                if len(parts) > 1:
                    manual_args = parts[1:]
        except (json.JSONDecodeError, KeyError):
            manual_args = sys.argv[1:]
    else:
        # Running directly - use command line args
        manual_args = sys.argv[1:]

    # Initialize message queue
    try:
        message_queue = MessageQueue()
    except Exception as e:
        print(f"Error initializing message queue: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse arguments - prefer parsed args from payload, fall back to manual parsing
    show_system = False
    show_code = False
    show_all = False
    ack_id = None
    ack_all = False
    ack_type = None
    read_id = None
    delete_id = None
    clear_all = False
    clear_type = None
    auto_run = False

    # Check if we have parsed args from dispatcher
    if parsed_args:
        # Use parsed args from dispatcher
        if parsed_args.get("filter") == "--sys":
            show_system = True
        elif parsed_args.get("filter") == "--code":
            show_code = True
        elif parsed_args.get("filter") == "--all":
            show_all = True

        if parsed_args.get("ack"):
            try:
                ack_id = int(parsed_args["ack"])
            except ValueError:
                print("Error: --ack requires a valid message ID", file=sys.stderr)
                sys.exit(1)

        if parsed_args.get("ack_all"):
            ack_all = True
            if parsed_args["ack_all"] == "--sys":
                ack_type = MessageType.SYSTEM
            elif parsed_args["ack_all"] == "--code":
                ack_type = MessageType.CODE

        if parsed_args.get("read"):
            try:
                read_id = int(parsed_args["read"])
            except ValueError:
                print("Error: --read requires a valid message ID", file=sys.stderr)
                sys.exit(1)

        if parsed_args.get("delete"):
            try:
                delete_id = int(parsed_args["delete"])
            except ValueError:
                print("Error: --delete requires a valid message ID", file=sys.stderr)
                sys.exit(1)

        if parsed_args.get("clear"):
            clear_all = True
            if parsed_args["clear"] == "--sys":
                clear_type = ("type", MessageType.SYSTEM)
            elif parsed_args["clear"] == "--code":
                clear_type = ("type", MessageType.CODE)
            elif parsed_args["clear"] == "--ack":
                clear_type = ("status", "acknowledged")

        if parsed_args.get("auto_run"):
            auto_run = True
    else:
        # Manual argument parsing for direct execution
        args = manual_args
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ["--sys", "-s"]:
                show_system = True
            elif arg in ["--code", "-c"]:
                show_code = True
            elif arg in ["--all", "-a"]:
                show_all = True
            elif arg == "--ack" and i + 1 < len(args):
                try:
                    ack_id = int(args[i + 1])
                    i += 1
                except ValueError:
                    print("Error: --ack requires a valid message ID", file=sys.stderr)
                    sys.exit(1)
            elif arg == "--ack-all":
                ack_all = True
                if i + 1 < len(args) and args[i + 1] in ["--sys", "--code"]:
                    ack_type = MessageType.SYSTEM if args[i + 1] == "--sys" else MessageType.CODE
                    i += 1
            elif arg == "--read" and i + 1 < len(args):
                try:
                    read_id = int(args[i + 1])
                    i += 1
                except ValueError:
                    print("Error: --read requires a valid message ID", file=sys.stderr)
                    sys.exit(1)
            elif arg == "--delete" and i + 1 < len(args):
                try:
                    delete_id = int(args[i + 1])
                    i += 1
                except ValueError:
                    print("Error: --delete requires a valid message ID", file=sys.stderr)
                    sys.exit(1)
            elif arg == "--clear":
                clear_all = True
                if i + 1 < len(args) and args[i + 1] in ["--sys", "--code", "--ack"]:
                    if args[i + 1] == "--sys":
                        clear_type = ("type", MessageType.SYSTEM)
                    elif args[i + 1] == "--code":
                        clear_type = ("type", MessageType.CODE)
                    elif args[i + 1] == "--ack":
                        clear_type = ("status", "acknowledged")
                    i += 1
            elif arg in ["--auto-run", "-ar"]:
                auto_run = True
            else:
                print(f"Unknown argument: {arg}", file=sys.stderr)
                print("Usage: /msg [OPTIONS]", file=sys.stderr)
                print("  --sys, -s              Show system messages", file=sys.stderr)
                print("  --code, -c             Show code messages", file=sys.stderr)
                print("  --all, -a              Show all messages", file=sys.stderr)
                print("  --read ID              Read full message", file=sys.stderr)
                print("  --ack ID               Acknowledge message", file=sys.stderr)
                print("  --ack-all [--sys|--code]  Acknowledge all messages", file=sys.stderr)
                print("  --delete ID            Delete message", file=sys.stderr)
                print("  --clear [--sys|--code|--ack]  Clear messages", file=sys.stderr)
                print("  --auto-run, -ar        Auto-run safe recommendations", file=sys.stderr)
                sys.exit(1)
            i += 1

    # Handle operations in priority order

    # 1. Read individual message
    if read_id is not None:
        message = message_queue.get_message_by_id(read_id)
        if message:
            _display_full_message(message)
        else:
            print(f"✗ Message {read_id} not found")
            sys.exit(1)
        return

    # 2. Delete individual message
    if delete_id is not None:
        if message_queue.delete_message(delete_id):
            print(f"✓ Message {delete_id} deleted")
        else:
            print(f"✗ Message {delete_id} not found")
            sys.exit(1)
        return

    # 3. Clear messages
    if clear_all:
        if clear_type:
            filter_type, filter_value = clear_type
            if filter_type == "type":
                count = message_queue.clear_messages(message_type=filter_value)
                print(f"✓ Cleared {count} {filter_value.value} message(s)")
            elif filter_type == "status":
                count = message_queue.clear_messages(status=filter_value)
                print(f"✓ Cleared {count} {filter_value} message(s)")
        else:
            count = message_queue.clear_messages()
            print(f"✓ Cleared {count} message(s)")
        return

    # 4. Acknowledge messages
    if ack_id is not None:
        if message_queue.acknowledge_message(ack_id):
            print(f"✓ Message {ack_id} acknowledged")
        else:
            print(f"✗ Message {ack_id} not found or already acknowledged")
            sys.exit(1)
        return

    if ack_all:
        count = message_queue.acknowledge_all(ack_type)
        if ack_type:
            type_name = ack_type.value
            print(f"✓ Acknowledged {count} {type_name} message(s)")
        else:
            print(f"✓ Acknowledged {count} message(s)")
        return

    # 5. Display messages (default behavior)
    if show_all or (not show_system and not show_code):
        # Show all messages (default behavior)
        messages = message_queue.get_messages(status="pending")
        _display_messages(messages, "All Messages")
    else:
        # Show specific types
        if show_system:
            system_msgs = message_queue.get_messages(
                message_type=MessageType.SYSTEM, status="pending"
            )
            _display_messages(system_msgs, "System Messages")

        if show_code:
            code_msgs = message_queue.get_messages(message_type=MessageType.CODE, status="pending")
            _display_messages(code_msgs, "Code Messages")

    # Auto-run safe recommendations if requested
    if auto_run:
        _auto_run_safe_recommendations(message_queue)
        return


def _auto_run_safe_recommendations(message_queue):
    """Auto-run safe recommendations from pending messages."""
    from isaac.core.session_manager import SessionManager
    from isaac.core.tier_validator import TierValidator

    # Get pending messages
    messages = message_queue.get_messages(status="pending")
    if not messages:
        print("No pending messages to auto-run")
        return

    # Initialize components
    session_mgr = SessionManager()
    validator = TierValidator(session_mgr.preferences)

    executed_count = 0
    skipped_count = 0

    print("🔍 Analyzing messages for safe auto-execution...")
    print()

    for msg in messages:
        command = _extract_executable_command(msg)
        if command:
            # Check if command is in safe tier (1 or 2)
            tier = validator.get_tier(command)
            if tier in [1, 2]:
                print(f"✓ Auto-executing safe command (tier {tier}): {command}")
                try:
                    # Import and execute through command router
                    from isaac.adapters.shell_detector import detect_shell
                    from isaac.core.command_router import CommandRouter

                    shell_adapter = detect_shell()
                    router = CommandRouter(session_mgr, shell_adapter)

                    # Execute the command
                    result = router.route_command(command)
                    if result.success:
                        print(f"  ✓ Success: {result.output.strip()[:100]}...")
                        executed_count += 1
                        # Acknowledge the message
                        message_queue.acknowledge_message(msg["id"])
                    else:
                        print(f"  ✗ Failed: {result.output.strip()[:100]}...")
                        skipped_count += 1

                except Exception as e:
                    print(f"  ✗ Error executing: {e}")
                    skipped_count += 1
            else:
                print(f"⚠️ Skipping unsafe command (tier {tier}): {command}")
                skipped_count += 1
        else:
            skipped_count += 1

    print()
    print(f"Auto-run complete: {executed_count} executed, {skipped_count} skipped")


def _extract_executable_command(message):
    """Extract executable command from message content or metadata."""
    # First check metadata for explicitly marked safe commands
    metadata = message.get("metadata", {})
    if metadata and "safe_commands" in metadata:
        safe_commands = metadata["safe_commands"]
        if isinstance(safe_commands, list) and safe_commands:
            # Return the first safe command
            return safe_commands[0]

    content = message.get("content", "").strip()

    # Look for common command patterns in messages
    import re

    # Pattern 1: "Run 'command'" or "run 'command'"
    run_pattern = r"[Rr]un\s+['\"]([^'\"]+)['\"]"
    match = re.search(run_pattern, content)
    if match:
        return match.group(1)

    # Pattern 2: Commands at the end of lines starting with common indicators
    lines = content.split("\n")
    for line in reversed(lines):  # Check from bottom up
        line = line.strip()
        if line and not line.startswith(("Found", "There are", "Metadata:", "-")):
            # Check if it looks like a command (contains spaces or common command chars)
            if " " in line or any(char in line for char in ["/", "\\", "-", "."]):
                # Filter out obvious non-commands
                if not any(
                    word in line.lower() for word in ["found", "available", "run", "see", "details"]
                ):
                    return line

    return None
    """Display a single message in full detail."""
    print("=" * 70)
    print(f"Message ID: {message['id']}")
    print(f"Type: {message['message_type']}")
    print(f"Priority: {message['priority']}")
    print(f"Status: {message['status']}")
    print(f"Created: {message['created_at']}")
    if message["acknowledged_at"]:
        print(f"Acknowledged: {message['acknowledged_at']}")
    print("=" * 70)
    print(f"\nTitle: {message['title']}")
    print()

    if message["content"]:
        print("Content:")
        print("-" * 70)
        print(message["content"])
        print("-" * 70)
        print()

    if message["metadata"]:
        print("Metadata:")
        print("-" * 70)
        for key, value in message["metadata"].items():
            print(f"  {key}: {value}")
        print("-" * 70)
        print()


def _display_messages(messages, title):
    """Display messages in a formatted way."""
    if not messages:
        print(f"\n{title}:")
        print("  No pending messages")
        return

    # Calculate breakdown by type
    system_count = sum(1 for msg in messages if msg["message_type"] == "system")
    code_count = sum(1 for msg in messages if msg["message_type"] == "code")

    breakdown = ""
    if system_count > 0:
        breakdown += f"!{system_count}"
    if code_count > 0:
        breakdown += f"¢{code_count}"

    if breakdown:
        breakdown = f" {breakdown}"

    print(f"\n{title} ({len(messages)} pending{breakdown}):")
    print("-" * 60)

    for msg in messages:
        # Priority indicator (text-based for Windows compatibility)
        priority = msg["priority"]
        if priority == "urgent":
            pri_indicator = "[URGENT]"
        elif priority == "high":
            pri_indicator = "[HIGH]"
        elif priority == "normal":
            pri_indicator = "[NORMAL]"
        else:
            pri_indicator = "[LOW]"

        # Type indicator
        msg_type = msg["message_type"]
        type_indicator = "!" if msg_type == "system" else "¢"

        # Format message
        print(f"{pri_indicator} {type_indicator} [{msg['id']}] {msg['title']}")

        # Show content if present
        if msg["content"]:
            # Truncate long content
            content = msg["content"]
            if len(content) > 100:
                content = content[:97] + "..."
            print(f"    {content}")

        # Show metadata if present
        if msg["metadata"]:
            metadata_items = []
            for key, value in msg["metadata"].items():
                if isinstance(value, (str, int, float, bool)):
                    metadata_items.append(f"{key}={value}")
            if metadata_items:
                print(f"    Metadata: {', '.join(metadata_items)}")

        print()


if __name__ == "__main__":
    main()
