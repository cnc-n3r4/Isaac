"""
Test Mistake Learning Framework
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from isaac.learning.mistake_learner import MistakeLearner, MistakeRecord, LearningPattern


class TestMistakeLearning:
    """Test the mistake learning system."""

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
        # Override the data_dir to use temp directory
        learner = MistakeLearner(mock_session_manager, start_background_learning=False)
        learner.data_dir = temp_data_dir / 'learning'
        learner.data_dir.mkdir(exist_ok=True)
        learner.db_path = learner.data_dir / 'mistakes.db'
        learner.patterns_file = learner.data_dir / 'learning_patterns.json'
        learner._init_database()
        learner.learning_patterns = {}
        yield learner

    def test_mistake_recording(self, mistake_learner):
        """Test recording mistakes."""
        mistake = MistakeRecord(
            id="test_mistake_1",
            timestamp=1234567890.0,
            mistake_type="command_error",
            original_input="wrong command",
            mistake_description="Command not found",
            user_correction="correct command",
            context={"shell": "bash"},
            severity="medium"
        )

        mistake_learner.record_mistake(mistake)

        # Verify it was recorded
        similar = mistake_learner.get_similar_mistakes("command_error", {})
        assert len(similar) == 1
        assert similar[0].id == "test_mistake_1"

    def test_pattern_learning(self, mistake_learner):
        """Test learning patterns from mistakes."""
        # Record multiple similar mistakes
        for i in range(5):
            mistake = MistakeRecord(
                id=f"test_mistake_{i}",
                timestamp=1234567890.0 + i,
                mistake_type="command_error",
                original_input=f"wrong_cmd_{i}",
                mistake_description="Command not found",
                user_correction="ls -la",  # Same correction
                context={"shell": "bash"},
                severity="medium"
            )
            mistake_learner.record_mistake(mistake)

        # Learn pattern
        pattern = mistake_learner.learn_from_mistakes("command_error")
        assert pattern is not None
        assert pattern.mistake_type == "command_error"
        assert pattern.correction_action == "ls -la"
        assert pattern.confidence > 0.5

    def test_pattern_application(self, mistake_learner):
        """Test applying learned patterns."""
        # Create a learning pattern manually
        pattern = LearningPattern(
            id="test_pattern",
            mistake_type="command_error",
            pattern_description="Test pattern",
            trigger_conditions={"shell": "bash"},
            correction_action="ls -la",
            confidence=0.8,
            created_at=1234567890.0
        )
        mistake_learner.learning_patterns[pattern.id] = pattern

        # Apply pattern
        correction = mistake_learner.apply_learning("command_error", {"shell": "bash"})
        assert correction == "ls -la"

        # Test non-matching context
        correction = mistake_learner.apply_learning("command_error", {"shell": "powershell"})
        assert correction is None

    def test_learning_stats(self, mistake_learner):
        """Test learning statistics."""
        # Record some mistakes
        mistake = MistakeRecord(
            id="stats_test_1",
            timestamp=1234567890.0,
            mistake_type="command_error",
            original_input="wrong",
            mistake_description="Error",
            user_correction="right",
            context={},
            severity="low"
        )
        mistake_learner.record_mistake(mistake)

        stats = mistake_learner.get_learning_stats()
        assert stats['total_mistakes'] == 1
        assert stats['learned_mistakes'] == 0  # Not learned yet
        assert 'command_error' in stats['mistake_types']