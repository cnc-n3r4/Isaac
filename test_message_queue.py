#!/usr/bin/env python3
"""
Test script for Message Queue System

Adds test messages and demonstrates the prompt indicator functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from isaac.core.message_queue import MessageQueue, MessageType, MessagePriority

def main():
    print("Testing Message Queue System")
    print("=" * 40)

    # Initialize message queue
    mq = MessageQueue()

    # Clear any existing messages for clean test
    mq.acknowledge_all()

    print("1. Adding test messages...")

    # Add system messages
    mq.add_message(
        MessageType.SYSTEM,
        "Windows Update Available",
        "Critical security updates are available for installation",
        MessagePriority.HIGH,
        {"update_count": 5, "reboot_required": True}
    )

    mq.add_message(
        MessageType.SYSTEM,
        "Disk Space Low",
        "C: drive has only 2GB free space remaining",
        MessagePriority.URGENT,
        {"drive": "C:", "free_gb": 2}
    )

    # Add code messages
    mq.add_message(
        MessageType.CODE,
        "Linting Issues Found",
        "Found 3 critical linting errors in main.py",
        MessagePriority.NORMAL,
        {"file": "main.py", "errors": 3, "warnings": 12}
    )

    mq.add_message(
        MessageType.CODE,
        "Test Suite Failing",
        "2 unit tests are failing in the authentication module",
        MessagePriority.HIGH,
        {"module": "auth", "failed_tests": 2, "total_tests": 45}
    )

    print("✓ Added 4 test messages (2 system, 2 code)")

    print("\n2. Testing prompt indicator...")
    indicator = mq.get_prompt_indicator()
    print(f"Prompt indicator: {indicator}")

    print("\n3. Testing message retrieval...")

    # Get all pending messages
    all_messages = mq.get_messages()
    print(f"Total pending messages: {len(all_messages)}")

    # Get system messages
    system_messages = mq.get_messages(message_type=MessageType.SYSTEM)
    print(f"System messages: {len(system_messages)}")

    # Get code messages
    code_messages = mq.get_messages(message_type=MessageType.CODE)
    print(f"Code messages: {len(code_messages)}")

    print("\n4. Testing message acknowledgment...")

    # Acknowledge first message
    if all_messages:
        first_msg_id = all_messages[0]['id']
        success = mq.acknowledge_message(first_msg_id)
        print(f"Acknowledged message {first_msg_id}: {success}")

        # Check updated counts
        updated_indicator = mq.get_prompt_indicator()
        print(f"Updated prompt indicator: {updated_indicator}")

    print("\n5. Testing message display...")
    print("All pending messages:")
    for msg in mq.get_messages():
        print(f"  [{msg['id']}] {msg['message_type']}: {msg['title']}")

    print("\n✓ Message Queue System test completed successfully!")

if __name__ == "__main__":
    main()