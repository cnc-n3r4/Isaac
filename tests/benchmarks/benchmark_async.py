#!/usr/bin/env python3
"""
Phase 3: Async AI Operations Benchmark
Demonstrates 10-20x performance improvement for batch operations
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

from isaac.ai.base import AIResponse
from isaac.ai.router import AIRouter


async def benchmark_async_operations():
    """Benchmark async vs sync AI operations"""
    print("=" * 80)
    print("PHASE 3: ASYNC AI OPERATIONS BENCHMARK")
    print("=" * 80)
    print()

    with patch("isaac.ai.router.GrokClient"), \
         patch("isaac.ai.router.ClaudeClient"), \
         patch("isaac.ai.router.OpenAIClient"):

        router = AIRouter()

        # Mock response with simulated API latency
        def mock_chat(messages, **kwargs):
            # Simulate API latency (200ms typical)
            time.sleep(0.2)
            return AIResponse(
                content="Test response",
                provider="grok",
                model="grok-beta",
                usage={"prompt_tokens": 100, "completion_tokens": 50},
                success=True
            )

        # Apply mock to client
        if router.clients.get("grok"):
            router.clients["grok"].chat = MagicMock(side_effect=mock_chat)

        # Test with different batch sizes
        batch_sizes = [5, 10, 20]

        for batch_size in batch_sizes:
            print(f"\n--- Batch Size: {batch_size} queries ---\n")

            # Create prompts
            prompts = [f"Query {i}" for i in range(batch_size)]
            messages_list = [
                [{"role": "user", "content": prompt}]
                for prompt in prompts
            ]

            # 1. Sequential execution (baseline)
            print("1. Sequential execution...")
            start = time.time()
            sequential_responses = []
            for messages in messages_list:
                response = router.chat(messages, prefer_provider="grok")
                sequential_responses.append(response)
            sequential_time = time.time() - start

            print(f"   Time: {sequential_time:.2f}s")
            print(f"   Throughput: {batch_size/sequential_time:.1f} queries/sec")

            # 2. Concurrent execution (async)
            print("\n2. Concurrent execution (async)...")
            start = time.time()
            concurrent_responses = await router.batch_query(messages_list, prefer_provider="grok")
            concurrent_time = time.time() - start

            print(f"   Time: {concurrent_time:.2f}s")
            print(f"   Throughput: {batch_size/concurrent_time:.1f} queries/sec")

            # 3. Calculate improvement
            speedup = sequential_time / concurrent_time
            improvement_pct = ((sequential_time - concurrent_time) / sequential_time) * 100

            print(f"\n3. Performance Improvement:")
            print(f"   Speedup: {speedup:.1f}x faster")
            print(f"   Time saved: {improvement_pct:.1f}%")
            print(f"   Time reduction: {sequential_time - concurrent_time:.2f}s")

            if speedup >= 10:
                print(f"   ✅ Target achieved (10-20x)")
            elif speedup >= 5:
                print(f"   ⚠️  Good but below target ({speedup:.1f}x vs 10x target)")
            else:
                print(f"   ❌ Below expectations ({speedup:.1f}x)")

    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)


async def benchmark_fallback_providers():
    """Benchmark concurrent fallback vs sequential fallback"""
    print("\n\n" + "=" * 80)
    print("FALLBACK PROVIDER BENCHMARK")
    print("=" * 80)
    print()

    with patch("isaac.ai.router.GrokClient"), \
         patch("isaac.ai.router.ClaudeClient"), \
         patch("isaac.ai.router.OpenAIClient"):

        router = AIRouter()

        # Mock responses - first 2 providers fail, third succeeds
        call_order = []

        def mock_grok_chat(messages, **kwargs):
            call_order.append("grok")
            time.sleep(0.3)  # Slow failure
            return AIResponse(
                content="",
                provider="grok",
                error="Timeout",
                success=False
            )

        def mock_claude_chat(messages, **kwargs):
            call_order.append("claude")
            time.sleep(0.2)  # Faster failure
            return AIResponse(
                content="",
                provider="claude",
                error="Rate limited",
                success=False
            )

        def mock_openai_chat(messages, **kwargs):
            call_order.append("openai")
            time.sleep(0.1)  # Fast success
            return AIResponse(
                content="Success!",
                provider="openai",
                model="gpt-4",
                usage={"prompt_tokens": 10, "completion_tokens": 5},
                success=True
            )

        # Apply mocks
        if router.clients.get("grok"):
            router.clients["grok"].chat = MagicMock(side_effect=mock_grok_chat)
        if router.clients.get("claude"):
            router.clients["claude"].chat = MagicMock(side_effect=mock_claude_chat)
        if router.clients.get("openai"):
            router.clients["openai"].chat = MagicMock(side_effect=mock_openai_chat)

        messages = [{"role": "user", "content": "test"}]

        # 1. Sequential fallback (default behavior)
        print("1. Sequential fallback (tries providers one by one)...")
        call_order.clear()
        start = time.time()
        response = router.chat(messages)
        sequential_time = time.time() - start

        print(f"   Time: {sequential_time:.2f}s")
        print(f"   Call order: {' -> '.join(call_order)}")
        print(f"   Result: {response.provider if response.success else 'All failed'}")

        # 2. Concurrent fallback (tries all at once)
        print("\n2. Concurrent fallback (tries all providers simultaneously)...")
        call_order.clear()
        start = time.time()
        response = await router.query_with_fallback(messages, providers=['grok', 'claude', 'openai'])
        concurrent_time = time.time() - start

        print(f"   Time: {concurrent_time:.2f}s")
        print(f"   Tried providers: grok, claude, openai (all at once)")
        print(f"   Winner: {response.provider if response.success else 'All failed'}")

        # 3. Calculate improvement
        if sequential_time > 0:
            speedup = sequential_time / concurrent_time
            print(f"\n3. Performance Improvement:")
            print(f"   Speedup: {speedup:.1f}x faster")
            print(f"   Time saved: {sequential_time - concurrent_time:.2f}s")
            print(f"   Note: Returns fastest successful provider!")

    print("\n" + "=" * 80)


async def benchmark_real_world_scenario():
    """Benchmark a real-world scenario: analyzing multiple files"""
    print("\n\n" + "=" * 80)
    print("REAL-WORLD SCENARIO: Analyzing 15 Code Files")
    print("=" * 80)
    print()

    with patch("isaac.ai.router.GrokClient"), \
         patch("isaac.ai.router.ClaudeClient"), \
         patch("isaac.ai.router.OpenAIClient"):

        router = AIRouter()

        # Mock response with realistic latency
        def mock_chat(messages, **kwargs):
            time.sleep(0.25)  # 250ms per file analysis
            return AIResponse(
                content="File analysis complete. No issues found.",
                provider="grok",
                model="grok-beta",
                usage={"prompt_tokens": 500, "completion_tokens": 100},
                success=True
            )

        if router.clients.get("grok"):
            router.clients["grok"].chat = MagicMock(side_effect=mock_chat)

        # Simulate analyzing 15 Python files
        files = [f"module_{i}.py" for i in range(1, 16)]
        messages_list = [
            [{"role": "user", "content": f"Analyze this file: {file}"}]
            for file in files
        ]

        print("Scenario: Analyze 15 Python files for code quality")
        print(f"Files: {', '.join(files)}")
        print()

        # Sequential
        print("Sequential analysis (one file at a time):")
        start = time.time()
        for messages in messages_list:
            router.chat(messages, prefer_provider="grok")
        sequential_time = time.time() - start
        print(f"  Total time: {sequential_time:.1f}s")
        print(f"  Average per file: {sequential_time/15:.2f}s")

        # Concurrent
        print("\nConcurrent analysis (all files at once):")
        start = time.time()
        await router.batch_query(messages_list, prefer_provider="grok")
        concurrent_time = time.time() - start
        print(f"  Total time: {concurrent_time:.1f}s")
        print(f"  Average per file: {concurrent_time/15:.2f}s")

        # Results
        speedup = sequential_time / concurrent_time
        time_saved = sequential_time - concurrent_time

        print(f"\nResults:")
        print(f"  ⚡ {speedup:.1f}x faster")
        print(f"  ⏱️  Saved {time_saved:.1f}s ({time_saved/60:.1f} minutes)")
        print(f"  💰 Same cost, way faster!")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    async def run_all_benchmarks():
        await benchmark_async_operations()
        await benchmark_fallback_providers()
        await benchmark_real_world_scenario()

    print("\n🚀 Starting Phase 3 Async Benchmarks...\n")
    asyncio.run(run_all_benchmarks())
    print("\n✅ All benchmarks complete!\n")
