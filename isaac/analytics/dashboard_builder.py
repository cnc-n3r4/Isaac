"""
Dashboard Builder

Build custom dashboards with metrics visualization.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from isaac.analytics.database import AnalyticsDatabase
from isaac.analytics.productivity_tracker import ProductivityTracker
from isaac.analytics.code_quality_tracker import CodeQualityTracker
from isaac.analytics.learning_tracker import LearningTracker
from isaac.analytics.team_tracker import TeamTracker


@dataclass
class Widget:
    """Dashboard widget"""
    widget_id: str
    widget_type: str  # 'metric', 'chart', 'list', 'table'
    title: str
    data_source: str
    config: Dict[str, Any]
    position: Dict[str, int]  # {'row': 0, 'col': 0, 'width': 1, 'height': 1}


@dataclass
class Dashboard:
    """Dashboard configuration"""
    dashboard_id: str
    name: str
    description: str
    widgets: List[Widget]
    refresh_interval: int = 60  # seconds
    created_at: str = ""
    updated_at: str = ""


class DashboardBuilder:
    """Build and manage custom analytics dashboards"""

    def __init__(self, db: Optional[AnalyticsDatabase] = None):
        """Initialize dashboard builder"""
        self.db = db or AnalyticsDatabase()
        self.productivity = ProductivityTracker(db)
        self.code_quality = CodeQualityTracker(db)
        self.learning = LearningTracker(db)
        self.team = TeamTracker(db=db)

        # Built-in dashboards
        self.built_in_dashboards = {
            'overview': self._create_overview_dashboard(),
            'productivity': self._create_productivity_dashboard(),
            'quality': self._create_quality_dashboard(),
            'learning': self._create_learning_dashboard(),
            'team': self._create_team_dashboard()
        }

    def _create_overview_dashboard(self) -> Dashboard:
        """Create overview dashboard with all key metrics"""
        return Dashboard(
            dashboard_id='overview',
            name='Overview Dashboard',
            description='High-level view of all metrics',
            widgets=[
                Widget(
                    widget_id='productivity_score',
                    widget_type='metric',
                    title='Efficiency Score',
                    data_source='productivity.efficiency_score',
                    config={'format': 'percentage', 'color': 'green'},
                    position={'row': 0, 'col': 0, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='quality_score',
                    widget_type='metric',
                    title='Code Quality',
                    data_source='code_quality.quality_score',
                    config={'format': 'percentage', 'color': 'blue'},
                    position={'row': 0, 'col': 1, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='learning_rate',
                    widget_type='metric',
                    title='Learning Rate',
                    data_source='learning.learning_rate',
                    config={'format': 'percentage', 'color': 'purple'},
                    position={'row': 0, 'col': 2, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='time_saved',
                    widget_type='metric',
                    title='Time Saved',
                    data_source='productivity.time_saved',
                    config={'format': 'hours', 'color': 'orange'},
                    position={'row': 0, 'col': 3, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='productivity_trend',
                    widget_type='chart',
                    title='Productivity Trend',
                    data_source='productivity.trend',
                    config={'chart_type': 'line', 'days': 7},
                    position={'row': 1, 'col': 0, 'width': 2, 'height': 2}
                ),
                Widget(
                    widget_id='quality_trend',
                    widget_type='chart',
                    title='Quality Trend',
                    data_source='code_quality.trend',
                    config={'chart_type': 'line', 'days': 7},
                    position={'row': 1, 'col': 2, 'width': 2, 'height': 2}
                ),
                Widget(
                    widget_id='recent_insights',
                    widget_type='list',
                    title='Recent Insights',
                    data_source='insights.recent',
                    config={'limit': 5},
                    position={'row': 3, 'col': 0, 'width': 4, 'height': 1}
                )
            ],
            created_at=datetime.now().isoformat()
        )

    def _create_productivity_dashboard(self) -> Dashboard:
        """Create productivity-focused dashboard"""
        return Dashboard(
            dashboard_id='productivity',
            name='Productivity Dashboard',
            description='Track efficiency and time savings',
            widgets=[
                Widget(
                    widget_id='commands_executed',
                    widget_type='metric',
                    title='Commands Executed',
                    data_source='productivity.commands_executed',
                    config={'format': 'number'},
                    position={'row': 0, 'col': 0, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='automations_run',
                    widget_type='metric',
                    title='Automations Run',
                    data_source='productivity.automation_runs',
                    config={'format': 'number'},
                    position={'row': 0, 'col': 1, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='time_saved_today',
                    widget_type='metric',
                    title='Time Saved Today',
                    data_source='productivity.time_saved',
                    config={'format': 'hours'},
                    position={'row': 0, 'col': 2, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='efficiency_trend',
                    widget_type='chart',
                    title='Efficiency Trend (7 days)',
                    data_source='productivity.trend',
                    config={'chart_type': 'area', 'days': 7},
                    position={'row': 1, 'col': 0, 'width': 3, 'height': 2}
                ),
                Widget(
                    widget_id='breakdown',
                    widget_type='table',
                    title='Productivity Breakdown',
                    data_source='productivity.breakdown',
                    config={},
                    position={'row': 3, 'col': 0, 'width': 3, 'height': 2}
                )
            ],
            created_at=datetime.now().isoformat()
        )

    def _create_quality_dashboard(self) -> Dashboard:
        """Create code quality dashboard"""
        return Dashboard(
            dashboard_id='quality',
            name='Code Quality Dashboard',
            description='Track code quality improvements',
            widgets=[
                Widget(
                    widget_id='quality_score',
                    widget_type='metric',
                    title='Overall Quality Score',
                    data_source='code_quality.quality_score',
                    config={'format': 'percentage', 'color': 'blue'},
                    position={'row': 0, 'col': 0, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='patterns_detected',
                    widget_type='metric',
                    title='Patterns Detected',
                    data_source='code_quality.patterns_detected',
                    config={'format': 'number', 'color': 'green'},
                    position={'row': 0, 'col': 1, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='anti_patterns',
                    widget_type='metric',
                    title='Anti-Patterns Found',
                    data_source='code_quality.anti_patterns_detected',
                    config={'format': 'number', 'color': 'red'},
                    position={'row': 0, 'col': 2, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='quality_trend',
                    widget_type='chart',
                    title='Quality Trend',
                    data_source='code_quality.trend',
                    config={'chart_type': 'line', 'days': 7},
                    position={'row': 1, 'col': 0, 'width': 3, 'height': 2}
                )
            ],
            created_at=datetime.now().isoformat()
        )

    def _create_learning_dashboard(self) -> Dashboard:
        """Create learning analytics dashboard"""
        return Dashboard(
            dashboard_id='learning',
            name='Learning Dashboard',
            description='Track Isaac learning progress',
            widgets=[
                Widget(
                    widget_id='patterns_learned',
                    widget_type='metric',
                    title='Patterns Learned',
                    data_source='learning.patterns_learned',
                    config={'format': 'number'},
                    position={'row': 0, 'col': 0, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='learning_rate',
                    widget_type='metric',
                    title='Learning Rate',
                    data_source='learning.learning_rate',
                    config={'format': 'percentage'},
                    position={'row': 0, 'col': 1, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='adaptation_score',
                    widget_type='metric',
                    title='Adaptation Score',
                    data_source='learning.adaptation_score',
                    config={'format': 'percentage'},
                    position={'row': 0, 'col': 2, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='learning_trend',
                    widget_type='chart',
                    title='Learning Trend',
                    data_source='learning.trend',
                    config={'chart_type': 'bar', 'days': 30},
                    position={'row': 1, 'col': 0, 'width': 3, 'height': 2}
                ),
                Widget(
                    widget_id='top_learnings',
                    widget_type='list',
                    title='Top Learnings',
                    data_source='learning.top_learnings',
                    config={'limit': 10},
                    position={'row': 3, 'col': 0, 'width': 3, 'height': 2}
                )
            ],
            created_at=datetime.now().isoformat()
        )

    def _create_team_dashboard(self) -> Dashboard:
        """Create team analytics dashboard"""
        return Dashboard(
            dashboard_id='team',
            name='Team Dashboard',
            description='Track team collaboration and productivity',
            widgets=[
                Widget(
                    widget_id='active_members',
                    widget_type='metric',
                    title='Active Members',
                    data_source='team.active_members',
                    config={'format': 'number'},
                    position={'row': 0, 'col': 0, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='collaboration_score',
                    widget_type='metric',
                    title='Collaboration Score',
                    data_source='team.collaboration_score',
                    config={'format': 'percentage'},
                    position={'row': 0, 'col': 1, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='contributions',
                    widget_type='metric',
                    title='Total Contributions',
                    data_source='team.contributions',
                    config={'format': 'number'},
                    position={'row': 0, 'col': 2, 'width': 1, 'height': 1}
                ),
                Widget(
                    widget_id='activity_timeline',
                    widget_type='chart',
                    title='Activity Timeline',
                    data_source='team.timeline',
                    config={'chart_type': 'stacked_bar', 'days': 7},
                    position={'row': 1, 'col': 0, 'width': 3, 'height': 2}
                ),
                Widget(
                    widget_id='top_contributors',
                    widget_type='table',
                    title='Top Contributors',
                    data_source='team.top_contributors',
                    config={'limit': 5},
                    position={'row': 3, 'col': 0, 'width': 3, 'height': 2}
                )
            ],
            created_at=datetime.now().isoformat()
        )

    def render_dashboard(
        self,
        dashboard_id: str,
        width: int = 80
    ) -> str:
        """Render dashboard as ASCII art for terminal"""
        if dashboard_id in self.built_in_dashboards:
            dashboard = self.built_in_dashboards[dashboard_id]
        else:
            return f"Dashboard '{dashboard_id}' not found"

        # Fetch data for all widgets
        widget_data = {}
        for widget in dashboard.widgets:
            widget_data[widget.widget_id] = self._fetch_widget_data(widget)

        # Render dashboard
        output = []
        output.append("=" * width)
        output.append(f" {dashboard.name}".center(width))
        output.append(f" {dashboard.description}".center(width))
        output.append("=" * width)
        output.append("")

        # Group widgets by row
        rows = {}
        for widget in dashboard.widgets:
            row = widget.position['row']
            if row not in rows:
                rows[row] = []
            rows[row].append(widget)

        # Render each row
        for row_num in sorted(rows.keys()):
            row_widgets = sorted(rows[row_num], key=lambda w: w.position['col'])

            # Render widgets in this row
            for widget in row_widgets:
                data = widget_data.get(widget.widget_id, {})
                rendered = self._render_widget(widget, data, width)
                output.append(rendered)
                output.append("")

        output.append("=" * width)
        output.append(f" Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(width))
        output.append("=" * width)

        return "\n".join(output)

    def _fetch_widget_data(self, widget: Widget) -> Dict[str, Any]:
        """Fetch data for a widget based on its data source"""
        source_parts = widget.data_source.split('.')

        if len(source_parts) < 2:
            return {}

        tracker_name = source_parts[0]
        metric_name = source_parts[1]

        try:
            if tracker_name == 'productivity':
                return self._fetch_productivity_data(metric_name, widget.config)
            elif tracker_name == 'code_quality':
                return self._fetch_quality_data(metric_name, widget.config)
            elif tracker_name == 'learning':
                return self._fetch_learning_data(metric_name, widget.config)
            elif tracker_name == 'team':
                return self._fetch_team_data(metric_name, widget.config)
            elif tracker_name == 'insights':
                return self._fetch_insights_data(metric_name, widget.config)
        except Exception as e:
            return {'error': str(e)}

        return {}

    def _fetch_productivity_data(
        self,
        metric: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch productivity metrics"""
        if metric == 'efficiency_score':
            return {'value': self.productivity.calculate_efficiency_score()}
        elif metric == 'time_saved':
            return {'value': self.productivity.time_saved / 3600}  # Convert to hours
        elif metric == 'commands_executed':
            return {'value': self.productivity.commands_executed}
        elif metric == 'automation_runs':
            return {'value': self.productivity.automation_runs}
        elif metric == 'trend':
            days = config.get('days', 7)
            return {'data': self.productivity.get_efficiency_trend(days)}
        elif metric == 'breakdown':
            return self.productivity.get_productivity_report()

        return {}

    def _fetch_quality_data(
        self,
        metric: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch code quality metrics"""
        snapshot = self.code_quality.get_current_snapshot()

        if metric == 'quality_score':
            return {'value': snapshot.quality_score}
        elif metric == 'patterns_detected':
            return {'value': snapshot.patterns_detected}
        elif metric == 'anti_patterns_detected':
            return {'value': snapshot.anti_patterns_detected}
        elif metric == 'trend':
            days = config.get('days', 7)
            return {'data': self.code_quality.get_quality_trend(days)}

        return {}

    def _fetch_learning_data(
        self,
        metric: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch learning metrics"""
        snapshot = self.learning.get_current_snapshot()

        if metric == 'patterns_learned':
            return {'value': snapshot.patterns_learned}
        elif metric == 'learning_rate':
            return {'value': snapshot.learning_rate}
        elif metric == 'adaptation_score':
            return {'value': snapshot.adaptation_score}
        elif metric == 'trend':
            days = config.get('days', 30)
            return {'data': self.learning.get_learning_trend(days)}
        elif metric == 'top_learnings':
            report = self.learning.get_learning_report()
            return {'items': report.get('top_learnings', [])}

        return {}

    def _fetch_team_data(
        self,
        metric: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch team metrics"""
        snapshot = self.team.get_current_snapshot()

        if metric == 'active_members':
            return {'value': snapshot.active_members}
        elif metric == 'collaboration_score':
            return {'value': snapshot.collaboration_score}
        elif metric == 'contributions':
            return {'value': snapshot.total_contributions}
        elif metric == 'timeline':
            days = config.get('days', 7)
            return {'data': self.team.get_activity_timeline(days)}
        elif metric == 'top_contributors':
            report = self.team.get_team_report()
            return {'items': report.get('top_contributors', [])}

        return {}

    def _fetch_insights_data(
        self,
        metric: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch insights from all trackers"""
        insights = []

        # Get insights from each tracker
        prod_report = self.productivity.get_productivity_report()
        quality_report = self.code_quality.get_quality_report()
        learning_report = self.learning.get_learning_report()

        insights.extend(prod_report.get('insights', []))
        insights.extend(quality_report.get('insights', []))
        insights.extend(learning_report.get('insights', []))

        return {'items': insights[:config.get('limit', 10)]}

    def _render_widget(
        self,
        widget: Widget,
        data: Dict[str, Any],
        width: int
    ) -> str:
        """Render a single widget"""
        if 'error' in data:
            return f"[{widget.title}] Error: {data['error']}"

        if widget.widget_type == 'metric':
            return self._render_metric_widget(widget, data, width)
        elif widget.widget_type == 'chart':
            return self._render_chart_widget(widget, data, width)
        elif widget.widget_type == 'list':
            return self._render_list_widget(widget, data, width)
        elif widget.widget_type == 'table':
            return self._render_table_widget(widget, data, width)

        return f"[{widget.title}] Unsupported widget type: {widget.widget_type}"

    def _render_metric_widget(
        self,
        widget: Widget,
        data: Dict[str, Any],
        width: int
    ) -> str:
        """Render metric widget"""
        value = data.get('value', 0)
        format_type = widget.config.get('format', 'number')

        if format_type == 'percentage':
            formatted = f"{value:.1f}%"
        elif format_type == 'hours':
            formatted = f"{value:.2f}h"
        else:
            formatted = f"{value:,.0f}"

        return f"┌─ {widget.title}\n│  {formatted}\n└─"

    def _render_chart_widget(
        self,
        widget: Widget,
        data: Dict[str, Any],
        width: int
    ) -> str:
        """Render simple ASCII chart"""
        chart_data = data.get('data', [])
        if not chart_data:
            return f"[{widget.title}] No data available"

        output = [f"┌─ {widget.title}"]

        # Simple bar chart representation
        if len(chart_data) <= 10:
            max_value = max((d.get('efficiency', d.get('average_quality', d.get('total', 1))) for d in chart_data), default=1)

            for item in chart_data:
                label = item.get('date', '')[-5:]  # Last 5 chars of date (MM-DD)
                value = item.get('efficiency', item.get('average_quality', item.get('total', 0)))
                bar_width = int((value / max_value) * 30) if max_value > 0 else 0
                bar = '█' * bar_width
                output.append(f"│ {label} │{bar} {value:.1f}")

        output.append("└─")
        return "\n".join(output)

    def _render_list_widget(
        self,
        widget: Widget,
        data: Dict[str, Any],
        width: int
    ) -> str:
        """Render list widget"""
        items = data.get('items', [])
        output = [f"┌─ {widget.title}"]

        if isinstance(items, list):
            for item in items:
                if isinstance(item, str):
                    output.append(f"│ • {item}")
                elif isinstance(item, dict):
                    # Format dict items
                    item_text = item.get('item', str(item))
                    output.append(f"│ • {item_text}")

        output.append("└─")
        return "\n".join(output)

    def _render_table_widget(
        self,
        widget: Widget,
        data: Dict[str, Any],
        width: int
    ) -> str:
        """Render table widget"""
        items = data.get('items', [])
        output = [f"┌─ {widget.title}"]

        if isinstance(items, list) and items:
            for item in items[:5]:  # Limit to 5 rows
                if isinstance(item, dict):
                    row = " | ".join(f"{k}: {v}" for k, v in item.items())
                    output.append(f"│ {row[:width-4]}")

        output.append("└─")
        return "\n".join(output)

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard configuration"""
        return self.built_in_dashboards.get(dashboard_id)

    def list_dashboards(self) -> List[str]:
        """List available dashboards"""
        return list(self.built_in_dashboards.keys())
