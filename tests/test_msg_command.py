#!/usr/bin/env python3
"""
Quick test of /msg command enhancements
"""

import sys
import tempfile
from pathlib import Path

# Add Isaac to path
sys.path.insert(0, str(Path(__file__).parent))

from isaac.core.message_queue import MessageQueue, MessageType, MessagePriority


def test_message_queue_enhancements():
    """Test new MessageQueue methods"""
    print("Testing MessageQueue enhancements...")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / 'test_messages.db'
        mq = MessageQueue(db_path)

        # Test 1: Add messages
        print("\n1. Adding test messages...")
        sys_id = mq.add_message(
            MessageType.SYSTEM,
            "Test System Message",
            "This is test content for a system message",
            MessagePriority.NORMAL
        )
        print(f"   ✓ Added system message ID: {sys_id}")

        code_id = mq.add_message(
            MessageType.CODE,
            "Test Code Message",
            "This is test content for a code message",
            MessagePriority.HIGH,
            metadata={'file': 'test.py', 'line': 42}
        )
        print(f"   ✓ Added code message ID: {code_id}")

        # Test 2: Get message by ID
        print("\n2. Testing get_message_by_id()...")
        msg = mq.get_message_by_id(sys_id)
        assert msg is not None, "Should retrieve message"
        assert msg['title'] == "Test System Message", "Title should match"
        assert msg['content'] == "This is test content for a system message", "Content should match"
        print(f"   ✓ Retrieved message {sys_id}")
        print(f"   ✓ Title: {msg['title']}")
        print(f"   ✓ Content: {msg['content'][:50]}...")

        # Test 3: Get message with metadata
        print("\n3. Testing message with metadata...")
        msg_with_meta = mq.get_message_by_id(code_id)
        assert msg_with_meta is not None, "Should retrieve message"
        assert 'metadata' in msg_with_meta, "Should have metadata"
        assert msg_with_meta['metadata']['file'] == 'test.py', "Metadata should match"
        print(f"   ✓ Retrieved message {code_id}")
        print(f"   ✓ Metadata: {msg_with_meta['metadata']}")

        # Test 4: Delete message
        print("\n4. Testing delete_message()...")
        success = mq.delete_message(sys_id)
        assert success, "Should delete message"
        deleted_msg = mq.get_message_by_id(sys_id)
        assert deleted_msg is None, "Message should be gone"
        print(f"   ✓ Deleted message {sys_id}")
        print(f"   ✓ Verified deletion")

        # Test 5: Add more messages for clear testing
        print("\n5. Adding more messages for clear testing...")
        for i in range(3):
            mq.add_message(
                MessageType.SYSTEM,
                f"System Message {i}",
                f"Content {i}",
                MessagePriority.NORMAL
            )
        for i in range(2):
            mq.add_message(
                MessageType.CODE,
                f"Code Message {i}",
                f"Content {i}",
                MessagePriority.NORMAL
            )
        print("   ✓ Added 3 system + 2 code messages")

        # Test 6: Clear by type
        print("\n6. Testing clear_messages() by type...")
        count = mq.clear_messages(message_type=MessageType.SYSTEM)
        assert count == 3, f"Should clear 3 system messages, got {count}"
        print(f"   ✓ Cleared {count} system messages")

        # Test 7: Clear all remaining
        print("\n7. Testing clear_messages() all...")
        count = mq.clear_messages()
        assert count == 3, f"Should clear 3 messages (2 code + 1 from earlier), got {count}"
        print(f"   ✓ Cleared {count} remaining messages")

        # Test 8: Clear acknowledged messages
        print("\n8. Testing clear by status...")
        msg_id = mq.add_message(MessageType.SYSTEM, "To Acknowledge", "Test")
        mq.acknowledge_message(msg_id)
        count = mq.clear_messages(status='acknowledged')
        assert count == 1, f"Should clear 1 acknowledged message, got {count}"
        print(f"   ✓ Cleared {count} acknowledged message")

    print("\n" + "=" * 60)
    print("✅ All MessageQueue tests passed!")


def test_msg_command_help():
    """Test that msg command shows proper help"""
    print("\nTesting /msg command help...")
    print("=" * 60)

    import subprocess

    result = subprocess.run(
        [sys.executable, "isaac/commands/msg/run.py", "--invalid"],
        capture_output=True,
        text=True
    )

    assert "--read ID" in result.stderr, "Should show --read in help"
    assert "--delete ID" in result.stderr, "Should show --delete in help"
    assert "--clear" in result.stderr, "Should show --clear in help"

    print("   ✓ Help text includes --read")
    print("   ✓ Help text includes --delete")
    print("   ✓ Help text includes --clear")
    print("✅ Command help test passed!")


if __name__ == '__main__':
    try:
        test_message_queue_enhancements()
        test_msg_command_help()
        print("\n" + "=" * 60)
        print("✅✅✅ ALL TESTS PASSED! ✅✅✅")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
