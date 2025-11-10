"""
Phase 3: Async AI Operations Tests
Testing async query methods for performance improvements
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest

from isaac.ai.base import AIResponse
from isaac.ai.router import AIRouter


@pytest.fixture
def mock_router():
    """Create AIRouter with mocked clients for testing"""
    with patch("isaac.ai.router.GrokClient"), \
         patch("isaac.ai.router.ClaudeClient"), \
         patch("isaac.ai.router.OpenAIClient"):
        router = AIRouter()

        # Mock a successful response
        mock_response = AIResponse(
            content="Test response",
            provider="grok",
            model="grok-beta",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            success=True
        )

        # Mock all clients to return successful responses
        for client in router.clients.values():
            if client:
                client.chat = MagicMock(return_value=mock_response)

        return router


@pytest.mark.asyncio
async def test_query_async():
    """Test async query method"""
    with patch("isaac.ai.router.GrokClient"), \
         patch("isaac.ai.router.ClaudeClient"), \
         patch("isaac.ai.router.OpenAIClient"):
        router = AIRouter()

        # Mock response
        mock_response = AIResponse(
            content="Hello, world!",
            provider="grok",
            model="grok-beta",
            usage={"prompt_tokens": 5, "completion_tokens": 3},
            success=True
        )

        # Mock client
        if router.clients.get("grok"):
            router.clients["grok"].chat = MagicMock(return_value=mock_response)

        # Test async query
        response = await router.query_async("test prompt", model="grok")

        assert response == "Hello, world!"


@pytest.mark.asyncio
async def test_chat_async():
    """Test async chat method"""
    with patch("isaac.ai.router.GrokClient"), \
         patch("isaac.ai.router.ClaudeClient"), \
         patch("isaac.ai.router.OpenAIClient"):
        router = AIRouter()

        # Mock response
        mock_response = AIResponse(
            content="Test response",
            provider="grok",
            model="grok-beta",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            success=True
        )

        # Mock client
        if router.clients.get("grok"):
            router.clients["grok"].chat = MagicMock(return_value=mock_response)

        # Test async chat
        messages = [{"role": "user", "content": "Hello"}]
        response = await router.chat_async(messages, prefer_provider="grok")

        assert response.success
        assert response.content == "Test response"


@pytest.mark.asyncio
async def test_batch_query():
    """Test batch query for concurrent processing"""
    with patch("isaac.ai.router.GrokClient"), \
         patch("isaac.ai.router.ClaudeClient"), \
         patch("isaac.ai.router.OpenAIClient"):
        router = AIRouter()

        # Mock response that includes the prompt for verification
        def mock_chat_side_effect(messages, **kwargs):
            prompt = messages[0]["content"]
            return AIResponse(
                content=f"Response to: {prompt}",
                provider="grok",
                model="grok-beta",
                usage={"prompt_tokens": 10, "completion_tokens": 20},
                success=True
            )

        # Mock client with side effect
        if router.clients.get("grok"):
            router.clients["grok"].chat = MagicMock(side_effect=mock_chat_side_effect)

        # Create test prompts
        messages_list = [
            [{"role": "user", "content": f"prompt {i}"}]
            for i in range(5)
        ]

        # Measure time
        start = time.time()
        responses = await router.batch_query(messages_list, prefer_provider="grok")
        elapsed = time.time() - start

        # Verify responses
        assert len(responses) == 5
        for i, response in enumerate(responses):
            assert response.success
            assert f"prompt {i}" in response.content

        # Batch should complete quickly (all concurrent)
        print(f"\nBatch query time: {elapsed:.2f}s")


@pytest.mark.asyncio
async def test_query_with_fallback():
    """Test fallback query with multiple providers"""
    with patch("isaac.ai.router.GrokClient"), \
         patch("isaac.ai.router.ClaudeClient"), \
         patch("isaac.ai.router.OpenAIClient"):
        router = AIRouter()

        # Mock responses - grok fails, claude succeeds
        mock_success = AIResponse(
            content="Success from Claude",
            provider="claude",
            model="claude-3",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            success=True
        )

        mock_failure = AIResponse(
            content="",
            provider="grok",
            model="grok-beta",
            error="Provider unavailable",
            success=False
        )

        # Mock clients
        if router.clients.get("grok"):
            router.clients["grok"].chat = MagicMock(return_value=mock_failure)
        if router.clients.get("claude"):
            router.clients["claude"].chat = MagicMock(return_value=mock_success)

        # Test fallback
        messages = [{"role": "user", "content": "test"}]
        response = await router.query_with_fallback(
            messages,
            providers=['grok', 'claude', 'openai']
        )

        # Should succeed with claude
        assert response.success
        assert response.provider == "claude"


@pytest.mark.asyncio
async def test_batch_performance_improvement():
    """
    Test that batch queries are significantly faster than sequential
    This simulates the 10-20x performance improvement
    """
    with patch("isaac.ai.router.GrokClient"), \
         patch("isaac.ai.router.ClaudeClient"), \
         patch("isaac.ai.router.OpenAIClient"):
        router = AIRouter()

        # Mock response with artificial delay (simulating API call)
        async def mock_chat_with_delay(messages, **kwargs):
            await asyncio.sleep(0.1)  # Simulate 100ms API call
            return AIResponse(
                content="Response",
                provider="grok",
                model="grok-beta",
                usage={"prompt_tokens": 10, "completion_tokens": 20},
                success=True
            )

        # Patch chat_async to use our mock
        router.chat_async = mock_chat_with_delay

        # Test data
        messages_list = [
            [{"role": "user", "content": f"prompt {i}"}]
            for i in range(10)
        ]

        # Sequential execution (simulated)
        start = time.time()
        sequential_responses = []
        for messages in messages_list:
            response = await router.chat_async(messages, prefer_provider="grok")
            sequential_responses.append(response)
        sequential_time = time.time() - start

        # Concurrent execution
        start = time.time()
        concurrent_responses = await router.batch_query(messages_list, prefer_provider="grok")
        concurrent_time = time.time() - start

        # Calculate speedup
        speedup = sequential_time / concurrent_time

        print(f"\nSequential: {sequential_time:.2f}s")
        print(f"Concurrent: {concurrent_time:.2f}s")
        print(f"Speedup: {speedup:.1f}x")

        # Batch should be much faster (close to 10x with 10 queries)
        assert concurrent_time < sequential_time
        assert speedup > 5, f"Speedup only {speedup:.1f}x, expected >5x"


def test_synchronous_query_backward_compatibility():
    """Test that synchronous query method still works"""
    with patch("isaac.ai.router.GrokClient"), \
         patch("isaac.ai.router.ClaudeClient"), \
         patch("isaac.ai.router.OpenAIClient"):
        router = AIRouter()

        # Mock response
        mock_response = AIResponse(
            content="Sync response",
            provider="grok",
            model="grok-beta",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            success=True
        )

        # Mock client
        if router.clients.get("grok"):
            router.clients["grok"].chat = MagicMock(return_value=mock_response)

        # Test synchronous query (backward compatibility)
        response = router.query("test prompt", model="grok")

        assert response == "Sync response"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
