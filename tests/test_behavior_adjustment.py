"""
Test Behavior Adjustment Engine
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from isaac.learning.behavior_adjustment import (
    BehaviorAdjustmentEngine, UserFeedback, BehaviorAdjustment, BehaviorProfile
)
from isaac.learning.mistake_learner import MistakeLearner


class TestBehaviorAdjustment:
    """Test the behavior adjustment system."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary directory for test data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_session_manager(self, temp_data_dir):
        """Mock session manager with temp data dir."""
        mock_sm = Mock()
        mock_sm.get_data_dir.return_value = temp_data_dir
        return mock_sm

    @pytest.fixture
    def mistake_learner(self, mock_session_manager, temp_data_dir):
        """Create mistake learner with temp database."""
        learner = MistakeLearner(mock_session_manager, start_background_learning=False)
        learner.data_dir = temp_data_dir / 'learning'
        learner.data_dir.mkdir(exist_ok=True)
        learner.db_path = learner.data_dir / 'mistakes.db'
        learner.patterns_file = learner.data_dir / 'learning_patterns.json'
        learner._init_database()
        learner.learning_patterns = {}
        yield learner

    @pytest.fixture
    def behavior_engine(self, mock_session_manager, mistake_learner, temp_data_dir):
        """Create behavior adjustment engine with temp data."""
        engine = BehaviorAdjustmentEngine(mock_session_manager, mistake_learner)
        engine.data_dir = temp_data_dir / 'behavior'
        engine.data_dir.mkdir(exist_ok=True)
        engine.feedback_file = engine.data_dir / 'user_feedback.json'
        engine.adjustments_file = engine.data_dir / 'behavior_adjustments.json'
        engine.profile_file = engine.data_dir / 'behavior_profile.json'
        # Reset data structures
        engine.feedback_history = []
        engine.behavior_adjustments = {}
        engine.behavior_profile = BehaviorProfile(
            user_id="test_user",
            response_style="balanced",
            suggestion_frequency="medium",
            detail_level="moderate",
            humor_level="subtle",
            technical_depth="intermediate",
            interaction_pace="moderate",
            last_updated=1234567890.0
        )
        yield engine

    def test_feedback_recording(self, behavior_engine):
        """Test recording user feedback."""
        feedback = UserFeedback(
            id="test_feedback_1",
            timestamp=1234567890.0,
            feedback_type="correction",
            context="Isaac suggested a verbose solution",
            user_response="Please be more concise",
            sentiment_score=-0.6,
            behavior_category="response_style"
        )

        behavior_engine.record_feedback(feedback)

        assert len(behavior_engine.feedback_history) == 1
        assert behavior_engine.feedback_history[0].id == "test_feedback_1"

    def test_negative_feedback_adjustment(self, behavior_engine):
        """Test that negative feedback triggers behavior adjustments."""
        import time
        current_time = time.time()
        
        # Record multiple negative feedback items
        for i in range(4):
            feedback = UserFeedback(
                id=f"neg_feedback_{i}",
                timestamp=current_time + i,
                feedback_type="correction",
                context="Too detailed response",
                user_response="Keep it brief",
                sentiment_score=-0.7,
                behavior_category="response_style"
            )
            behavior_engine.record_feedback(feedback)

        # Check if adjustment was applied
        adjustments = behavior_engine.get_behavior_adjustments("response_style")
        assert len(adjustments) >= 1

        # Check if profile was updated
        profile = behavior_engine.get_current_behavior_profile()
        # Should have adjusted to be more concise
        assert profile.response_style in ["concise", "balanced"]

    def test_behavior_profile_management(self, behavior_engine):
        """Test behavior profile management."""
        profile = behavior_engine.get_current_behavior_profile()

        assert profile.user_id == "test_user"
        assert profile.response_style == "balanced"
        assert profile.suggestion_frequency == "medium"

        # Test profile attributes
        assert hasattr(profile, 'confidence_scores')
        assert isinstance(profile.confidence_scores, dict)

    def test_adjustment_analysis(self, behavior_engine):
        """Test analysis of adjustment effectiveness."""
        # Create some mock adjustments
        adjustment = BehaviorAdjustment(
            id="test_adj_1",
            behavior_category="response_style",
            current_value="detailed",
            target_value="concise",
            confidence=0.8,
            reason="User feedback indicated preference for concise responses",
            applied_at=1234567890.0,
            effectiveness_score=0.7
        )
        behavior_engine.behavior_adjustments[adjustment.id] = adjustment

        analysis = behavior_engine.analyze_behavior_effectiveness()

        assert 'total_adjustments' in analysis
        assert analysis['total_adjustments'] == 1
        assert 'category_effectiveness' in analysis
        assert 'response_style' in analysis['category_effectiveness']

    def test_adjustment_filtering(self, behavior_engine):
        """Test filtering adjustments by category."""
        # Create adjustments for different categories
        adj1 = BehaviorAdjustment(
            id="adj1", behavior_category="response_style",
            current_value="detailed", target_value="concise",
            confidence=0.8, reason="test", applied_at=1234567890.0
        )
        adj2 = BehaviorAdjustment(
            id="adj2", behavior_category="suggestion_frequency",
            current_value="high", target_value="medium",
            confidence=0.7, reason="test", applied_at=1234567890.0
        )

        behavior_engine.behavior_adjustments.update({adj1.id: adj1, adj2.id: adj2})

        # Test filtering
        all_adjustments = behavior_engine.get_behavior_adjustments()
        assert len(all_adjustments) == 2

        style_adjustments = behavior_engine.get_behavior_adjustments("response_style")
        assert len(style_adjustments) == 1
        assert style_adjustments[0].behavior_category == "response_style"