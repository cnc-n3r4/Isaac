#!/usr/bin/env python3
"""
Test script for Streaming Executor
"""

import asyncio
from isaac.tools.registry import ToolRegistry
from isaac.core.streaming_executor import StreamingExecutor, ExecutionEvent


async def test_streaming_executor():
    print("⚡ Testing Streaming Executor")
    print("=" * 50)

    # Create registry and executor
    registry = ToolRegistry()
    executor = StreamingExecutor(registry)

    # Event listener
    def event_listener(event: ExecutionEvent):
        print(f"📢 Event: {event.event_type} - {event.tool_name} - {event.message}")

    executor.add_event_listener(event_listener)

    print("Testing single tool execution:")
    async for event in executor.execute_tool_streaming('read', {'file_path': 'README.md'}):
        print(f"  {event.event_type}: {event.message}")

    print("\nTesting multiple tool execution:")
    tool_calls = [
        {'tool_name': 'read', 'tool_args': {'file_path': 'README.md', 'limit': 5}},
        {'tool_name': 'glob', 'tool_args': {'pattern': '*.md'}}
    ]

    async for event in executor.execute_multiple_tools(tool_calls, max_concurrent=2):
        print(f"  {event.event_type}: {event.tool_name} - {event.message}")

    executor.shutdown()
    print("\n✅ Streaming Executor test completed!")


if __name__ == "__main__":
    asyncio.run(test_streaming_executor())