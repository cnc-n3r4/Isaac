# 📊 Quick Start - Advanced Analytics

## Installation Complete ✅

The Advanced Analytics system is now fully implemented and ready to use!

## Quick Usage Examples

### 1. View Analytics Summary
```bash
/analytics summary
```

Shows high-level overview of all metrics including productivity, quality, learning, and team stats.

### 2. View Dashboard
```bash
/analytics dashboard overview
```

Interactive dashboard with real-time metrics and visualizations.

### 3. Generate Reports
```bash
# Productivity report (last 7 days)
/analytics productivity 7

# Code quality report (last 14 days)
/analytics quality 14

# Learning analytics (last 30 days)
/analytics learning 30

# Team collaboration report
/analytics team 7
```

### 4. Analyze Code Quality
```bash
/analytics analyze src/main.py
```

Get instant quality metrics for any file.

### 5. Export Reports
```bash
# Export as HTML
/analytics export full html ~/reports/analytics.html

# Export as Markdown
/analytics export productivity markdown ~/reports/productivity.md

# Export as JSON
/analytics export quality json ~/reports/quality.json
```

### 6. Get Insights
```bash
/analytics insights
```

Top actionable insights from your analytics data.

## Python API Usage

```python
from isaac.analytics import AnalyticsManager

# Initialize
manager = AnalyticsManager()

# Track command execution
manager.record_command_execution(
    command_name='build',
    execution_time=5.0,
    success=True,
    estimated_manual_time=30.0
)

# Analyze code
analysis = manager.code_quality.analyze_file('src/main.py')
print(f"Quality Score: {analysis['quality_score']:.1f}%")

# Get summary
summary = manager.get_summary()

# View dashboard
dashboard = manager.get_dashboard('overview')
print(dashboard)

# Export report
manager.export_report(
    report_type='full',
    format='html',
    output_path='report.html'
)
```

## Run Demo

```bash
python examples/analytics_demo.py
```

See all features in action with working examples.

## Documentation

- **Full Documentation**: `isaac/analytics/README.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **Tests**: `tests/test_analytics.py`

## Available Dashboards

- `overview` - High-level view of all metrics
- `productivity` - Productivity and efficiency focus
- `quality` - Code quality metrics
- `learning` - Learning analytics
- `team` - Team collaboration

## Available Reports

- `productivity` - Productivity metrics and time saved
- `quality` - Code quality analysis
- `learning` - Learning and adaptation metrics
- `team` - Team collaboration stats
- `full` - Complete analytics report

## Export Formats

- `json` - Machine-readable data
- `csv` - Spreadsheet-compatible
- `html` - Interactive web report
- `markdown` - Documentation-friendly

## Configuration

Analytics are enabled by default. To configure:

```python
manager = AnalyticsManager()

# Disable tracking
manager.disable()

# Enable tracking
manager.enable()

# Clear old data (90 days)
manager.clear_old_data(days=90)
```

## Storage Location

Analytics data is stored at: `~/.isaac/analytics.db`

## Performance

- Tracking overhead: <100ms per event
- Storage: ~1MB per 10,000 metrics
- Auto-cleanup: After 90 days (configurable)

## Next Steps

1. ✅ Start using `/analytics summary` to see your metrics
2. ✅ Analyze your code with `/analytics analyze <file>`
3. ✅ Export reports with `/analytics export`
4. ✅ Check insights with `/analytics insights`
5. ✅ Explore dashboards with `/analytics dashboard`

## Support

- See full documentation: `isaac/analytics/README.md`
- Run the demo: `python examples/analytics_demo.py`
- Check tests: `python tests/test_analytics.py`

## Features

✅ Productivity tracking
✅ Code quality analysis
✅ Learning analytics
✅ Team collaboration
✅ Custom dashboards
✅ Multi-format exports
✅ Real-time metrics
✅ Comprehensive insights

---

**Phase 5.3 - Advanced Analytics**: 100% Complete ✅

Ready to use! Start tracking your productivity and code quality today.
