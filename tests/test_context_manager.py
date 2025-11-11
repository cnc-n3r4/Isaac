#!/usr/bin/env python3
"""
Test script for Context Manager
"""

from isaac.core.context_manager import ConversationContext


def test_context_manager():
    print("📝 Testing Context Manager")
    print("=" * 50)

    # Create context manager
    context_mgr = ConversationContext()

    print("Initial statistics:")
    stats = context_mgr.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nAdding conversation entries:")
    context_mgr.add_entry("user", "read the README file")
    context_mgr.add_entry("assistant", "I'll help you read the README file")
    context_mgr.add_entry("tool", "read tool executed successfully")

    print("\nRecent history:")
    history = context_mgr.get_recent_history(3)
    for entry in history:
        print(f"  {entry.role}: {entry.content[:50]}...")

    print("\nUpdating project context:")
    context_mgr.update_project_context(
        current_directory="/home/user/projects",
        working_files=["README.md", "main.py"]
    )

    print("\nRelevant context for 'read file' query:")
    relevant = context_mgr.get_relevant_context("read file")
    print(f"  Working files: {relevant['working_files']}")
    print(f"  Current directory: {relevant['current_directory']}")

    print("\nFinal statistics:")
    stats = context_mgr.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ Context Manager test completed!")


if __name__ == "__main__":
    test_context_manager()