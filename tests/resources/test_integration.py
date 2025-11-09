"""
Integration tests for Resource Optimization system
"""

import unittest
import time
import os
import tempfile
import shutil
from pathlib import Path

# Add isaac to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.resources.monitor import ResourceMonitor
from isaac.resources.optimizer import OptimizationEngine
from isaac.resources.cleanup import CleanupManager
from isaac.resources.predictor import ResourcePredictor
from isaac.resources.cost_tracker import CostTracker
from isaac.resources.alerts import AlertManager
from isaac.commands.resources.resources_command import ResourcesCommand


class TestResourceMonitor(unittest.TestCase):
    """Test ResourceMonitor"""

    def setUp(self):
        self.monitor = ResourceMonitor(history_size=100, monitor_interval=0.1)

    def test_capture_snapshot(self):
        """Test capturing resource snapshot"""
        snapshot = self.monitor.capture_snapshot()

        self.assertIsNotNone(snapshot)
        self.assertGreaterEqual(snapshot.cpu_percent, 0)
        self.assertLessEqual(snapshot.cpu_percent, 100)
        self.assertGreaterEqual(snapshot.memory_percent, 0)
        self.assertLessEqual(snapshot.memory_percent, 100)
        self.assertGreater(snapshot.memory_used_mb, 0)
        self.assertGreater(snapshot.disk_free_gb, 0)

    def test_history_tracking(self):
        """Test that history is tracked"""
        initial_count = len(self.monitor.history)

        for _ in range(5):
            self.monitor.capture_snapshot()
            time.sleep(0.1)

        self.assertEqual(len(self.monitor.history), initial_count + 5)

    def test_get_top_processes(self):
        """Test getting top processes"""
        processes = self.monitor.get_top_processes(limit=5, sort_by='cpu')

        self.assertIsNotNone(processes)
        self.assertGreater(len(processes), 0)
        self.assertLessEqual(len(processes), 5)

        # Check process info structure
        proc = processes[0]
        self.assertIsNotNone(proc.pid)
        self.assertIsNotNone(proc.name)
        self.assertGreaterEqual(proc.cpu_percent, 0)

    def test_get_statistics(self):
        """Test getting statistics"""
        # Capture some snapshots
        for _ in range(10):
            self.monitor.capture_snapshot()
            time.sleep(0.1)

        stats = self.monitor.get_statistics(minutes=1)

        self.assertIn('cpu', stats)
        self.assertIn('memory', stats)
        self.assertIn('current', stats['cpu'])
        self.assertIn('average', stats['cpu'])
        self.assertIn('max', stats['cpu'])
        self.assertIn('min', stats['cpu'])

    def test_background_monitoring(self):
        """Test background monitoring thread"""
        self.monitor.start_monitoring()
        time.sleep(0.5)
        self.assertTrue(len(self.monitor.history) > 0)
        self.monitor.stop_monitoring()


class TestOptimizationEngine(unittest.TestCase):
    """Test OptimizationEngine"""

    def setUp(self):
        self.optimizer = OptimizationEngine()

    def test_analyze(self):
        """Test optimization analysis"""
        suggestions = self.optimizer.analyze()

        self.assertIsNotNone(suggestions)
        # May or may not have suggestions depending on system state
        for suggestion in suggestions:
            self.assertIsNotNone(suggestion.category)
            self.assertIsNotNone(suggestion.severity)
            self.assertIsNotNone(suggestion.title)
            self.assertIsNotNone(suggestion.description)

    def test_get_suggestions_by_severity(self):
        """Test filtering suggestions by severity"""
        self.optimizer.analyze()
        high = self.optimizer.get_suggestions_by_severity('high')

        for suggestion in high:
            self.assertEqual(suggestion.severity, 'high')

    def test_get_auto_fixable_suggestions(self):
        """Test getting auto-fixable suggestions"""
        self.optimizer.analyze()
        auto_fixable = self.optimizer.get_auto_fixable_suggestions()

        for suggestion in auto_fixable:
            self.assertTrue(suggestion.auto_fixable)
            self.assertIsNotNone(suggestion.fix_command)


