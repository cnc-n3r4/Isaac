"""
Behavior Adjustment Engine - Phase 3.5 Self-Improving System
Automatically adjusts Isaac's behavior based on user feedback patterns.
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics

from isaac.core.session_manager import SessionManager
from isaac.learning.mistake_learner import MistakeLearner


@dataclass
class UserFeedback:
    """A piece of user feedback about Isaac's behavior."""
    id: str
    timestamp: float
    feedback_type: str  # 'positive', 'negative', 'correction', 'preference'
    context: str  # What Isaac did/said
    user_response: str  # User's feedback/correction
    sentiment_score: float  # -1.0 to 1.0
    behavior_category: str  # 'response_style', 'suggestion_frequency', 'detail_level', etc.
    adjustment_suggestion: Optional[str] = None


@dataclass
class BehaviorAdjustment:
    """An adjustment to Isaac's behavior based on feedback."""
    id: str
    behavior_category: str
    current_value: Any
    target_value: Any
    confidence: float
    reason: str
    applied_at: Optional[float] = None
    effectiveness_score: Optional[float] = None


@dataclass
class BehaviorProfile:
    """Profile of user's preferred behavior patterns."""
    user_id: str
    response_style: str  # 'concise', 'detailed', 'balanced'
    suggestion_frequency: str  # 'low', 'medium', 'high'
    detail_level: str  # 'brief', 'moderate', 'comprehensive'
    humor_level: str  # 'none', 'subtle', 'moderate', 'high'
    technical_depth: str  # 'beginner', 'intermediate', 'expert'
    interaction_pace: str  # 'slow', 'moderate', 'fast'
    last_updated: float
    confidence_scores: Dict[str, float] = None

    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = {}


