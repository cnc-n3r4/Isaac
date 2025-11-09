"""
Resources Command

Comprehensive resource monitoring, optimization, and management.
"""

from typing import Dict, Any

from isaac.resources.monitor import ResourceMonitor
from isaac.resources.optimizer import OptimizationEngine
from isaac.resources.cleanup import CleanupManager
from isaac.resources.predictor import ResourcePredictor
from isaac.resources.cost_tracker import CostTracker
from isaac.resources.alerts import AlertManager
from isaac.core.flag_parser import FlagParser


class ResourcesCommand:
    """
    /resources - Resource optimization and monitoring

    Subcommands:
        monitor         - Show current resource usage
        optimize        - Get optimization suggestions
        cleanup         - Clean up resources
        predict         - Predict future resource usage
        costs           - Track and analyze costs
        alerts          - Manage resource alerts
        start           - Start background monitoring
        stop            - Stop background monitoring
        stats           - Show resource statistics
        export          - Export resource data
    """

    def __init__(self):
        self.monitor = ResourceMonitor(history_size=1000, monitor_interval=5.0)
        self.optimizer = OptimizationEngine()
        self.cleanup = CleanupManager()
        self.predictor = ResourcePredictor(self.monitor)
        self.cost_tracker = CostTracker()
        self.alert_manager = AlertManager(monitor=self.monitor)

        # Don't start monitoring by default - let user control it
        self._monitoring_started = False

    def execute(self, args: str) -> str:
        """Execute the resources command"""
        # Convert string args to list
        if isinstance(args, str):
            args_list = args.split() if args.strip() else []
        else:
            args_list = args

        parser = FlagParser()
        parsed = parser.parse(args_list)

        subcommand = parsed.positional_args[0] if parsed.positional_args else 'monitor'
        subcommand_args = parsed.positional_args[1:] if len(parsed.positional_args) > 1 else []

        # Route to subcommand
        if subcommand == 'monitor':
            return self._cmd_monitor(parsed.flags)
        elif subcommand == 'optimize':
            return self._cmd_optimize(parsed.flags)
        elif subcommand == 'cleanup':
            return self._cmd_cleanup(subcommand_args, parsed.flags)
        elif subcommand == 'predict':
            return self._cmd_predict(subcommand_args, parsed.flags)
        elif subcommand == 'costs':
            return self._cmd_costs(subcommand_args, parsed.flags)
        elif subcommand == 'alerts':
            return self._cmd_alerts(subcommand_args, parsed.flags)
        elif subcommand == 'start':
            return self._cmd_start()
        elif subcommand == 'stop':
            return self._cmd_stop()
        elif subcommand == 'stats':
            return self._cmd_stats(parsed.flags)
        elif subcommand == 'export':
            return self._cmd_export(subcommand_args, parsed.flags)
        else:
            return self._help()

    def _cmd_monitor(self, flags: Dict[str, Any]) -> str:
        """Show current resource usage"""
        state = self.monitor.get_current_state()
        snapshot = state['snapshot']

        output = []
        output.append("=== Current Resource Usage ===\n")

        # CPU
        cpu = snapshot['cpu_percent']
        cpu_bar = self._create_bar(cpu, 100, 40)
        output.append(f"CPU:    {cpu_bar} {cpu:.1f}%")

        # Memory
        mem = snapshot['memory_percent']
        mem_bar = self._create_bar(mem, 100, 40)
        mem_used = snapshot['memory_used_mb'] / 1024
        mem_avail = snapshot['memory_available_mb'] / 1024
        output.append(f"Memory: {mem_bar} {mem:.1f}% ({mem_used:.1f}GB / {mem_used + mem_avail:.1f}GB)")

        # Disk
        disk = snapshot['disk_percent']
        disk_bar = self._create_bar(disk, 100, 40)
        disk_used = snapshot['disk_used_gb']
        disk_free = snapshot['disk_free_gb']
        output.append(f"Disk:   {disk_bar} {disk:.1f}% ({disk_used:.1f}GB / {disk_used + disk_free:.1f}GB)")

        # Network
        net_sent = snapshot['network_sent_mb']
        net_recv = snapshot['network_recv_mb']
        output.append(f"\nNetwork: ↑ {net_sent:.1f}MB  ↓ {net_recv:.1f}MB (since monitoring started)")

        # Load average
        load = snapshot['load_average']
        output.append(f"Load Avg: {load[0]:.2f}, {load[1]:.2f}, {load[2]:.2f}")

        # Processes
        output.append(f"Processes: {snapshot['process_count']}")

        # Top processes if verbose flag
        if flags.get('verbose') or flags.get('v'):
            output.append("\n=== Top CPU Processes ===")
            for proc in state['top_cpu_processes']:
                output.append(f"  {proc['name']:20} PID:{proc['pid']:6} CPU:{proc['cpu_percent']:5.1f}% MEM:{proc['memory_mb']:7.1f}MB")

            output.append("\n=== Top Memory Processes ===")
            for proc in state['top_memory_processes']:
                output.append(f"  {proc['name']:20} PID:{proc['pid']:6} MEM:{proc['memory_mb']:7.1f}MB CPU:{proc['cpu_percent']:5.1f}%")

        return '\n'.join(output)

    def _cmd_optimize(self, flags: Dict[str, Any]) -> str:
        """Get optimization suggestions"""
        output = []
        output.append("=== Analyzing Resources ===\n")

        suggestions = self.optimizer.analyze()

        if not suggestions:
            return "✓ No optimization suggestions - your system looks good!"

        # Group by severity
        critical = [s for s in suggestions if s.severity == 'critical']
        high = [s for s in suggestions if s.severity == 'high']
        medium = [s for s in suggestions if s.severity == 'medium']
        low = [s for s in suggestions if s.severity == 'low']

        # Show summary
        total_savings = self.optimizer.estimate_total_savings()
        output.append(f"Found {len(suggestions)} optimization opportunities")
        output.append(f"Potential savings: ~{total_savings}\n")

        # Show suggestions by severity
        for severity, items in [('Critical', critical), ('High', high), ('Medium', medium), ('Low', low)]:
            if items:
                output.append(f"=== {severity} Priority ===")
                for s in items:
                    icon = "🔴" if severity == "Critical" else "🟡" if severity == "High" else "🟢"
                    output.append(f"\n{icon} {s.title}")
                    output.append(f"   {s.description}")
                    output.append(f"   Savings: {s.potential_savings}")
                    output.append(f"   Action: {s.action}")
                    if s.auto_fixable:
                        output.append(f"   ✓ Can be auto-fixed with: /resources cleanup {s.category}")
                output.append("")

        return '\n'.join(output)

    def _cmd_cleanup(self, args: list, flags: Dict[str, Any]) -> str:
        """Clean up resources"""
        if not args:
            return "Usage: /resources cleanup <docker|temp|cache|all> [--confirm]"

        category = args[0]
        confirm = flags.get('confirm') or flags.get('y')

        if not confirm:
            return "Add --confirm flag to proceed with cleanup (this will delete data)"

        output = []
        output.append("=== Running Cleanup ===\n")

        results = []

        if category == 'docker' or category == 'all':
            output.append("Cleaning Docker resources...")
            docker_results = self.cleanup.cleanup_all_docker()
            results.extend(docker_results)

        if category == 'temp' or category == 'all':
            output.append("Cleaning temporary files...")
            temp_result = self.cleanup.cleanup_temp_files(older_than_days=7)
            results.append(temp_result)

        if category == 'cache' or category == 'all':
            output.append("Cleaning package caches...")
            for pkg_mgr in ['pip', 'npm']:
                cache_result = self.cleanup.cleanup_package_cache(pkg_mgr)
                results.append(cache_result)

        # Show results
        output.append("\n=== Cleanup Results ===\n")

        total_freed = 0
        total_items = 0

        for result in results:
            if result.success:
                icon = "✓"
                total_freed += result.space_freed_mb
                total_items += result.items_cleaned
            else:
                icon = "✗"

            output.append(f"{icon} {result.description}")
            if result.success:
                if result.space_freed_mb > 0:
                    output.append(f"   Freed: {result.space_freed_mb:.1f} MB")
                if result.items_cleaned > 0:
                    output.append(f"   Items: {result.items_cleaned}")
            else:
                output.append(f"   Error: {result.error}")

        output.append(f"\nTotal freed: {total_freed:.1f} MB")
        output.append(f"Total items cleaned: {total_items}")

        return '\n'.join(output)

    def _cmd_predict(self, args: list, flags: Dict[str, Any]) -> str:
        """Predict future resource usage"""
        resource = args[0] if args else 'cpu'
        minutes = int(flags.get('minutes', 60))

        if resource not in ['cpu', 'memory', 'disk']:
            return "Resource must be: cpu, memory, or disk"

        # Ensure we have some data
        if len(self.monitor.history) < 10:
            # Capture a few snapshots
            for _ in range(10):
                self.monitor.capture_snapshot()
                import time
                time.sleep(0.5)

        prediction = self.predictor.predict_resource_usage(resource, minutes)

        if not prediction:
            return "Unable to generate prediction (insufficient data)"

        output = []
        output.append(f"=== {resource.upper()} Prediction ({minutes} minutes ahead) ===\n")

        output.append(f"Predicted value: {prediction.predicted_value:.1f}%")
        output.append(f"Trend: {prediction.trend}")
        output.append(f"Confidence: {prediction.confidence:.1f}%")
        output.append(f"Warning level: {prediction.warning_level}")
        output.append(f"\nRecommendation: {prediction.recommendation}")

        # Show time to limit if requested
        if flags.get('ttl'):
            ttl = self.predictor.predict_time_to_limit(resource, limit_percent=90.0)
            if ttl:
                output.append(f"\n=== Time to 90% Capacity ===")
                if ttl.get('will_reach_limit'):
                    if ttl.get('already_at_limit'):
                        output.append("Already at or above limit")
                    else:
                        hours = ttl.get('hours_to_limit', 0)
                        output.append(f"Estimated: {hours:.1f} hours")
                        output.append(f"Time: {ttl.get('time_to_limit_readable', 'N/A')}")
                else:
                    output.append(ttl.get('reason', 'Will not reach limit'))

        return '\n'.join(output)

    def _cmd_costs(self, args: list, flags: Dict[str, Any]) -> str:
        """Track and analyze costs"""
        subcommand = args[0] if args else 'summary'

        if subcommand == 'summary':
            days = int(flags.get('days', 30))
            breakdown = self.cost_tracker.get_cost_breakdown(days)

            output = []
            output.append(f"=== Cost Summary (Last {days} Days) ===\n")

            output.append(f"Total Cost: ${breakdown['total_cost']:.2f}")
            output.append(f"Entries: {breakdown['entry_count']}")

            if breakdown['by_service']:
                output.append("\n=== By Service ===")
                for service, cost in sorted(breakdown['by_service'].items(), key=lambda x: x[1], reverse=True):
                    output.append(f"  {service:15} ${cost:.2f}")

            if breakdown['by_provider']:
                output.append("\n=== By Provider ===")
                for provider, cost in sorted(breakdown['by_provider'].items(), key=lambda x: x[1], reverse=True):
                    output.append(f"  {provider:15} ${cost:.2f}")

            return '\n'.join(output)

        elif subcommand == 'forecast':
            days = int(flags.get('days', 30))
            forecast = self.cost_tracker.forecast_costs(days)

            output = []
            output.append(f"=== Cost Forecast ({days} Days Ahead) ===\n")

            output.append(f"Average daily cost: ${forecast['avg_daily_cost']:.2f}")
            output.append(f"Forecast total: ${forecast['forecast_total']:.2f}")

            return '\n'.join(output)

        elif subcommand == 'trends':
            trends = self.cost_tracker.get_cost_trends()

            output = []
            output.append("=== Cost Trends ===\n")

            output.append(f"Last 7 days: ${trends['last_7_days']:.2f}")
            output.append(f"Previous 7 days: ${trends['previous_7_days']:.2f}")
            output.append(f"Change: {trends['change_percent']:+.1f}%")
            output.append(f"Trend: {trends['trend']}")
            output.append(f"\nLast 30 days: ${trends['last_30_days']:.2f}")

            return '\n'.join(output)

        elif subcommand == 'budgets':
            alerts = self.cost_tracker.check_budgets()

            if not alerts:
                return "✓ All budgets within limits"

            output = []
            output.append("=== Budget Alerts ===\n")

            for alert in alerts:
                icon = "🔴" if alert['severity'] == 'critical' else "🟡"
                output.append(f"{icon} {alert['budget_name']} ({alert['period']})")
                output.append(f"   Limit: ${alert['limit_usd']:.2f}")
                output.append(f"   Current: ${alert['current_cost']:.2f} ({alert['percent_used']:.1f}%)")
                if alert['over_budget']:
                    output.append(f"   ⚠ OVER BUDGET by ${alert['current_cost'] - alert['limit_usd']:.2f}")

            return '\n'.join(output)

        else:
            return "Usage: /resources costs <summary|forecast|trends|budgets>"

    def _cmd_alerts(self, args: list, flags: Dict[str, Any]) -> str:
        """Manage resource alerts"""
        subcommand = args[0] if args else 'list'

        if subcommand == 'list':
            active = self.alert_manager.get_active_alerts()

            if not active:
                return "✓ No active alerts"

            output = []
            output.append("=== Active Alerts ===\n")

            for alert in active:
                icon = "🔴" if alert.severity == 'critical' else "🟡" if alert.severity == 'warning' else "ℹ️"
                ack = " [ACK]" if alert.acknowledged else ""
                output.append(f"{icon} {alert.title}{ack}")
                output.append(f"   {alert.message}")
                output.append(f"   Category: {alert.category} | Severity: {alert.severity}")
                output.append(f"   ID: {alert.alert_id}")
                output.append("")

            return '\n'.join(output)

        elif subcommand == 'summary':
            summary = self.alert_manager.get_alert_summary()

            output = []
            output.append("=== Alert Summary ===\n")

            output.append(f"Total active: {summary['total_active']}")
            output.append(f"Unacknowledged: {summary['unacknowledged']}")

            output.append("\nBy Severity:")
            for severity, count in summary['by_severity'].items():
                if count > 0:
                    output.append(f"  {severity}: {count}")

            output.append("\nBy Category:")
            for category, count in summary['by_category'].items():
                output.append(f"  {category}: {count}")

            return '\n'.join(output)

        elif subcommand == 'ack':
            if len(args) < 2:
                return "Usage: /resources alerts ack <alert_id>"

            alert_id = args[1]
            if self.alert_manager.acknowledge_alert(alert_id):
                return f"✓ Alert {alert_id} acknowledged"
            else:
                return f"✗ Alert {alert_id} not found"

        elif subcommand == 'rules':
            output = []
            output.append("=== Alert Rules ===\n")

            for rule in self.alert_manager.rules:
                status = "✓" if rule.enabled else "✗"
                output.append(f"{status} {rule.rule_id}")
                output.append(f"   {rule.category}: {rule.metric} {rule.comparison} {rule.threshold}")
                output.append(f"   Severity: {rule.severity} | Cooldown: {rule.cooldown_minutes}min")
                output.append("")

            return '\n'.join(output)

        else:
            return "Usage: /resources alerts <list|summary|ack|rules>"

    def _cmd_start(self) -> str:
        """Start background monitoring"""
        if self._monitoring_started:
            return "✓ Monitoring already running"

        self.monitor.start_monitoring()
        self.alert_manager.start_monitoring(interval=60.0)
        self._monitoring_started = True

        return "✓ Started background resource monitoring"

    def _cmd_stop(self) -> str:
        """Stop background monitoring"""
        if not self._monitoring_started:
            return "✓ Monitoring not running"

        self.monitor.stop_monitoring()
        self.alert_manager.stop_monitoring()
        self._monitoring_started = False

        return "✓ Stopped background resource monitoring"

    def _cmd_stats(self, flags: Dict[str, Any]) -> str:
        """Show resource statistics"""
        minutes = int(flags.get('minutes', 5))

        stats = self.monitor.get_statistics(minutes)

        if 'error' in stats:
            return f"Error: {stats['error']}"

        output = []
        output.append(f"=== Resource Statistics (Last {minutes} Minutes) ===\n")

        output.append("CPU:")
        output.append(f"  Current: {stats['cpu']['current']:.1f}%")
        output.append(f"  Average: {stats['cpu']['average']:.1f}%")
        output.append(f"  Min/Max: {stats['cpu']['min']:.1f}% / {stats['cpu']['max']:.1f}%")

        output.append("\nMemory:")
        output.append(f"  Current: {stats['memory']['current']:.1f}%")
        output.append(f"  Average: {stats['memory']['average']:.1f}%")
        output.append(f"  Min/Max: {stats['memory']['min']:.1f}% / {stats['memory']['max']:.1f}%")

        output.append("\nDisk:")
        output.append(f"  Used: {stats['disk']['used_gb']:.1f} GB")
        output.append(f"  Free: {stats['disk']['free_gb']:.1f} GB")
        output.append(f"  Usage: {stats['disk']['percent']:.1f}%")

        output.append(f"\nSnapshots analyzed: {stats['snapshots_analyzed']}")

        return '\n'.join(output)

    def _cmd_export(self, args: list, flags: Dict[str, Any]) -> str:
        """Export resource data"""
        filepath = args[0] if args else '~/.isaac/resources/export.json'
        filepath = os.path.expanduser(filepath)

        self.monitor.export_history(filepath)

        return f"✓ Exported resource data to {filepath}"

    def _create_bar(self, value: float, max_value: float, width: int = 40) -> str:
        """Create a progress bar"""
        percent = min(100, (value / max_value) * 100)
        filled = int((percent / 100) * width)
        empty = width - filled

        # Color based on percentage
        if percent >= 90:
            bar_char = "█"  # Critical
        elif percent >= 75:
            bar_char = "▓"  # Warning
        else:
            bar_char = "▒"  # Normal

        return f"[{bar_char * filled}{'░' * empty}]"

    def _help(self) -> str:
        """Show help message"""
        return """
=== Resources Command ===

Usage: /resources <subcommand> [options]

Subcommands:
  monitor           Show current resource usage
  optimize          Get optimization suggestions
  cleanup           Clean up resources
    docker          Clean Docker images/containers/volumes
    temp            Clean temporary files
    cache           Clean package caches
    all             Clean everything
  predict           Predict future resource usage
    cpu|memory|disk Resource to predict
    --minutes N     Minutes ahead to predict (default: 60)
    --ttl           Show time to limit
  costs             Track and analyze costs
    summary         Show cost summary
    forecast        Forecast future costs
    trends          Show cost trends
    budgets         Check budget alerts
  alerts            Manage resource alerts
    list            List active alerts
    summary         Show alert summary
    ack <id>        Acknowledge an alert
    rules           List alert rules
  start             Start background monitoring
  stop              Stop background monitoring
  stats             Show resource statistics
    --minutes N     Minutes of history (default: 5)
  export [path]     Export resource data

Flags:
  --verbose, -v     Show detailed information
  --confirm, -y     Confirm destructive actions
  --days N          Number of days for analysis

Examples:
  /resources monitor --verbose
  /resources optimize
  /resources cleanup docker --confirm
  /resources predict cpu --minutes 120 --ttl
  /resources costs summary --days 7
  /resources alerts list
  /resources start
"""


# Import os module for path operations
import os
