# 📊 Isaac Advanced Analytics System

Comprehensive analytics system for tracking productivity, code quality, learning, and team metrics.

## Overview

The Analytics System provides deep insights into:

- **Productivity Metrics** - Track efficiency gains, time saved, and automation effectiveness
- **Code Quality Metrics** - Monitor code improvements, patterns, and anti-patterns
- **Learning Analytics** - Track what Isaac learns and how it adapts to you
- **Team Analytics** - Measure collaboration and team productivity
- **Custom Dashboards** - Build your own metrics visualizations
- **Report Export** - Generate reports in JSON, CSV, HTML, and Markdown

## Architecture

```
isaac/analytics/
├── database.py              # SQLite database for all analytics
├── analytics_manager.py     # Central coordinator
├── productivity_tracker.py  # Productivity metrics
├── code_quality_tracker.py  # Code quality metrics
├── learning_tracker.py      # Learning analytics
├── team_tracker.py          # Team collaboration metrics
├── dashboard_builder.py     # Dashboard visualization
└── report_exporter.py       # Report generation
```

## Quick Start

### Basic Usage

```python
from isaac.analytics import AnalyticsManager

# Initialize analytics
manager = AnalyticsManager()

# Record command execution
manager.record_command_execution(
    command_name='build',
    execution_time=5.0,
    success=True,
    estimated_manual_time=30.0  # Saved 25 seconds
)

# Get summary
summary = manager.get_summary()
print(summary)

# View dashboard
dashboard = manager.get_dashboard('overview')
print(dashboard)
```

### Command Line Interface

```bash
# Show summary
/analytics summary

# View dashboard
/analytics dashboard overview

# Productivity report
/analytics productivity 7

# Export report
/analytics export full html ~/reports/analytics.html

# Analyze file
/analytics analyze src/main.py
```

## Components

### 1. Productivity Tracker

Tracks efficiency and time savings:

```python
from isaac.analytics import ProductivityTracker, AnalyticsDatabase

db = AnalyticsDatabase()
tracker = ProductivityTracker(db)

# Record command
tracker.record_command_execution(
    command_name='test',
    execution_time=2.0,
    estimated_manual_time=10.0
)

# Record automation
tracker.record_automation_run(
    automation_name='deploy_pipeline',
    steps_automated=5,
    time_saved=300.0  # 5 minutes
)

# Get efficiency score
score = tracker.calculate_efficiency_score()
print(f"Efficiency: {score:.1f}%")

# Get report
report = tracker.get_productivity_report()
```

**Metrics Tracked:**
- Commands executed
- Time saved through automation
- Patterns applied
- Errors prevented
- Suggestions accepted
- Efficiency score (0-100)

### 2. Code Quality Tracker

Monitors code quality improvements:

```python
from isaac.analytics import CodeQualityTracker

tracker = CodeQualityTracker()

# Analyze file
analysis = tracker.analyze_file('src/main.py')
print(f"Quality Score: {analysis['quality_score']:.1f}%")
print(f"Complexity: {analysis['complexity_score']:.1f}%")
print(f"Maintainability: {analysis['maintainability_score']:.1f}%")

# Record pattern detection
tracker.record_pattern_detection(
    pattern_name='singleton',
    file_path='src/service.py',
    confidence=0.85
)

# Record improvement
tracker.record_code_improvement(
    improvement_type='refactoring',
    file_path='src/main.py',
    before_score=60.0,
    after_score=85.0
)
```

**Metrics Tracked:**
- Quality score (0-100)
- Complexity score
- Maintainability score
- Patterns detected
- Anti-patterns found
- Code improvements

### 3. Learning Tracker

Tracks Isaac's learning and adaptation:

```python
from isaac.analytics import LearningTracker

tracker = LearningTracker()

# Record learned pattern
tracker.record_pattern_learned(
    pattern_name='factory_pattern',
    pattern_type='design_pattern',
    confidence=0.9
)

# Record user preference
tracker.record_preference_adaptation(
    preference_name='indentation',
    preference_value='4 spaces',
    confidence=0.95
)

# Get learning rate
rate = tracker.calculate_learning_rate()
print(f"Learning Rate: {rate:.1f}%")

# Get knowledge graph
graph = tracker.get_knowledge_graph()
```

