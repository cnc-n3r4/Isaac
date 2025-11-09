"""
Report Exporter

Export analytics reports in various formats (JSON, CSV, HTML, Markdown).
"""

import json
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from io import StringIO

from isaac.analytics.database import AnalyticsDatabase
from isaac.analytics.productivity_tracker import ProductivityTracker
from isaac.analytics.code_quality_tracker import CodeQualityTracker
from isaac.analytics.learning_tracker import LearningTracker
from isaac.analytics.team_tracker import TeamTracker


class ReportExporter:
    """Export analytics reports in various formats"""

    def __init__(self, db: Optional[AnalyticsDatabase] = None):
        """Initialize report exporter"""
        self.db = db or AnalyticsDatabase()
        self.productivity = ProductivityTracker(db)
        self.code_quality = CodeQualityTracker(db)
        self.learning = LearningTracker(db)
        self.team = TeamTracker(db=db)

    def export_report(
        self,
        report_type: str,
        format: str,
        output_path: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Export a report in specified format

        Args:
            report_type: 'productivity', 'quality', 'learning', 'team', or 'full'
            format: 'json', 'csv', 'html', or 'markdown'
            output_path: Path to save file (optional)
            start_date: Start date for report
            end_date: End date for report

        Returns:
            Report content as string or path to saved file
        """
        # Generate report data
        if report_type == 'productivity':
            data = self.productivity.get_productivity_report(start_date, end_date)
        elif report_type == 'quality':
            data = self.code_quality.get_quality_report(start_date, end_date)
        elif report_type == 'learning':
            data = self.learning.get_learning_report(start_date, end_date)
        elif report_type == 'team':
            data = self.team.get_team_report(start_date, end_date)
        elif report_type == 'full':
            data = self._generate_full_report(start_date, end_date)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        # Export in specified format
        if format == 'json':
            content = self._export_json(data)
        elif format == 'csv':
            content = self._export_csv(data, report_type)
        elif format == 'html':
            content = self._export_html(data, report_type)
        elif format == 'markdown':
            content = self._export_markdown(data, report_type)
        else:
            raise ValueError(f"Unknown format: {format}")

        # Save to file if path provided
        if output_path:
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return output_path

        return content

    def _generate_full_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive report with all analytics"""
        return {
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start': start_date or (datetime.now() - timedelta(days=7)).isoformat(),
                'end': end_date or datetime.now().isoformat()
            },
            'productivity': self.productivity.get_productivity_report(start_date, end_date),
            'code_quality': self.code_quality.get_quality_report(start_date, end_date),
            'learning': self.learning.get_learning_report(start_date, end_date),
            'team': self.team.get_team_report(start_date, end_date)
        }

    def _export_json(self, data: Dict[str, Any]) -> str:
        """Export as JSON"""
        return json.dumps(data, indent=2, default=str)

    def _export_csv(self, data: Dict[str, Any], report_type: str) -> str:
        """Export as CSV"""
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['Isaac Analytics Report'])
        writer.writerow(['Report Type', report_type])
        writer.writerow(['Generated At', datetime.now().isoformat()])
        writer.writerow([])

        # Write summary data
        if 'summary' in data:
            writer.writerow(['Summary'])
            for key, value in data['summary'].items():
                writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])

        # Write trend data if available
        if report_type == 'productivity' and 'breakdown' in data:
            writer.writerow(['Productivity Breakdown'])
            for metric_type, metric_data in data['breakdown'].items():
                writer.writerow([metric_type, metric_data.get('count', 0), metric_data.get('total_value', 0)])
            writer.writerow([])

        # Write insights
        if 'insights' in data:
            writer.writerow(['Insights'])
            for insight in data['insights']:
                writer.writerow([insight])

        return output.getvalue()

    def _export_html(self, data: Dict[str, Any], report_type: str) -> str:
        """Export as HTML"""
        html = []
        html.append('<!DOCTYPE html>')
        html.append('<html>')
        html.append('<head>')
        html.append('<meta charset="UTF-8">')
        html.append('<title>Isaac Analytics Report</title>')
        html.append('<style>')
        html.append('''
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .section {
                background: white;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .metric {
                display: inline-block;
                margin: 10px 20px 10px 0;
                padding: 15px 20px;
                background: #f8f9fa;
                border-radius: 5px;
                border-left: 4px solid #667eea;
            }
            .metric-label {
                font-size: 0.9em;
                color: #666;
                margin-bottom: 5px;
            }
            .metric-value {
                font-size: 1.8em;
                font-weight: bold;
                color: #333;
            }
            .insight {
                padding: 10px 15px;
                margin: 8px 0;
                background: #e7f3ff;
                border-left: 4px solid #2196F3;
                border-radius: 4px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #667eea;
                color: white;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
        ''')
        html.append('</style>')
        html.append('</head>')
        html.append('<body>')

        # Header
        html.append('<div class="header">')
        html.append(f'<h1>📊 Isaac Analytics Report</h1>')
        html.append(f'<p><strong>Report Type:</strong> {report_type.title()}</p>')
        html.append(f'<p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>')
        if 'period' in data:
            html.append(f'<p><strong>Period:</strong> {data["period"].get("start", "N/A")[:10]} to {data["period"].get("end", "N/A")[:10]}</p>')
        html.append('</div>')

        # Summary section
        if 'summary' in data:
            html.append('<div class="section">')
            html.append('<h2>📈 Summary</h2>')
            for key, value in data['summary'].items():
                label = key.replace('_', ' ').title()
                html.append('<div class="metric">')
                html.append(f'<div class="metric-label">{label}</div>')

                # Format value based on type
                if isinstance(value, float):
                    if 'percentage' in key or 'score' in key:
                        formatted_value = f"{value:.1f}%"
                    elif 'hours' in key:
                        formatted_value = f"{value:.2f}h"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)

                html.append(f'<div class="metric-value">{formatted_value}</div>')
                html.append('</div>')
            html.append('</div>')

        # Current session section
        if 'current_session' in data:
            html.append('<div class="section">')
            html.append('<h2>🔄 Current Session</h2>')
            html.append('<table>')
            html.append('<tr><th>Metric</th><th>Value</th></tr>')
            for key, value in data['current_session'].items():
                if key != 'timestamp':
                    label = key.replace('_', ' ').title()
                    formatted_value = f"{value:.1f}" if isinstance(value, float) else str(value)
                    html.append(f'<tr><td>{label}</td><td>{formatted_value}</td></tr>')
            html.append('</table>')
            html.append('</div>')

        # Insights section
        if 'insights' in data and data['insights']:
            html.append('<div class="section">')
            html.append('<h2>💡 Insights</h2>')
            for insight in data['insights']:
                html.append(f'<div class="insight">{insight}</div>')
            html.append('</div>')

        html.append('</body>')
        html.append('</html>')

        return '\n'.join(html)

    def _export_markdown(self, data: Dict[str, Any], report_type: str) -> str:
        """Export as Markdown"""
        md = []
        md.append(f'# 📊 Isaac Analytics Report')
        md.append('')
        md.append(f'**Report Type:** {report_type.title()}  ')
        md.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  ')

        if 'period' in data:
            start = data['period'].get('start', 'N/A')[:10]
            end = data['period'].get('end', 'N/A')[:10]
            md.append(f'**Period:** {start} to {end}  ')

        md.append('')
        md.append('---')
        md.append('')

        # Summary section
        if 'summary' in data:
            md.append('## 📈 Summary')
            md.append('')
            for key, value in data['summary'].items():
                label = key.replace('_', ' ').title()

                # Format value
                if isinstance(value, float):
                    if 'percentage' in key or 'score' in key:
                        formatted_value = f"{value:.1f}%"
                    elif 'hours' in key:
                        formatted_value = f"{value:.2f}h"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)

                md.append(f'- **{label}:** {formatted_value}')
            md.append('')

        # Current session
        if 'current_session' in data:
            md.append('## 🔄 Current Session')
            md.append('')
            md.append('| Metric | Value |')
            md.append('|--------|-------|')
            for key, value in data['current_session'].items():
                if key != 'timestamp':
                    label = key.replace('_', ' ').title()
                    formatted_value = f"{value:.1f}" if isinstance(value, float) else str(value)
                    md.append(f'| {label} | {formatted_value} |')
            md.append('')

        # Breakdown section (for productivity reports)
        if 'breakdown' in data:
            md.append('## 📊 Breakdown')
            md.append('')
            for metric_type, metric_data in data['breakdown'].items():
                md.append(f'### {metric_type.replace("_", " ").title()}')
                md.append(f'- Count: {metric_data.get("count", 0)}')
                md.append(f'- Total Value: {metric_data.get("total_value", 0):.2f}')
                md.append('')

        # Top contributors (for team reports)
        if 'top_contributors' in data:
            md.append('## 🏆 Top Contributors')
            md.append('')
            md.append('| User | Score | Contributions |')
            md.append('|------|-------|---------------|')
            for contributor in data['top_contributors'][:10]:
                user_id = contributor.get('user_id', 'Unknown')
                score = contributor.get('score', 0)
                stats = contributor.get('stats', {})
                contributions = stats.get('contributions', 0)
                md.append(f'| {user_id} | {score:.1f} | {contributions} |')
            md.append('')

        # Top learnings (for learning reports)
        if 'top_learnings' in data:
            md.append('## 🧠 Top Learnings')
            md.append('')
            for learning in data['top_learnings']:
                learning_type = learning.get('type', '').replace('_', ' ').title()
                item = learning.get('item', '')
                confidence = learning.get('confidence', 0)
                md.append(f'- **{learning_type}:** {item} (Confidence: {confidence:.1f})')
            md.append('')

        # Insights section
        if 'insights' in data and data['insights']:
            md.append('## 💡 Insights')
            md.append('')
            for insight in data['insights']:
                md.append(f'- {insight}')
            md.append('')

        md.append('---')
        md.append('')
        md.append('*Generated by Isaac Analytics System*')

        return '\n'.join(md)

    def export_dashboard(
        self,
        dashboard_id: str,
        format: str = 'html',
        output_path: Optional[str] = None
    ) -> str:
        """Export a dashboard visualization"""
        from isaac.analytics.dashboard_builder import DashboardBuilder

        builder = DashboardBuilder(self.db)
        dashboard = builder.get_dashboard(dashboard_id)

        if not dashboard:
            raise ValueError(f"Dashboard '{dashboard_id}' not found")

        if format == 'html':
            content = self._export_dashboard_html(builder, dashboard_id)
        else:
            # Fall back to ASCII rendering
            content = builder.render_dashboard(dashboard_id)

        if output_path:
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return output_path

        return content

    def _export_dashboard_html(
        self,
        builder,
        dashboard_id: str
    ) -> str:
        """Export dashboard as interactive HTML"""
        dashboard = builder.get_dashboard(dashboard_id)

        html = []
        html.append('<!DOCTYPE html>')
        html.append('<html>')
        html.append('<head>')
        html.append('<meta charset="UTF-8">')
        html.append(f'<title>{dashboard.name} - Isaac Analytics</title>')
        html.append('<style>')
        html.append('''
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
            }
            .dashboard-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .widgets-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }
            .widget {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .widget-title {
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 15px;
                color: #333;
            }
            .widget-value {
                font-size: 2.5em;
                font-weight: bold;
                color: #667eea;
            }
        ''')
        html.append('</style>')
        html.append('</head>')
        html.append('<body>')

        html.append('<div class="dashboard-header">')
        html.append(f'<h1>{dashboard.name}</h1>')
        html.append(f'<p>{dashboard.description}</p>')
        html.append('</div>')

        html.append('<div class="widgets-grid">')

        # Render widgets
        for widget in dashboard.widgets:
            widget_data = builder._fetch_widget_data(widget)
            html.append('<div class="widget">')
            html.append(f'<div class="widget-title">{widget.title}</div>')

            if 'value' in widget_data:
                value = widget_data['value']
                format_type = widget.config.get('format', 'number')

                if format_type == 'percentage':
                    formatted = f"{value:.1f}%"
                elif format_type == 'hours':
                    formatted = f"{value:.2f}h"
                else:
                    formatted = f"{value:,.0f}"

                html.append(f'<div class="widget-value">{formatted}</div>')

            html.append('</div>')

        html.append('</div>')
        html.append(f'<p style="text-align: center; margin-top: 30px; color: #666;">Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>')
        html.append('</body>')
        html.append('</html>')

        return '\n'.join(html)

    def schedule_report(
        self,
        report_type: str,
        format: str,
        output_path: str,
        schedule: str  # 'daily', 'weekly', 'monthly'
    ):
        """Schedule automated report generation"""
        # This would integrate with a task scheduler
        # For now, just create a config file
        config = {
            'report_type': report_type,
            'format': format,
            'output_path': output_path,
            'schedule': schedule,
            'created_at': datetime.now().isoformat()
        }

        config_dir = os.path.expanduser("~/.isaac/analytics/scheduled_reports")
        os.makedirs(config_dir, exist_ok=True)

        config_file = os.path.join(
            config_dir,
            f"{report_type}_{schedule}.json"
        )

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        return config_file
