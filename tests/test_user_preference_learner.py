"""
Tests for User Preference Learner - Phase 3.5 Self-Improving System
"""

import pytest
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from dataclasses import asdict

from isaac.learning.user_preference_learner import (
    UserPreferenceLearner, UserPreferences, CodingPattern
)
from isaac.core.session_manager import SessionManager


class TestUserPreferenceLearner:
    """Test suite for UserPreferenceLearner."""

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
    def preference_learner(self, temp_dir, mock_session_manager):
        """Create a test preference learner instance."""
        with patch('pathlib.Path.home', return_value=temp_dir):
            learner = UserPreferenceLearner(mock_session_manager)
        return learner

    def test_initialization(self, preference_learner):
        """Test learner initialization."""
        assert preference_learner.session_manager is not None
        assert preference_learner.user_preferences is not None
        assert isinstance(preference_learner.user_preferences, UserPreferences)
        assert preference_learner.learned_patterns == {}

    def test_observe_coding_pattern(self, preference_learner):
        """Test observing coding patterns."""
        # Observe a naming pattern
        preference_learner.observe_coding_pattern(
            'naming_conventions',
            'variable_style',
            'snake_case'
        )

        # Check pattern was created
        pattern = preference_learner.user_preferences.get_preference('naming_conventions', 'variable_style')
        assert pattern is not None
        assert pattern.pattern_type == 'naming_conventions'
        assert pattern.pattern_key == 'variable_style'
        assert pattern.preference_value == 'snake_case'
        assert pattern.confidence > 0
        assert pattern.occurrences == 1

    def test_pattern_confidence_update(self, preference_learner):
        """Test pattern confidence updates with repeated observations."""
        # First observation
        preference_learner.observe_coding_pattern('naming_conventions', 'function_style', 'camelCase')
        pattern = preference_learner.user_preferences.get_preference('naming_conventions', 'function_style')
        initial_confidence = pattern.confidence

        # Reinforce same preference
        preference_learner.observe_coding_pattern('naming_conventions', 'function_style', 'camelCase')
        pattern = preference_learner.user_preferences.get_preference('naming_conventions', 'function_style')
        assert pattern.confidence > initial_confidence
        assert pattern.occurrences == 2

        # Challenge with different preference
        old_confidence = pattern.confidence
        preference_learner.observe_coding_pattern('naming_conventions', 'function_style', 'PascalCase')
        pattern = preference_learner.user_preferences.get_preference('naming_conventions', 'function_style')
        assert pattern.confidence < old_confidence

    def test_observe_command_usage(self, preference_learner):
        """Test observing command usage patterns."""
        # Observe successful command
        preference_learner.observe_command_usage(
            'git', ['status'], success=True,
            context={'timestamp': time.time()}
        )

        pattern = preference_learner.user_preferences.get_preference('command_patterns', 'git_status')
        assert pattern is not None
        assert pattern.preference_value['command'] == 'git'
        assert pattern.preference_value['args'] == ['status']

    def test_observe_file_operation(self, preference_learner):
        """Test observing file operation patterns."""
        preference_learner.observe_file_operation(
            'edit', '/path/to/file.py', 'python',
            context={'operation': 'edit'}
        )

        pattern = preference_learner.user_preferences.get_preference('workflow_patterns', 'edit_python')
        assert pattern is not None
        assert pattern.preference_value['extension'] == '.py'
        assert pattern.preference_value['operation'] == 'edit'

    def test_observe_ai_interaction(self, preference_learner):
        """Test observing AI interaction patterns."""
        # Test communication style analysis
        preference_learner.observe_ai_interaction(
            'query', 'please show me how to do this', 'response text',
            user_feedback='too detailed'
        )

        # Check communication style was recorded
        comm_pattern = preference_learner.user_preferences.get_preference('communication_style', 'input_style')
        assert comm_pattern is not None
        assert comm_pattern.preference_value == 'polite'

        # Check response preference was recorded
        response_pattern = preference_learner.user_preferences.get_preference('response_length', 'preferred_length')
        assert response_pattern is not None

    def test_get_personalized_suggestion(self, preference_learner):
        """Test getting personalized suggestions."""
        # Build up some preferences
        preference_learner.observe_coding_pattern('naming_conventions', 'class_style', 'PascalCase')
        preference_learner.observe_coding_pattern('naming_conventions', 'class_style', 'PascalCase')
        preference_learner.observe_coding_pattern('naming_conventions', 'class_style', 'PascalCase')

        # Get suggestion
        suggestion = preference_learner.get_personalized_suggestion(
            'naming_conventions',
            {'file_type': 'python', 'context': 'class_definition'}
        )

        assert suggestion == 'PascalCase'

    def test_get_coding_style_recommendations(self, preference_learner):
        """Test getting coding style recommendations."""
        # Build up high-confidence preferences
        for _ in range(10):  # Build high confidence
            preference_learner.observe_coding_pattern('naming_conventions', 'variable_style', 'snake_case')

        recommendations = preference_learner.get_coding_style_recommendations({})
        assert len(recommendations) > 0
        assert any('snake_case' in rec for rec in recommendations)

    def test_get_workflow_suggestions(self, preference_learner):
        """Test getting workflow suggestions."""
        # Build up command preferences
        for _ in range(5):
            preference_learner.observe_command_usage('pytest', ['--cov'], success=True)

        suggestions = preference_learner.get_workflow_suggestions({})
        assert len(suggestions) > 0
        assert any('pytest' in suggestion for suggestion in suggestions)

    def test_communication_style_analysis(self, preference_learner):
        """Test communication style analysis."""
        assert preference_learner._analyze_communication_style("please help me") == 'polite'
        assert preference_learner._analyze_communication_style("show me quickly") == 'direct'
        assert preference_learner._analyze_communication_style("this is a very detailed question with many words and lots of content here") == 'detailed'
        assert preference_learner._analyze_communication_style("help") == 'concise'

    def test_response_preference_analysis(self, preference_learner):
        """Test response preference analysis."""
        assert preference_learner._analyze_response_preference("short response", "too long") == 'concise'
        assert preference_learner._analyze_response_preference("brief response", "more detail") == 'detailed'
        assert preference_learner._analyze_response_preference("medium response", "just right") == 'balanced'

    def test_technical_level_analysis(self, preference_learner):
        """Test technical level analysis."""
        assert preference_learner._analyze_technical_level("explain API architecture") == 'technical'
        assert preference_learner._analyze_technical_level("how to install") == 'simple'
        assert preference_learner._analyze_technical_level("implement algorithm") == 'intermediate'

    def test_context_match_calculation(self, preference_learner):
        """Test context match score calculation."""
        pattern = CodingPattern(
            pattern_type='naming_conventions',
            pattern_key='variable_style_python',
            preference_value='snake_case',
            confidence=0.8,
            last_seen=time.time()
        )

        # High match
        score = preference_learner._calculate_context_match(
            pattern, {'file_type': 'python', 'operation': 'variable'}
        )
        assert score > 0.8  # Should be boosted

        # Lower match for old pattern
        pattern.last_seen = time.time() - (40 * 24 * 3600)  # 40 days ago
        score = preference_learner._calculate_context_match(pattern, {})
        assert score < 0.8  # Should be reduced

    def test_observation_weight_calculation(self, preference_learner):
        """Test observation weight calculation."""
        # Recent successful observation
        weight = preference_learner._calculate_observation_weight({
            'timestamp': time.time(),
            'success': True
        })
        assert weight > 1.0

        # Old observation
        weight = preference_learner._calculate_observation_weight({
            'timestamp': time.time() - (48 * 3600),  # 48 hours ago
            'success': True
        })
        assert weight < 1.5  # Should be less than very recent

        # Failed observation
        weight = preference_learner._calculate_observation_weight({
            'timestamp': time.time(),
            'success': False
        })
        assert weight < 1.2  # Should be reduced

    def test_get_top_preferences(self, preference_learner):
        """Test getting top preferences."""
        # Create multiple preferences with different confidence levels
        preference_learner.observe_coding_pattern('naming_conventions', 'style1', 'value1')
        for _ in range(5):
            preference_learner.observe_coding_pattern('naming_conventions', 'style2', 'value2')

        top_prefs = preference_learner.user_preferences.get_top_preferences('naming_conventions', 2)
        assert len(top_prefs) == 2
        assert top_prefs[0][1].confidence > top_prefs[1][1].confidence

    def test_data_persistence(self, preference_learner, temp_dir):
        """Test data persistence to disk."""
        # Create some data
        preference_learner.observe_coding_pattern('test_category', 'test_key', 'test_value')
        preference_learner._save_user_preferences()

        # Create new instance (simulates restart)
        with patch('pathlib.Path.home', return_value=temp_dir):
            new_learner = UserPreferenceLearner(preference_learner.session_manager)

        # Check data was loaded
        pattern = new_learner.user_preferences.get_preference('test_category', 'test_key')
        assert pattern is not None
        assert pattern.preference_value == 'test_value'

    def test_learning_stats(self, preference_learner):
        """Test learning statistics generation."""
        # Add some patterns
        preference_learner.observe_coding_pattern('naming_conventions', 'style1', 'value1')
        for _ in range(10):  # Build high confidence
            preference_learner.observe_coding_pattern('naming_conventions', 'style2', 'value2')

        stats = preference_learner.get_learning_stats()
        assert stats['total_patterns'] >= 2
        assert stats['high_confidence_patterns'] >= 1
        assert 'naming_conventions' in stats['learning_categories']
        assert 'profile_age_days' in stats
        assert 'last_updated' in stats

    def test_preference_data_structures(self):
        """Test preference data structures."""
        # Test CodingPattern
        pattern = CodingPattern(
            pattern_type='test_type',
            pattern_key='test_key',
            preference_value='test_value',
            confidence=0.75,
            occurrences=5
        )

        pattern.update_confidence('test_value', 1.0)
        assert pattern.confidence > 0.75
        assert pattern.occurrences == 6

        # Test UserPreferences
        prefs = UserPreferences(
            user_id='test_user',
            created_at=time.time(),
            last_updated=time.time()
        )

        test_pattern = CodingPattern('test', 'key', 'value')
        prefs.set_preference('naming_conventions', 'test_key', test_pattern)

        retrieved = prefs.get_preference('naming_conventions', 'test_key')
        assert retrieved == test_pattern

        # Test serialization
        data = asdict(prefs)
        assert isinstance(data, dict)
        assert data['user_id'] == 'test_user'