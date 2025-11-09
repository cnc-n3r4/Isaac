"""
Self-Improving Learning System - Phase 3.5
Components for continuous learning and improvement.
"""

from .behavior_adjustment import (
    BehaviorAdjustment,
    BehaviorAdjustmentEngine,
    BehaviorProfile,
    UserFeedback,
)
from .continuous_learning_coordinator import ContinuousLearningCoordinator
from .learning_metrics import LearningInsight, LearningMetrics, LearningMetricsDashboard
from .mistake_learner import LearningPattern, MistakeLearner, MistakeRecord
from .performance_analytics import (
    PerformanceAlert,
    PerformanceAnalytics,
    PerformanceMetric,
)
from .user_preference_learner import (
    CodingPattern,
    UserPreferenceLearner,
    UserPreferences,
)

__all__ = [
    "MistakeLearner",
    "MistakeRecord",
    "LearningPattern",
    "BehaviorAdjustmentEngine",
    "UserFeedback",
    "BehaviorAdjustment",
    "BehaviorProfile",
    "LearningMetricsDashboard",
    "LearningMetrics",
    "LearningInsight",
    "UserPreferenceLearner",
    "UserPreferences",
    "CodingPattern",
    "ContinuousLearningCoordinator",
    "PerformanceAnalytics",
    "PerformanceMetric",
    "PerformanceAlert",
]
