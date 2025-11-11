#!/usr/bin/env python3
"""
Test script for Tool Registry
"""

from isaac.tools.registry import ToolRegistry

def test_registry():
    print("🛠️  Testing Tool Registry")
    print("=" * 50)

    # Create registry
    registry = ToolRegistry()

    # Get info
    info = registry.get_tool_info()
    print(f"Total tools registered: {info['total_tools']}")
    print()

    print("Registered Tools:")
    for name, details in info['tools'].items():
        print(f"  📋 {name}")
        print(f"     Description: {details['description']}")
        print(f"     Capabilities: {', '.join(details['capabilities'])}")
        print()

    print("Tools for coding tasks:")
    coding_tools = registry.get_tools_for_task('coding')
    for tool in coding_tools:
        func = tool['function']
        print(f"  🔧 {func['name']}: {func['description']}")
    print()

    print("Tools for search tasks:")
    search_tools = registry.get_tools_for_task('search')
    for tool in search_tools:
        func = tool['function']
        print(f"  🔍 {func['name']}: {func['description']}")
    print()

    # Test tool execution
    print("Testing tool execution:")
    if 'read' in registry.tool_instances:
        result = registry.execute_tool('read', {'file_path': 'README.md'})
        print(f"Read tool result: success={result.get('success', False)}")
        if not result.get('success', True):
            print(f"  Error: {result.get('error', 'Unknown')}")
    else:
        print("Read tool not found")

    print("\n✅ Tool Registry test completed!")

if __name__ == "__main__":
    test_registry()