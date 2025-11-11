#!/usr/bin/env python3
"""
Test script for AI Router
Demonstrates multi-provider routing with tool calling
"""

import os
import sys
from pathlib import Path

# Add Isaac to path
sys.path.insert(0, str(Path(__file__).parent))

from isaac.ai import AIRouter
from isaac.tools import ReadTool, GrepTool, GlobTool


def test_basic_chat():
    """Test basic chat without tools"""
    print("=" * 60)
    print("TEST 1: Basic Chat (No Tools)")
    print("=" * 60)
    
    router = AIRouter()
    
    # Show available providers
    providers = router.get_available_providers()
    print(f"Available providers: {', '.join(providers)}")
    print()
    
    # Simple chat
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2? Answer briefly."}
    ]
    
    response = router.chat(messages=messages)
    
    print(f"Provider used: {response.provider}")
    print(f"Model: {response.model}")
    print(f"Response: {response.content}")
    print(f"Usage: {response.usage}")
    print(f"Success: {response.success}")
    
    if response.error:
        print(f"Error: {response.error}")
    
    print()


def test_tool_calling():
    """Test chat with tool calling"""
    print("=" * 60)
    print("TEST 2: Tool Calling")
    print("=" * 60)
    
    router = AIRouter()
    
    # Get tool schemas
    read_tool = ReadTool()
    grep_tool = GrepTool()
    
    tools = [
        read_tool.to_dict(),
        grep_tool.to_dict()
    ]
    
    print(f"Registered tools: {', '.join(t['function']['name'] for t in tools)}")
    print()
    
    # Chat with tools
    messages = [
        {"role": "system", "content": "You are a code assistant. Use the available tools to help the user."},
        {"role": "user", "content": "List the available tools you have access to."}
    ]
    
    response = router.chat(messages=messages, tools=tools)
    
    print(f"Provider used: {response.provider}")
    print(f"Response: {response.content}")
    print(f"Has tool calls: {response.has_tool_calls}")
    
    if response.tool_calls:
        print(f"Tool calls requested:")
        for tc in response.tool_calls:
            print(f"  - {tc.name}({tc.arguments})")
    
    print()


def test_fallback():
    """Test provider fallback"""
    print("=" * 60)
    print("TEST 3: Provider Fallback")
    print("=" * 60)
    
    router = AIRouter()
    
    # Try with specific provider preference
    messages = [
        {"role": "user", "content": "Say hello"}
    ]
    
    # Test each provider
    for provider in ['grok', 'claude', 'openai']:
        print(f"\nTrying with preferred provider: {provider}")
        response = router.chat(messages=messages, prefer_provider=provider)
        print(f"  Actually used: {response.provider}")
        print(f"  Success: {response.success}")
        if response.error:
            print(f"  Error: {response.error}")
        else:
            print(f"  Response: {response.content[:50]}...")


def test_stats():
    """Test usage statistics"""
    print("=" * 60)
    print("TEST 4: Usage Statistics")
    print("=" * 60)
    
    router = AIRouter()
    
    # Make a few calls
    messages = [{"role": "user", "content": "Hi"}]
    for i in range(3):
        router.chat(messages=messages)
    
    # Get stats
    stats = router.get_stats()
    
    print(f"Total calls: {stats['total_calls']}")
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Total cost: ${stats['total_cost']:.4f}")
    print(f"Cost limit: ${stats['cost_limit']:.2f}")
    print(f"Cost remaining: ${stats['cost_remaining']:.2f}")
    print()
    
    print("Per-provider stats:")
    for provider, pstats in stats['usage'].items():
        print(f"  {provider}:")
        print(f"    Calls: {pstats['calls']}")
        print(f"    Tokens: {pstats['tokens']}")
        print(f"    Cost: ${pstats['cost']:.4f}")
        print(f"    Failures: {pstats['failures']}")


def main():
    """Run all tests"""
    print("\n🤖 Isaac AI Router Test Suite\n")
    
    # Check for API keys
    api_keys = {
        'XAI_API_KEY': os.environ.get('XAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY'),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY')
    }
    
    print("API Key Status:")
    for key, value in api_keys.items():
        status = "✓ Set" if value else "✗ Not set"
        print(f"  {key}: {status}")
    
    if not any(api_keys.values()):
        print("\n⚠️  No API keys found! Set at least one:")
        print("  export XAI_API_KEY='your-key'")
        print("  export ANTHROPIC_API_KEY='your-key'")
        print("  export OPENAI_API_KEY='your-key'")
        sys.exit(1)
    
    print()
    
    try:
        # Run tests
        test_basic_chat()
        test_tool_calling()
        test_fallback()
        test_stats()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
