"""
Learning Metrics Dashboard - Phase 3.5 Self-Improving System
Provides comprehensive metrics and insights into system learning and improvement.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics

from isaac.core.session_manager import SessionManager
from isaac.learning.mistake_learner import MistakeLearner
from isaac.learning.behavior_adjustment import BehaviorAdjustmentEngine


@dataclass
class LearningMetrics:
    """Comprehensive learning metrics for the system."""
    timestamp: float
    period_days: int

    # Mistake learning metrics
    total_mistakes: int = 0
    learned_mistakes: int = 0
    learning_patterns: int = 0
    mistake_types: Dict[str, int] = None
    learning_rate: float = 0.0

    # Behavior adjustment metrics
    total_adjustments: int = 0
    effective_adjustments: int = 0
    adjustment_categories: Dict[str, int] = None
    behavior_profile_confidence: Dict[str, float] = None

    # Overall learning health
    learning_health_score: float = 0.0  # 0-100
    improvement_trend: List[float] = None  # Recent performance scores
    recommendations: List[str] = None

    def __post_init__(self):
        if self.mistake_types is None:
            self.mistake_types = {}
        if self.adjustment_categories is None:
            self.adjustment_categories = {}
        if self.behavior_profile_confidence is None:
            self.behavior_profile_confidence = {}
        if self.improvement_trend is None:
            self.improvement_trend = []
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class LearningInsight:
    """An actionable insight about the learning system."""
    id: str
    insight_type: str  # 'improvement', 'warning', 'opportunity'
    title: str
    description: str
    metric: str
    value: Any
    threshold: Any
    recommendation: str
    priority: str  # 'low', 'medium', 'high', 'critical'
    created_at: float


class LearningMetricsDashboard:
    """Dashboard for monitoring and analyzing learning system performance."""

    def __init__(self, session_manager: SessionManager,
                 mistake_learner: MistakeLearner,
                 behavior_engine: BehaviorAdjustmentEngine):
        self.session_manager = session_manager
        self.mistake_learner = mistake_learner
        self.behavior_engine = behavior_engine

        self.data_dir = Path.home() / '.isaac' / 'learning_metrics'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Data files
        self.metrics_file = self.data_dir / 'learning_metrics.json'
        self.insights_file = self.data_dir / 'learning_insights.json'

        # Data structures
        self.metrics_history: List[LearningMetrics] = []
        self.learning_insights: List[LearningInsight] = []

        # Load data
        self._load_metrics_history()
        self._load_learning_insights()

    def generate_current_metrics(self, period_days: int = 7) -> LearningMetrics:
        """Generate current learning metrics for the specified period."""
        # Get data from learning components
        mistake_stats = self.mistake_learner.get_learning_stats()
        behavior_analysis = self.behavior_engine.analyze_behavior_effectiveness()
        behavior_profile = self.behavior_engine.get_current_behavior_profile()

        # Calculate metrics
        metrics = LearningMetrics(
            timestamp=time.time(),
            period_days=period_days,
            total_mistakes=mistake_stats.get('total_mistakes', 0),
            learned_mistakes=mistake_stats.get('learned_mistakes', 0),
            learning_patterns=mistake_stats.get('learning_patterns', 0),
            mistake_types=mistake_stats.get('mistake_types', {}),
            learning_rate=mistake_stats.get('learning_rate', 0.0),
            total_adjustments=behavior_analysis.get('total_adjustments', 0),
            adjustment_categories={
                cat: data['total_adjustments']
                for cat, data in behavior_analysis.get('category_effectiveness', {}).items()
            },
            behavior_profile_confidence=behavior_profile.confidence_scores
        )

        # Calculate learning health score
        metrics.learning_health_score = self._calculate_learning_health_score(metrics)

        # Calculate improvement trend
        metrics.improvement_trend = self._calculate_improvement_trend(period_days)

        # Generate recommendations
        metrics.recommendations = self._generate_recommendations(metrics)

        # Store metrics
        self.metrics_history.append(metrics)
        self._save_metrics_history()

        # Generate insights
        self._generate_insights(metrics)

        return metrics

    def _calculate_learning_health_score(self, metrics: LearningMetrics) -> float:
        """Calculate overall learning health score (0-100)."""
        score = 0.0

        # Learning rate component (0-40 points)
        learning_rate_score = min(metrics.learning_rate * 100, 40)
        score += learning_rate_score

        # Pattern development component (0-30 points)
        pattern_score = min(metrics.learning_patterns * 2, 30)  # 15 patterns = max
        score += pattern_score

        # Behavior adaptation component (0-30 points)
        avg_confidence = statistics.mean(metrics.behavior_profile_confidence.values()) if metrics.behavior_profile_confidence else 0.0
        adaptation_score = avg_confidence * 30
        score += adaptation_score

        return min(score, 100.0)

    def _calculate_improvement_trend(self, period_days: int) -> List[float]:
        """Calculate recent improvement trend."""
        if len(self.metrics_history) < 2:
            return [50.0]  # Default neutral score

        # Get recent metrics
        cutoff_time = time.time() - (period_days * 24 * 3600)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]

        if len(recent_metrics) < 2:
            return [recent_metrics[0].learning_health_score if recent_metrics else 50.0]

        # Return health scores for trend analysis
        return [m.learning_health_score for m in recent_metrics[-10:]]  # Last 10 data points

    def _generate_recommendations(self, metrics: LearningMetrics) -> List[str]:
        """Generate recommendations based on current metrics."""
        recommendations = []

        # Learning rate recommendations
        if metrics.learning_rate < 0.3:
            recommendations.append("Learning rate is low. Consider increasing mistake tracking or pattern generation.")
        elif metrics.learning_rate > 0.8:
            recommendations.append("Excellent learning rate! The system is effectively learning from mistakes.")

        # Pattern development recommendations
        if metrics.learning_patterns < 5:
            recommendations.append("Few learning patterns detected. More user interactions needed to build patterns.")
        elif metrics.learning_patterns > 20:
            recommendations.append("Many learning patterns developed. Consider reviewing and consolidating similar patterns.")

        # Behavior adaptation recommendations
        avg_confidence = statistics.mean(metrics.behavior_profile_confidence.values()) if metrics.behavior_profile_confidence else 0.0
        if avg_confidence < 0.5:
            recommendations.append("Low confidence in behavior adaptations. More feedback needed for reliable adjustments.")
        elif avg_confidence > 0.8:
            recommendations.append("High confidence in behavior adaptations. The system is well-tuned to user preferences.")

        # Health score recommendations
        if metrics.learning_health_score < 40:
            recommendations.append("Learning health is poor. Focus on increasing mistake learning and behavior adaptation.")
        elif metrics.learning_health_score > 80:
            recommendations.append("Learning health is excellent! The system is performing optimally.")

        return recommendations[:5]  # Limit to top 5 recommendations

    def _generate_insights(self, metrics: LearningMetrics):
        """Generate actionable insights from metrics."""
        insights = []

        # Learning rate insight
        if metrics.learning_rate < 0.2:
            insights.append(LearningInsight(
                id=f"insight_learning_rate_{int(time.time())}",
                insight_type="warning",
                title="Low Learning Rate",
                description=f"Learning rate is {metrics.learning_rate:.1%}, below recommended threshold of 20%",
                metric="learning_rate",
                value=metrics.learning_rate,
                threshold=0.2,
                recommendation="Increase mistake tracking frequency or improve pattern matching algorithms",
                priority="high",
                created_at=time.time()
            ))

        # Pattern development insight
        if metrics.learning_patterns == 0:
            insights.append(LearningInsight(
                id=f"insight_no_patterns_{int(time.time())}",
                insight_type="opportunity",
                title="No Learning Patterns",
                description="System has not developed any learning patterns yet",
                metric="learning_patterns",
                value=0,
                threshold=1,
                recommendation="Encourage more user interactions to build initial learning patterns",
                priority="medium",
                created_at=time.time()
            ))

        # Behavior adaptation insight
        avg_confidence = statistics.mean(metrics.behavior_profile_confidence.values()) if metrics.behavior_profile_confidence else 0.0
        if avg_confidence < 0.4:
            insights.append(LearningInsight(
                id=f"insight_low_adaptation_{int(time.time())}",
                insight_type="improvement",
                title="Low Behavior Adaptation Confidence",
                description=f"Average adaptation confidence is {avg_confidence:.1%}, indicating uncertain behavior adjustments",
                metric="behavior_adaptation_confidence",
                value=avg_confidence,
                threshold=0.4,
                recommendation="Collect more user feedback to improve behavior adaptation accuracy",
                priority="medium",
                created_at=time.time()
            ))

        # Add insights to history
        self.learning_insights.extend(insights)
        self._save_learning_insights()

    def get_metrics_history(self, limit: int = 10) -> List[LearningMetrics]:
        """Get recent metrics history."""
        return self.metrics_history[-limit:]

    def get_learning_insights(self, insight_type: Optional[str] = None,
                            priority: Optional[str] = None, limit: int = 10) -> List[LearningInsight]:
        """Get learning insights, optionally filtered."""
        insights = self.learning_insights

        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]

        if priority:
            insights = [i for i in insights if i.priority == priority]

        # Sort by creation time (most recent first)
        insights.sort(key=lambda i: i.created_at, reverse=True)

        return insights[:limit]

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get a comprehensive dashboard summary."""
        if not self.metrics_history:
            return {"message": "No metrics available. Generate initial metrics first."}

        latest_metrics = self.metrics_history[-1]

        # Calculate trends
        health_trend = "stable"
        if len(latest_metrics.improvement_trend) >= 2:
            recent_avg = statistics.mean(latest_metrics.improvement_trend[-3:]) if len(latest_metrics.improvement_trend) >= 3 else latest_metrics.improvement_trend[-1]
            earlier_avg = statistics.mean(latest_metrics.improvement_trend[:-3]) if len(latest_metrics.improvement_trend) >= 6 else latest_metrics.improvement_trend[0]

            if recent_avg > earlier_avg + 5:
                health_trend = "improving"
            elif recent_avg < earlier_avg - 5:
                health_trend = "declining"

        # Get active insights
        active_insights = self.get_learning_insights(limit=5)

        return {
            "current_health_score": latest_metrics.learning_health_score,
            "health_trend": health_trend,
            "total_mistakes": latest_metrics.total_mistakes,
            "learning_patterns": latest_metrics.learning_patterns,
            "behavior_adjustments": latest_metrics.total_adjustments,
            "learning_rate": latest_metrics.learning_rate,
            "active_insights": len(active_insights),
            "recommendations": latest_metrics.recommendations,
            "generated_at": datetime.fromtimestamp(latest_metrics.timestamp).isoformat()
        }

    def _load_metrics_history(self):
        """Load metrics history from disk."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    self.metrics_history = [LearningMetrics(**item) for item in data]
            except Exception as e:
                print(f"Error loading metrics history: {e}")

    def _save_metrics_history(self):
        """Save metrics history to disk."""
        try:
            data = [asdict(m) for m in self.metrics_history[-100:]]  # Keep last 100
            with open(self.metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving metrics history: {e}")

    def _load_learning_insights(self):
        """Load learning insights from disk."""
        if self.insights_file.exists():
            try:
                with open(self.insights_file, 'r') as f:
                    data = json.load(f)
                    self.learning_insights = [LearningInsight(**item) for item in data]
            except Exception as e:
                print(f"Error loading learning insights: {e}")

    def _save_learning_insights(self):
        """Save learning insights to disk."""
        try:
            data = [asdict(i) for i in self.learning_insights[-200:]]  # Keep last 200
            with open(self.insights_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving learning insights: {e}")