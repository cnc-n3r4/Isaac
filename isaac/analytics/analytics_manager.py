"""
Analytics Manager

Central manager coordinating all analytics components.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from isaac.analytics.database import AnalyticsDatabase
from isaac.analytics.productivity_tracker import ProductivityTracker
from isaac.analytics.code_quality_tracker import CodeQualityTracker
from isaac.analytics.learning_tracker import LearningTracker
from isaac.analytics.team_tracker import TeamTracker
from isaac.analytics.dashboard_builder import DashboardBuilder
from isaac.analytics.report_exporter import ReportExporter


class AnalyticsManager:
    """Central manager for all analytics functionality"""

    def __init__(
        self,
        team_id: str = "default",
        db_path: Optional[str] = None
    ):
        """Initialize analytics manager"""
        self.db = AnalyticsDatabase(db_path)

        # Initialize all trackers
        self.productivity = ProductivityTracker(self.db)
        self.code_quality = CodeQualityTracker(self.db)
        self.learning = LearningTracker(self.db)
        self.team = TeamTracker(team_id, self.db)

        # Initialize tools
        self.dashboard = DashboardBuilder(self.db)
        self.exporter = ReportExporter(self.db)

        self.enabled = True

    def record_command_execution(
        self,
        command_name: str,
        execution_time: float,
        success: bool,
        error_message: Optional[str] = None,
        estimated_manual_time: Optional[float] = None
    ):
        """Record command execution with analytics"""
        if not self.enabled:
            return

        # Record in database
        self.db.record_command_execution(
            command_name=command_name,
            execution_time=execution_time,
            success=success,
            error_message=error_message
        )

        # Update productivity tracker
        self.productivity.record_command_execution(
            command_name=command_name,
            execution_time=execution_time,
            estimated_manual_time=estimated_manual_time
        )

    def record_code_change(
        self,
        file_path: str,
        change_type: str = 'edit'
    ):
        """Record code change and analyze quality"""
        if not self.enabled:
            return

        # Analyze file quality
        analysis = self.code_quality.analyze_file(file_path)

        # Record any patterns or anti-patterns detected
        # This would integrate with pattern detection systems

    def record_pattern_learned(
        self,
        pattern_name: str,
        pattern_type: str,
        confidence: float
    ):
        """Record newly learned pattern"""
        if not self.enabled:
            return

        self.learning.record_pattern_learned(
            pattern_name=pattern_name,
            pattern_type=pattern_type,
            confidence=confidence
        )

    def record_user_preference(
        self,
        preference_name: str,
        preference_value: Any,
        confidence: float
    ):
        """Record learned user preference"""
        if not self.enabled:
            return

        self.learning.record_preference_adaptation(
            preference_name=preference_name,
            preference_value=preference_value,
            confidence=confidence
        )

    def record_team_contribution(
        self,
        user_id: str,
        contribution_type: str,
        contribution_value: float = 1.0
    ):
        """Record team member contribution"""
        if not self.enabled:
            return

        self.team.record_contribution(
            user_id=user_id,
            contribution_type=contribution_type,
            contribution_value=contribution_value
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all analytics"""
        productivity_snapshot = self.productivity.get_current_snapshot()
        quality_snapshot = self.code_quality.get_current_snapshot()
        learning_snapshot = self.learning.get_current_snapshot()
        team_snapshot = self.team.get_current_snapshot()

        return {
            'timestamp': datetime.now().isoformat(),
            'productivity': {
                'efficiency_score': productivity_snapshot.efficiency_score,
                'time_saved_hours': productivity_snapshot.time_saved / 3600,
                'commands_executed': productivity_snapshot.commands_executed,
                'automations_run': productivity_snapshot.automation_runs
            },
            'code_quality': {
                'quality_score': quality_snapshot.quality_score,
                'files_analyzed': quality_snapshot.files_analyzed,
                'patterns_detected': quality_snapshot.patterns_detected,
                'anti_patterns_detected': quality_snapshot.anti_patterns_detected
            },
            'learning': {
                'learning_rate': learning_snapshot.learning_rate,
                'adaptation_score': learning_snapshot.adaptation_score,
                'patterns_learned': learning_snapshot.patterns_learned,
                'preferences_adapted': learning_snapshot.preferences_adapted
            },
            'team': {
                'active_members': team_snapshot.active_members,
                'collaboration_score': team_snapshot.collaboration_score,
                'contributions': team_snapshot.total_contributions
            }
        }

    def get_dashboard(self, dashboard_id: str = 'overview', width: int = 80) -> str:
        """Render a dashboard"""
        return self.dashboard.render_dashboard(dashboard_id, width)

    def export_report(
        self,
        report_type: str,
        format: str = 'markdown',
        output_path: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """Export a report"""
        return self.exporter.export_report(
            report_type=report_type,
            format=format,
            output_path=output_path,
            start_date=start_date,
            end_date=end_date
        )

    def list_dashboards(self) -> List[str]:
        """List available dashboards"""
        return self.dashboard.list_dashboards()

    def enable(self):
        """Enable analytics tracking"""
        self.enabled = True

    def disable(self):
        """Disable analytics tracking"""
        self.enabled = False

    def clear_old_data(self, days: int = 90):
        """Clear analytics data older than specified days"""
        self.db.clear_old_data(days)

    def get_insights(self) -> List[str]:
        """Get combined insights from all trackers"""
        insights = []

        # Get productivity insights
        prod_report = self.productivity.get_productivity_report()
        insights.extend(prod_report.get('insights', []))

        # Get quality insights
        quality_report = self.code_quality.get_quality_report()
        insights.extend(quality_report.get('insights', []))

        # Get learning insights
        learning_report = self.learning.get_learning_report()
        insights.extend(learning_report.get('insights', []))

        # Get team insights
        team_report = self.team.get_team_report()
        insights.extend(team_report.get('insights', []))

        return insights[:10]  # Return top 10 insights
