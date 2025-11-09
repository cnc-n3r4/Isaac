"""
Integration Tests for Self-Improving Learning System (Phase 3.5)
Tests the complete learning system working together.
"""

import unittest
import time
import tempfile
import shutil
from pathlib import Path

from isaac.core.session_manager import SessionManager
from isaac.learning import (
    MistakeLearner,
    BehaviorAdjustmentEngine,
    LearningMetricsDashboard,
    UserPreferenceLearner,
    MistakeRecord,
    UserFeedback,
    ContinuousLearningCoordinator,
    PerformanceAnalytics
)


class TestLearningSystemIntegration(unittest.TestCase):
    """Test the complete learning system integration."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.original_home = Path.home()

        # Initialize session manager
        self.session_manager = SessionManager(config={'disable_learning': False})

        # Verify learning components were initialized
        self.assertIsNotNone(self.session_manager.mistake_learner)
        self.assertIsNotNone(self.session_manager.behavior_engine)
        self.assertIsNotNone(self.session_manager.metrics_dashboard)
        self.assertIsNotNone(self.session_manager.preference_learner)

    def tearDown(self):
        """Clean up test environment."""
        # Stop background learning
        if hasattr(self.session_manager, 'mistake_learner') and self.session_manager.mistake_learner:
            self.session_manager.mistake_learner.stop_learning()

        # Clean up temp directory
        try:
            shutil.rmtree(self.test_dir)
        except Exception:
            pass

    def test_mistake_learning_flow(self):
        """Test complete mistake learning workflow."""
        # Record a mistake
        mistake = MistakeRecord(
            id="test_mistake_1",
            timestamp=time.time(),
            mistake_type="command_error",
            original_input="git psuh origin main",
            mistake_description="Typo in git command",
            user_correction="git push origin main",
            context={"test": True},
            severity="low"
        )

        self.session_manager.mistake_learner.record_mistake(mistake)

        # Verify mistake was recorded
        similar = self.session_manager.mistake_learner.get_similar_mistakes(
            "command_error", {}, limit=10
        )
        self.assertGreater(len(similar), 0)

        # Get learning stats
        stats = self.session_manager.mistake_learner.get_learning_stats()
        self.assertGreater(stats['total_mistakes'], 0)

    def test_behavior_adjustment_flow(self):
        """Test behavior adjustment workflow."""
        # Record user feedback
        feedback = UserFeedback(
            id="test_feedback_1",
            timestamp=time.time(),
            feedback_type="negative",
            context="Response was too verbose",
            user_response="Please be more concise",
            sentiment_score=-0.5,
            behavior_category="response_style"
        )

        self.session_manager.behavior_engine.record_feedback(feedback)

        # Get behavior profile
        profile = self.session_manager.behavior_engine.get_current_behavior_profile()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user_id, "default")

    def test_preference_learning_flow(self):
        """Test user preference learning workflow."""
        # Observe coding patterns
        self.session_manager.preference_learner.observe_coding_pattern(
            pattern_type='naming_conventions',
            pattern_key='variable_naming',
            observed_value='snake_case',
            context={'timestamp': time.time()}
        )

        self.session_manager.preference_learner.observe_coding_pattern(
            pattern_type='naming_conventions',
            pattern_key='variable_naming',
            observed_value='snake_case',
            context={'timestamp': time.time()}
        )

        # Get preferences
        stats = self.session_manager.preference_learner.get_learning_stats()
        self.assertGreater(stats['total_patterns'], 0)

    def test_metrics_dashboard(self):
        """Test metrics dashboard generation."""
        # Generate metrics
        metrics = self.session_manager.metrics_dashboard.generate_current_metrics(period_days=7)

        self.assertIsNotNone(metrics)
        self.assertGreaterEqual(metrics.learning_health_score, 0)
        self.assertLessEqual(metrics.learning_health_score, 100)

        # Get dashboard summary
        summary = self.session_manager.metrics_dashboard.get_dashboard_summary()
        self.assertIn('current_health_score', summary)
        self.assertIn('recommendations', summary)

    def test_session_manager_convenience_methods(self):
        """Test SessionManager convenience methods for learning."""
        # Track a mistake via session manager
        self.session_manager.track_mistake(
            mistake_type='command_error',
            description='Test mistake',
            correction='Test correction',
            original_input='test input',
            severity='low'
        )

        # Record feedback via session manager
        self.session_manager.record_user_feedback(
            feedback_type='positive',
            context='Test context',
            response='Good job!',
            category='response_style',
            sentiment=0.8
        )

        # Observe pattern via session manager
        self.session_manager.observe_coding_pattern(
            pattern_type='test_patterns',
            pattern_key='test_key',
            observed_value='test_value'
        )

        # Get learning stats
        stats = self.session_manager.get_learning_stats()
        self.assertTrue(stats['learning_enabled'])
        self.assertIn('components', stats)

    def test_continuous_learning_coordinator(self):
        """Test continuous learning coordinator."""
        coordinator = ContinuousLearningCoordinator(self.session_manager)

        # Get status before starting
        status_before = coordinator.get_coordination_status()
        self.assertFalse(status_before['active'])

        # Start coordinator
        coordinator.start()
        time.sleep(0.5)  # Give it time to start

        # Get status after starting
        status_after = coordinator.get_coordination_status()
        self.assertTrue(status_after['active'])

        # Force a learning cycle
        coordinator.force_learning_cycle()

        # Get learning summary
        summary = coordinator.get_learning_summary()
        self.assertIn('coordination', summary)
        self.assertIn('components', summary)

        # Stop coordinator
        coordinator.stop()

    def test_performance_analytics(self):
        """Test performance analytics."""
        analytics = PerformanceAnalytics(self.session_manager)

        # Record some metrics
        analytics.record_command_execution('ls -la', 0.1, True)
        analytics.record_ai_query('translation', 1.5, token_count=150)
        analytics.record_learning_overhead('pattern_matching', 0.05)

        # Get statistics
        stats = analytics.get_metric_statistics('command_execution_time', period_minutes=60)
        self.assertIn('mean', stats)

        # Get performance summary
        summary = analytics.get_performance_summary()
        self.assertIn('metrics', summary)
        self.assertIn('alerts', summary)

        # Get recommendations
        recommendations = analytics.get_optimization_recommendations()
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

    def test_cross_component_integration(self):
        """Test that components work together correctly."""
        # Record mistake
        self.session_manager.track_mistake(
            mistake_type='command_typo',
            description='Typo in command',
            correction='corrected_command',
            original_input='wrong_command'
        )

        # Record feedback
        self.session_manager.record_user_feedback(
            feedback_type='positive',
            context='Good correction',
            response='Thanks for fixing that!',
            sentiment=0.9
        )

        # Observe patterns
        self.session_manager.observe_coding_pattern(
            pattern_type='command_patterns',
            pattern_key='git_usage',
            observed_value='git pull origin main'
        )

        # Generate metrics that aggregate everything
        metrics = self.session_manager.metrics_dashboard.generate_current_metrics()

        # Verify metrics include data from all components
        self.assertGreater(metrics.total_mistakes, 0)
        self.assertIsInstance(metrics.recommendations, list)

        # Get comprehensive stats
        stats = self.session_manager.get_learning_stats()
        self.assertIn('mistakes', stats['components'])
        self.assertIn('behavior', stats['components'])
        self.assertIn('preferences', stats['components'])
        self.assertIn('metrics', stats['components'])


class TestLearningSystemDisabled(unittest.TestCase):
    """Test that system works correctly when learning is disabled."""

    def test_disabled_learning(self):
        """Test that disabled learning doesn't break the system."""
        session_manager = SessionManager(config={'disable_learning': True})

        # Learning components should be None
        self.assertIsNone(session_manager.mistake_learner)
        self.assertIsNone(session_manager.behavior_engine)
        self.assertIsNone(session_manager.metrics_dashboard)
        self.assertIsNone(session_manager.preference_learner)

        # Convenience methods should gracefully do nothing
        session_manager.track_mistake('test', 'test', 'test')
        session_manager.record_user_feedback('test', 'test', 'test')
        session_manager.observe_coding_pattern('test', 'test', 'test')

        # Get stats should indicate learning is disabled
        stats = session_manager.get_learning_stats()
        self.assertFalse(stats['learning_enabled'])


if __name__ == '__main__':
    unittest.main()
