#!/usr/bin/env python3
"""
Test script for Agentic Orchestrator
"""

import asyncio
from isaac.core.session_manager import SessionManager
from isaac.core.agentic_orchestrator import AgenticOrchestrator


async def test_agentic_orchestrator():
    print("🎭 Testing Agentic Orchestrator")
    print("=" * 50)

    # Create session manager
    session_mgr = SessionManager()

    # Create orchestrator
    orchestrator = AgenticOrchestrator(session_mgr)

    # Event listener
    def event_listener(event):
        print(f"📢 {event['type']}: {event.get('message', event.get('user_input', ''))}")

    orchestrator.add_event_listener(event_listener)

    print("Testing simple agentic task:")
    user_input = "read the README.md file"

    async for event in orchestrator.execute_agentic_task(user_input):
        print(f"  {event['type']}: {event.get('content', event.get('final_answer', event.get('error', '')))}")
        if event['type'] == 'task_complete':
            break

    print("\n✅ Agentic Orchestrator test completed!")


if __name__ == "__main__":
    asyncio.run(test_agentic_orchestrator())