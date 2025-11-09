"""
Productivity Tracker

Tracks efficiency gains, time saved, and productivity metrics.
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from isaac.analytics.database import AnalyticsDatabase


@dataclass
class ProductivitySnapshot:
    """A snapshot of productivity metrics"""
    timestamp: str
    commands_executed: int
    time_saved: float  # in seconds
    automation_runs: int
    patterns_applied: int
    errors_prevented: int
    suggestions_accepted: int
    efficiency_score: float


class ProductivityTracker:
    """Tracks productivity metrics and efficiency gains"""

    def __init__(self, db: Optional[AnalyticsDatabase] = None):
        """Initialize productivity tracker"""
        self.db = db or AnalyticsDatabase()
        self.session_start = time.time()
        self.session_id = datetime.now().isoformat()

        # Real-time counters
        self.commands_executed = 0
        self.time_saved = 0.0
        self.automation_runs = 0
        self.patterns_applied = 0
        self.errors_prevented = 0
        self.suggestions_accepted = 0

        # Baseline metrics for comparison
        self.baseline_metrics = self._load_baseline_metrics()

    def _load_baseline_metrics(self) -> Dict[str, float]:
        """Load baseline metrics for comparison"""
        # Get historical averages to establish baseline
        try:
            stats = self.db.get_aggregate_stats(
                'productivity_metrics',
                'metric_value',
                start_date=(datetime.now() - timedelta(days=30)).isoformat()
            )
            return {
                'avg_commands_per_session': stats.get('avg', 10.0),
                'avg_time_saved': stats.get('avg', 0.0),
                'avg_efficiency': stats.get('avg', 50.0)
            }
        except Exception:
            return {
                'avg_commands_per_session': 10.0,
                'avg_time_saved': 0.0,
                'avg_efficiency': 50.0
            }

    def record_command_execution(
        self,
        command_name: str,
        execution_time: float,
        estimated_manual_time: Optional[float] = None
    ):
        """Record command execution and calculate time saved"""
        self.commands_executed += 1

        # Estimate time saved if manual time is provided
        if estimated_manual_time:
            time_saved = max(0, estimated_manual_time - execution_time)
            self.time_saved += time_saved

            self.db.record_productivity_metric(
                metric_type='time_saved',
                metric_name=command_name,
                metric_value=time_saved,
                session_id=self.session_id,
                metadata=json.dumps({
                    'execution_time': execution_time,
                    'manual_time': estimated_manual_time
                })
            )

        # Record command execution
        self.db.record_productivity_metric(
            metric_type='command_execution',
            metric_name=command_name,
            metric_value=1,
            session_id=self.session_id,
            metadata=json.dumps({'execution_time': execution_time})
        )

    def record_automation_run(
        self,
        automation_name: str,
        steps_automated: int,
        time_saved: float
    ):
        """Record automated task execution"""
        self.automation_runs += 1
        self.time_saved += time_saved

        self.db.record_productivity_metric(
            metric_type='automation',
            metric_name=automation_name,
            metric_value=time_saved,
            session_id=self.session_id,
            metadata=json.dumps({'steps_automated': steps_automated})
        )

    def record_pattern_application(
        self,
        pattern_name: str,
        lines_of_code_saved: int
    ):
        """Record pattern application for code reuse"""
        self.patterns_applied += 1

        # Estimate time saved (assume 1 minute per 10 lines of code)
        time_saved = (lines_of_code_saved / 10.0) * 60

        self.db.record_productivity_metric(
            metric_type='pattern_application',
            metric_name=pattern_name,
            metric_value=time_saved,
            session_id=self.session_id,
            metadata=json.dumps({'lines_saved': lines_of_code_saved})
        )

    def record_error_prevention(
        self,
        error_type: str,
        time_saved: float
    ):
        """Record error that was prevented"""
        self.errors_prevented += 1
        self.time_saved += time_saved

        self.db.record_productivity_metric(
            metric_type='error_prevention',
            metric_name=error_type,
            metric_value=time_saved,
            session_id=self.session_id
        )

    def record_suggestion_accepted(
        self,
        suggestion_type: str,
        time_saved: float
    ):
        """Record accepted suggestion"""
        self.suggestions_accepted += 1
        self.time_saved += time_saved

        self.db.record_productivity_metric(
            metric_type='suggestion',
            metric_name=suggestion_type,
            metric_value=time_saved,
            session_id=self.session_id
        )

    def calculate_efficiency_score(self) -> float:
        """Calculate current efficiency score (0-100)"""
        session_duration = time.time() - self.session_start
        if session_duration < 60:  # Less than 1 minute
            return 50.0  # Neutral score for new sessions

        # Factors contributing to efficiency
        command_factor = min(
            100,
            (self.commands_executed / (session_duration / 60)) * 10
        )
        time_saved_factor = min(100, (self.time_saved / session_duration) * 100)
        automation_factor = min(100, self.automation_runs * 10)
        pattern_factor = min(100, self.patterns_applied * 5)
        error_prevention_factor = min(100, self.errors_prevented * 10)

        # Weighted average
        efficiency = (
            command_factor * 0.2 +
            time_saved_factor * 0.3 +
            automation_factor * 0.2 +
            pattern_factor * 0.15 +
            error_prevention_factor * 0.15
        )

        return min(100.0, max(0.0, efficiency))

    def get_current_snapshot(self) -> ProductivitySnapshot:
        """Get current productivity snapshot"""
        return ProductivitySnapshot(
            timestamp=datetime.now().isoformat(),
            commands_executed=self.commands_executed,
            time_saved=self.time_saved,
            automation_runs=self.automation_runs,
            patterns_applied=self.patterns_applied,
            errors_prevented=self.errors_prevented,
            suggestions_accepted=self.suggestions_accepted,
            efficiency_score=self.calculate_efficiency_score()
        )

    def get_productivity_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate productivity report"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).isoformat()
        if not end_date:
            end_date = datetime.now().isoformat()

        # Get metrics from database
        metrics = self.db.query_metrics(
            'productivity_metrics',
            start_date=start_date,
            end_date=end_date
        )

        # Aggregate by type
        aggregated = {}
        for metric in metrics:
            metric_type = metric['metric_type']
            if metric_type not in aggregated:
                aggregated[metric_type] = {
                    'count': 0,
                    'total_value': 0.0,
                    'items': []
                }
            aggregated[metric_type]['count'] += 1
            aggregated[metric_type]['total_value'] += metric['metric_value']
            aggregated[metric_type]['items'].append(metric)

        # Calculate totals
        total_time_saved = sum(
            m['metric_value'] for m in metrics
            if m['metric_type'] in ['time_saved', 'automation', 'error_prevention', 'suggestion']
        )

        total_commands = aggregated.get('command_execution', {}).get('count', 0)
        total_automations = aggregated.get('automation', {}).get('count', 0)
        total_patterns = aggregated.get('pattern_application', {}).get('count', 0)
        total_errors_prevented = aggregated.get('error_prevention', {}).get('count', 0)

        # Calculate productivity gain
        days_elapsed = (
            datetime.fromisoformat(end_date) -
            datetime.fromisoformat(start_date)
        ).days or 1

        hours_saved = total_time_saved / 3600
        productivity_gain = (
            hours_saved / (days_elapsed * 8)
        ) * 100  # Percentage of 8-hour workday

        return {
            'period': {
                'start': start_date,
                'end': end_date,
                'days': days_elapsed
            },
            'summary': {
                'total_commands_executed': total_commands,
                'total_time_saved_seconds': total_time_saved,
                'total_time_saved_hours': hours_saved,
                'total_automations': total_automations,
                'total_patterns_applied': total_patterns,
                'total_errors_prevented': total_errors_prevented,
                'productivity_gain_percentage': productivity_gain
            },
            'current_session': asdict(self.get_current_snapshot()),
            'breakdown': aggregated,
            'insights': self._generate_insights(aggregated, total_time_saved)
        }

    def _generate_insights(
        self,
        aggregated: Dict[str, Any],
        total_time_saved: float
    ) -> List[str]:
        """Generate insights from productivity data"""
        insights = []

        # Time saved insights
        hours_saved = total_time_saved / 3600
        if hours_saved >= 1:
            insights.append(
                f"💡 You've saved {hours_saved:.1f} hours through automation and intelligent assistance"
            )

        # Automation insights
        automation_count = aggregated.get('automation', {}).get('count', 0)
        if automation_count > 10:
            insights.append(
                f"🤖 Automation is working well! {automation_count} automated tasks executed"
            )

        # Pattern insights
        pattern_count = aggregated.get('pattern_application', {}).get('count', 0)
        if pattern_count > 5:
            insights.append(
                f"📐 Code patterns are accelerating development: {pattern_count} patterns applied"
            )

        # Error prevention insights
        error_count = aggregated.get('error_prevention', {}).get('count', 0)
        if error_count > 0:
            insights.append(
                f"🛡️  Prevented {error_count} potential errors before they occurred"
            )

        # Efficiency insights
        if not insights:
            insights.append(
                "📊 Continue using Isaac to build up productivity metrics"
            )

        return insights

    def get_efficiency_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get efficiency trend over time"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        metrics = self.db.query_metrics(
            'productivity_metrics',
            start_date=start_date
        )

        # Group by day
        daily_metrics = {}
        for metric in metrics:
            date = metric['timestamp'][:10]  # Get just the date part
            if date not in daily_metrics:
                daily_metrics[date] = {
                    'commands': 0,
                    'time_saved': 0.0,
                    'automations': 0,
                    'patterns': 0
                }

            if metric['metric_type'] == 'command_execution':
                daily_metrics[date]['commands'] += 1
            elif metric['metric_type'] in ['time_saved', 'automation', 'error_prevention']:
                daily_metrics[date]['time_saved'] += metric['metric_value']
            elif metric['metric_type'] == 'automation':
                daily_metrics[date]['automations'] += 1
            elif metric['metric_type'] == 'pattern_application':
                daily_metrics[date]['patterns'] += 1

        # Convert to list and calculate efficiency scores
        trend = []
        for date, metrics in sorted(daily_metrics.items()):
            efficiency = min(100, (
                metrics['commands'] * 5 +
                (metrics['time_saved'] / 60) * 10 +
                metrics['automations'] * 10 +
                metrics['patterns'] * 5
            ))
            trend.append({
                'date': date,
                'efficiency': efficiency,
                **metrics
            })

        return trend
