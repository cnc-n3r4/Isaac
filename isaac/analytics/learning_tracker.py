"""
Learning Analytics Tracker

Tracks what Isaac is learning and how it improves over time.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from isaac.analytics.database import AnalyticsDatabase


@dataclass
class LearningSnapshot:
    """A snapshot of learning metrics"""
    timestamp: str
    patterns_learned: int
    preferences_adapted: int
    mistakes_learned_from: int
    behavior_adjustments: int
    learning_rate: float
    adaptation_score: float


class LearningTracker:
    """Tracks learning analytics and system improvement"""

    def __init__(self, db: Optional[AnalyticsDatabase] = None):
        """Initialize learning tracker"""
        self.db = db or AnalyticsDatabase()
        self.session_id = datetime.now().isoformat()

        # Counters
        self.patterns_learned = 0
        self.preferences_adapted = 0
        self.mistakes_learned = 0
        self.behavior_adjustments = 0

    def record_pattern_learned(
        self,
        pattern_name: str,
        pattern_type: str,
        confidence: float,
        usage_count: int = 0
    ):
        """Record a newly learned pattern"""
        self.patterns_learned += 1

        self.db.record_learning_metric(
            learning_type='pattern_learned',
            learning_item=pattern_name,
            confidence=confidence,
            usage_count=usage_count,
            session_id=self.session_id,
            metadata=json.dumps({'pattern_type': pattern_type})
        )

    def record_preference_adaptation(
        self,
        preference_name: str,
        preference_value: Any,
        confidence: float
    ):
        """Record a user preference that was learned"""
        self.preferences_adapted += 1

        self.db.record_learning_metric(
            learning_type='preference_adapted',
            learning_item=preference_name,
            confidence=confidence,
            session_id=self.session_id,
            metadata=json.dumps({'value': str(preference_value)})
        )

    def record_mistake_learned(
        self,
        mistake_type: str,
        correction: str,
        success_rate_improvement: float
    ):
        """Record learning from a mistake"""
        self.mistakes_learned += 1

        self.db.record_learning_metric(
            learning_type='mistake_learned',
            learning_item=mistake_type,
            confidence=success_rate_improvement,
            session_id=self.session_id,
            metadata=json.dumps({'correction': correction})
        )

    def record_behavior_adjustment(
        self,
        behavior_name: str,
        adjustment_type: str,
        effectiveness: float
    ):
        """Record a behavior adjustment"""
        self.behavior_adjustments += 1

        self.db.record_learning_metric(
            learning_type='behavior_adjustment',
            learning_item=behavior_name,
            confidence=effectiveness,
            session_id=self.session_id,
            metadata=json.dumps({'adjustment_type': adjustment_type})
        )

    def record_skill_improvement(
        self,
        skill_name: str,
        before_score: float,
        after_score: float,
        usage_count: int
    ):
        """Record improvement in a specific skill"""
        improvement = after_score - before_score

        self.db.record_learning_metric(
            learning_type='skill_improvement',
            learning_item=skill_name,
            confidence=after_score,
            usage_count=usage_count,
            success_rate=improvement,
            session_id=self.session_id,
            metadata=json.dumps({
                'before_score': before_score,
                'after_score': after_score,
                'improvement': improvement
            })
        )

    def calculate_learning_rate(self) -> float:
        """Calculate current learning rate (0-100)"""
        # Get recent learning metrics
        recent_metrics = self.db.query_metrics(
            'learning_analytics',
            start_date=(datetime.now() - timedelta(days=7)).isoformat()
        )

        if not recent_metrics:
            return 0.0

        # Count different learning types
        pattern_count = len([
            m for m in recent_metrics
            if m['learning_type'] == 'pattern_learned'
        ])
        preference_count = len([
            m for m in recent_metrics
            if m['learning_type'] == 'preference_adapted'
        ])
        mistake_count = len([
            m for m in recent_metrics
            if m['learning_type'] == 'mistake_learned'
        ])
        behavior_count = len([
            m for m in recent_metrics
            if m['learning_type'] == 'behavior_adjustment'
        ])

        # Calculate learning rate
        total_learning_events = (
            pattern_count + preference_count +
            mistake_count + behavior_count
        )

        # Normalize to 0-100 scale
        # Assume 50+ learning events per week = 100% learning rate
        learning_rate = min(100, (total_learning_events / 50) * 100)

        return learning_rate

    def calculate_adaptation_score(self) -> float:
        """Calculate how well Isaac is adapting to user (0-100)"""
        # Get metrics from last 30 days
        metrics = self.db.query_metrics(
            'learning_analytics',
            start_date=(datetime.now() - timedelta(days=30)).isoformat()
        )

        if not metrics:
            return 50.0  # Neutral score

        # Calculate average confidence across all learning
        confidences = [m['confidence'] for m in metrics if m['confidence']]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 50.0

        # Count successful adaptations
        success_rates = [
            m['success_rate'] for m in metrics
            if m['success_rate'] is not None
        ]
        avg_success = (
            sum(success_rates) / len(success_rates)
            if success_rates else 0.0
        )

        # Combined adaptation score
        adaptation = (avg_confidence * 0.6 + avg_success * 0.4)

        return min(100, max(0, adaptation))

    def get_current_snapshot(self) -> LearningSnapshot:
        """Get current learning snapshot"""
        return LearningSnapshot(
            timestamp=datetime.now().isoformat(),
            patterns_learned=self.patterns_learned,
            preferences_adapted=self.preferences_adapted,
            mistakes_learned_from=self.mistakes_learned,
            behavior_adjustments=self.behavior_adjustments,
            learning_rate=self.calculate_learning_rate(),
            adaptation_score=self.calculate_adaptation_score()
        )

    def get_learning_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate learning analytics report"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.now().isoformat()

        # Get metrics from database
        metrics = self.db.query_metrics(
            'learning_analytics',
            start_date=start_date,
            end_date=end_date
        )

        # Aggregate by learning type
        learning_breakdown = {}
        for metric in metrics:
            learning_type = metric['learning_type']
            if learning_type not in learning_breakdown:
                learning_breakdown[learning_type] = {
                    'count': 0,
                    'items': [],
                    'avg_confidence': 0.0
                }

            learning_breakdown[learning_type]['count'] += 1
            learning_breakdown[learning_type]['items'].append({
                'item': metric['learning_item'],
                'confidence': metric['confidence'],
                'timestamp': metric['timestamp']
            })

        # Calculate average confidences
        for learning_type, data in learning_breakdown.items():
            confidences = [
                item['confidence'] for item in data['items']
                if item['confidence'] is not None
            ]
            data['avg_confidence'] = (
                sum(confidences) / len(confidences)
                if confidences else 0.0
            )

        # Get totals
        total_patterns = learning_breakdown.get('pattern_learned', {}).get('count', 0)
        total_preferences = learning_breakdown.get('preference_adapted', {}).get('count', 0)
        total_mistakes = learning_breakdown.get('mistake_learned', {}).get('count', 0)
        total_behaviors = learning_breakdown.get('behavior_adjustment', {}).get('count', 0)
        total_skills = learning_breakdown.get('skill_improvement', {}).get('count', 0)

        return {
            'period': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'total_patterns_learned': total_patterns,
                'total_preferences_adapted': total_preferences,
                'total_mistakes_learned_from': total_mistakes,
                'total_behavior_adjustments': total_behaviors,
                'total_skill_improvements': total_skills,
                'learning_rate': self.calculate_learning_rate(),
                'adaptation_score': self.calculate_adaptation_score()
            },
            'current_session': asdict(self.get_current_snapshot()),
            'breakdown': learning_breakdown,
            'insights': self._generate_learning_insights(
                total_patterns, total_preferences,
                total_mistakes, total_behaviors
            ),
            'top_learnings': self._get_top_learnings(metrics)
        }

    def _generate_learning_insights(
        self,
        patterns: int,
        preferences: int,
        mistakes: int,
        behaviors: int
    ) -> List[str]:
        """Generate insights from learning data"""
        insights = []

        total_learning = patterns + preferences + mistakes + behaviors

        if total_learning > 50:
            insights.append(
                f"🧠 Isaac is actively learning! {total_learning} learning events recorded"
            )

        if patterns > 20:
            insights.append(
                f"📚 {patterns} code patterns learned - improving code generation"
            )

        if preferences > 10:
            insights.append(
                f"🎯 {preferences} preferences adapted - becoming more personalized"
            )

        if mistakes > 5:
            insights.append(
                f"💡 Learned from {mistakes} mistakes - continuously improving"
            )

        if behaviors > 5:
            insights.append(
                f"⚙️  {behaviors} behavior adjustments - adapting to your workflow"
            )

        learning_rate = self.calculate_learning_rate()
        if learning_rate >= 80:
            insights.append("🚀 High learning rate - Isaac is improving rapidly")
        elif learning_rate < 20:
            insights.append("📊 More interactions will help Isaac learn faster")

        return insights

    def _get_top_learnings(
        self,
        metrics: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get top learnings by confidence"""
        # Sort by confidence
        sorted_metrics = sorted(
            metrics,
            key=lambda m: m.get('confidence', 0) or 0,
            reverse=True
        )

        top_learnings = []
        for metric in sorted_metrics[:limit]:
            top_learnings.append({
                'type': metric['learning_type'],
                'item': metric['learning_item'],
                'confidence': metric['confidence'],
                'timestamp': metric['timestamp']
            })

        return top_learnings

    def get_learning_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get learning trend over time"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        metrics = self.db.query_metrics(
            'learning_analytics',
            start_date=start_date
        )

        # Group by day
        daily_learning = {}
        for metric in metrics:
            date = metric['timestamp'][:10]
            if date not in daily_learning:
                daily_learning[date] = {
                    'patterns': 0,
                    'preferences': 0,
                    'mistakes': 0,
                    'behaviors': 0,
                    'total': 0
                }

            daily_learning[date]['total'] += 1

            if metric['learning_type'] == 'pattern_learned':
                daily_learning[date]['patterns'] += 1
            elif metric['learning_type'] == 'preference_adapted':
                daily_learning[date]['preferences'] += 1
            elif metric['learning_type'] == 'mistake_learned':
                daily_learning[date]['mistakes'] += 1
            elif metric['learning_type'] == 'behavior_adjustment':
                daily_learning[date]['behaviors'] += 1

        # Convert to list
        trend = []
        for date, data in sorted(daily_learning.items()):
            trend.append({
                'date': date,
                **data
            })

        return trend

    def get_knowledge_graph(self) -> Dict[str, Any]:
        """Get a knowledge graph of what Isaac has learned"""
        # Get all learning metrics
        metrics = self.db.query_metrics('learning_analytics')

        # Build knowledge graph
        graph = {
            'nodes': [],
            'edges': [],
            'categories': {}
        }

        for metric in metrics:
            learning_type = metric['learning_type']
            learning_item = metric['learning_item']

            # Add to categories
            if learning_type not in graph['categories']:
                graph['categories'][learning_type] = []

            graph['categories'][learning_type].append({
                'item': learning_item,
                'confidence': metric['confidence'],
                'usage_count': metric.get('usage_count', 0)
            })

            # Add node
            graph['nodes'].append({
                'id': f"{learning_type}:{learning_item}",
                'type': learning_type,
                'label': learning_item,
                'confidence': metric['confidence']
            })

        return graph
