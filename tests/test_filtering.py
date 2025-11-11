#!/usr/bin/env python3
"""
Test message filtering
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from isaac.core.message_queue import MessageQueue, MessageType

def test_filtering():
    mq = MessageQueue()
    print('All messages:', len(mq.get_messages(status='pending')))
    print('System messages:', len(mq.get_messages(message_type=MessageType.SYSTEM, status='pending')))
    print('Code messages:', len(mq.get_messages(message_type=MessageType.CODE, status='pending')))

if __name__ == "__main__":
    test_filtering()