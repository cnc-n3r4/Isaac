#!/usr/bin/env python3
"""
Isaac Agent Demo
Demonstrates AI agent with tool calling capabilities
"""

import os
import sys
from pathlib import Path

# Add Isaac to path
sys.path.insert(0, str(Path(__file__).parent))

from isaac.ai import IsaacAgent


def demo_file_operations():
    """Demo: File operations with AI"""
    print("=" * 60)
    print("DEMO: File Operations with AI Agent")
    print("=" * 60)
    print()
    
    agent = IsaacAgent()
    
    # Example 1: Read a file
    print("1. Reading a file...")
    result = agent.chat("Read the first 30 lines of isaac/ai/base.py")
    
    if result['success']:
        print(f"✓ Success!")
        print(f"  Tools used: {len(result['tool_executions'])}")
        for exec in result['tool_executions']:
            print(f"    - {exec['tool']}: {exec['arguments']}")
        print(f"\n  Response:\n{result['response'][:200]}...")
    else:
        print(f"✗ Failed: {result['error']}")
    
    print("\n" + "-" * 60 + "\n")
    
    # Example 2: Find files
    print("2. Finding files...")
    result = agent.chat("List all Python files in the isaac/ai directory")
    
    if result['success']:
        print(f"✓ Success!")
        print(f"  Tools used: {len(result['tool_executions'])}")
        print(f"\n  Response:\n{result['response']}")
    else:
        print(f"✗ Failed: {result['error']}")
    
    print("\n" + "-" * 60 + "\n")
    
    # Example 3: Search code
    print("3. Searching code...")
    result = agent.chat("Find all classes in the isaac/tools directory")
    
    if result['success']:
        print(f"✓ Success!")
        print(f"  Tools used: {len(result['tool_executions'])}")
        print(f"\n  Response:\n{result['response']}")
    else:
        print(f"✗ Failed: {result['error']}")
    
    print()


def demo_stats():
    """Demo: Usage statistics"""
    print("=" * 60)
    print("DEMO: Usage Statistics")
    print("=" * 60)
    print()
    
    agent = IsaacAgent()
    
    # Make a few calls
    print("Making 3 test calls...")
    for i in range(3):
        agent.chat(f"Say hello {i+1}")
    
    # Get stats
    stats = agent.get_stats()
    
    print(f"\nStatistics:")
    print(f"  Total calls: {stats['total_calls']}")
    print(f"  Total tokens: {stats['total_tokens']}")
    print(f"  Total cost: ${stats['total_cost']:.4f}")
    print(f"  Cost limit: ${stats['cost_limit']:.2f}")
    print(f"  Remaining: ${stats['cost_remaining']:.2f}")
    
    print(f"\nPer-provider breakdown:")
    for provider, pstats in stats['usage'].items():
        if pstats['calls'] > 0:
            print(f"  {provider}:")
            print(f"    Calls: {pstats['calls']}")
            print(f"    Tokens: {pstats['tokens']}")
            print(f"    Cost: ${pstats['cost']:.4f}")
            print(f"    Failures: {pstats['failures']}")
    
    print()


def demo_conversation():
    """Demo: Multi-turn conversation"""
    print("=" * 60)
    print("DEMO: Multi-turn Conversation")
    print("=" * 60)
    print()
    
    agent = IsaacAgent()
    
    # Turn 1
    print("User: What files are in the isaac/tools directory?")
    result = agent.chat("What files are in the isaac/tools directory?")
    if result['success']:
        print(f"Agent: {result['response']}\n")
    
    # Turn 2 (context maintained)
    print("User: Read the first one")
    result = agent.chat("Read the first one")
    if result['success']:
        print(f"Agent: {result['response'][:200]}...\n")
    
    # Show conversation history
    history = agent.get_conversation_history()
    print(f"Conversation has {len(history)} messages")
    
    print()


def main():
    """Run all demos"""
    print("\n🤖 Isaac AI Agent Demonstration\n")
    
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
        # Run demos
        demo_file_operations()
        demo_stats()
        demo_conversation()
        
        print("=" * 60)
        print("✅ All demos completed!")
        print("=" * 60)
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
