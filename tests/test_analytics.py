"""
Tests for Analytics System

Test all analytics components.
"""

import os
import tempfile
import pytest
from datetime import datetime, timedelta

from isaac.analytics.database import AnalyticsDatabase
from isaac.analytics.productivity_tracker import ProductivityTracker
from isaac.analytics.code_quality_tracker import CodeQualityTracker
from isaac.analytics.learning_tracker import LearningTracker
from isaac.analytics.team_tracker import TeamTracker
from isaac.analytics.analytics_manager import AnalyticsManager
from isaac.analytics.dashboard_builder import DashboardBuilder
from isaac.analytics.report_exporter import ReportExporter


class TestAnalyticsDatabase:
    """Test analytics database"""

    def test_database_creation(self):
        """Test database is created successfully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            assert os.path.exists(db_path)

    def test_record_productivity_metric(self):
        """Test recording productivity metrics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)

            db.record_productivity_metric(
                metric_type='command_execution',
                metric_name='test_command',
                metric_value=1.0
            )

            metrics = db.query_metrics('productivity_metrics')
            assert len(metrics) == 1
            assert metrics[0]['metric_name'] == 'test_command'

    def test_record_code_quality_metric(self):
        """Test recording code quality metrics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)

            db.record_code_quality_metric(
                metric_type='quality_score',
                metric_name='overall_quality',
                metric_value=85.0,
                file_path='/test/file.py'
            )

            metrics = db.query_metrics('code_quality_metrics')
            assert len(metrics) == 1
            assert metrics[0]['metric_value'] == 85.0

    def test_query_with_date_range(self):
        """Test querying with date range"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)

            # Record metric
            db.record_productivity_metric(
                metric_type='test',
                metric_name='test',
                metric_value=1.0
            )

            # Query with date range
            start = (datetime.now() - timedelta(days=1)).isoformat()
            end = (datetime.now() + timedelta(days=1)).isoformat()

            metrics = db.query_metrics(
                'productivity_metrics',
                start_date=start,
                end_date=end
            )

            assert len(metrics) >= 1


class TestProductivityTracker:
    """Test productivity tracker"""

    def test_tracker_initialization(self):
        """Test tracker initializes correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            tracker = ProductivityTracker(db)

            assert tracker.commands_executed == 0
            assert tracker.time_saved == 0.0

    def test_record_command(self):
        """Test recording command execution"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            tracker = ProductivityTracker(db)

            tracker.record_command_execution(
                command_name='test_command',
                execution_time=0.5,
                estimated_manual_time=5.0
            )

            assert tracker.commands_executed == 1
            assert tracker.time_saved > 0

    def test_efficiency_score(self):
        """Test efficiency score calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            tracker = ProductivityTracker(db)

            score = tracker.calculate_efficiency_score()
            assert 0 <= score <= 100


class TestCodeQualityTracker:
    """Test code quality tracker"""

    def test_analyze_python_file(self):
        """Test analyzing Python file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write('''
def hello():
    """Say hello"""
    return "Hello, World!"

class TestClass:
    """Test class"""
    pass
''')

            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            tracker = CodeQualityTracker(db)

            analysis = tracker.analyze_file(test_file)

            assert 'quality_score' in analysis
            assert analysis['functions'] >= 1
            assert analysis['classes'] >= 1

    def test_analyze_nonexistent_file(self):
        """Test analyzing nonexistent file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            tracker = CodeQualityTracker(db)

            analysis = tracker.analyze_file('/nonexistent/file.py')
            assert 'error' in analysis


class TestLearningTracker:
    """Test learning tracker"""

    def test_record_pattern_learned(self):
        """Test recording learned pattern"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            tracker = LearningTracker(db)

            tracker.record_pattern_learned(
                pattern_name='singleton',
                pattern_type='design_pattern',
                confidence=0.85
            )

            assert tracker.patterns_learned == 1

    def test_learning_rate(self):
        """Test learning rate calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            tracker = LearningTracker(db)

            rate = tracker.calculate_learning_rate()
            assert 0 <= rate <= 100


class TestTeamTracker:
    """Test team tracker"""

    def test_record_contribution(self):
        """Test recording team contribution"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            tracker = TeamTracker(team_id='test_team', db=db)

            tracker.record_contribution(
                user_id='user1',
                contribution_type='code_commit',
                contribution_value=1.0
            )

            assert tracker.contributions == 1

    def test_collaboration_score(self):
        """Test collaboration score calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            tracker = TeamTracker(team_id='test_team', db=db)

            score = tracker.calculate_collaboration_score()
            assert 0 <= score <= 100


class TestAnalyticsManager:
    """Test analytics manager"""

    def test_manager_initialization(self):
        """Test manager initializes all components"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            manager = AnalyticsManager(db_path=db_path)

            assert manager.productivity is not None
            assert manager.code_quality is not None
            assert manager.learning is not None
            assert manager.team is not None

    def test_get_summary(self):
        """Test getting analytics summary"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            manager = AnalyticsManager(db_path=db_path)

            summary = manager.get_summary()

            assert 'productivity' in summary
            assert 'code_quality' in summary
            assert 'learning' in summary
            assert 'team' in summary

    def test_enable_disable(self):
        """Test enabling and disabling analytics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            manager = AnalyticsManager(db_path=db_path)

            assert manager.enabled is True

            manager.disable()
            assert manager.enabled is False

            manager.enable()
            assert manager.enabled is True


class TestDashboardBuilder:
    """Test dashboard builder"""

    def test_list_dashboards(self):
        """Test listing available dashboards"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            builder = DashboardBuilder(db)

            dashboards = builder.list_dashboards()
            assert len(dashboards) > 0
            assert 'overview' in dashboards

    def test_get_dashboard(self):
        """Test getting dashboard configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            builder = DashboardBuilder(db)

            dashboard = builder.get_dashboard('overview')
            assert dashboard is not None
            assert dashboard.name == 'Overview Dashboard'

    def test_render_dashboard(self):
        """Test rendering dashboard"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            builder = DashboardBuilder(db)

            output = builder.render_dashboard('overview')
            assert len(output) > 0
            assert 'Overview Dashboard' in output


class TestReportExporter:
    """Test report exporter"""

    def test_export_json(self):
        """Test exporting report as JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            exporter = ReportExporter(db)

            output = exporter.export_report(
                report_type='productivity',
                format='json'
            )

            assert len(output) > 0
            assert '{' in output  # Valid JSON

    def test_export_markdown(self):
        """Test exporting report as Markdown"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            exporter = ReportExporter(db)

            output = exporter.export_report(
                report_type='productivity',
                format='markdown'
            )

            assert len(output) > 0
            assert '#' in output  # Markdown header

    def test_export_html(self):
        """Test exporting report as HTML"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            exporter = ReportExporter(db)

            output = exporter.export_report(
                report_type='productivity',
                format='html'
            )

            assert len(output) > 0
            assert '<!DOCTYPE html>' in output

    def test_export_to_file(self):
        """Test exporting report to file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = AnalyticsDatabase(db_path)
            exporter = ReportExporter(db)

            output_path = os.path.join(tmpdir, "report.html")
            result = exporter.export_report(
                report_type='productivity',
                format='html',
                output_path=output_path
            )

            assert result == output_path
            assert os.path.exists(output_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
