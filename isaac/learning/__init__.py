"""
Self-Improving Learning System - Phase 3.5
Components for continuous learning and improvement.
"""

from .mistake_learner import MistakeLearner, MistakeRecord, LearningPattern
from .behavior_adjustment import BehaviorAdjustmentEngine, UserFeedback, BehaviorAdjustment, BehaviorProfile

__all__ = [
    'MistakeLearner',
    'MistakeRecord',
    'LearningPattern',
    'BehaviorAdjustmentEngine',
    'UserFeedback',
    'BehaviorAdjustment',
    'BehaviorProfile'
]