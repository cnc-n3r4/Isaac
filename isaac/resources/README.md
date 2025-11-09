# Resource Optimization Module

## Overview

The Resource Optimization module provides comprehensive monitoring, optimization, and management of system resources in Isaac. This implements **Phase 5.1** of the Isaac roadmap.

## Features

### 1. **Resource Monitoring** (`monitor.py`)
Real-time tracking of system resources:
- **CPU usage** - Current and historical CPU utilization
- **Memory usage** - RAM usage, available memory, swap
- **Disk usage** - Disk space, free space, usage percentage
- **Network I/O** - Network traffic sent/received
- **Process tracking** - Top processes by CPU and memory
- **Background monitoring** - Continuous monitoring in separate thread
- **History tracking** - Configurable history retention (default: 1000 snapshots)

### 2. **Optimization Engine** (`optimizer.py`)
Intelligent analysis and suggestions:
- **Docker cleanup** - Detect dangling images, stopped containers, unused volumes
- **Temp file analysis** - Find large temporary file directories
- **Package cache detection** - Identify bloated pip, npm, apt caches
- **Log file analysis** - Detect large log files needing rotation
- **Browser cache** - Find large browser caches
- **Node modules** - Detect multiple node_modules directories
- **Auto-fixable suggestions** - Provide automated cleanup commands
- **Severity levels** - Critical, high, medium, low priority

### 3. **Cleanup Manager** (`cleanup.py`)
Automated resource cleanup:
- **Docker cleanup** - Remove images, containers, volumes with space tracking
- **Temp file cleanup** - Remove old temporary files (configurable age)
- **Package cache cleanup** - Clear pip, npm, apt caches
- **Cleanup history** - Track all cleanup operations and space freed
- **Safe defaults** - Require confirmation for destructive operations

### 4. **Resource Predictor** (`predictor.py`)
Predict future resource needs:
- **Usage prediction** - Predict CPU/memory/disk usage N minutes ahead
- **Trend analysis** - Linear regression for resource trends
- **Time to limit** - Predict when resources will reach capacity
- **Pattern analysis** - Detect usage patterns and anomalies
- **Confidence scoring** - Provide confidence levels for predictions
- **Capacity planning** - Generate capacity recommendations

### 5. **Cost Tracker** (`cost_tracker.py`)
Track cloud resource costs:
- **Cost tracking** - Record costs by service, provider, resource
- **Budget management** - Set budgets with alert thresholds
- **Cost forecasting** - Predict future costs based on trends
- **Cost breakdown** - Analyze costs by service, provider, time
- **Pricing estimates** - Built-in pricing for AWS, GCP, Azure
- **Export reports** - Generate cost reports in JSON

### 6. **Alert Manager** (`alerts.py`)
Proactive resource alerts:
- **Configurable rules** - Set custom alert thresholds
- **Default rules** - Pre-configured CPU, memory, disk alerts
- **Severity levels** - Info, warning, critical alerts
- **Alert cooldown** - Prevent alert spam with configurable cooldown
- **Auto-resolution** - Automatically resolve alerts when values return to normal
- **Alert history** - Track all alerts with acknowledgment
- **Background monitoring** - Continuous rule checking in separate thread

## Usage

### Command Interface

The `/resources` command provides access to all functionality:

```bash
# Monitor current usage
/resources monitor
/resources monitor --verbose  # Show top processes

# Get optimization suggestions
/resources optimize

# Clean up resources (requires --confirm)
/resources cleanup docker --confirm
/resources cleanup temp --confirm
/resources cleanup cache --confirm
/resources cleanup all --confirm

# Predict future usage
/resources predict cpu --minutes 120
/resources predict memory --ttl  # Show time to limit

# Track costs
/resources costs summary --days 30
/resources costs forecast --days 30
/resources costs trends
/resources costs budgets

# Manage alerts
/resources alerts list
/resources alerts summary
/resources alerts ack <alert_id>
/resources alerts rules

# Background monitoring
/resources start  # Start background monitoring
/resources stop   # Stop background monitoring

# Statistics
/resources stats --minutes 60

# Export data
/resources export ~/resource_data.json
```

### Programmatic Usage

