"""
Analytics Command

Comprehensive analytics interface for Isaac.
"""

import os
from datetime import datetime, timedelta

from isaac.analytics.analytics_manager import AnalyticsManager


class AnalyticsCommand:
    """Analytics command implementation"""

    def __init__(self):
        """Initialize analytics command"""
        self.manager = AnalyticsManager()

    def execute(self, args: list) -> str:
        """Execute analytics command"""
        if not args or args[0] in ['help', '--help', '-h']:
            return self._help()

        subcommand = args[0]

        if subcommand == 'summary':
            return self._summary()
        elif subcommand == 'dashboard':
            dashboard_id = args[1] if len(args) > 1 else 'overview'
            return self._dashboard(dashboard_id)
        elif subcommand == 'productivity':
            return self._productivity_report(args[1:])
        elif subcommand == 'quality':
            return self._quality_report(args[1:])
        elif subcommand == 'learning':
            return self._learning_report(args[1:])
        elif subcommand == 'team':
            return self._team_report(args[1:])
        elif subcommand == 'export':
            return self._export(args[1:])
        elif subcommand == 'insights':
            return self._insights()
        elif subcommand == 'dashboards':
            return self._list_dashboards()
        elif subcommand == 'enable':
            return self._enable()
        elif subcommand == 'disable':
            return self._disable()
        elif subcommand == 'clear':
            days = int(args[1]) if len(args) > 1 else 90
            return self._clear_old_data(days)
        elif subcommand == 'analyze':
            if len(args) < 2:
                return "❌ Usage: /analytics analyze <file_path>"
            return self._analyze_file(args[1])
        else:
            return f"❌ Unknown subcommand: {subcommand}\n\nUse '/analytics help' for usage information"

    def _help(self) -> str:
        """Show help message"""
        return """
📊 Analytics Command - Comprehensive Analytics System

USAGE:
  /analytics <subcommand> [options]

SUBCOMMANDS:

  Basic:
    summary              Show summary of all analytics
    insights             Show top insights from analytics
    dashboards           List available dashboards

  Reports:
    productivity [days]  Show productivity report (default: 7 days)
    quality [days]       Show code quality report (default: 7 days)
    learning [days]      Show learning analytics report (default: 30 days)
    team [days]          Show team analytics report (default: 7 days)

  Dashboards:
    dashboard [id]       Display interactive dashboard
                         Available: overview, productivity, quality, learning, team

  Export:
    export <type> <format> [output_path]
                         Export report in specified format
                         Types: productivity, quality, learning, team, full
                         Formats: json, csv, html, markdown

  Analysis:
    analyze <file>       Analyze a file for code quality metrics

  Management:
    enable               Enable analytics tracking
    disable              Disable analytics tracking
    clear [days]         Clear data older than N days (default: 90)

EXAMPLES:

  # Show summary
  /analytics summary

  # View overview dashboard
  /analytics dashboard overview

  # Get productivity report for last 14 days
  /analytics productivity 14

  # Export full report as HTML
  /analytics export full html ~/reports/analytics.html

  # Get insights
  /analytics insights

  # Analyze a file
  /analytics analyze src/main.py

For more information, see the Analytics documentation.
"""

    def _summary(self) -> str:
        """Show analytics summary"""
        summary = self.manager.get_summary()

        output = []
        output.append("=" * 80)
        output.append("📊 ANALYTICS SUMMARY".center(80))
        output.append("=" * 80)
        output.append("")

        # Productivity
        prod = summary['productivity']
        output.append("⚡ PRODUCTIVITY")
        output.append(f"  Efficiency Score:    {prod['efficiency_score']:.1f}%")
        output.append(f"  Time Saved:          {prod['time_saved_hours']:.2f} hours")
        output.append(f"  Commands Executed:   {prod['commands_executed']}")
        output.append(f"  Automations Run:     {prod['automations_run']}")
        output.append("")

        # Code Quality
        quality = summary['code_quality']
        output.append("✨ CODE QUALITY")
        output.append(f"  Quality Score:       {quality['quality_score']:.1f}%")
        output.append(f"  Files Analyzed:      {quality['files_analyzed']}")
        output.append(f"  Patterns Detected:   {quality['patterns_detected']}")
        output.append(f"  Anti-Patterns:       {quality['anti_patterns_detected']}")
        output.append("")

        # Learning
        learning = summary['learning']
        output.append("🧠 LEARNING")
        output.append(f"  Learning Rate:       {learning['learning_rate']:.1f}%")
        output.append(f"  Adaptation Score:    {learning['adaptation_score']:.1f}%")
        output.append(f"  Patterns Learned:    {learning['patterns_learned']}")
        output.append(f"  Preferences Adapted: {learning['preferences_adapted']}")
        output.append("")

        # Team
        team = summary['team']
        output.append("👥 TEAM")
        output.append(f"  Active Members:      {team['active_members']}")
        output.append(f"  Collaboration Score: {team['collaboration_score']:.1f}%")
        output.append(f"  Contributions:       {team['contributions']}")
        output.append("")

        output.append("=" * 80)
        output.append(f" Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(80))
        output.append("=" * 80)

        return "\n".join(output)

    def _dashboard(self, dashboard_id: str) -> str:
        """Display dashboard"""
        try:
            return self.manager.get_dashboard(dashboard_id)
        except Exception as e:
            return f"❌ Error displaying dashboard: {str(e)}"

    def _productivity_report(self, args: list) -> str:
        """Show productivity report"""
        days = int(args[0]) if args else 7
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        report = self.manager.productivity.get_productivity_report(
            start_date=start_date
        )

        output = []
        output.append("=" * 80)
        output.append(f"⚡ PRODUCTIVITY REPORT (Last {days} days)".center(80))
        output.append("=" * 80)
        output.append("")

        summary = report['summary']
        output.append("📈 Summary:")
        output.append(f"  Commands Executed:      {summary['total_commands_executed']}")
        output.append(f"  Time Saved:             {summary['total_time_saved_hours']:.2f} hours")
        output.append(f"  Automations:            {summary['total_automations']}")
        output.append(f"  Patterns Applied:       {summary['total_patterns_applied']}")
        output.append(f"  Errors Prevented:       {summary['total_errors_prevented']}")
        output.append(f"  Productivity Gain:      {summary['productivity_gain_percentage']:.1f}%")
        output.append("")

        if report['insights']:
            output.append("💡 Insights:")
            for insight in report['insights']:
                output.append(f"  {insight}")
            output.append("")

        output.append("=" * 80)

        return "\n".join(output)

    def _quality_report(self, args: list) -> str:
        """Show code quality report"""
        days = int(args[0]) if args else 7
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        report = self.manager.code_quality.get_quality_report(
            start_date=start_date
        )

        output = []
        output.append("=" * 80)
        output.append(f"✨ CODE QUALITY REPORT (Last {days} days)".center(80))
        output.append("=" * 80)
        output.append("")

        summary = report['summary']
        output.append("📊 Summary:")
        output.append(f"  Files Analyzed:         {summary['files_analyzed']}")
        output.append(f"  Average Quality Score:  {summary['average_quality_score']:.1f}%")
        output.append(f"  Patterns Detected:      {summary['total_patterns_detected']}")
        output.append(f"  Anti-Patterns Found:    {summary['total_anti_patterns_detected']}")
        output.append(f"  Quality Improvement:    {summary['total_improvement']:.1f} points")
        output.append(f"  Trend:                  {summary['quality_trend'].upper()}")
        output.append("")

        if report['insights']:
            output.append("💡 Insights:")
            for insight in report['insights']:
                output.append(f"  {insight}")
            output.append("")

        output.append("=" * 80)

        return "\n".join(output)

    def _learning_report(self, args: list) -> str:
        """Show learning analytics report"""
        days = int(args[0]) if args else 30
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        report = self.manager.learning.get_learning_report(
            start_date=start_date
        )

        output = []
        output.append("=" * 80)
        output.append(f"🧠 LEARNING ANALYTICS REPORT (Last {days} days)".center(80))
        output.append("=" * 80)
        output.append("")

        summary = report['summary']
        output.append("📚 Summary:")
        output.append(f"  Patterns Learned:       {summary['total_patterns_learned']}")
        output.append(f"  Preferences Adapted:    {summary['total_preferences_adapted']}")
        output.append(f"  Mistakes Learned From:  {summary['total_mistakes_learned_from']}")
        output.append(f"  Behavior Adjustments:   {summary['total_behavior_adjustments']}")
        output.append(f"  Skill Improvements:     {summary['total_skill_improvements']}")
        output.append(f"  Learning Rate:          {summary['learning_rate']:.1f}%")
        output.append(f"  Adaptation Score:       {summary['adaptation_score']:.1f}%")
        output.append("")

        if report['insights']:
            output.append("💡 Insights:")
            for insight in report['insights']:
                output.append(f"  {insight}")
            output.append("")

        if report['top_learnings']:
            output.append("🏆 Top Learnings:")
            for learning in report['top_learnings'][:5]:
                output.append(f"  • {learning['type']}: {learning['item']} (confidence: {learning['confidence']:.1f})")
            output.append("")

        output.append("=" * 80)

        return "\n".join(output)

    def _team_report(self, args: list) -> str:
        """Show team analytics report"""
        days = int(args[0]) if args else 7
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        report = self.manager.team.get_team_report(
            start_date=start_date
        )

        output = []
        output.append("=" * 80)
        output.append(f"👥 TEAM ANALYTICS REPORT (Last {days} days)".center(80))
        output.append("=" * 80)
        output.append("")

        summary = report['summary']
        output.append("📊 Summary:")
        output.append(f"  Active Members:         {summary['active_members']}")
        output.append(f"  Total Contributions:    {summary['total_contributions']}")
        output.append(f"  Collaborations:         {summary['total_collaborations']}")
        output.append(f"  Code Reviews:           {summary['total_code_reviews']}")
        output.append(f"  Patterns Shared:        {summary['total_patterns_shared']}")
        output.append(f"  Knowledge Shared:       {summary['total_knowledge_shared']}")
        output.append(f"  Collaboration Score:    {summary['collaboration_score']:.1f}%")
        output.append("")

        if report['insights']:
            output.append("💡 Insights:")
            for insight in report['insights']:
                output.append(f"  {insight}")
            output.append("")

        if report['top_contributors']:
            output.append("🏆 Top Contributors:")
            for i, contributor in enumerate(report['top_contributors'][:5], 1):
                output.append(f"  {i}. {contributor['user_id']} (score: {contributor['score']:.1f})")
            output.append("")

        output.append("=" * 80)

        return "\n".join(output)

    def _export(self, args: list) -> str:
        """Export report"""
        if len(args) < 2:
            return "❌ Usage: /analytics export <type> <format> [output_path]\n\n" \
                   "Types: productivity, quality, learning, team, full\n" \
                   "Formats: json, csv, html, markdown"

        report_type = args[0]
        format = args[1]
        output_path = args[2] if len(args) > 2 else None

        try:
            result = self.manager.export_report(
                report_type=report_type,
                format=format,
                output_path=output_path
            )

            if output_path:
                return f"✅ Report exported to: {result}"
            else:
                return result
        except Exception as e:
            return f"❌ Error exporting report: {str(e)}"

    def _insights(self) -> str:
        """Show insights"""
        insights = self.manager.get_insights()

        output = []
        output.append("=" * 80)
        output.append("💡 TOP INSIGHTS".center(80))
        output.append("=" * 80)
        output.append("")

        if insights:
            for insight in insights:
                output.append(f"  {insight}")
                output.append("")
        else:
            output.append("  No insights available yet.")
            output.append("  Continue using Isaac to build up analytics data.")
            output.append("")

        output.append("=" * 80)

        return "\n".join(output)

    def _list_dashboards(self) -> str:
        """List available dashboards"""
        dashboards = self.manager.list_dashboards()

        output = []
        output.append("=" * 80)
        output.append("📊 AVAILABLE DASHBOARDS".center(80))
        output.append("=" * 80)
        output.append("")

        for dashboard_id in dashboards:
            output.append(f"  • {dashboard_id}")

        output.append("")
        output.append("Usage: /analytics dashboard <id>")
        output.append("=" * 80)

        return "\n".join(output)

    def _enable(self) -> str:
        """Enable analytics"""
        self.manager.enable()
        return "✅ Analytics tracking enabled"

    def _disable(self) -> str:
        """Disable analytics"""
        self.manager.disable()
        return "⚠️  Analytics tracking disabled"

    def _clear_old_data(self, days: int) -> str:
        """Clear old analytics data"""
        try:
            self.manager.clear_old_data(days)
            return f"✅ Cleared analytics data older than {days} days"
        except Exception as e:
            return f"❌ Error clearing data: {str(e)}"

    def _analyze_file(self, file_path: str) -> str:
        """Analyze a file for code quality"""
        if not os.path.exists(file_path):
            return f"❌ File not found: {file_path}"

        try:
            analysis = self.manager.code_quality.analyze_file(file_path)

            if 'error' in analysis:
                return f"❌ Error analyzing file: {analysis['error']}"

            output = []
            output.append("=" * 80)
            output.append(f"📊 FILE ANALYSIS: {os.path.basename(file_path)}".center(80))
            output.append("=" * 80)
            output.append("")
            output.append(f"File: {file_path}")
            output.append("")

            if 'quality_score' in analysis:
                output.append(f"Quality Score:        {analysis['quality_score']:.1f}%")

            if 'lines' in analysis:
                output.append(f"Lines of Code:        {analysis['lines']}")

            if 'functions' in analysis:
                output.append(f"Functions:            {analysis['functions']}")

            if 'classes' in analysis:
                output.append(f"Classes:              {analysis['classes']}")

            if 'docstrings' in analysis:
                output.append(f"Docstrings:           {analysis['docstrings']}")

            if 'complexity_score' in analysis:
                output.append(f"Complexity Score:     {analysis['complexity_score']:.1f}%")

            if 'maintainability_score' in analysis:
                output.append(f"Maintainability:      {analysis['maintainability_score']:.1f}%")

            output.append("")
            output.append("=" * 80)

            return "\n".join(output)
        except Exception as e:
            return f"❌ Error analyzing file: {str(e)}"


def run(args: list) -> str:
    """Run analytics command"""
    command = AnalyticsCommand()
    return command.execute(args)
