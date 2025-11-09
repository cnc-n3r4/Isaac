#!/usr/bin/env python3
"""
Test script for Phase 7: RAG Query Engine
"""

import sys
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from isaac.ai.rag_engine import RAGQueryEngine, CodebaseAwareChat

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_rag_engine_components():
    """Test RAG engine initialization and configuration"""
    print("\n=== Testing RAG Engine Components ===\n")

    # Create mock components
    class MockXaiClient:
        def chat(self, prompt, system_prompt=None):
            if system_prompt:
                return f"Response using context: {len(system_prompt)} chars of context"
            return f"Response without context"

    class MockKnowledgeBase:
        def search(self, query, top_k=5):
            # Return mock search results
            return {
                'success': True,
                'results': [
                    {
                        'content': 'class XaiClient:\n    """AI client"""',
                        'metadata': {
                            'file': 'isaac/ai/xai_client.py',
                            'start_line': 11,
                            'end_line': 12
                        },
                        'score': 0.95
                    },
                    {
                        'content': 'def chat(self, prompt):',
                        'metadata': {
                            'file': 'isaac/ai/xai_client.py',
                            'start_line': 154,
                            'end_line': 154
                        },
                        'score': 0.85
                    }
                ]
            }

    xai_client = MockXaiClient()
    kb = MockKnowledgeBase()

    # Create RAG engine
    rag = RAGQueryEngine(xai_client, kb)

    print("✓ RAG engine initialized")
    print(f"  Max context chunks: {rag.max_context_chunks}")
    print(f"  Context char limit: {rag.context_char_limit}")
    print(f"  Relevance threshold: {rag.relevance_threshold}")

    # Test configuration
    rag.configure(
        max_context_chunks=3,
        context_char_limit=2000,
        relevance_threshold=0.7
    )

    assert rag.max_context_chunks == 3
    assert rag.context_char_limit == 2000
    assert rag.relevance_threshold == 0.7

    print("✓ Configuration works")

    return True


def test_context_building():
    """Test context building from search results"""
    print("\n=== Testing Context Building ===\n")

    class MockXaiClient:
        def chat(self, prompt, system_prompt=None):
            return "Mock response"

    class MockKnowledgeBase:
        def search(self, query, top_k=5):
            return {
                'success': True,
                'results': [
                    {
                        'content': 'def authenticate(user, password):\n    """Verify credentials"""',
                        'metadata': {
                            'file': 'auth/login.py',
                            'start_line': 10,
                            'end_line': 11
                        },
                        'score': 0.92
                    },
                    {
                        'content': 'class AuthManager:\n    def login(self):',
                        'metadata': {
                            'file': 'auth/manager.py',
                            'start_line': 5,
                            'end_line': 6
                        },
                        'score': 0.88
                    }
                ]
            }

    rag = RAGQueryEngine(MockXaiClient(), MockKnowledgeBase())

    # Perform search
    results = rag._search_codebase("authentication", top_k=5)
    assert len(results) == 2, "Should return filtered results"
    print(f"✓ Search returned {len(results)} results")

    # Build context
    context = rag._build_context(results, include_file_paths=True)
    assert len(context) > 0, "Context should not be empty"
    assert 'auth/login.py' in context, "Should include file paths"
    assert 'authenticate' in context, "Should include code content"
    print(f"✓ Context built: {len(context)} chars")
    print(f"  Includes file paths: {'✓' if 'auth/login.py' in context else '✗'}")
    print(f"  Includes code content: {'✓' if 'authenticate' in context else '✗'}")

    return True