class TestCleanupManager(unittest.TestCase):
    """Test CleanupManager"""

    def setUp(self):
        # Use temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        history_file = os.path.join(self.temp_dir, 'cleanup_history.json')
        self.cleanup = CleanupManager(history_file=history_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_cleanup_history_tracking(self):
        """Test that cleanup history is tracked"""
        initial_count = len(self.cleanup.cleanup_history)

        # Note: Not actually running cleanup since it requires Docker/permissions
        # Just verify the structure works

        self.assertIsNotNone(self.cleanup.cleanup_history)
        self.assertEqual(len(self.cleanup.cleanup_history), initial_count)

    def test_get_cleanup_history(self):
        """Test getting cleanup history"""
        history = self.cleanup.get_cleanup_history(limit=10)

        self.assertIsNotNone(history)
        self.assertIsInstance(history, list)


class TestResourcePredictor(unittest.TestCase):
    """Test ResourcePredictor"""

    def setUp(self):
        self.monitor = ResourceMonitor(history_size=100)
        # Capture some data points
        for _ in range(20):
            self.monitor.capture_snapshot()
            time.sleep(0.05)

        self.predictor = ResourcePredictor(self.monitor)

    def test_predict_resource_usage(self):
        """Test predicting resource usage"""
        prediction = self.predictor.predict_resource_usage('cpu', minutes_ahead=60)

        if prediction:  # May be None if insufficient data
            self.assertIsNotNone(prediction.resource_type)
            self.assertEqual(prediction.resource_type, 'cpu')
            self.assertGreaterEqual(prediction.predicted_value, 0)
            self.assertLessEqual(prediction.predicted_value, 100)
            self.assertGreaterEqual(prediction.confidence, 0)
            self.assertLessEqual(prediction.confidence, 100)
            self.assertIn(prediction.trend, ['increasing', 'decreasing', 'stable'])

    def test_predict_time_to_limit(self):
        """Test predicting time to limit"""
        ttl = self.predictor.predict_time_to_limit('memory', limit_percent=90.0)

        if ttl:  # May be None if insufficient data
            self.assertIn('will_reach_limit', ttl)
            if ttl['will_reach_limit'] and not ttl.get('already_at_limit'):
                self.assertIn('hours_to_limit', ttl)
                self.assertIn('time_to_limit', ttl)

    def test_analyze_patterns(self):
        """Test pattern analysis"""
        patterns = self.predictor.analyze_patterns(hours=1)

        if 'error' not in patterns:
            self.assertIn('cpu', patterns)
            self.assertIn('memory', patterns)
            self.assertIn('average', patterns['cpu'])
            self.assertIn('stability', patterns['cpu'])


class TestCostTracker(unittest.TestCase):
    """Test CostTracker"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        data_file = os.path.join(self.temp_dir, 'cost_data.json')
        self.tracker = CostTracker(data_file=data_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_add_cost(self):
        """Test adding cost entry"""
        initial_count = len(self.tracker.entries)

        self.tracker.add_cost(
            service='compute',
            provider='aws',
            resource_type='t2.micro',
            resource_id='i-12345',
            cost_usd=0.023,
            units='hours',
            quantity=1.0
        )

        self.assertEqual(len(self.tracker.entries), initial_count + 1)

    def test_estimate_cost(self):
        """Test cost estimation"""
        cost = self.tracker.estimate_cost('aws', 'compute', 't2.micro', 10)

        self.assertIsNotNone(cost)
        self.assertGreater(cost, 0)

    def test_add_budget(self):
        """Test adding budget"""
        initial_count = len(self.tracker.budgets)

        self.tracker.add_budget(
            name='Development',
            limit_usd=100.0,
            period='monthly'
        )

        self.assertEqual(len(self.tracker.budgets), initial_count + 1)

    def test_get_cost_breakdown(self):
        """Test cost breakdown"""
        # Add some costs
        self.tracker.add_cost('compute', 'aws', 't2.micro', 'i-1', 1.0, 'hours', 1)
        self.tracker.add_cost('storage', 'aws', 's3', 'bucket-1', 0.5, 'gb', 10)

        breakdown = self.tracker.get_cost_breakdown(days=30)

        self.assertIn('total_cost', breakdown)
        self.assertIn('by_service', breakdown)
        self.assertIn('by_provider', breakdown)
        self.assertEqual(breakdown['total_cost'], 1.5)

    def test_forecast_costs(self):
        """Test cost forecasting"""
        # Add some historical costs
        for i in range(10):
            self.tracker.add_cost('compute', 'aws', 't2.micro', f'i-{i}', 0.5, 'hours', 1)

        forecast = self.tracker.forecast_costs(days_ahead=30)

        self.assertIn('forecast_total', forecast)
        self.assertIn('avg_daily_cost', forecast)


class TestAlertManager(unittest.TestCase):
    """Test AlertManager"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        data_file = os.path.join(self.temp_dir, 'alerts.json')
        self.monitor = ResourceMonitor()
        self.alert_manager = AlertManager(data_file=data_file, monitor=self.monitor)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_default_rules_created(self):
        """Test that default rules are created"""
        self.assertGreater(len(self.alert_manager.rules), 0)

        # Check for expected rules
        rule_ids = [r.rule_id for r in self.alert_manager.rules]
        self.assertIn('cpu_high', rule_ids)
        self.assertIn('memory_high', rule_ids)
        self.assertIn('disk_high', rule_ids)

    def test_add_rule(self):
        """Test adding custom rule"""
        initial_count = len(self.alert_manager.rules)

        self.alert_manager.add_rule(
            rule_id='test_rule',
            category='cpu',
            metric='cpu_percent',
            threshold=50.0,
            severity='warning',
            title_template='Test Alert',
            message_template='Test message'
        )

        self.assertEqual(len(self.alert_manager.rules), initial_count + 1)

    def test_enable_disable_rule(self):
        """Test enabling/disabling rules"""
        rule_id = self.alert_manager.rules[0].rule_id

        self.alert_manager.disable_rule(rule_id)
        rule = [r for r in self.alert_manager.rules if r.rule_id == rule_id][0]
        self.assertFalse(rule.enabled)

        self.alert_manager.enable_rule(rule_id)
        rule = [r for r in self.alert_manager.rules if r.rule_id == rule_id][0]
        self.assertTrue(rule.enabled)

    def test_get_alert_summary(self):
        """Test getting alert summary"""
        summary = self.alert_manager.get_alert_summary()

        self.assertIn('total_active', summary)
        self.assertIn('by_severity', summary)
        self.assertIn('by_category', summary)
        self.assertIn('unacknowledged', summary)


class TestResourcesCommand(unittest.TestCase):
    """Test ResourcesCommand integration"""

    def setUp(self):
        self.command = ResourcesCommand()

    def test_monitor_command(self):
        """Test monitor subcommand"""
        result = self.command.execute('monitor')

        self.assertIsNotNone(result)
        self.assertIn('CPU', result)
        self.assertIn('Memory', result)
        self.assertIn('Disk', result)

    def test_optimize_command(self):
        """Test optimize subcommand"""
        result = self.command.execute('optimize')

        self.assertIsNotNone(result)
        # May or may not have suggestions

    def test_stats_command(self):
        """Test stats subcommand"""
        # Capture some data first
        for _ in range(10):
            self.command.monitor.capture_snapshot()
            time.sleep(0.1)

        result = self.command.execute('stats')

        self.assertIsNotNone(result)
        self.assertIn('CPU', result)
        self.assertIn('Average', result)

    def test_alerts_list_command(self):
        """Test alerts list subcommand"""
        result = self.command.execute('alerts list')

        self.assertIsNotNone(result)

    def test_costs_summary_command(self):
        """Test costs summary subcommand"""
        result = self.command.execute('costs summary')

        self.assertIsNotNone(result)
        self.assertIn('Cost Summary', result)

    def test_start_stop_monitoring(self):
        """Test start/stop monitoring"""
        result = self.command.execute('start')
        self.assertIn('Started', result)

        time.sleep(0.5)

        result = self.command.execute('stop')
        self.assertIn('Stopped', result)


def run_tests():
    """Run all integration tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestResourceMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestOptimizationEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestCleanupManager))
    suite.addTests(loader.loadTestsFromTestCase(TestResourcePredictor))
    suite.addTests(loader.loadTestsFromTestCase(TestCostTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestAlertManager))
    suite.addTests(loader.loadTestsFromTestCase(TestResourcesCommand))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
