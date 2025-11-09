# isaac/commands/msg.py

"""
Message Queue Management Command

Provides interface for viewing and managing AI assistant notifications.
/msg command with support for filtering by type and acknowledging messages.
"""

import sys
from typing import List, Dict, Any
from isaac.core.message_queue import MessageQueue, MessageType
from isaac.commands.base import BaseCommand


class MsgCommand(BaseCommand):
    """Message queue management command."""

    @property
    def name(self) -> str:
        return "msg"

    @property
    def description(self) -> str:
        return "View and manage AI assistant message notifications"

    @property
    def usage(self) -> str:
        return "/msg [--sys|--code|--all] [--ack ID|--ack-all]"

    def execute(self, args: List[str]) -> bool:
        """
        Execute message command.

        Args:
            args: Command arguments

        Returns:
            True if command executed successfully
        """
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
                    print("Error: --ack requires a valid message ID")
                    return False
            elif arg == '--ack-all':
                ack_all = True
                if i + 1 < len(args) and args[i + 1] in ['--sys', '--code']:
                    ack_type = MessageType.SYSTEM if args[i + 1] == '--sys' else MessageType.CODE
                    i += 1
            else:
                print(f"Unknown argument: {arg}")
                print(f"Usage: {self.usage}")
                return False
            i += 1

        # Initialize message queue
        try:
            message_queue = MessageQueue()
        except Exception as e:
            print(f"Error initializing message queue: {e}")
            return False

        # Handle acknowledgments first
        if ack_id is not None:
            if message_queue.acknowledge_message(ack_id):
                print(f"✓ Message {ack_id} acknowledged")
            else:
                print(f"✗ Message {ack_id} not found or already acknowledged")
            return True

        if ack_all:
            count = message_queue.acknowledge_all(ack_type)
            if ack_type:
                type_name = ack_type.value
                print(f"✓ Acknowledged {count} {type_name} message(s)")
            else:
                print(f"✓ Acknowledged {count} message(s)")
            return True

        # Determine what to show
        if show_all or (not show_system and not show_code):
            # Show all messages (default behavior)
            messages = message_queue.get_messages(status='pending')
            self._display_messages(messages, "All Messages")
        else:
            # Show specific types
            if show_system:
                system_msgs = message_queue.get_messages(
                    message_type=MessageType.SYSTEM, status='pending'
                )
                self._display_messages(system_msgs, "System Messages")

            if show_code:
                code_msgs = message_queue.get_messages(
                    message_type=MessageType.CODE, status='pending'
                )
                self._display_messages(code_msgs, "Code Messages")

        return True

    def _display_messages(self, messages: List[Dict[str, Any]], title: str) -> None:
        """Display messages in a formatted way."""
        if not messages:
            print(f"\n{title}:")
            print("  No pending messages")
            return

        print(f"\n{title} ({len(messages)} pending):")
        print("-" * 60)

        for msg in messages:
            # Priority indicator
            priority = msg['priority']
            if priority == 'urgent':
                pri_indicator = "🔴"
            elif priority == 'high':
                pri_indicator = "🟠"
            elif priority == 'normal':
                pri_indicator = "🟡"
            else:
                pri_indicator = "🟢"

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

    def get_help(self) -> str:
        """Get detailed help for the command."""
        return f"""
Message Queue Management

View and manage AI assistant notifications. Messages are categorized by type:
  ! - System operations (updates, monitoring, cloud sync)
  ¢ - Code operations (linting, testing, debugging, analysis)

USAGE:
  {self.usage}

EXAMPLES:
  /msg                    # Show all pending messages
  /msg --all             # Same as above
  /msg --sys             # Show only system messages
  /msg --code            # Show only code messages
  /msg --ack 123         # Acknowledge message ID 123
  /msg --ack-all         # Acknowledge all messages
  /msg --ack-all --sys   # Acknowledge all system messages

SHORTCUTS:
  -s, --sys     System messages only
  -c, --code    Code messages only
  -a, --all     All messages (default)

The prompt shows message counts: $[!2¢1]> (2 system, 1 code pending)
"""</content>
<parameter name="filePath">c:\Projects\Isaac2\isaac\commands\msg.py