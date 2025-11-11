#!/usr/bin/env python3
"""
Test Autonomous Monitoring System

Tests the complete monitoring system including:
- Monitor manager initialization
- Individual monitor functionality
- Message queue integration
- Prompt indicator updates
"""

import sys
import time
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from isaac.monitoring.monitor_manager import MonitorManager
from isaac.core.message_queue import MessageQueue, MessageType, MessagePriority


def test_monitor_manager():
    """Test monitor manager initialization and control."""
    print("Testing Monitor Manager...")

    manager = MonitorManager()

    # Test initialization
    manager.initialize_monitors()
    monitors = manager.list_monitors()
    print(f"✓ Initialized monitors: {monitors}")

    assert 'system' in monitors, "System monitor not found"
    assert 'code' in monitors, "Code monitor not found"

    # Test status
    status = manager.get_monitor_status()
    print(f"✓ Monitor status: {status}")

    # Test starting monitors
    manager.start_all()
    time.sleep(1)  # Let monitors start

    status = manager.get_monitor_status()
    running_count = sum(1 for m in status.values() if m['running'])
    print(f"✓ Started {running_count} monitors")

    # Test stopping monitors
    manager.stop_all()
    time.sleep(1)  # Let monitors stop

    status = manager.get_monitor_status()
    running_count = sum(1 for m in status.values() if m['running'])
    print(f"✓ Stopped monitors (running: {running_count})")

    print("Monitor Manager tests passed!\n")


def test_message_integration():
    """Test that monitors can send messages to queue."""
    print("Testing Message Queue Integration...")

    # Clear any existing messages
    queue = MessageQueue()
    queue.acknowledge_all()  # Clear all messages

    # Create a simple monitor instance for testing
    from isaac.monitoring.system_monitor import SystemMonitor
    monitor = SystemMonitor()

    # Send test messages
    msg_id1 = monitor._send_message(
        MessageType.SYSTEM,
        "Test System Message",
        "This is a test system notification",
        MessagePriority.NORMAL
    )

    msg_id2 = monitor._send_message(
        MessageType.CODE,
        "Test Code Message",
        "This is a test code notification",
        MessagePriority.HIGH
    )

    print(f"✓ Sent test messages: {msg_id1}, {msg_id2}")

    # Check prompt indicator
    indicator = queue.get_prompt_indicator()
    print(f"✓ Prompt indicator: {indicator}")

    # Should show [!1¢1]> for 1 system and 1 code message
    assert '[!1¢1]>' in indicator, f"Expected indicator with counts, got: {indicator}"

    # Check message retrieval
    messages = queue.get_messages()
    print(f"✓ Retrieved {len(messages)} messages")

    assert len(messages) >= 2, f"Expected at least 2 messages, got {len(messages)}"

    # Clean up
    queue.acknowledge_all()
    print("Message integration tests passed!\n")


def test_monitor_functionality():
    """Test actual monitoring functionality (basic checks)."""
    print("Testing Monitor Functionality...")

    queue = MessageQueue()
    queue.acknowledge_all()  # Clear messages

    # Test system monitor
    from isaac.monitoring.system_monitor import SystemMonitor
    system_monitor = SystemMonitor()

    # Run a check (should not generate messages on healthy system)
    system_monitor._perform_check()

    # Test code monitor
    from isaac.monitoring.code_monitor import CodeMonitor
    code_monitor = CodeMonitor()

    # Run a check
    code_monitor._perform_check()

    # Check if any messages were generated
    messages = queue.get_messages()
    print(f"✓ Monitors generated {len(messages)} messages during checks")

    # Clean up
    queue.acknowledge_all()
    print("Monitor functionality tests passed!\n")


def main():
    """Run all monitoring system tests."""
    print("🧪 Testing Autonomous Monitoring System\n")

    try:
        test_monitor_manager()
        test_message_integration()
        test_monitor_functionality()

        print("🎉 All monitoring system tests passed!")
        return 0

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())