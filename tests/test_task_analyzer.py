#!/usr/bin/env python3
"""
Test TaskAnalyzer - Phase 3 Enhanced AI Routing

Tests automatic task complexity detection and AI provider selection.
"""

import sys
from pathlib import Path

# Add Isaac to path
sys.path.insert(0, str(Path(__file__).parent))

from isaac.ai.task_analyzer import TaskAnalyzer, TaskComplexity, TaskType


def test_complexity_detection():
    """Test task complexity detection"""
    print("=" * 60)
    print("TEST 1: Complexity Detection")
    print("=" * 60)

    analyzer = TaskAnalyzer()

    test_cases = [
        ("Hi, how are you?", TaskComplexity.SIMPLE),
        ("What is 2+2?", TaskComplexity.SIMPLE),
        ("Explain the difference between async and sync programming", TaskComplexity.MEDIUM),
        ("Debug the authentication issue in my login system", TaskComplexity.COMPLEX),
        ("Design a scalable microservices architecture for high-traffic e-commerce", TaskComplexity.EXPERT),
        ("Review this code and suggest optimizations", TaskComplexity.COMPLEX),
    ]

    passed = 0
    for message, expected in test_cases:
        messages = [{"role": "user", "content": message}]
        result = analyzer.analyze_task(messages)

        detected = TaskComplexity(result['complexity'])
        status = "✓" if detected == expected else "✗"

        print(f"{status} '{message[:50]}...'")
        print(f"   Expected: {expected.value}, Got: {detected.value}")

        if detected == expected:
            passed += 1

    print(f"\nPassed: {passed}/{len(test_cases)}")
    print()


def test_task_type_detection():
    """Test task type detection"""
    print("=" * 60)
    print("TEST 2: Task Type Detection")
    print("=" * 60)

    analyzer = TaskAnalyzer()

    test_cases = [
        ("Write a function to calculate factorial", TaskType.CODE_WRITE),
        ("Show me the contents of main.py", TaskType.CODE_READ),
        ("Fix the bug in the authentication module", TaskType.CODE_WRITE),
        ("Analyze the performance of this algorithm", TaskType.ANALYSIS),
        ("What's the weather like?", TaskType.CHAT),
        ("Search for TODO comments in the codebase", TaskType.SEARCH),
    ]

    passed = 0
    for message, expected in test_cases:
        messages = [{"role": "user", "content": message}]
        result = analyzer.analyze_task(messages)

        detected = TaskType(result['task_type'])
        status = "✓" if detected == expected else "✗"

        print(f"{status} '{message[:50]}...'")
        print(f"   Expected: {expected.value}, Got: {detected.value}")

        if detected == expected:
            passed += 1

    print(f"\nPassed: {passed}/{len(test_cases)}")
    print()


def test_provider_selection():
    """Test AI provider selection logic"""
    print("=" * 60)
    print("TEST 3: Provider Selection")
    print("=" * 60)

    analyzer = TaskAnalyzer()

    test_cases = [
        ("What is Python?", "openai"),  # Simple -> cheap
        ("Explain decorators in Python", "openai"),  # Simple explain -> cheap (updated)
        ("Debug this complex race condition", "claude"),  # Complex code -> Claude
        ("Design a distributed caching system with high availability", "claude"),  # Expert -> Claude
        ("Write a REST API endpoint for user authentication", "claude"),  # Code write -> Claude
    ]

    passed = 0
    for message, expected in test_cases:
        messages = [{"role": "user", "content": message}]
        result = analyzer.analyze_task(messages)

        provider = result['recommended_provider']
        status = "✓" if provider == expected else "✗"

        print(f"{status} '{message[:50]}...'")
        print(f"   Expected: {expected}, Got: {provider}")
        print(f"   Reasoning: {result['reasoning']}")

        if provider == expected:
            passed += 1

    print(f"\nPassed: {passed}/{len(test_cases)}")
    print()


