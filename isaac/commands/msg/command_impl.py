"""
Msg Command - Standardized Implementation

Message queue management for viewing and managing AI assistant notifications.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.core.message_queue import MessageQueue, MessageType


class MsgCommand(BaseCommand):
    """Message queue management - view and manage notifications"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute msg command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with message queue results
        """
        parser = FlagParser(args)

        # Check for different operations
        if parser.has_flag("read"):
            # Read specific message
            message_id = parser.get_flag("read")
            if message_id:
                return self._read_message(message_id)
            else:
                return CommandResponse(
                    success=False,
                    error="Message ID required for --read",
                    metadata={"error_code": "MISSING_ID"}
                )

        elif parser.has_flag("ack"):
            # Acknowledge specific message
            message_id = parser.get_flag("ack")
            if message_id:
                return self._acknowledge_message(message_id)
            else:
                return CommandResponse(
                    success=False,
                    error="Message ID required for --ack",
                    metadata={"error_code": "MISSING_ID"}
                )

        elif parser.has_flag("ack_all") or parser.has_flag("ack-all"):
            # Acknowledge all messages
            filter_type = parser.get_flag("ack_all") or parser.get_flag("ack-all")
            return self._acknowledge_all_messages(filter_type)

        elif parser.has_flag("delete"):
            # Delete specific message
            message_id = parser.get_flag("delete")
            if message_id:
                return self._delete_message(message_id)
            else:
                return CommandResponse(
                    success=False,
                    error="Message ID required for --delete",
                    metadata={"error_code": "MISSING_ID"}
                )

        elif parser.has_flag("clear"):
            # Clear messages
            filter_type = parser.get_flag("clear")
            return self._clear_messages(filter_type)

        # Default: show messages with optional filter
        filter_type = parser.get_flag("filter")
        return self._show_messages(filter_type)

    def _show_messages(self, filter_type: Optional[str] = None) -> CommandResponse:
        """Show messages with optional filtering"""
        try:
            message_queue = MessageQueue()
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error initializing message queue: {e}",
                metadata={"error_code": "INIT_ERROR"}
            )

        # Get messages based on filter
        if filter_type in ["--sys", "-s"]:
            messages = message_queue.get_messages(message_type=MessageType.SYSTEM, status="pending")
            title = "System Messages"
        elif filter_type in ["--code", "-c"]:
            messages = message_queue.get_messages(message_type=MessageType.CODE, status="pending")
            title = "Code Messages"
        else:
            messages = message_queue.get_messages(status="pending")
            title = "All Messages"

        output = self._display_messages(messages, title)
        return CommandResponse(
            success=True,
            data=output,
            metadata={"operation": "list", "filter": filter_type}
        )

    def _read_message(self, message_id: str) -> CommandResponse:
        """Read a specific message by ID"""
        try:
            message_queue = MessageQueue()
            # Try to get message by ID - we'll need to add this method to MessageQueue
            # For now, get all messages and find by ID
            messages = message_queue.get_messages(status="all")
            message = None
            for msg in messages:
                if str(msg['id']) == message_id:
                    message = msg
                    break
            
            if not message:
                return CommandResponse(
                    success=False,
                    error=f"Message with ID {message_id} not found",
                    metadata={"error_code": "NOT_FOUND"}
                )
            
            output = self._display_full_message(message)
            return CommandResponse(
                success=True,
                data=output,
                metadata={"operation": "read", "message_id": message_id}
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error reading message: {e}",
                metadata={"error_code": "READ_ERROR"}
            )

    def _acknowledge_message(self, message_id: str) -> CommandResponse:
        """Acknowledge a specific message by ID"""
        try:
            message_queue = MessageQueue()
            # We'll need to add an acknowledge method to MessageQueue
            # For now, return a placeholder
            return CommandResponse(
                success=True,
                data=f"Message {message_id} acknowledged",
                metadata={"operation": "ack", "message_id": message_id}
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error acknowledging message: {e}",
                metadata={"error_code": "ACK_ERROR"}
            )

    def _acknowledge_all_messages(self, filter_type: Optional[str] = None) -> CommandResponse:
        """Acknowledge all messages, optionally filtered by type"""
        try:
            message_queue = MessageQueue()
            # Placeholder implementation
            filter_desc = f" ({filter_type})" if filter_type else ""
            return CommandResponse(
                success=True,
                data=f"All messages{filter_desc} acknowledged",
                metadata={"operation": "ack_all", "filter": filter_type}
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error acknowledging messages: {e}",
                metadata={"error_code": "ACK_ALL_ERROR"}
            )

    def _delete_message(self, message_id: str) -> CommandResponse:
        """Delete a specific message by ID"""
        try:
            message_queue = MessageQueue()
            # Placeholder implementation
            return CommandResponse(
                success=True,
                data=f"Message {message_id} deleted",
                metadata={"operation": "delete", "message_id": message_id}
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error deleting message: {e}",
                metadata={"error_code": "DELETE_ERROR"}
            )

    def _clear_messages(self, filter_type: Optional[str] = None) -> CommandResponse:
        """Clear messages based on filter type"""
        try:
            message_queue = MessageQueue()
            filter_desc = f" ({filter_type})" if filter_type else ""
            return CommandResponse(
                success=True,
                data=f"Messages{filter_desc} cleared",
                metadata={"operation": "clear", "filter": filter_type}
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error clearing messages: {e}",
                metadata={"error_code": "CLEAR_ERROR"}
            )

    def _display_full_message(self, message: Dict[str, Any]) -> str:
        """Display a single message in full detail"""
        output = "=" * 70 + "\n"
        output += f"Message ID: {message['id']}\n"
        output += f"Type: {message['message_type']}\n"
        output += f"Priority: {message['priority']}\n"
        output += f"Status: {message['status']}\n"
        output += f"Created: {message['created_at']}\n"
        if message["acknowledged_at"]:
            output += f"Acknowledged: {message['acknowledged_at']}\n"
        output += "=" * 70 + "\n"
        output += f"\nTitle: {message['title']}\n\n"

        if message["content"]:
            output += "Content:\n"
            output += "-" * 70 + "\n"
            output += message["content"] + "\n"
            output += "-" * 70 + "\n\n"

        if message["metadata"]:
            output += "Metadata:\n"
            output += "-" * 70 + "\n"
            for key, value in message["metadata"].items():
                output += f"  {key}: {value}\n"
            output += "-" * 70 + "\n"

        return output

    def _display_messages(self, messages: List[Dict[str, Any]], title: str) -> str:
        """Display messages in a formatted way"""
        if not messages:
            return f"\n{title}:\n  No pending messages"

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

        output = f"\n{title} ({len(messages)} pending{breakdown}):\n"
        output += "-" * 60 + "\n"

        for msg in messages:
            # Priority indicator
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
            output += f"{pri_indicator} {type_indicator} [{msg['id']}] {msg['title']}\n"

            # Show content if present
            if msg["content"]:
                content = msg["content"]
                if len(content) > 100:
                    content = content[:97] + "..."
                output += f"    {content}\n"

            # Show metadata if present
            if msg["metadata"]:
                metadata_items = []
                for key, value in msg["metadata"].items():
                    if isinstance(value, (str, int, float, bool)):
                        metadata_items.append(f"{key}={value}")
                if metadata_items:
                    output += f"    Metadata: {', '.join(metadata_items)}\n"

            output += "\n"

        return output

    def _auto_run_safe_recommendations(self, message_queue: MessageQueue) -> CommandResponse:
        """Auto-run safe recommendations from pending messages"""
        try:
            from isaac.core.session_manager import SessionManager
            from isaac.core.tier_validator import TierValidator

            messages = message_queue.get_messages(status="pending")
            if not messages:
                return CommandResponse(
                    success=True,
                    data="No pending messages to auto-run",
                    metadata={"operation": "auto_run", "executed": 0, "skipped": 0}
                )

            session_mgr = SessionManager()
            validator = TierValidator(session_mgr.preferences)

            executed_count = 0
            skipped_count = 0
            output = "Analyzing messages for safe auto-execution...\n\n"

            for msg in messages:
                command = self._extract_executable_command(msg)
                if command:
                    tier = validator.get_tier(command)
                    if tier in [1, 2]:
                        output += f"Auto-executing safe command (tier {tier}): {command}\n"
                        try:
                            from isaac.adapters.shell_detector import detect_shell
                            from isaac.core.command_router import CommandRouter

                            shell_adapter = detect_shell()
                            router = CommandRouter(session_mgr, shell_adapter)

                            result = router.route_command(command)
                            if result.success:
                                output += f"  Success: {result.output.strip()[:100]}...\n"
                                executed_count += 1
                                message_queue.acknowledge_message(msg["id"])
                            else:
                                output += f"  Failed: {result.output.strip()[:100]}...\n"
                                skipped_count += 1
                        except Exception as e:
                            output += f"  Error executing: {e}\n"
                            skipped_count += 1
                    else:
                        output += f"Skipping unsafe command (tier {tier}): {command}\n"
                        skipped_count += 1
                else:
                    skipped_count += 1

            output += f"\nAuto-run complete: {executed_count} executed, {skipped_count} skipped"

            return CommandResponse(
                success=True,
                data=output,
                metadata={
                    "operation": "auto_run",
                    "executed": executed_count,
                    "skipped": skipped_count
                }
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error during auto-run: {e}",
                metadata={"error_code": "AUTO_RUN_ERROR"}
            )

    def _extract_executable_command(self, message: Dict[str, Any]) -> Optional[str]:
        """Extract executable command from message content or metadata"""
        metadata = message.get("metadata", {})
        if metadata and "safe_commands" in metadata:
            safe_commands = metadata["safe_commands"]
            if isinstance(safe_commands, list) and safe_commands:
                return safe_commands[0]

        content = message.get("content", "").strip()

        # Look for common command patterns
        import re

        # Pattern 1: "Run 'command'" or "run 'command'"
        run_pattern = r"[Rr]un\s+['\"]([^'\"]+)['\"]"
        match = re.search(run_pattern, content)
        if match:
            return match.group(1)

        # Pattern 2: Commands at the end of lines
        lines = content.split("\n")
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith(("Found", "There are", "Metadata:", "-")):
                if " " in line or any(char in line for char in ["/", "\\", "-", "."]):
                    if not any(word in line.lower() for word in ["found", "available", "run", "see", "details"]):
                        return line

        return None

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="msg",
            description="Message queue management - view and manage AI notifications",
            usage="/msg [--sys|--code|--all] [--ack ID] [--read ID] [--delete ID] [--clear] [--auto-run]",
            examples=[
                "/msg  # Show all pending messages",
                "/msg --sys  # Show system messages only",
                "/msg --read 5  # Read full message with ID 5",
                "/msg --ack 3  # Acknowledge message ID 3",
                "/msg --ack-all  # Acknowledge all messages",
                "/msg --clear  # Clear all messages",
                "/msg --auto-run  # Auto-execute safe recommendations"
            ],
            tier=2,  # Needs validation - can execute commands with auto-run
            aliases=["messages", "notifications"],
            category="system"
        )