**Metrics Tracked:**
- Patterns learned
- Preferences adapted
- Mistakes learned from
- Behavior adjustments
- Learning rate
- Adaptation score

### 4. Team Tracker

Measures team collaboration:

```python
from isaac.analytics import TeamTracker

tracker = TeamTracker(team_id='myteam')

# Record contribution
tracker.record_contribution(
    user_id='alice',
    contribution_type='code_commit',
    contribution_value=1.0
)

# Record code review
tracker.record_code_review(
    reviewer_id='bob',
    author_id='alice',
    review_quality=0.9
)

# Record pair programming
tracker.record_pair_programming(
    user1_id='alice',
    user2_id='bob',
    duration_minutes=60,
    productivity_score=0.85
)

# Get collaboration score
score = tracker.calculate_collaboration_score()
```

**Metrics Tracked:**
- Active team members
- Contributions
- Collaborations
- Code reviews
- Patterns shared
- Knowledge sharing
- Collaboration score

### 5. Dashboard Builder

Create custom dashboards:

```python
from isaac.analytics import DashboardBuilder

builder = DashboardBuilder()

# List available dashboards
dashboards = builder.list_dashboards()
# ['overview', 'productivity', 'quality', 'learning', 'team']

# Render dashboard
output = builder.render_dashboard('overview')
print(output)

# Get dashboard config
dashboard = builder.get_dashboard('productivity')
```

**Built-in Dashboards:**
- `overview` - High-level view of all metrics
- `productivity` - Productivity and efficiency focus
- `quality` - Code quality metrics
- `learning` - Learning analytics
- `team` - Team collaboration

### 6. Report Exporter

Export analytics in various formats:

```python
from isaac.analytics import ReportExporter

exporter = ReportExporter()

# Export as JSON
json_report = exporter.export_report(
    report_type='productivity',
    format='json'
)

# Export as HTML
html_report = exporter.export_report(
    report_type='full',
    format='html',
    output_path='report.html'
)

# Export as Markdown
md_report = exporter.export_report(
    report_type='quality',
    format='markdown',
    start_date='2024-01-01',
    end_date='2024-01-31'
)

# Schedule automated report
config = exporter.schedule_report(
    report_type='full',
    format='html',
    output_path='~/reports/weekly.html',
    schedule='weekly'
)
```

**Export Formats:**
- JSON - Machine-readable data
- CSV - Spreadsheet-compatible
- HTML - Interactive web report
- Markdown - Documentation-friendly

## Database Schema

### Tables

**productivity_metrics**
- Command execution tracking
- Time saved metrics
- Automation runs
- Pattern applications

**code_quality_metrics**
- Quality scores by file
- Pattern detections
- Anti-pattern warnings
- Code improvements

**learning_analytics**
- Patterns learned
- Preferences adapted
- Mistakes and corrections
- Behavior adjustments

**team_analytics**
- Member contributions
- Collaboration events
- Code reviews
- Knowledge sharing

**command_analytics**
- Command execution history
- Success/failure rates
- Performance metrics

**custom_metrics**
- User-defined metrics
- Tagged data
- Flexible schema

## Integration

### SessionManager Integration

```python
from isaac.analytics import AnalyticsManager

class SessionManager:
    def __init__(self):
        # Initialize analytics
        self.analytics = AnalyticsManager()

    def execute_command(self, command, args):
        start = time.time()
        try:
            result = command.run(args)
            success = True
            error = None
        except Exception as e:
            success = False
            error = str(e)

        # Record in analytics
        self.analytics.record_command_execution(
            command_name=command.name,
            execution_time=time.time() - start,
            success=success,
            error_message=error
        )

        return result
```

### CommandRouter Integration

```python
class CommandRouter:
    def __init__(self):
        self.analytics = AnalyticsManager()

    def route_command(self, command_str):
        # Parse and execute
        result = self._execute(command_str)

        # Track in analytics
        self.analytics.record_command_execution(...)

        return result
```

## Configuration

### Environment Variables