def test_detailed_analysis():
    """Test detailed task analysis output"""
    print("=" * 60)
    print("TEST 4: Detailed Analysis")
    print("=" * 60)

    analyzer = TaskAnalyzer()

    message = "Debug the authentication bug in login.py and implement a fix with proper error handling"
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": message}
    ]

    # Add some tools to simulate tool calling scenario
    tools = [
        {"function": {"name": "read_file"}},
        {"function": {"name": "edit_file"}},
        {"function": {"name": "grep"}},
    ]

    result = analyzer.analyze_task(messages, tools=tools)

    print(f"Task: {message}\n")
    print(f"Complexity: {result['complexity']}")
    print(f"Task Type: {result['task_type']}")
    print(f"Recommended Provider: {result['recommended_provider']}")
    print(f"Fallback Providers: {', '.join(result['fallback_providers'])}")
    print(f"Token Estimate: {result['token_estimate']}")
    print(f"Cost Estimate: ${result['cost_estimate']['total']:.6f}")
    print(f"Reasoning: {result['reasoning']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print()


def test_provider_comparison():
    """Test provider comparison functionality"""
    print("=" * 60)
    print("TEST 5: Provider Comparison")
    print("=" * 60)

    analyzer = TaskAnalyzer()

    # Compare providers for a complex code task
    comparison = analyzer.compare_providers(
        TaskComplexity.COMPLEX,
        TaskType.CODE_WRITE
    )

    print("Providers ranked for: COMPLEX CODE_WRITE\n")
    for i, provider_info in enumerate(comparison, 1):
        print(f"{i}. {provider_info['provider'].upper()}")
        print(f"   Score: {provider_info['score']:.2f}")
        print(f"   Speed: {provider_info['speed']}")
        print(f"   Cost: ${provider_info['cost_per_1m']['input']:.2f}/$"
              f"{provider_info['cost_per_1m']['output']:.2f} per 1M tokens")
        print(f"   Strengths: {', '.join(provider_info['strengths'])}")
        print()


def test_cost_estimation():
    """Test cost estimation accuracy"""
    print("=" * 60)
    print("TEST 6: Cost Estimation")
    print("=" * 60)

    analyzer = TaskAnalyzer()

    # Short simple task
    messages1 = [{"role": "user", "content": "What is 2+2?"}]
    result1 = analyzer.analyze_task(messages1)

    # Long complex task
    long_message = "Analyze this codebase and provide a comprehensive review. " * 50
    messages2 = [{"role": "user", "content": long_message}]
    result2 = analyzer.analyze_task(messages2)

    print("Short simple task:")
    print(f"  Provider: {result1['recommended_provider']}")
    print(f"  Tokens: {result1['token_estimate']['total']}")
    print(f"  Cost: ${result1['cost_estimate']['total']:.6f}\n")

    print("Long complex task:")
    print(f"  Provider: {result2['recommended_provider']}")
    print(f"  Tokens: {result2['token_estimate']['total']}")
    print(f"  Cost: ${result2['cost_estimate']['total']:.6f}\n")

    # Verify cost is higher for longer task
    assert result2['cost_estimate']['total'] > result1['cost_estimate']['total'], \
        "Cost should be higher for longer task"
    print("✓ Cost scales with task size")
    print()


def test_context_preferences():
    """Test context-based provider preferences"""
    print("=" * 60)
    print("TEST 7: Context Preferences")
    print("=" * 60)

    analyzer = TaskAnalyzer()

    messages = [{"role": "user", "content": "Explain async/await in Python"}]

    # Test with user preference
    context = {'prefer_provider': 'claude'}
    result = analyzer.analyze_task(messages, context=context)

    print("Task: Explain async/await (medium complexity)")
    print(f"Without preference: Would use {analyzer.analyze_task(messages)['recommended_provider']}")
    print(f"With preference for Claude: {result['recommended_provider']}")

    assert result['recommended_provider'] == 'claude', "Should respect user preference"
    print("✓ User preferences respected")
    print()


def main():
    """Run all tests"""
    print("\n🧪 TaskAnalyzer Test Suite - Phase 3\n")

    try:
        test_complexity_detection()
        test_task_type_detection()
        test_provider_selection()
        test_detailed_analysis()
        test_provider_comparison()
        test_cost_estimation()
        test_context_preferences()

        print("=" * 60)
        print("✅ All tests completed!")
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


if __name__ == '__main__':
    main()
