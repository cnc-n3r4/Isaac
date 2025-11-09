"""
Learn Command - Interface for Isaac's self-improving learning system
Provides access to mistake learning, behavior adjustment, and metrics
"""

import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from isaac.core.session_manager import SessionManager
from isaac.learning import (
    MistakeLearner,
    BehaviorAdjustmentEngine,
    LearningMetricsDashboard,
    UserPreferenceLearner,
    MistakeRecord,
    UserFeedback
)


class LearnCommand:
    """Command interface for self-improving learning system."""

    def __init__(self, session_manager: Optional[SessionManager] = None):
        """Initialize learn command.

        Args:
            session_manager: Session manager instance (creates default if None)
        """
        self.session_manager = session_manager or SessionManager()

        # Initialize learning components
        self.mistake_learner = MistakeLearner(self.session_manager, start_background_learning=True)
        self.behavior_engine = BehaviorAdjustmentEngine(self.session_manager, self.mistake_learner)
        self.metrics_dashboard = LearningMetricsDashboard(
            self.session_manager,
            self.mistake_learner,
            self.behavior_engine
        )
        self.preference_learner = UserPreferenceLearner(self.session_manager)

    def execute(self, args: List[str]) -> Dict[str, Any]:
        """Execute learn command.

        Args:
            args: Command arguments

        Returns:
            Command result
        """
        if not args:
            return self._show_dashboard()

        subcommand = args[0].lower()

        if subcommand == 'stats':
            return self._show_stats(args[1:])
        elif subcommand == 'mistakes':
            return self._show_mistakes(args[1:])
        elif subcommand == 'patterns':
            return self._show_patterns(args[1:])
        elif subcommand == 'behavior':
            return self._show_behavior(args[1:])
        elif subcommand == 'metrics':
            return self._show_metrics(args[1:])
        elif subcommand == 'preferences':
            return self._show_preferences(args[1:])
        elif subcommand == 'track':
            return self._track_mistake(args[1:])
        elif subcommand == 'feedback':
            return self._record_feedback(args[1:])
        elif subcommand == 'reset':
            return self._reset_learning(args[1:])
        elif subcommand == 'help':
            return self._show_help()
        else:
            return {
                'success': False,
                'output': f"Unknown subcommand: {subcommand}\n{self._get_help_text()}",
                'exit_code': 1
            }

    def _show_dashboard(self) -> Dict[str, Any]:
        """Show learning dashboard summary."""
        try:
            # Generate current metrics
            metrics = self.metrics_dashboard.generate_current_metrics(period_days=7)
            summary = self.metrics_dashboard.get_dashboard_summary()

            output = "🧠 Isaac Learning System Dashboard\n"
            output += "=" * 60 + "\n\n"

            # Health score with visual indicator
            health = summary['current_health_score']
            health_bar = self._get_health_bar(health)
            output += f"📊 Learning Health: {health:.1f}/100 {health_bar}\n"
            output += f"📈 Trend: {summary['health_trend'].upper()}\n\n"

            # Key metrics
            output += "Key Metrics:\n"
            output += f"  • Total Mistakes Tracked: {summary['total_mistakes']}\n"
            output += f"  • Learning Patterns: {summary['learning_patterns']}\n"
            output += f"  • Behavior Adjustments: {summary['behavior_adjustments']}\n"
            output += f"  • Learning Rate: {summary['learning_rate']:.1%}\n\n"

            # Active insights
            if summary['active_insights'] > 0:
                output += f"⚠️  {summary['active_insights']} Active Insights\n\n"

            # Recommendations
            if summary['recommendations']:
                output += "💡 Recommendations:\n"
                for i, rec in enumerate(summary['recommendations'][:3], 1):
                    output += f"  {i}. {rec}\n"
                output += "\n"

            output += f"Generated: {summary['generated_at']}\n\n"
            output += "💡 Use '/learn stats' for detailed statistics\n"
            output += "💡 Use '/learn help' for all available commands\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error generating dashboard: {e}",
                'exit_code': 1
            }

    def _get_health_bar(self, score: float) -> str:
        """Generate visual health bar."""
        filled = int(score / 10)
        empty = 10 - filled

        if score >= 80:
            bar_char = "🟢"
        elif score >= 60:
            bar_char = "🟡"
        elif score >= 40:
            bar_char = "🟠"
        else:
            bar_char = "🔴"

        return bar_char * filled + "⚪" * empty

    def _show_stats(self, args: List[str]) -> Dict[str, Any]:
        """Show detailed learning statistics."""
        try:
            # Get stats from all components
            mistake_stats = self.mistake_learner.get_learning_stats()
            behavior_analysis = self.behavior_engine.analyze_behavior_effectiveness()
            preference_stats = self.preference_learner.get_learning_stats()

            output = "📊 Detailed Learning Statistics\n"
            output += "=" * 60 + "\n\n"

            # Mistake Learning
            output += "🔴 Mistake Learning:\n"
            output += f"  Total Mistakes: {mistake_stats['total_mistakes']}\n"
            output += f"  Learned From: {mistake_stats['learned_mistakes']}\n"
            output += f"  Learning Patterns: {mistake_stats['learning_patterns']}\n"
            output += f"  Learning Rate: {mistake_stats['learning_rate']:.1%}\n"

            if mistake_stats['mistake_types']:
                output += "\n  Mistake Types:\n"
                for mtype, count in mistake_stats['mistake_types'].items():
                    output += f"    • {mtype}: {count}\n"

            # Behavior Adjustment
            output += "\n🎯 Behavior Adjustment:\n"
            if behavior_analysis.get('total_adjustments', 0) > 0:
                output += f"  Total Adjustments: {behavior_analysis['total_adjustments']}\n"
                output += f"  Most Adjusted: {behavior_analysis.get('most_adjusted_category', 'N/A')}\n"

                if 'category_effectiveness' in behavior_analysis:
                    output += "\n  By Category:\n"
                    for cat, data in behavior_analysis['category_effectiveness'].items():
                        output += f"    • {cat}: {data['total_adjustments']} adjustments "
                        output += f"(confidence: {data['avg_confidence']:.1%})\n"
            else:
                output += "  No adjustments yet\n"

            # User Preferences
            output += "\n👤 User Preferences:\n"
            if preference_stats.get('total_patterns', 0) > 0:
                output += f"  Total Patterns: {preference_stats['total_patterns']}\n"
                output += f"  High Confidence: {preference_stats['high_confidence_patterns']}\n"
                output += f"  Profile Age: {preference_stats['profile_age_days']:.1f} days\n"
                output += f"  Last Updated: {preference_stats['last_updated']}\n"

                if preference_stats.get('learning_categories'):
                    output += "\n  Learning Categories:\n"
                    for cat in preference_stats['learning_categories']:
                        output += f"    • {cat}\n"
            else:
                output += "  No preferences learned yet\n"

            output += "\n"
            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error generating statistics: {e}",
                'exit_code': 1
            }

    def _show_mistakes(self, args: List[str]) -> Dict[str, Any]:
        """Show recent mistakes."""
        try:
            limit = 10
            if args and args[0].isdigit():
                limit = int(args[0])

            # Get recent mistakes from different types
            mistake_types = ['command_error', 'ai_response', 'pattern_failure']
            all_mistakes = []

            for mtype in mistake_types:
                mistakes = self.mistake_learner.get_similar_mistakes(mtype, {}, limit=limit)
                all_mistakes.extend(mistakes)

            # Sort by timestamp
            all_mistakes.sort(key=lambda m: m.timestamp, reverse=True)
            all_mistakes = all_mistakes[:limit]

            output = f"🔍 Recent Mistakes (Last {limit})\n"
            output += "=" * 60 + "\n\n"

            if not all_mistakes:
                output += "No mistakes tracked yet.\n"
                output += "\n💡 Mistakes are automatically tracked as you use Isaac.\n"
            else:
                for i, mistake in enumerate(all_mistakes, 1):
                    timestamp = datetime.fromtimestamp(mistake.timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    learned_status = "✓ Learned" if mistake.learned else "○ Pending"

                    output += f"{i}. [{mistake.severity.upper()}] {learned_status}\n"
                    output += f"   Type: {mistake.mistake_type}\n"
                    output += f"   Time: {timestamp}\n"
                    output += f"   Issue: {mistake.mistake_description[:80]}...\n" if len(mistake.mistake_description) > 80 else f"   Issue: {mistake.mistake_description}\n"
                    output += f"   Correction: {mistake.user_correction[:60]}...\n\n" if len(mistake.user_correction) > 60 else f"   Correction: {mistake.user_correction}\n\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error retrieving mistakes: {e}",
                'exit_code': 1
            }

    def _show_patterns(self, args: List[str]) -> Dict[str, Any]:
        """Show learned patterns."""
        try:
            patterns = self.mistake_learner.learning_patterns

            output = "🧩 Learned Patterns\n"
            output += "=" * 60 + "\n\n"

            if not patterns:
                output += "No patterns learned yet.\n"
                output += "\n💡 Patterns develop automatically from repeated mistakes.\n"
                output += "💡 Use '/learn track' to manually record mistakes.\n"
            else:
                for i, (pattern_id, pattern) in enumerate(patterns.items(), 1):
                    confidence_bar = "█" * int(pattern.confidence * 10) + "░" * (10 - int(pattern.confidence * 10))

                    output += f"{i}. {pattern.pattern_description}\n"
                    output += f"   ID: {pattern_id}\n"
                    output += f"   Type: {pattern.mistake_type}\n"
                    output += f"   Confidence: {confidence_bar} {pattern.confidence:.1%}\n"
                    output += f"   Success: {pattern.success_count} | Failure: {pattern.failure_count}\n"
                    output += f"   Action: {pattern.correction_action[:70]}...\n\n" if len(pattern.correction_action) > 70 else f"   Action: {pattern.correction_action}\n\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error retrieving patterns: {e}",
                'exit_code': 1
            }

    def _show_behavior(self, args: List[str]) -> Dict[str, Any]:
        """Show behavior profile."""
        try:
            profile = self.behavior_engine.get_current_behavior_profile()
            adjustments = self.behavior_engine.get_behavior_adjustments(limit=5)

            output = "🎭 Behavior Profile\n"
            output += "=" * 60 + "\n\n"

            output += f"User ID: {profile.user_id}\n"
            output += f"Last Updated: {datetime.fromtimestamp(profile.last_updated).strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            output += "Current Preferences:\n"
            output += f"  • Response Style: {profile.response_style}\n"
            output += f"  • Suggestion Frequency: {profile.suggestion_frequency}\n"
            output += f"  • Detail Level: {profile.detail_level}\n"
            output += f"  • Humor Level: {profile.humor_level}\n"
            output += f"  • Technical Depth: {profile.technical_depth}\n"
            output += f"  • Interaction Pace: {profile.interaction_pace}\n\n"

            if profile.confidence_scores:
                output += "Confidence Scores:\n"
                for category, score in profile.confidence_scores.items():
                    conf_bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                    output += f"  • {category}: {conf_bar} {score:.1%}\n"
                output += "\n"

            if adjustments:
                output += "Recent Adjustments:\n"
                for i, adj in enumerate(adjustments[:5], 1):
                    timestamp = datetime.fromtimestamp(adj.applied_at).strftime('%Y-%m-%d %H:%M:%S') if adj.applied_at else 'Pending'
                    output += f"  {i}. [{adj.behavior_category}] {adj.current_value} → {adj.target_value}\n"
                    output += f"     Reason: {adj.reason[:60]}...\n" if len(adj.reason) > 60 else f"     Reason: {adj.reason}\n"
                    output += f"     Applied: {timestamp}\n\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error retrieving behavior profile: {e}",
                'exit_code': 1
            }

    def _show_metrics(self, args: List[str]) -> Dict[str, Any]:
        """Show detailed metrics."""
        try:
            period_days = 7
            if args and args[0].isdigit():
                period_days = int(args[0])

            metrics = self.metrics_dashboard.generate_current_metrics(period_days=period_days)
            insights = self.metrics_dashboard.get_learning_insights(limit=5)

            output = f"📈 Learning Metrics (Last {period_days} Days)\n"
            output += "=" * 60 + "\n\n"

            # Health Score
            health_bar = self._get_health_bar(metrics.learning_health_score)
            output += f"Learning Health Score: {metrics.learning_health_score:.1f}/100 {health_bar}\n\n"

            # Metrics breakdown
            output += "Metrics Breakdown:\n"
            output += f"  • Total Mistakes: {metrics.total_mistakes}\n"
            output += f"  • Learned Mistakes: {metrics.learned_mistakes}\n"
            output += f"  • Learning Patterns: {metrics.learning_patterns}\n"
            output += f"  • Learning Rate: {metrics.learning_rate:.1%}\n"
            output += f"  • Total Adjustments: {metrics.total_adjustments}\n\n"

            # Improvement trend
            if len(metrics.improvement_trend) > 1:
                output += "Improvement Trend:\n"
                trend_line = "  "
                for score in metrics.improvement_trend[-10:]:
                    if score >= 80:
                        trend_line += "🟢"
                    elif score >= 60:
                        trend_line += "🟡"
                    elif score >= 40:
                        trend_line += "🟠"
                    else:
                        trend_line += "🔴"
                output += trend_line + "\n\n"

            # Insights
            if insights:
                output += "Active Insights:\n"
                for i, insight in enumerate(insights[:3], 1):
                    priority_emoji = {"critical": "🚨", "high": "⚠️", "medium": "ℹ️", "low": "💡"}
                    emoji = priority_emoji.get(insight.priority, "ℹ️")
                    output += f"  {i}. {emoji} [{insight.priority.upper()}] {insight.title}\n"
                    output += f"     {insight.description[:70]}...\n" if len(insight.description) > 70 else f"     {insight.description}\n"
                output += "\n"

            # Recommendations
            if metrics.recommendations:
                output += "Recommendations:\n"
                for i, rec in enumerate(metrics.recommendations[:3], 1):
                    output += f"  {i}. {rec}\n"
                output += "\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error generating metrics: {e}",
                'exit_code': 1
            }

    def _show_preferences(self, args: List[str]) -> Dict[str, Any]:
        """Show user preferences."""
        try:
            prefs = self.preference_learner.user_preferences
            stats = self.preference_learner.get_learning_stats()

            output = "👤 User Preferences\n"
            output += "=" * 60 + "\n\n"

            if not prefs:
                output += "No preferences learned yet.\n"
            else:
                output += f"Profile Age: {stats['profile_age_days']:.1f} days\n"
                output += f"Total Patterns: {stats['total_patterns']}\n"
                output += f"High Confidence: {stats['high_confidence_patterns']}\n\n"

                # Show top preferences by category
                categories = ['naming_conventions', 'code_structure', 'command_patterns',
                            'communication_style', 'workflow_patterns']

                for category in categories:
                    top_prefs = prefs.get_top_preferences(category, limit=3)
                    if top_prefs:
                        output += f"{category.replace('_', ' ').title()}:\n"
                        for key, pattern in top_prefs:
                            if pattern.confidence > 0.5:
                                conf_bar = "█" * int(pattern.confidence * 10) + "░" * (10 - int(pattern.confidence * 10))
                                output += f"  • {pattern.pattern_key}: {conf_bar} {pattern.confidence:.1%}\n"
                                output += f"    Value: {str(pattern.preference_value)[:60]}...\n" if len(str(pattern.preference_value)) > 60 else f"    Value: {pattern.preference_value}\n"
                        output += "\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error retrieving preferences: {e}",
                'exit_code': 1
            }

    def _track_mistake(self, args: List[str]) -> Dict[str, Any]:
        """Manually track a mistake."""
        try:
            if len(args) < 3:
                return {
                    'success': False,
                    'output': "Usage: /learn track <type> <description> <correction>",
                    'exit_code': 1
                }

            mistake_type = args[0]
            description = args[1]
            correction = ' '.join(args[2:])

            # Create mistake record
            mistake = MistakeRecord(
                id=f"manual_{int(time.time())}",
                timestamp=time.time(),
                mistake_type=mistake_type,
                original_input="manual_entry",
                mistake_description=description,
                user_correction=correction,
                context={'manual': True},
                severity='medium'
            )

            # Record it
            self.mistake_learner.record_mistake(mistake)

            output = "✓ Mistake tracked successfully\n\n"
            output += f"Type: {mistake_type}\n"
            output += f"Description: {description}\n"
            output += f"Correction: {correction}\n\n"
            output += "💡 This will contribute to pattern learning.\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error tracking mistake: {e}",
                'exit_code': 1
            }

    def _record_feedback(self, args: List[str]) -> Dict[str, Any]:
        """Record user feedback."""
        try:
            if len(args) < 2:
                return {
                    'success': False,
                    'output': "Usage: /learn feedback <category> <feedback_text>",
                    'exit_code': 1
                }

            category = args[0]
            feedback_text = ' '.join(args[1:])

            # Determine sentiment (simple heuristic)
            positive_words = ['good', 'great', 'excellent', 'perfect', 'love', 'like']
            negative_words = ['bad', 'poor', 'wrong', 'hate', 'dislike', 'terrible']

            feedback_lower = feedback_text.lower()
            sentiment = 0.0

            for word in positive_words:
                if word in feedback_lower:
                    sentiment += 0.3
            for word in negative_words:
                if word in feedback_lower:
                    sentiment -= 0.3

            sentiment = max(-1.0, min(1.0, sentiment))

            # Create feedback record
            feedback = UserFeedback(
                id=f"feedback_{int(time.time())}",
                timestamp=time.time(),
                feedback_type='correction' if sentiment < 0 else 'positive',
                context="manual_feedback",
                user_response=feedback_text,
                sentiment_score=sentiment,
                behavior_category=category
            )

            # Record it
            self.behavior_engine.record_feedback(feedback)

            output = "✓ Feedback recorded successfully\n\n"
            output += f"Category: {category}\n"
            output += f"Sentiment: {sentiment:.2f}\n"
            output += f"Feedback: {feedback_text}\n\n"
            output += "💡 This will help adjust Isaac's behavior.\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error recording feedback: {e}",
                'exit_code': 1
            }

    def _reset_learning(self, args: List[str]) -> Dict[str, Any]:
        """Reset learning data (with confirmation)."""
        try:
            if not args or args[0].lower() != 'confirm':
                return {
                    'success': False,
                    'output': "⚠️  WARNING: This will reset ALL learning data!\n\n"
                            "To confirm, run: /learn reset confirm",
                    'exit_code': 1
                }

            # Stop background learning
            self.mistake_learner.stop_learning()

            # Delete data directories
            isaac_dir = Path.home() / '.isaac'
            directories = ['learning', 'behavior', 'learning_metrics']

            for dirname in directories:
                dir_path = isaac_dir / dirname
                if dir_path.exists():
                    import shutil
                    shutil.rmtree(dir_path)

            output = "✓ Learning data reset successfully\n\n"
            output += "The following data has been cleared:\n"
            output += "  • Mistake learning database\n"
            output += "  • Learning patterns\n"
            output += "  • Behavior adjustments\n"
            output += "  • Behavior profile\n"
            output += "  • Learning metrics\n"
            output += "  • User preferences\n\n"
            output += "💡 Learning will restart from scratch on next use.\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error resetting learning data: {e}",
                'exit_code': 1
            }

    def _show_help(self) -> Dict[str, Any]:
        """Show help information."""
        return {
            'success': True,
            'output': self._get_help_text(),
            'exit_code': 0
        }

    def _get_help_text(self) -> str:
        """Get help text."""
        return """🧠 Isaac Self-Improving Learning System

USAGE:
  /learn [subcommand] [options]

SUBCOMMANDS:
  (no args)            Show learning dashboard summary
  stats                Show detailed learning statistics
  mistakes [limit]     Show recent mistakes (default: 10)
  patterns             Show learned patterns
  behavior             Show behavior profile and adjustments
  metrics [days]       Show detailed metrics (default: 7 days)
  preferences          Show user preferences and patterns
  track <type> <desc> <correction>  Manually track a mistake
  feedback <category> <text>         Record user feedback
  reset confirm        Reset all learning data (requires confirmation)
  help                 Show this help message

EXAMPLES:
  /learn                              # Show dashboard
  /learn stats                        # Show all statistics
  /learn mistakes 20                  # Show last 20 mistakes
  /learn patterns                     # Show learned patterns
  /learn behavior                     # Show behavior profile
  /learn metrics 30                   # Show metrics for last 30 days
  /learn track command_error "git psuh" "git push"
  /learn feedback response_style "too verbose, prefer concise"
  /learn reset confirm                # Reset all learning data

LEARNING COMPONENTS:
  • Mistake Learning: Tracks and learns from errors
  • Behavior Adjustment: Adapts to user preferences
  • Learning Metrics: Monitors learning effectiveness
  • User Preferences: Learns coding style and patterns

The learning system continuously improves Isaac's assistance based on your interactions."""

    def cleanup(self):
        """Cleanup resources."""
        if hasattr(self, 'mistake_learner'):
            self.mistake_learner.stop_learning()
