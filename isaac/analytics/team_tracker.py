"""
Team Analytics Tracker

Tracks team productivity, collaboration, and shared metrics.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

from isaac.analytics.database import AnalyticsDatabase


@dataclass
class TeamSnapshot:
    """A snapshot of team metrics"""
    timestamp: str
    team_id: str
    active_members: int
    total_contributions: int
    collaboration_score: float
    shared_patterns: int
    knowledge_sharing_events: int


class TeamTracker:
    """Tracks team analytics and collaboration metrics"""

    def __init__(
        self,
        team_id: str = "default",
        db: Optional[AnalyticsDatabase] = None
    ):
        """Initialize team tracker"""
        self.db = db or AnalyticsDatabase()
        self.team_id = team_id
        self.session_id = datetime.now().isoformat()

        # Counters
        self.contributions = 0
        self.shared_patterns = 0
        self.knowledge_shares = 0

    def record_contribution(
        self,
        user_id: str,
        contribution_type: str,
        contribution_value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a team member contribution"""
        self.contributions += 1

        self.db.record_team_activity(
            activity_type='contribution',
            activity_name=contribution_type,
            activity_value=contribution_value,
            team_id=self.team_id,
            user_id=user_id,
            metadata=json.dumps(metadata) if metadata else None
        )

    def record_pattern_share(
        self,
        user_id: str,
        pattern_name: str,
        usage_count: int = 0
    ):
        """Record sharing of a code pattern with team"""
        self.shared_patterns += 1

        self.db.record_team_activity(
            activity_type='pattern_share',
            activity_name=pattern_name,
            activity_value=float(usage_count),
            team_id=self.team_id,
            user_id=user_id
        )

    def record_knowledge_share(
        self,
        user_id: str,
        knowledge_type: str,
        impact_score: float
    ):
        """Record knowledge sharing event"""
        self.knowledge_shares += 1

        self.db.record_team_activity(
            activity_type='knowledge_share',
            activity_name=knowledge_type,
            activity_value=impact_score,
            team_id=self.team_id,
            user_id=user_id
        )

    def record_collaboration(
        self,
        users: List[str],
        collaboration_type: str,
        effectiveness: float
    ):
        """Record collaboration event"""
        # Record for each user
        for user_id in users:
            self.db.record_team_activity(
                activity_type='collaboration',
                activity_name=collaboration_type,
                activity_value=effectiveness,
                team_id=self.team_id,
                user_id=user_id,
                metadata=json.dumps({'collaborators': users})
            )

    def record_code_review(
        self,
        reviewer_id: str,
        author_id: str,
        review_quality: float
    ):
        """Record code review activity"""
        # Record for reviewer
        self.db.record_team_activity(
            activity_type='code_review',
            activity_name='review_given',
            activity_value=review_quality,
            team_id=self.team_id,
            user_id=reviewer_id,
            metadata=json.dumps({'author': author_id})
        )

        # Record for author
        self.db.record_team_activity(
            activity_type='code_review',
            activity_name='review_received',
            activity_value=review_quality,
            team_id=self.team_id,
            user_id=author_id,
            metadata=json.dumps({'reviewer': reviewer_id})
        )

    def record_pair_programming(
        self,
        user1_id: str,
        user2_id: str,
        duration_minutes: float,
        productivity_score: float
    ):
        """Record pair programming session"""
        for user_id in [user1_id, user2_id]:
            self.db.record_team_activity(
                activity_type='pair_programming',
                activity_name='session',
                activity_value=productivity_score,
                team_id=self.team_id,
                user_id=user_id,
                metadata=json.dumps({
                    'duration': duration_minutes,
                    'partner': user2_id if user_id == user1_id else user1_id
                })
            )

    def calculate_collaboration_score(self) -> float:
        """Calculate team collaboration score (0-100)"""
        # Get recent team activities
        recent_activities = self.db.query_metrics(
            'team_analytics',
            start_date=(datetime.now() - timedelta(days=7)).isoformat(),
            filters={'team_id': self.team_id}
        )

        if not recent_activities:
            return 0.0

        # Count collaboration events
        collaborations = len([
            a for a in recent_activities
            if a['activity_type'] in ['collaboration', 'pair_programming', 'code_review']
        ])

        # Count knowledge sharing
        knowledge_shares = len([
            a for a in recent_activities
            if a['activity_type'] in ['knowledge_share', 'pattern_share']
        ])

        # Calculate score
        # More collaborations and knowledge sharing = higher score
        score = min(100, (
            collaborations * 5 +
            knowledge_shares * 3
        ))

        return score

    def get_current_snapshot(self) -> TeamSnapshot:
        """Get current team snapshot"""
        # Get active members (unique users in last 24 hours)
        recent_activities = self.db.query_metrics(
            'team_analytics',
            start_date=(datetime.now() - timedelta(hours=24)).isoformat(),
            filters={'team_id': self.team_id}
        )

        active_members = len(set(
            a['user_id'] for a in recent_activities
            if a.get('user_id')
        ))

        return TeamSnapshot(
            timestamp=datetime.now().isoformat(),
            team_id=self.team_id,
            active_members=active_members,
            total_contributions=self.contributions,
            collaboration_score=self.calculate_collaboration_score(),
            shared_patterns=self.shared_patterns,
            knowledge_sharing_events=self.knowledge_shares
        )

    def get_team_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate team analytics report"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).isoformat()
        if not end_date:
            end_date = datetime.now().isoformat()

        # Get all team activities
        activities = self.db.query_metrics(
            'team_analytics',
            start_date=start_date,
            end_date=end_date,
            filters={'team_id': self.team_id}
        )

        # Aggregate by user
        user_stats = defaultdict(lambda: {
            'contributions': 0,
            'collaborations': 0,
            'reviews_given': 0,
            'reviews_received': 0,
            'patterns_shared': 0,
            'knowledge_shared': 0,
            'pair_sessions': 0
        })

        for activity in activities:
            user_id = activity.get('user_id', 'unknown')
            activity_type = activity['activity_type']

            if activity_type == 'contribution':
                user_stats[user_id]['contributions'] += 1
            elif activity_type == 'collaboration':
                user_stats[user_id]['collaborations'] += 1
            elif activity_type == 'code_review':
                if activity['activity_name'] == 'review_given':
                    user_stats[user_id]['reviews_given'] += 1
                else:
                    user_stats[user_id]['reviews_received'] += 1
            elif activity_type == 'pattern_share':
                user_stats[user_id]['patterns_shared'] += 1
            elif activity_type == 'knowledge_share':
                user_stats[user_id]['knowledge_shared'] += 1
            elif activity_type == 'pair_programming':
                user_stats[user_id]['pair_sessions'] += 1

        # Calculate team totals
        total_contributions = sum(u['contributions'] for u in user_stats.values())
        total_collaborations = sum(u['collaborations'] for u in user_stats.values())
        total_reviews = sum(u['reviews_given'] for u in user_stats.values())
        total_patterns = sum(u['patterns_shared'] for u in user_stats.values())
        total_knowledge = sum(u['knowledge_shared'] for u in user_stats.values())

        return {
            'team_id': self.team_id,
            'period': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'active_members': len(user_stats),
                'total_contributions': total_contributions,
                'total_collaborations': total_collaborations,
                'total_code_reviews': total_reviews,
                'total_patterns_shared': total_patterns,
                'total_knowledge_shared': total_knowledge,
                'collaboration_score': self.calculate_collaboration_score()
            },
            'current_snapshot': asdict(self.get_current_snapshot()),
            'members': dict(user_stats),
            'insights': self._generate_team_insights(
                user_stats, total_collaborations,
                total_reviews, total_patterns
            ),
            'top_contributors': self._get_top_contributors(user_stats)
        }

    def _generate_team_insights(
        self,
        user_stats: Dict[str, Dict[str, int]],
        collaborations: int,
        reviews: int,
        patterns: int
    ) -> List[str]:
        """Generate insights from team data"""
        insights = []

        team_size = len(user_stats)

        if team_size == 0:
            insights.append("📊 No team activity yet - start collaborating!")
            return insights

        if team_size >= 5:
            insights.append(f"👥 Active team of {team_size} members")

        if collaborations > 20:
            insights.append(
                f"🤝 High collaboration! {collaborations} collaborative events"
            )

        if reviews > 10:
            insights.append(
                f"👀 Strong code review culture: {reviews} reviews conducted"
            )

        if patterns > 5:
            insights.append(
                f"📚 Knowledge sharing is active: {patterns} patterns shared"
            )

        collaboration_score = self.calculate_collaboration_score()
        if collaboration_score >= 80:
            insights.append("🌟 Excellent team collaboration score!")
        elif collaboration_score >= 50:
            insights.append("👍 Good collaboration - keep it up!")
        else:
            insights.append("💡 More collaboration could boost team productivity")

        return insights

    def _get_top_contributors(
        self,
        user_stats: Dict[str, Dict[str, int]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get top contributors"""
        # Calculate contribution scores
        contributors = []
        for user_id, stats in user_stats.items():
            score = (
                stats['contributions'] * 1.0 +
                stats['collaborations'] * 2.0 +
                stats['reviews_given'] * 1.5 +
                stats['patterns_shared'] * 3.0 +
                stats['knowledge_shared'] * 2.5
            )
            contributors.append({
                'user_id': user_id,
                'score': score,
                'stats': stats
            })

        # Sort by score
        contributors.sort(key=lambda c: c['score'], reverse=True)

        return contributors[:limit]

    def get_collaboration_matrix(self) -> Dict[str, Any]:
        """Get collaboration matrix showing who works with whom"""
        # Get collaboration activities
        activities = self.db.query_metrics(
            'team_analytics',
            filters={
                'team_id': self.team_id,
            }
        )

        # Build collaboration matrix
        matrix = defaultdict(lambda: defaultdict(int))

        for activity in activities:
            if activity['activity_type'] in ['collaboration', 'pair_programming', 'code_review']:
                user_id = activity.get('user_id')
                if not user_id:
                    continue

                # Parse metadata for collaborators
                metadata = activity.get('metadata')
                if metadata:
                    try:
                        data = json.loads(metadata)
                        if 'collaborators' in data:
                            for collaborator in data['collaborators']:
                                if collaborator != user_id:
                                    matrix[user_id][collaborator] += 1
                        elif 'partner' in data:
                            matrix[user_id][data['partner']] += 1
                        elif 'author' in data:
                            matrix[user_id][data['author']] += 1
                        elif 'reviewer' in data:
                            matrix[user_id][data['reviewer']] += 1
                    except json.JSONDecodeError:
                        pass

        # Convert to regular dict
        return {
            user: dict(collaborators)
            for user, collaborators in matrix.items()
        }

    def get_activity_timeline(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get team activity timeline"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        activities = self.db.query_metrics(
            'team_analytics',
            start_date=start_date,
            filters={'team_id': self.team_id}
        )

        # Group by day
        daily_activities = defaultdict(lambda: {
            'contributions': 0,
            'collaborations': 0,
            'reviews': 0,
            'patterns': 0,
            'active_users': set()
        })

        for activity in activities:
            date = activity['timestamp'][:10]
            activity_type = activity['activity_type']
            user_id = activity.get('user_id')

            if user_id:
                daily_activities[date]['active_users'].add(user_id)

            if activity_type == 'contribution':
                daily_activities[date]['contributions'] += 1
            elif activity_type in ['collaboration', 'pair_programming']:
                daily_activities[date]['collaborations'] += 1
            elif activity_type == 'code_review':
                daily_activities[date]['reviews'] += 1
            elif activity_type in ['pattern_share', 'knowledge_share']:
                daily_activities[date]['patterns'] += 1

        # Convert to list
        timeline = []
        for date, data in sorted(daily_activities.items()):
            timeline.append({
                'date': date,
                'contributions': data['contributions'],
                'collaborations': data['collaborations'],
                'reviews': data['reviews'],
                'patterns': data['patterns'],
                'active_users': len(data['active_users'])
            })

        return timeline
