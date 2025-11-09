"""
Tests for Learning Metrics Dashboard - Phase 3.5 Self-Improving System
"""

import pytest
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from dataclasses import asdict

from isaac.learning.learning_metrics import LearningMetricsDashboard, LearningMetrics, LearningInsight
from isaac.core.session_manager import SessionManager
from isaac.learning.mistake_learner import MistakeLearner
from isaac.learning.behavior_adjustment import BehaviorAdjustmentEngine


class TestLearningMetricsDashboard:
    """Test suite for LearningMetricsDashboard."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp:
            yield Path(temp)

    @pytest.fixture
    def mock_session_manager(self):
        """Mock SessionManager."""
        return Mock(spec=SessionManager)

    @pytest.fixture
    def mock_mistake_learner(self):
        """Mock MistakeLearner with test data."""
        learner = Mock(spec=MistakeLearner)
        learner.get_learning_stats.return_value = {
            'total_mistakes': 25,
            'learned_mistakes': 18,
            'learning_patterns': 7,
            'mistake_types': {'syntax': 10, 'logic': 8, 'import': 7},
            'learning_rate': 0.72
        }
        return learner

    @pytest.fixture
    def mock_behavior_engine(self):
        """Mock BehaviorAdjustmentEngine with test data."""
        engine = Mock(spec=BehaviorAdjustmentEngine)
        engine.analyze_behavior_effectiveness.return_value = {
            'total_adjustments': 12,
            'category_effectiveness': {
                'response_style': {'total_adjustments': 5, 'effective_adjustments': 4},
                'tool_usage': {'total_adjustments': 4, 'effective_adjustments': 3},
                'communication': {'total_adjustments': 3, 'effective_adjustments': 2}
            }
        }
        engine.get_current_behavior_profile.return_value = Mock(
            confidence_scores={'response_style': 0.85, 'tool_usage': 0.72, 'communication': 0.68}
        )
        return engine

    @pytest.fixture
    def dashboard(self, temp_dir, mock_session_manager, mock_mistake_learner, mock_behavior_engine):
        """Create a test dashboard instance."""
        with patch('pathlib.Path.home', return_value=temp_dir):
            dashboard = LearningMetricsDashboard(
                mock_session_manager,
                mock_mistake_learner,
                mock_behavior_engine
            )
        return dashboard

    def test_initialization(self, dashboard):
        """Test dashboard initialization."""
        assert dashboard.session_manager is not None
        assert dashboard.mistake_learner is not None
        assert dashboard.behavior_engine is not None
        assert dashboard.metrics_history == []
        assert dashboard.learning_insights == []

    def test_generate_current_metrics(self, dashboard, mock_mistake_learner, mock_behavior_engine):
        """Test generating current metrics."""
        metrics = dashboard.generate_current_metrics(period_days=7)

        assert isinstance(metrics, LearningMetrics)
        assert metrics.period_days == 7
        assert metrics.total_mistakes == 25
        assert metrics.learned_mistakes == 18
        assert metrics.learning_patterns == 7
        assert metrics.learning_rate == 0.72
        assert metrics.total_adjustments == 12
        assert 'response_style' in metrics.adjustment_categories
        assert 'tool_usage' in metrics.adjustment_categories
        assert 'communication' in metrics.adjustment_categories
        assert 0.0 <= metrics.learning_health_score <= 100.0
        assert isinstance(metrics.improvement_trend, list)
        assert isinstance(metrics.recommendations, list)

    def test_calculate_learning_health_score(self, dashboard):
        """Test learning health score calculation."""
        # High performing metrics
        metrics = LearningMetrics(
            timestamp=time.time(),
            period_days=7,
            learning_rate=0.9,
            learning_patterns=15,
            behavior_profile_confidence={'test': 0.9}
        )
        score = dashboard._calculate_learning_health_score(metrics)
        assert score == 97.0  # 40 (learning) + 30 (patterns) + 27 (adaptation) = 97

        # Low performing metrics
        metrics = LearningMetrics(
            timestamp=time.time(),
            period_days=7,
            learning_rate=0.1,
            learning_patterns=2,
            behavior_profile_confidence={'test': 0.3}
        )
        score = dashboard._calculate_learning_health_score(metrics)
        assert score < 50.0  # Should be lower

    def test_calculate_improvement_trend(self, dashboard):
        """Test improvement trend calculation."""
        # No history
        trend = dashboard._calculate_improvement_trend(7)
        assert trend == [50.0]

        # Add some history
        dashboard.metrics_history = [
            LearningMetrics(timestamp=time.time() - 86400 * i, period_days=7,
                          learning_health_score=float(i * 10))
            for i in range(5, 0, -1)  # 50, 40, 30, 20, 10
        ]

        trend = dashboard._calculate_improvement_trend(7)
        assert len(trend) == 5
        assert trend == [50.0, 40.0, 30.0, 20.0, 10.0]

    def test_generate_recommendations(self, dashboard):
        """Test recommendation generation."""
        # Low performance metrics
        metrics = LearningMetrics(
            timestamp=time.time(),
            period_days=7,
            learning_rate=0.1,
            learning_patterns=2,
            behavior_profile_confidence={'test': 0.3},
            learning_health_score=25.0
        )
        recommendations = dashboard._generate_recommendations(metrics)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("learning rate is low" in rec.lower() for rec in recommendations)
        assert any("few learning patterns" in rec.lower() for rec in recommendations)
        assert any("low confidence" in rec.lower() for rec in recommendations)

        # High performance metrics
        metrics = LearningMetrics(
            timestamp=time.time(),
            period_days=7,
            learning_rate=0.9,
            learning_patterns=25,
            behavior_profile_confidence={'test': 0.9},
            learning_health_score=95.0
        )
        recommendations = dashboard._generate_recommendations(metrics)

        assert isinstance(recommendations, list)
        assert any("excellent learning rate" in rec.lower() for rec in recommendations)

    def test_generate_insights(self, dashboard):
        """Test insight generation."""
        # Low performance metrics
        metrics = LearningMetrics(
            timestamp=time.time(),
            period_days=7,
            learning_rate=0.1,
            learning_patterns=0,
            behavior_profile_confidence={'test': 0.3}
        )

        dashboard._generate_insights(metrics)

        assert len(dashboard.learning_insights) > 0

        # Check for expected insights
        low_rate_insights = [i for i in dashboard.learning_insights if i.metric == 'learning_rate']
        assert len(low_rate_insights) > 0
        assert low_rate_insights[0].priority == 'high'

        no_patterns_insights = [i for i in dashboard.learning_insights if i.metric == 'learning_patterns']
        assert len(no_patterns_insights) > 0
        assert no_patterns_insights[0].priority == 'medium'

    def test_get_metrics_history(self, dashboard):
        """Test retrieving metrics history."""
        # Add some metrics
        for i in range(15):
            metrics = LearningMetrics(timestamp=time.time() - i * 3600, period_days=7)
            dashboard.metrics_history.append(metrics)

        # Test default limit
        history = dashboard.get_metrics_history()
        assert len(history) == 10

        # Test custom limit
        history = dashboard.get_metrics_history(limit=5)
        assert len(history) == 5

    def test_get_learning_insights(self, dashboard):
        """Test retrieving learning insights."""
        # Add some insights
        insights = [
            LearningInsight(
                id=f"test_{i}",
                insight_type="warning" if i % 2 == 0 else "improvement",
                title=f"Test Insight {i}",
                description=f"Description {i}",
                metric="test_metric",
                value=i,
                threshold=5,
                recommendation=f"Recommendation {i}",
                priority="high" if i < 3 else "medium",
                created_at=time.time() - i * 3600
            )
            for i in range(10)
        ]
        dashboard.learning_insights = insights

        # Test unfiltered
        all_insights = dashboard.get_learning_insights()
        assert len(all_insights) == 10

        # Test type filter
        warning_insights = dashboard.get_learning_insights(insight_type="warning")
        assert len(warning_insights) == 5

        # Test priority filter
        high_priority = dashboard.get_learning_insights(priority="high")
        assert len(high_priority) == 3

        # Test limit
        limited = dashboard.get_learning_insights(limit=3)
        assert len(limited) == 3

    def test_get_dashboard_summary(self, dashboard):
        """Test dashboard summary generation."""
        # No metrics
        summary = dashboard.get_dashboard_summary()
        assert "message" in summary
        assert "No metrics available" in summary["message"]

        # Add metrics
        metrics = dashboard.generate_current_metrics()
        summary = dashboard.get_dashboard_summary()

        required_keys = [
            "current_health_score", "health_trend", "total_mistakes",
            "learning_patterns", "behavior_adjustments", "learning_rate",
            "active_insights", "recommendations", "generated_at"
        ]

        for key in required_keys:
            assert key in summary

        assert isinstance(summary["current_health_score"], float)
        assert summary["health_trend"] in ["stable", "improving", "declining"]
        assert isinstance(summary["recommendations"], list)

    def test_data_persistence(self, dashboard, temp_dir):
        """Test data persistence to disk."""
        # Generate some data
        dashboard.generate_current_metrics()
        dashboard._generate_insights(LearningMetrics(
            timestamp=time.time(), period_days=7,
            learning_rate=0.1, learning_patterns=0,
            behavior_profile_confidence={'test': 0.3}
        ))

        # Force save
        dashboard._save_metrics_history()
        dashboard._save_learning_insights()

        # Create new dashboard instance (simulates restart)
        with patch('pathlib.Path.home', return_value=temp_dir):
            new_dashboard = LearningMetricsDashboard(
                dashboard.session_manager,
                dashboard.mistake_learner,
                dashboard.behavior_engine
            )

        # Check data was loaded
        assert len(new_dashboard.metrics_history) == 1
        assert len(new_dashboard.learning_insights) > 0

    def test_metrics_data_structure(self):
        """Test LearningMetrics data structure."""
        metrics = LearningMetrics(
            timestamp=time.time(),
            period_days=7,
            total_mistakes=10,
            learned_mistakes=7,
            learning_patterns=3,
            mistake_types={'syntax': 5, 'logic': 3},
            learning_rate=0.7,
            total_adjustments=5,
            adjustment_categories={'style': 3, 'tools': 2},
            behavior_profile_confidence={'style': 0.8, 'tools': 0.6},
            learning_health_score=75.0,
            improvement_trend=[70.0, 72.0, 75.0],
            recommendations=["Good progress", "Keep learning"]
        )

        # Test serialization
        data = asdict(metrics)
        assert isinstance(data, dict)
        assert data['total_mistakes'] == 10
        assert data['learning_health_score'] == 75.0

    def test_insight_data_structure(self):
        """Test LearningInsight data structure."""
        insight = LearningInsight(
            id="test_insight_123",
            insight_type="improvement",
            title="Test Insight",
            description="This is a test insight",
            metric="learning_rate",
            value=0.85,
            threshold=0.8,
            recommendation="Continue current approach",
            priority="medium",
            created_at=time.time()
        )

        # Test serialization
        data = asdict(insight)
        assert isinstance(data, dict)
        assert data['id'] == "test_insight_123"
        assert data['insight_type'] == "improvement"
        assert data['priority'] == "medium"