class BehaviorAdjustmentEngine:
    """Engine for adjusting Isaac's behavior based on user feedback."""

    def __init__(self, session_manager: SessionManager, mistake_learner: MistakeLearner):
        self.session_manager = session_manager
        self.mistake_learner = mistake_learner

        self.data_dir = Path.home() / '.isaac' / 'behavior'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Data files
        self.feedback_file = self.data_dir / 'user_feedback.json'
        self.adjustments_file = self.data_dir / 'behavior_adjustments.json'
        self.profile_file = self.data_dir / 'behavior_profile.json'

        # Data structures
        self.feedback_history: List[UserFeedback] = []
        self.behavior_adjustments: Dict[str, BehaviorAdjustment] = {}
        self.behavior_profile: Optional[BehaviorProfile] = None

        # Load data
        self._load_feedback_history()
        self._load_behavior_adjustments()
        self._load_behavior_profile()

        # Default profile if none exists
        if self.behavior_profile is None:
            self.behavior_profile = BehaviorProfile(
                user_id="default",
                response_style="balanced",
                suggestion_frequency="medium",
                detail_level="moderate",
                humor_level="subtle",
                technical_depth="intermediate",
                interaction_pace="moderate",
                last_updated=time.time()
            )
            self._save_behavior_profile()

    def record_feedback(self, feedback: UserFeedback):
        """Record user feedback for behavior analysis."""
        self.feedback_history.append(feedback)
        self._save_feedback_history()

        # Analyze feedback and potentially create adjustments
        adjustment = self._analyze_feedback_for_adjustment(feedback)
        if adjustment:
            self.apply_behavior_adjustment(adjustment)

    def _analyze_feedback_for_adjustment(self, feedback: UserFeedback) -> Optional[BehaviorAdjustment]:
        """Analyze feedback to determine if behavior adjustment is needed."""
        # Analyze recent feedback for patterns
        recent_feedback = self._get_recent_feedback(feedback.behavior_category, hours=24)

        if len(recent_feedback) < 3:  # Need minimum samples
            return None

        # Calculate sentiment trend
        sentiments = [f.sentiment_score for f in recent_feedback]
        avg_sentiment = statistics.mean(sentiments)

        # Check for consistent negative feedback
        negative_count = sum(1 for s in sentiments if s < -0.3)
        if negative_count >= len(sentiments) * 0.6:  # 60% negative
            return self._create_adjustment_for_negative_feedback(feedback, avg_sentiment)

        # Check for consistent positive feedback on specific behaviors
        positive_count = sum(1 for s in sentiments if s > 0.3)
        if positive_count >= len(sentiments) * 0.7:  # 70% positive
            return self._create_adjustment_for_positive_feedback(feedback, avg_sentiment)

        return None

    def _get_recent_feedback(self, category: str, hours: int) -> List[UserFeedback]:
        """Get recent feedback for a specific category."""
        cutoff_time = time.time() - (hours * 3600)
        return [
            f for f in self.feedback_history
            if f.behavior_category == category and f.timestamp > cutoff_time
        ]

    def _create_adjustment_for_negative_feedback(self, feedback: UserFeedback,
                                               avg_sentiment: float) -> BehaviorAdjustment:
        """Create adjustment based on negative feedback pattern."""
        adjustment_id = f"adj_negative_{feedback.behavior_category}_{int(time.time())}"

        # Determine what to adjust based on category
        if feedback.behavior_category == "response_style":
            current = self.behavior_profile.response_style
            target = "concise" if current == "detailed" else "balanced"
            reason = f"User shows dissatisfaction with {current} responses (avg sentiment: {avg_sentiment:.2f})"

        elif feedback.behavior_category == "suggestion_frequency":
            current = self.behavior_profile.suggestion_frequency
            target = "low" if current in ["medium", "high"] else "medium"
            reason = f"Reducing suggestion frequency due to negative feedback (avg sentiment: {avg_sentiment:.2f})"

        elif feedback.behavior_category == "detail_level":
            current = self.behavior_profile.detail_level
            target = "brief" if current in ["moderate", "comprehensive"] else "moderate"
            reason = f"Reducing detail level due to user feedback (avg sentiment: {avg_sentiment:.2f})"

        else:
            target = "balanced"  # Default fallback
            reason = f"General behavior adjustment due to negative feedback (avg sentiment: {avg_sentiment:.2f})"

        return BehaviorAdjustment(
            id=adjustment_id,
            behavior_category=feedback.behavior_category,
            current_value=current,
            target_value=target,
            confidence=min(0.8, abs(avg_sentiment)),
            reason=reason
        )

    def _create_adjustment_for_positive_feedback(self, feedback: UserFeedback,
                                               avg_sentiment: float) -> BehaviorAdjustment:
        """Create adjustment to reinforce positive feedback patterns."""
        adjustment_id = f"adj_positive_{feedback.behavior_category}_{int(time.time())}"

        # Reinforce what's working well
        current = getattr(self.behavior_profile, feedback.behavior_category, "balanced")
        target = current  # Keep doing what works
        reason = f"Reinforcing successful {feedback.behavior_category} (avg sentiment: {avg_sentiment:.2f})"

        return BehaviorAdjustment(
            id=adjustment_id,
            behavior_category=feedback.behavior_category,
            current_value=current,
            target_value=target,
            confidence=min(0.9, avg_sentiment),
            reason=reason
        )

    def apply_behavior_adjustment(self, adjustment: BehaviorAdjustment):
        """Apply a behavior adjustment to the profile."""
        # Update the behavior profile
        if hasattr(self.behavior_profile, adjustment.behavior_category):
            setattr(self.behavior_profile, adjustment.behavior_category, adjustment.target_value)
            self.behavior_profile.last_updated = time.time()

            # Update confidence score
            self.behavior_profile.confidence_scores[adjustment.behavior_category] = adjustment.confidence

            self._save_behavior_profile()

        # Record the adjustment
        adjustment.applied_at = time.time()
        self.behavior_adjustments[adjustment.id] = adjustment
        self._save_behavior_adjustments()

    def get_current_behavior_profile(self) -> BehaviorProfile:
        """Get the current behavior profile."""
        return self.behavior_profile

    def get_behavior_adjustments(self, category: Optional[str] = None,
                               limit: int = 10) -> List[BehaviorAdjustment]:
        """Get behavior adjustments, optionally filtered by category."""
        adjustments = list(self.behavior_adjustments.values())

        if category:
            adjustments = [a for a in adjustments if a.behavior_category == category]

        # Sort by application time (most recent first)
        adjustments.sort(key=lambda a: a.applied_at or 0, reverse=True)

        return adjustments[:limit]

    def analyze_behavior_effectiveness(self) -> Dict[str, Any]:
        """Analyze the effectiveness of behavior adjustments."""
        if not self.behavior_adjustments:
            return {"message": "No adjustments to analyze"}

        # Calculate effectiveness metrics
        applied_adjustments = [a for a in self.behavior_adjustments.values() if a.applied_at]

        if not applied_adjustments:
            return {"message": "No applied adjustments to analyze"}

        # Group by category
        category_effectiveness = {}
        for adjustment in applied_adjustments:
            cat = adjustment.behavior_category
            if cat not in category_effectiveness:
                category_effectiveness[cat] = {
                    'total_adjustments': 0,
                    'avg_confidence': 0,
                    'recent_adjustments': 0
                }

            category_effectiveness[cat]['total_adjustments'] += 1
            category_effectiveness[cat]['avg_confidence'] += adjustment.confidence

            # Count recent adjustments (last 7 days)
            if adjustment.applied_at and (time.time() - adjustment.applied_at) < (7 * 24 * 3600):
                category_effectiveness[cat]['recent_adjustments'] += 1

        # Calculate averages
        for cat_data in category_effectiveness.values():
            if cat_data['total_adjustments'] > 0:
                cat_data['avg_confidence'] /= cat_data['total_adjustments']

        return {
            'total_adjustments': len(applied_adjustments),
            'category_effectiveness': category_effectiveness,
            'most_adjusted_category': max(category_effectiveness.keys(),
                                        key=lambda k: category_effectiveness[k]['total_adjustments'])
        }

    def _load_feedback_history(self):
        """Load feedback history from disk."""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    data = json.load(f)
                    self.feedback_history = [UserFeedback(**item) for item in data]
            except Exception as e:
                print(f"Error loading feedback history: {e}")

    def _save_feedback_history(self):
        """Save feedback history to disk."""
        try:
            data = [asdict(f) for f in self.feedback_history[-1000:]]  # Keep last 1000
            with open(self.feedback_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving feedback history: {e}")

    def _load_behavior_adjustments(self):
        """Load behavior adjustments from disk."""
        if self.adjustments_file.exists():
            try:
                with open(self.adjustments_file, 'r') as f:
                    data = json.load(f)
                    for adj_id, adj_data in data.items():
                        self.behavior_adjustments[adj_id] = BehaviorAdjustment(**adj_data)
            except Exception as e:
                print(f"Error loading behavior adjustments: {e}")

    def _save_behavior_adjustments(self):
        """Save behavior adjustments to disk."""
        try:
            data = {aid: asdict(adj) for aid, adj in self.behavior_adjustments.items()}
            with open(self.adjustments_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving behavior adjustments: {e}")

    def _load_behavior_profile(self):
        """Load behavior profile from disk."""
        if self.profile_file.exists():
            try:
                with open(self.profile_file, 'r') as f:
                    data = json.load(f)
                    self.behavior_profile = BehaviorProfile(**data)
            except Exception as e:
                print(f"Error loading behavior profile: {e}")

    def _save_behavior_profile(self):
        """Save behavior profile to disk."""
        try:
            with open(self.profile_file, 'w') as f:
                json.dump(asdict(self.behavior_profile), f, indent=2)
        except Exception as e:
            print(f"Error saving behavior profile: {e}")