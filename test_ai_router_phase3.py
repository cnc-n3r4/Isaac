#!/usr/bin/env python3
"""
Test AIRouter Phase 3 Integration

Tests the integration of TaskAnalyzer and CostOptimizer into AIRouter.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add Isaac to path
sys.path.insert(0, str(Path(__file__).parent))

from isaac.ai.router import AIRouter
from isaac.ai.base import AIResponse
from isaac.ai.routing_config import RoutingConfigManager
from isaac.ai.cost_optimizer import CostOptimizer


def test_router_initialization():
    """Test Phase 3 router initialization"""
    print("=" * 60)
    print("TEST 1: Router Initialization")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'ai_config.json'

        # Mock environment to avoid API key errors
        with patch.dict('os.environ', {}, clear=True):
            router = AIRouter(config_path=config_path)

            # Verify Phase 3 components initialized
            assert router.task_analyzer is not None, "TaskAnalyzer should be initialized"
            assert router.cost_optimizer is not None, "CostOptimizer should be initialized"
            assert router.routing_config is not None, "RoutingConfig should be initialized"

            print("✓ TaskAnalyzer initialized")
            print("✓ CostOptimizer initialized")
            print("✓ RoutingConfig initialized")

            # Verify performance stats structure
            assert 'grok' in router.performance_stats
            assert 'claude' in router.performance_stats
            assert 'openai' in router.performance_stats
            print("✓ Performance tracking initialized")

    print()


def test_task_analyzer_integration():
    """Test TaskAnalyzer is called during chat"""
    print("=" * 60)
    print("TEST 2: TaskAnalyzer Integration")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'ai_config.json'

        with patch.dict('os.environ', {}, clear=True):
            router = AIRouter(config_path=config_path)

            # Mock task analyzer
            mock_analysis = {
                'complexity': 'complex',
                'task_type': 'code_write',
                'recommended_provider': 'claude',
                'estimated_tokens': {'input': 1000, 'output': 500},
                'reasoning': 'Code writing requires Claude'
            }
            router.task_analyzer.analyze_task = Mock(return_value=mock_analysis)

            # Mock cost optimizer affordability check
            router.cost_optimizer.can_afford_request = Mock(return_value=(True, "Within budget"))

            # Mock all clients to return None (no API keys)
            router.clients = {'grok': None, 'claude': None, 'openai': None}

            # Try to make a request (will fail due to no clients, but should call analyzer)
            messages = [{"role": "user", "content": "Write a sorting function"}]
            response = router.chat(messages)

            # Verify TaskAnalyzer was called
            router.task_analyzer.analyze_task.assert_called_once()
            call_args = router.task_analyzer.analyze_task.call_args
            assert call_args[1]['messages'] == messages
            print("✓ TaskAnalyzer called with correct messages")

            # Verify cost check was performed
            router.cost_optimizer.can_afford_request.assert_called_once()
            print("✓ Cost affordability checked")

    print()


def test_cost_tracking_integration():
    """Test CostOptimizer tracks successful requests"""
    print("=" * 60)
    print("TEST 3: Cost Tracking Integration")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'ai_config.json'

        with patch.dict('os.environ', {}, clear=True):
            router = AIRouter(config_path=config_path)

            # Mock successful response (success is derived from error=None)
            mock_response = AIResponse(
                content="Here's a sorting function...",
                provider='claude',
                usage={'prompt_tokens': 1000, 'completion_tokens': 500}
            )

            # Mock client
            mock_client = Mock()
            mock_client.chat = Mock(return_value=mock_response)
            mock_client.get_cost_estimate = Mock(return_value=0.015)  # For legacy stats
            router.clients['claude'] = mock_client

            # Mock task analysis
            router.task_analyzer.analyze_task = Mock(return_value={
                'complexity': 'medium',
                'task_type': 'code_write',
                'recommended_provider': 'claude',
                'estimated_tokens': {'input': 1000, 'output': 500},
                'reasoning': 'Test'
            })

            # Mock cost optimizer methods
            router.cost_optimizer.can_afford_request = Mock(return_value=(True, "Within budget"))

            # Store original track_usage for verification
            track_usage_mock = Mock(return_value={
                'cost': 0.015,
                'daily_total': 0.015,
                'monthly_total': 0.015,
                'budget_status': 'ok'
            })
            router.cost_optimizer.track_usage = track_usage_mock

            # Make request
            messages = [{"role": "user", "content": "Write a function"}]
            response = router.chat(messages)

            # Verify tracking was called
            assert track_usage_mock.called, "track_usage should have been called"
            call_kwargs = track_usage_mock.call_args[1]
            assert call_kwargs['provider'] == 'claude', f"Expected claude, got {call_kwargs['provider']}"
            assert call_kwargs['input_tokens'] == 1000, f"Expected 1000 input tokens, got {call_kwargs['input_tokens']}"
            assert call_kwargs['output_tokens'] == 500, f"Expected 500 output tokens, got {call_kwargs['output_tokens']}"
            assert call_kwargs['task_type'] == 'code_write', f"Expected code_write, got {call_kwargs['task_type']}"
            print("✓ Cost tracking called with correct parameters")

            # Verify metadata in response
            assert 'routing' in response.metadata
            assert 'cost' in response.metadata
            assert 'performance' in response.metadata
            print("✓ Response metadata includes routing info")
            print("✓ Response metadata includes cost info")
            print("✓ Response metadata includes performance info")

    print()


def test_budget_enforcement():
    """Test budget limits are enforced"""
    print("=" * 60)
    print("TEST 4: Budget Enforcement")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'ai_config.json'

        with patch.dict('os.environ', {}, clear=True):
            router = AIRouter(config_path=config_path)

            # Mock task analysis
            router.task_analyzer.analyze_task = Mock(return_value={
                'complexity': 'complex',
                'task_type': 'analysis',
                'recommended_provider': 'claude',
                'estimated_tokens': {'input': 10000, 'output': 5000},
                'reasoning': 'Test'
            })

            # Mock budget exceeded
            router.cost_optimizer.can_afford_request = Mock(return_value=(False, "Daily budget exceeded"))
            router.cost_optimizer.suggest_cheaper_provider = Mock(return_value=None)

            # Make request
            messages = [{"role": "user", "content": "Complex analysis"}]
            response = router.chat(messages)

            # Should return error about budget
            assert not response.success
            assert 'budget' in response.error.lower()
            print("✓ Request rejected when budget exceeded")

            # Verify metadata includes budget status
            assert 'budget_status' in response.metadata
            print("✓ Error response includes budget status")

    print()


def test_cheaper_provider_fallback():
    """Test fallback to cheaper provider when budget is tight"""
    print("=" * 60)
    print("TEST 5: Cheaper Provider Fallback")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'ai_config.json'

        with patch.dict('os.environ', {}, clear=True):
            router = AIRouter(config_path=config_path)

            # Mock task analysis recommending expensive provider
            router.task_analyzer.analyze_task = Mock(return_value={
                'complexity': 'medium',
                'task_type': 'chat',
                'recommended_provider': 'claude',
                'estimated_tokens': {'input': 1000, 'output': 500},
                'reasoning': 'Test'
            })

            # Mock: can't afford Claude, but can use OpenAI
            router.cost_optimizer.can_afford_request = Mock(return_value=(False, "Too expensive"))
            router.cost_optimizer.suggest_cheaper_provider = Mock(return_value='openai')

            # Mock OpenAI client
            mock_response = AIResponse(
                content="Response from OpenAI",
                provider='openai',
                usage={'prompt_tokens': 1000, 'completion_tokens': 500}
            )
            mock_client = Mock()
            mock_client.chat = Mock(return_value=mock_response)
            mock_client.get_cost_estimate = Mock(return_value=0.002)  # For legacy stats
            router.clients['openai'] = mock_client

            # Mock cost tracking
            router.cost_optimizer.track_usage = Mock(return_value={
                'cost': 0.002,
                'daily_total': 0.002,
                'monthly_total': 0.002,
                'budget_status': 'ok'
            })

            # Make request
            messages = [{"role": "user", "content": "Simple question"}]
            response = router.chat(messages)

            # Should succeed with cheaper provider
            assert response.success
            assert response.provider == 'openai'
            print("✓ Switched to cheaper provider when budget tight")

            # Verify routing metadata shows fallback
            assert response.metadata['routing']['recommended_provider'] == 'openai'
            assert response.metadata['routing']['actual_provider'] == 'openai'
            print("✓ Routing metadata shows provider switch")

    print()


def test_performance_tracking():
    """Test performance metrics are tracked"""
    print("=" * 60)
    print("TEST 6: Performance Tracking")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'ai_config.json'

        with patch.dict('os.environ', {}, clear=True):
            router = AIRouter(config_path=config_path)

            # Mock successful response
            mock_response = AIResponse(
                content="Response",
                provider='grok',
                usage={'prompt_tokens': 100, 'completion_tokens': 50}
            )
            mock_client = Mock()
            mock_client.chat = Mock(return_value=mock_response)
            mock_client.get_cost_estimate = Mock(return_value=0.001)  # For legacy stats
            router.clients['grok'] = mock_client

            # Mock task analysis
            router.task_analyzer.analyze_task = Mock(return_value={
                'complexity': 'simple',
                'task_type': 'chat',
                'recommended_provider': 'grok',
                'estimated_tokens': {'input': 100, 'output': 50},
                'reasoning': 'Simple task'
            })

            # Mock cost optimizer
            router.cost_optimizer.can_afford_request = Mock(return_value=(True, "Within budget"))
            router.cost_optimizer.track_usage = Mock(return_value={
                'cost': 0.001,
                'daily_total': 0.001,
                'monthly_total': 0.001,
                'budget_status': 'ok'
            })

            # Make request
            messages = [{"role": "user", "content": "Quick question"}]
            response = router.chat(messages)

            # Verify performance stats updated
            assert router.performance_stats['grok']['requests'] == 1
            assert router.performance_stats['grok']['total_time'] > 0
            assert router.performance_stats['grok']['avg_time'] > 0
            print("✓ Performance stats updated")

            # Verify response metadata includes performance
            assert 'performance' in response.metadata
            assert 'response_time' in response.metadata['performance']
            assert response.metadata['performance']['response_time'] > 0
            print("✓ Response includes performance metrics")

    print()


def test_enhanced_stats():
    """Test Phase 3 enhanced statistics"""
    print("=" * 60)
    print("TEST 7: Enhanced Statistics")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'ai_config.json'

        with patch.dict('os.environ', {}, clear=True):
            router = AIRouter(config_path=config_path)

            # Get stats
            stats = router.get_stats()

            # Verify Phase 3 stats included
            assert 'cost_tracking' in stats
            assert 'performance' in stats
            assert 'routing_config' in stats
            print("✓ Stats include cost_tracking")
            print("✓ Stats include performance")
            print("✓ Stats include routing_config")

            # Verify cost tracking structure
            assert 'daily' in stats['cost_tracking']
            assert 'monthly' in stats['cost_tracking']
            assert 'forecast' in stats['cost_tracking']
            assert 'report' in stats['cost_tracking']
            print("✓ Cost tracking has daily/monthly/forecast/report")

    print()


def test_budget_health_check():
    """Test budget health check utility"""
    print("=" * 60)
    print("TEST 8: Budget Health Check")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'ai_config.json'

        with patch.dict('os.environ', {}, clear=True):
            router = AIRouter(config_path=config_path)

            # Get budget health
            health = router.check_budget_health()

            # Verify structure
            assert 'budget_status' in health
            assert 'forecast' in health
            assert 'recommendations' in health
            assert 'health_score' in health
            print("✓ Budget health has all required fields")

            # Verify health score is valid
            assert health['health_score'] in ['excellent', 'good', 'warning', 'critical']
            print(f"✓ Health score: {health['health_score']}")

    print()


def test_task_preview():
    """Test task preview (analyze without executing)"""
    print("=" * 60)
    print("TEST 9: Task Preview")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'ai_config.json'

        with patch.dict('os.environ', {}, clear=True):
            router = AIRouter(config_path=config_path)

            # Preview a task
            messages = [{"role": "user", "content": "Write a complex algorithm"}]
            analysis = router.analyze_task_preview(messages)

            # Verify analysis structure
            assert 'complexity' in analysis
            assert 'task_type' in analysis
            assert 'recommended_provider' in analysis
            assert 'reasoning' in analysis
            print("✓ Task preview returns complete analysis")
            print(f"  Complexity: {analysis['complexity']}")
            print(f"  Task type: {analysis['task_type']}")
            print(f"  Provider: {analysis['recommended_provider']}")

    print()


def main():
    """Run all Phase 3 integration tests"""
    print("\n🧪 AIRouter Phase 3 Integration Test Suite\n")

    try:
        test_router_initialization()
        test_task_analyzer_integration()
        test_cost_tracking_integration()
        test_budget_enforcement()
        test_cheaper_provider_fallback()
        test_performance_tracking()
        test_enhanced_stats()
        test_budget_health_check()
        test_task_preview()

        print("=" * 60)
        print("✅ All Phase 3 integration tests passed!")
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
