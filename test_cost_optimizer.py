#!/usr/bin/env python3
"""
Test CostOptimizer - Phase 3 Enhanced AI Routing

Tests cost tracking, budget management, and optimization features.
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Add Isaac to path
sys.path.insert(0, str(Path(__file__).parent))

from isaac.ai.cost_optimizer import CostOptimizer
from isaac.ai.routing_config import RoutingConfigManager


def test_cost_tracking():
    """Test basic cost tracking functionality"""
    print("=" * 60)
    print("TEST 1: Cost Tracking")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'config.json'
        storage_path = Path(tmpdir) / 'costs.json'

        config_mgr = RoutingConfigManager(config_path)
        optimizer = CostOptimizer(config_mgr, storage_path)

        # Track some usage
        result = optimizer.track_usage(
            provider='grok',
            input_tokens=1000,
            output_tokens=500,
            task_type='code_write'
        )

        assert 'cost' in result
        assert result['cost'] > 0
        print(f"✓ Tracked usage: ${result['cost']:.6f}")

        # Verify daily/monthly totals
        assert result['daily_total'] == result['cost']
        assert result['monthly_total'] == result['cost']
        print(f"✓ Daily total: ${result['daily_total']:.6f}")
        print(f"✓ Monthly total: ${result['monthly_total']:.6f}")

    print()


def test_budget_checking():
    """Test budget limit checking"""
    print("=" * 60)
    print("TEST 2: Budget Checking")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'config.json'
        storage_path = Path(tmpdir) / 'costs.json'

        config_mgr = RoutingConfigManager(config_path)

        # Set low limits for testing
        config_mgr.set_cost_limit('daily', 1.0)
        config_mgr.set_cost_limit('monthly', 10.0)

        optimizer = CostOptimizer(config_mgr, storage_path)

        # Check initial status
        status = optimizer.check_budget_status()
        assert status['enabled'] == True
        assert status['daily']['status'] == 'ok'
        print("✓ Initial budget status: OK")

        # Track usage to approach limit
        for i in range(5):
            optimizer.track_usage(
                provider='grok',
                input_tokens=20000,  # This will cost ~$0.10
                output_tokens=10000,
                task_type='test'
            )

        status = optimizer.check_budget_status()
        print(f"✓ After usage: Daily ${status['daily']['spent']:.2f} / ${status['daily']['limit']:.2f}")
        print(f"  Status: {status['daily']['status']}")

        # Verify warning or exceeded status
        assert status['daily']['status'] in ['warning', 'exceeded']

    print()


def test_affordability_check():
    """Test can_afford_request functionality"""
    print("=" * 60)
    print("TEST 3: Affordability Check")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'config.json'
        storage_path = Path(tmpdir) / 'costs.json'

        config_mgr = RoutingConfigManager(config_path)
        config_mgr.set_cost_limit('daily', 0.50)  # Very low limit

        optimizer = CostOptimizer(config_mgr, storage_path)

        # Small request should be affordable
        can_afford, reason = optimizer.can_afford_request(
            provider='openai',
            estimated_tokens={'input': 100, 'output': 100}
        )
        assert can_afford == True
        print(f"✓ Small request affordable: {reason}")

        # Use most of budget
        optimizer.track_usage(
            provider='grok',
            input_tokens=40000,
            output_tokens=20000,
            task_type='test'
        )

        # Large request should not be affordable
        can_afford, reason = optimizer.can_afford_request(
            provider='claude',
            estimated_tokens={'input': 50000, 'output': 50000}
        )
        assert can_afford == False
        print(f"✓ Large request not affordable: {reason}")

    print()


def test_cheaper_provider_suggestion():
    """Test cheaper provider suggestion"""
    print("=" * 60)
    print("TEST 4: Cheaper Provider Suggestion")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'config.json'
        storage_path = Path(tmpdir) / 'costs.json'

        config_mgr = RoutingConfigManager(config_path)
        optimizer = CostOptimizer(config_mgr, storage_path)

        # Get cheaper provider for simple task
        cheaper = optimizer.suggest_cheaper_provider(
            complexity='simple',
            estimated_tokens={'input': 1000, 'output': 1000}
        )

        print(f"✓ Suggested cheaper provider: {cheaper}")
        # OpenAI should be cheapest for simple tasks
        assert cheaper == 'openai'

    print()


def test_cost_report():
    """Test cost report generation"""
    print("=" * 60)
    print("TEST 5: Cost Report")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'config.json'
        storage_path = Path(tmpdir) / 'costs.json'

        config_mgr = RoutingConfigManager(config_path)
        optimizer = CostOptimizer(config_mgr, storage_path)

        # Track various usage
        for provider in ['grok', 'claude', 'openai']:
            for task_type in ['code_write', 'chat', 'analysis']:
                optimizer.track_usage(
                    provider=provider,
                    input_tokens=1000,
                    output_tokens=500,
                    task_type=task_type
                )

        # Generate report
        report = optimizer.get_cost_report(days=7)

        assert 'total_cost' in report
        assert 'provider_totals' in report
        assert 'task_type_totals' in report
        assert report['period_days'] == 7

        print(f"✓ Report generated")
        print(f"  Total cost: ${report['total_cost']:.4f}")
        print(f"  Total tokens: {report['total_tokens']}")
        print(f"  Providers: {list(report['provider_totals'].keys())}")
        print(f"  Task types: {list(report['task_type_totals'].keys())}")

    print()


def test_monthly_forecast():
    """Test monthly cost forecasting"""
    print("=" * 60)
    print("TEST 6: Monthly Forecast")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'config.json'
        storage_path = Path(tmpdir) / 'costs.json'

        config_mgr = RoutingConfigManager(config_path)
        config_mgr.set_cost_limit('monthly', 100.0)

        optimizer = CostOptimizer(config_mgr, storage_path)

        # Track some usage
        for i in range(10):
            optimizer.track_usage(
                provider='grok',
                input_tokens=5000,
                output_tokens=2500,
                task_type='test'
            )

        # Get forecast
        forecast = optimizer.forecast_monthly_cost()

        assert 'projected_total' in forecast
        assert 'on_track' in forecast
        assert 'daily_average' in forecast

        print(f"✓ Forecast generated")
        print(f"  Current spend: ${forecast['current_spend']:.2f}")
        print(f"  Daily average: ${forecast['daily_average']:.2f}")
        print(f"  Projected total: ${forecast['projected_total']:.2f}")
        print(f"  Monthly limit: ${forecast['monthly_limit']:.2f}")
        print(f"  On track: {forecast['on_track']}")

    print()


def test_alert_generation():
    """Test automatic alert generation"""
    print("=" * 60)
    print("TEST 7: Alert Generation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'config.json'
        storage_path = Path(tmpdir) / 'costs.json'

        config_mgr = RoutingConfigManager(config_path)
        config_mgr.set_cost_limit('daily', 1.0)
        config_mgr.set_cost_limit('monthly', 10.0)

        optimizer = CostOptimizer(config_mgr, storage_path)

        # Use enough to trigger warning (80% threshold)
        for i in range(8):
            optimizer.track_usage(
                provider='grok',
                input_tokens=10000,
                output_tokens=5000,
                task_type='test'
            )

        # Check for alerts
        alerts = optimizer.get_recent_alerts(count=5)

        print(f"✓ Alerts generated: {len(alerts)}")
        for alert in alerts:
            print(f"  [{alert['severity']}] {alert['type']}: {alert['message']}")

        # Should have at least one alert
        assert len(alerts) > 0

    print()


def test_persistence():
    """Test data persistence across instances"""
    print("=" * 60)
    print("TEST 8: Data Persistence")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'config.json'
        storage_path = Path(tmpdir) / 'costs.json'

        config_mgr = RoutingConfigManager(config_path)

        # Create optimizer and track usage
        optimizer1 = CostOptimizer(config_mgr, storage_path)
        result1 = optimizer1.track_usage(
            provider='grok',
            input_tokens=1000,
            output_tokens=500,
            task_type='test'
        )

        cost1 = result1['daily_total']
        print(f"✓ First instance tracked: ${cost1:.6f}")

        # Create new optimizer instance (should load saved data)
        optimizer2 = CostOptimizer(config_mgr, storage_path)
        result2 = optimizer2.track_usage(
            provider='grok',
            input_tokens=1000,
            output_tokens=500,
            task_type='test'
        )

        cost2 = result2['daily_total']
        print(f"✓ Second instance tracked: ${cost2:.6f}")

        # Second total should be ~2x first (accumulated)
        assert cost2 > cost1
        assert abs(cost2 - (cost1 * 2)) < 0.001  # Allow small floating point difference

        print(f"✓ Data persisted correctly")

    print()


def test_old_data_cleanup():
    """Test cleanup of old data"""
    print("=" * 60)
    print("TEST 9: Old Data Cleanup")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'config.json'
        storage_path = Path(tmpdir) / 'costs.json'

        config_mgr = RoutingConfigManager(config_path)
        optimizer = CostOptimizer(config_mgr, storage_path)

        # Add current usage
        optimizer.track_usage(
            provider='grok',
            input_tokens=1000,
            output_tokens=500,
            task_type='test'
        )

        initial_count = len(optimizer.cost_data['usage_history'])
        print(f"✓ Initial usage entries: {initial_count}")

        # Clean old data (keep 90 days)
        optimizer.clear_old_data(days_to_keep=90)

        final_count = len(optimizer.cost_data['usage_history'])
        print(f"✓ After cleanup: {final_count}")

        # Should still have recent data
        assert final_count == initial_count

    print()


def main():
    """Run all cost optimizer tests"""
    print("\n🧪 CostOptimizer Test Suite - Phase 3\n")

    try:
        test_cost_tracking()
        test_budget_checking()
        test_affordability_check()
        test_cheaper_provider_suggestion()
        test_cost_report()
        test_monthly_forecast()
        test_alert_generation()
        test_persistence()
        test_old_data_cleanup()

        print("=" * 60)
        print("✅ All CostOptimizer tests passed!")
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