def test_rag_vs_direct_query():
    """Test RAG vs direct query modes"""
    print("\n=== Testing RAG vs Direct Query ===\n")

    class MockXaiClient:
        def __init__(self):
            self.last_system_prompt = None

        def chat(self, prompt, system_prompt=None):
            self.last_system_prompt = system_prompt
            if system_prompt:
                return f"RAG response (with {len(system_prompt)} chars context)"
            return "Direct response (no context)"

    class MockKnowledgeBase:
        def search(self, query, top_k=5):
            return {
                'success': True,
                'results': [
                    {
                        'content': 'relevant code',
                        'metadata': {'file': 'test.py', 'start_line': 1, 'end_line': 1},
                        'score': 0.9
                    }
                ]
            }

    client = MockXaiClient()
    kb = MockKnowledgeBase()
    rag = RAGQueryEngine(client, kb)

    # Test RAG query (with codebase)
    print("Test 1: RAG query (use_codebase=True)")
    result = rag.query("test query", use_codebase=True)
    assert result['success'], "RAG query should succeed"
    assert result['source'] == 'rag', "Should use RAG"
    assert len(result['context_used']) > 0, "Should have context"
    assert client.last_system_prompt is not None, "Should inject context"
    print(f"  ✓ Used RAG with {len(result['context_used'])} context chunks")

    # Test direct query (without codebase)
    print("\nTest 2: Direct query (use_codebase=False)")
    client.last_system_prompt = None
    result = rag.query("test query", use_codebase=False)
    assert result['success'], "Direct query should succeed"
    assert result['source'] == 'direct', "Should use direct"
    assert len(result['context_used']) == 0, "Should have no context"
    assert client.last_system_prompt is None, "Should not inject context"
    print(f"  ✓ Used direct query (no context)")

    return True


def test_fallback_integration():
    """Test RAG engine with fallback manager"""
    print("\n=== Testing Fallback Integration ===\n")

    from isaac.core.fallback_manager import FallbackManager

    class FailingXaiClient:
        def __init__(self):
            self.call_count = 0

        def chat(self, prompt, system_prompt=None):
            self.call_count += 1
            if self.call_count <= 2:
                raise Exception("API temporarily unavailable")
            return "Success after retries"

    class MockKnowledgeBase:
        def search(self, query, top_k=5):
            return {
                'success': True,
                'results': []  # No results, will use direct query
            }

    fallback_mgr = FallbackManager()
    client = FailingXaiClient()
    kb = MockKnowledgeBase()

    rag = RAGQueryEngine(client, kb, fallback_manager=fallback_mgr)

    # First call should fail
    result = rag.query("test")
    assert not result['success'], "Should fail on first try"
    print("  ✓ First call failed as expected")

    # Second call should also fail
    result = rag.query("test")
    assert not result['success'], "Should fail on second try"
    print("  ✓ Second call failed as expected")

    # Third call should succeed
    result = rag.query("test")
    assert result['success'], "Should succeed on third try"
    print("  ✓ Third call succeeded (service recovered)")

    return True


def test_relevance_filtering():
    """Test relevance score filtering"""
    print("\n=== Testing Relevance Filtering ===\n")

    class MockXaiClient:
        def chat(self, prompt, system_prompt=None):
            return "Response"

    class MockKnowledgeBase:
        def search(self, query, top_k=5):
            return {
                'success': True,
                'results': [
                    {'content': 'high relevance', 'metadata': {}, 'score': 0.9},
                    {'content': 'medium relevance', 'metadata': {}, 'score': 0.6},
                    {'content': 'low relevance', 'metadata': {}, 'score': 0.3},
                    {'content': 'very low relevance', 'metadata': {}, 'score': 0.1}
                ]
            }

    rag = RAGQueryEngine(MockXaiClient(), MockKnowledgeBase())

    # Default threshold is 0.5
    results = rag._search_codebase("test", top_k=10)
    assert len(results) == 2, "Should filter out results below 0.5 threshold"
    print(f"✓ Filtered to {len(results)}/4 results (threshold=0.5)")

    # Change threshold
    rag.configure(relevance_threshold=0.7)
    results = rag._search_codebase("test", top_k=10)
    assert len(results) == 1, "Should filter out results below 0.7 threshold"
    print(f"✓ Filtered to {len(results)}/4 results (threshold=0.7)")

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Phase 7: RAG Query Engine Test Suite")
    print("=" * 60)

    tests = [
        ("RAG Engine Components", test_rag_engine_components),
        ("Context Building", test_context_building),
        ("RAG vs Direct Query", test_rag_vs_direct_query),
        ("Fallback Integration", test_fallback_integration),
        ("Relevance Filtering", test_relevance_filtering),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {name} test passed")
            else:
                failed += 1
                print(f"\n✗ {name} test failed")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} test failed with error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