```python
from isaac.resources import (
    ResourceMonitor,
    OptimizationEngine,
    CleanupManager,
    ResourcePredictor,
    CostTracker,
    AlertManager
)

# Monitor resources
monitor = ResourceMonitor()
snapshot = monitor.capture_snapshot()
print(f"CPU: {snapshot.cpu_percent}%")

# Get optimization suggestions
optimizer = OptimizationEngine()
suggestions = optimizer.analyze()
for s in suggestions:
    print(f"{s.title}: {s.potential_savings}")

# Clean up Docker
cleanup = CleanupManager()
result = cleanup.cleanup_docker_images()
print(f"Freed {result.space_freed_mb} MB")

# Predict usage
predictor = ResourcePredictor(monitor)
prediction = predictor.predict_resource_usage('cpu', minutes_ahead=60)
print(f"Predicted CPU in 1 hour: {prediction.predicted_value}%")

# Track costs
tracker = CostTracker()
tracker.add_cost('compute', 'aws', 't2.micro', 'i-123', 0.023, 'hours', 1)
breakdown = tracker.get_cost_breakdown(days=30)
print(f"Total cost: ${breakdown['total_cost']}")

# Set up alerts
alert_mgr = AlertManager(monitor=monitor)
alert_mgr.add_rule(
    rule_id='custom_cpu',
    category='cpu',
    metric='cpu_percent',
    threshold=75.0,
    severity='warning',
    title_template='Custom CPU Alert',
    message_template='CPU at {current_value}%'
)
alert_mgr.start_monitoring()
```

## Architecture

### Data Flow

```
┌─────────────────┐
│ ResourceMonitor │──┐
└─────────────────┘  │
                     ├──> Snapshots ──> History
┌─────────────────┐  │
│  AlertManager   │──┘
└─────────────────┘
         │
         ├──> Check Rules ──> Trigger Alerts
         │
         └──> Callbacks

┌─────────────────┐
│   Predictor     │──> Monitor History ──> Predictions
└─────────────────┘

┌─────────────────┐
│   Optimizer     │──> System Analysis ──> Suggestions
└─────────────────┘

┌─────────────────┐
│    Cleanup      │──> Execute Cleanups ──> Track Results
└─────────────────┘

┌─────────────────┐
│  CostTracker    │──> Cost Entries ──> Analysis/Forecasting
└─────────────────┘
```

### Storage

All components use local JSON storage:
- `~/.isaac/resources/cleanup_history.json` - Cleanup operations
- `~/.isaac/resources/cost_data.json` - Cost tracking
- `~/.isaac/resources/alerts.json` - Alert history and rules

### Background Threads

- **ResourceMonitor** - Optional background monitoring thread (configurable interval)
- **AlertManager** - Background rule checking thread (60s interval by default)

## Testing

Comprehensive integration tests in `tests/resources/test_integration.py`:

```bash
# Run all tests
python tests/resources/test_integration.py

# Test coverage:
# - 28 integration tests
# - All core components tested
# - Command interface tested
# - Edge cases handled
```

## Configuration

### Monitor Settings

```python
monitor = ResourceMonitor(
    history_size=1000,      # Number of snapshots to keep
    monitor_interval=5.0    # Seconds between snapshots
)
```

### Alert Settings

```python
alert_mgr = AlertManager(monitor=monitor)

# Modify existing rule
alert_mgr.disable_rule('cpu_high')
alert_mgr.enable_rule('cpu_high')

# Add custom rule
alert_mgr.add_rule(
    rule_id='custom',
    category='memory',
    metric='memory_percent',
    threshold=85.0,
    comparison='greater',
    severity='critical',
    title_template='Critical Memory',
    message_template='Memory at {current_value}%',
    cooldown_minutes=10
)
```

## Performance

- **Monitoring overhead**: <100ms per snapshot
- **History storage**: ~1KB per snapshot (configurable retention)
- **Background threads**: Minimal CPU usage (<1%)
- **Disk I/O**: JSON writes only on changes

## Dependencies

- **psutil** (7.1.3+) - System and process utilities

## Future Enhancements

Potential improvements for future versions:

1. **Machine Learning Predictions** - Use ML for more accurate resource predictions
2. **Distributed Monitoring** - Monitor multiple machines from central dashboard
3. **Custom Metrics** - Allow user-defined resource metrics
4. **Integration with Cloud APIs** - Direct cloud cost API integration
5. **Visualization** - Real-time graphs and charts
6. **Alerting Integrations** - Slack, email, webhook notifications
7. **Resource Limits** - Automatically enforce resource limits
8. **Auto-scaling** - Trigger scaling based on predictions

## License

Part of the Isaac project.
