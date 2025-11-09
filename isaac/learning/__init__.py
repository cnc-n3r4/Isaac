"""
Self-Improving Learning System - Phase 3.5
Components for continuous learning and improvement.
"""

from .mistake_learner import MistakeLearner, MistakeRecord, LearningPattern
from .behavior_adjustment import BehaviorAdjustmentEngine, UserFeedback, BehaviorAdjustment, BehaviorProfile
from .learning_metrics import LearningMetricsDashboard, LearningMetrics, LearningInsight
from .user_preference_learner import UserPreferenceLearner, UserPreferences, CodingPattern
from .continuous_learning_coordinator import ContinuousLearningCoordinator
from .performance_analytics import PerformanceAnalytics, PerformanceMetric, PerformanceAlert

__all__ = [
    'MistakeLearner',
    'MistakeRecord',
    'LearningPattern',
    'BehaviorAdjustmentEngine',
    'UserFeedback',
    'BehaviorAdjustment',
    'BehaviorProfile',
    'LearningMetricsDashboard',
    'LearningMetrics',
    'LearningInsight',
    'UserPreferenceLearner',
    'UserPreferences',
    'CodingPattern',
    'ContinuousLearningCoordinator',
    'PerformanceAnalytics',
    'PerformanceMetric',
    'PerformanceAlert'
]