```bash
# Analytics database path
export ISAAC_ANALYTICS_DB=~/.isaac/analytics.db

# Enable/disable analytics
export ISAAC_ANALYTICS_ENABLED=true

# Data retention (days)
export ISAAC_ANALYTICS_RETENTION=90
```

### Programmatic Configuration

```python
manager = AnalyticsManager()

# Enable/disable
manager.enable()
manager.disable()

# Clear old data
manager.clear_old_data(days=90)
```

## Best Practices

### 1. Regular Monitoring

```bash
# Daily summary
/analytics summary

# Weekly productivity review
/analytics productivity 7

# Monthly learning review
/analytics learning 30
```

### 2. Export Reports Regularly

```bash
# Weekly HTML report
/analytics export full html ~/reports/$(date +%Y-%m-%d).html

# Monthly team report
/analytics export team markdown ~/reports/team-$(date +%Y-%m).md
```

### 3. Track Improvements

```python
# Before refactoring
before = tracker.analyze_file('src/main.py')

# ... refactor ...

# After refactoring
after = tracker.analyze_file('src/main.py')

# Record improvement
tracker.record_code_improvement(
    improvement_type='refactoring',
    file_path='src/main.py',
    before_score=before['quality_score'],
    after_score=after['quality_score']
)
```

### 4. Use Dashboards

```bash
# Morning: Check overview
/analytics dashboard overview

# Mid-day: Check productivity
/analytics dashboard productivity

# End of day: Review insights
/analytics insights
```

## Performance

- **Overhead**: <100ms per tracked event
- **Storage**: ~1MB per 10,000 metrics
- **Queries**: Indexed for fast retrieval
- **Retention**: Automatic cleanup after 90 days (configurable)

## Troubleshooting

### Database Issues

```python
# Check database
from isaac.analytics import AnalyticsDatabase
db = AnalyticsDatabase()

# Test query
metrics = db.query_metrics('productivity_metrics', limit=10)
print(f"Found {len(metrics)} metrics")
```

### Clear and Reset

```python
manager = AnalyticsManager()

# Clear old data
manager.clear_old_data(days=0)  # Clear all

# Or manually delete
import os
os.remove(os.path.expanduser('~/.isaac/analytics.db'))
```

## Examples

### Complete Workflow Example

```python
from isaac.analytics import AnalyticsManager

# Initialize
manager = AnalyticsManager()

# 1. Track command execution
manager.record_command_execution(
    command_name='build',
    execution_time=5.0,
    success=True,
    estimated_manual_time=30.0
)

# 2. Analyze code quality
analysis = manager.code_quality.analyze_file('src/main.py')
print(f"Quality: {analysis['quality_score']:.1f}%")

# 3. Record learning
manager.record_pattern_learned(
    pattern_name='observer_pattern',
    pattern_type='design_pattern',
    confidence=0.85
)

# 4. Get summary
summary = manager.get_summary()
print(f"Efficiency: {summary['productivity']['efficiency_score']:.1f}%")
print(f"Learning Rate: {summary['learning']['learning_rate']:.1f}%")

# 5. View dashboard
dashboard = manager.get_dashboard('overview')
print(dashboard)

# 6. Export report
manager.export_report(
    report_type='full',
    format='html',
    output_path='report.html'
)
```

## API Reference

See individual module documentation:
- [Database API](database.py)
- [Productivity Tracker API](productivity_tracker.py)
- [Code Quality Tracker API](code_quality_tracker.py)
- [Learning Tracker API](learning_tracker.py)
- [Team Tracker API](team_tracker.py)
- [Dashboard Builder API](dashboard_builder.py)
- [Report Exporter API](report_exporter.py)

## Future Enhancements

- Real-time streaming dashboards
- Machine learning-based predictions
- Advanced visualizations (charts, graphs)
- Integration with external tools (GitHub, Jira)
- Custom metric definitions
- Alert system for anomalies
- Comparative analytics across teams

## Contributing

The analytics system is designed to be extensible. Add new metrics by:

1. Extending the database schema
2. Creating new tracker methods
3. Adding dashboard widgets
4. Implementing export formats

## License

Part of the Isaac project.
