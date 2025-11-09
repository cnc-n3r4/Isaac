"""
Performance Analytics - Phase 3.5 Self-Improving System
Tracks and optimizes system performance metrics for continuous improvement.
"""

import json
import statistics
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from isaac.core.session_manager import SessionManager


@dataclass
class PerformanceMetric:
    """A performance metric measurement."""

    metric_name: str
    timestamp: float
    value: float
    unit: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Alert for performance issues."""

    id: str
    alert_type: str  # 'degradation', 'improvement', 'anomaly'
    metric_name: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    current_value: float
    expected_value: float
    recommendation: str
    created_at: float


class PerformanceAnalytics:
    """
    Tracks and analyzes system performance for optimization.

    Monitors:
    - Command execution times
    - AI response latencies
    - Learning system overhead
    - Pattern matching performance
    - System resource usage
    """

    def __init__(self, session_manager: SessionManager):
        """Initialize performance analytics.

        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager

        self.data_dir = Path.home() / ".isaac" / "performance"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Data files
        self.metrics_file = self.data_dir / "performance_metrics.json"
        self.alerts_file = self.data_dir / "performance_alerts.json"

        # In-memory data structures
        self.recent_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.performance_alerts: List[PerformanceAlert] = []

        # Performance baselines
        self.baselines: Dict[str, float] = {}

        # Load existing data
        self._load_performance_data()
        self._calculate_baselines()

    def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "ms",
        context: Optional[Dict[str, Any]] = None,
    ):
        """Record a performance metric.

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement (ms, seconds, bytes, etc.)
            context: Additional context about the measurement
        """
        metric = PerformanceMetric(
            metric_name=metric_name,
            timestamp=time.time(),
            value=value,
            unit=unit,
            context=context or {},
        )

        self.recent_metrics[metric_name].append(metric)

        # Check for performance issues
        self._check_for_performance_issues(metric)

        # Periodically save metrics
        if len(self.recent_metrics[metric_name]) % 100 == 0:
            self._save_performance_data()

    def record_command_execution(self, command: str, execution_time: float, success: bool):
        """Record command execution performance.

        Args:
            command: The executed command
            execution_time: Time taken to execute (seconds)
            success: Whether command succeeded
        """
        self.record_metric(
            metric_name="command_execution_time",
            value=execution_time * 1000,  # Convert to ms
            unit="ms",
            context={"command": command[:50], "success": success},  # Truncate long commands
        )

        # Track success rate
        success_value = 1.0 if success else 0.0
        self.record_metric(
            metric_name="command_success_rate",
            value=success_value,
            unit="ratio",
            context={"command": command[:50]},
        )

    def record_ai_query(
        self, query_type: str, response_time: float, token_count: Optional[int] = None
    ):
        """Record AI query performance.

        Args:
            query_type: Type of AI query (translation, correction, validation, etc.)
            response_time: Time taken to get response (seconds)
            token_count: Number of tokens in response (if available)
        """
        self.record_metric(
            metric_name=f"ai_{query_type}_latency",
            value=response_time * 1000,  # Convert to ms
            unit="ms",
            context={"query_type": query_type, "tokens": token_count},
        )

        if token_count:
            self.record_metric(
                metric_name=f"ai_{query_type}_tokens",
                value=float(token_count),
                unit="tokens",
                context={"query_type": query_type},
            )

    def record_learning_overhead(self, operation: str, overhead_time: float):
        """Record learning system overhead.

        Args:
            operation: Learning operation (pattern_matching, mistake_tracking, etc.)
            overhead_time: Time overhead (seconds)
        """
        self.record_metric(
            metric_name=f"learning_{operation}_overhead",
            value=overhead_time * 1000,  # Convert to ms
            unit="ms",
            context={"operation": operation},
        )

    def get_metric_statistics(self, metric_name: str, period_minutes: int = 60) -> Dict[str, Any]:
        """Get statistics for a specific metric over a time period.

        Args:
            metric_name: Name of the metric
            period_minutes: Time period to analyze

        Returns:
            Dictionary with metric statistics
        """
        if metric_name not in self.recent_metrics:
            return {"error": "Metric not found"}

        cutoff_time = time.time() - (period_minutes * 60)
        recent_values = [
            m.value for m in self.recent_metrics[metric_name] if m.timestamp > cutoff_time
        ]

        if not recent_values:
            return {"error": "No recent data"}

        return {
            "metric": metric_name,
            "period_minutes": period_minutes,
            "count": len(recent_values),
            "min": min(recent_values),
            "max": max(recent_values),
            "mean": statistics.mean(recent_values),
            "median": statistics.median(recent_values),
            "stdev": statistics.stdev(recent_values) if len(recent_values) > 1 else 0,
            "unit": (
                self.recent_metrics[metric_name][0].unit
                if self.recent_metrics[metric_name]
                else "unknown"
            ),
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary.

        Returns:
            Dictionary with performance overview
        """
        summary = {
            "timestamp": time.time(),
            "metrics": {},
            "alerts": {
                "total": len(self.performance_alerts),
                "critical": sum(1 for a in self.performance_alerts if a.severity == "critical"),
                "high": sum(1 for a in self.performance_alerts if a.severity == "high"),
                "recent": [],
            },
        }

        # Get statistics for key metrics
        key_metrics = [
            "command_execution_time",
            "command_success_rate",
            "ai_translation_latency",
            "learning_pattern_matching_overhead",
        ]

        for metric in key_metrics:
            if metric in self.recent_metrics:
                summary["metrics"][metric] = self.get_metric_statistics(metric, period_minutes=60)

        # Get recent alerts
        recent_alerts = sorted(self.performance_alerts, key=lambda a: a.created_at, reverse=True)[
            :5
        ]

        summary["alerts"]["recent"] = [
            {
                "type": a.alert_type,
                "metric": a.metric_name,
                "severity": a.severity,
                "description": a.description,
                "recommendation": a.recommendation,
            }
            for a in recent_alerts
        ]

        return summary

    def get_optimization_recommendations(self) -> List[str]:
        """Get recommendations for performance optimization.

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        # Analyze command execution performance
        if "command_execution_time" in self.recent_metrics:
            stats = self.get_metric_statistics("command_execution_time", period_minutes=60)
            if stats.get("mean", 0) > 1000:  # >1 second average
                recommendations.append(
                    "High command execution time detected. Consider reviewing "
                    "command complexity or system resources."
                )

        # Analyze AI query latency
        ai_metrics = [k for k in self.recent_metrics.keys() if k.startswith("ai_")]
        for metric in ai_metrics:
            stats = self.get_metric_statistics(metric, period_minutes=60)
            if stats.get("mean", 0) > 2000:  # >2 seconds
                recommendations.append(
                    f"High {metric} detected. Consider using a faster AI provider "
                    f"or reducing query complexity."
                )

        # Analyze learning overhead
        if "learning_pattern_matching_overhead" in self.recent_metrics:
            stats = self.get_metric_statistics(
                "learning_pattern_matching_overhead", period_minutes=60
            )
            if stats.get("mean", 0) > 100:  # >100ms overhead
                recommendations.append(
                    "High learning system overhead. Consider pattern consolidation "
                    "or reducing pattern matching frequency."
                )

        # Analyze success rate
        if "command_success_rate" in self.recent_metrics:
            stats = self.get_metric_statistics("command_success_rate", period_minutes=60)
            if stats.get("mean", 1.0) < 0.8:  # <80% success rate
                recommendations.append(
                    "Low command success rate. Review recent mistakes and consider "
                    "improving command validation or auto-correction."
                )

        # Check for active critical alerts
        critical_alerts = [a for a in self.performance_alerts if a.severity == "critical"]
        if critical_alerts:
            recommendations.append(
                f"{len(critical_alerts)} critical performance alerts active. "
                f"Review alerts for immediate action items."
            )

        if not recommendations:
            recommendations.append("Performance looks good! No optimization needed at this time.")

        return recommendations

    def _check_for_performance_issues(self, metric: PerformanceMetric):
        """Check if a metric indicates a performance issue.

        Args:
            metric: The performance metric to check
        """
        # Only check if we have a baseline
        if metric.metric_name not in self.baselines:
            return

        baseline = self.baselines[metric.metric_name]

        # Check for significant degradation (>50% worse than baseline)
        if metric.value > baseline * 1.5:
            # Check if we already have a recent alert for this
            recent_cutoff = time.time() - 3600  # Last hour
            existing_alert = any(
                a.metric_name == metric.metric_name and a.created_at > recent_cutoff
                for a in self.performance_alerts
            )

            if not existing_alert:
                alert = PerformanceAlert(
                    id=f"alert_{metric.metric_name}_{int(time.time())}",
                    alert_type="degradation",
                    metric_name=metric.metric_name,
                    severity="high" if metric.value > baseline * 2 else "medium",
                    description=f"{metric.metric_name} degraded significantly",
                    current_value=metric.value,
                    expected_value=baseline,
                    recommendation=f"Review recent changes affecting {metric.metric_name}",
                    created_at=time.time(),
                )

                self.performance_alerts.append(alert)
                self._save_alerts()

        # Check for anomalous values (>3 standard deviations)
        if len(self.recent_metrics[metric.metric_name]) > 10:
            recent_values = [m.value for m in list(self.recent_metrics[metric.metric_name])[-100:]]
            mean = statistics.mean(recent_values)
            stdev = statistics.stdev(recent_values) if len(recent_values) > 1 else 0

            if stdev > 0 and abs(metric.value - mean) > 3 * stdev:
                # Anomaly detected
                alert = PerformanceAlert(
                    id=f"anomaly_{metric.metric_name}_{int(time.time())}",
                    alert_type="anomaly",
                    metric_name=metric.metric_name,
                    severity="medium",
                    description=f"Anomalous {metric.metric_name} value detected",
                    current_value=metric.value,
                    expected_value=mean,
                    recommendation="Investigate unusual system behavior or external factors",
                    created_at=time.time(),
                )

                self.performance_alerts.append(alert)
                self._save_alerts()

    def _calculate_baselines(self):
        """Calculate performance baselines from historical data."""
        for metric_name, metrics in self.recent_metrics.items():
            if len(metrics) >= 10:
                values = [m.value for m in metrics]
                # Use median as baseline (more robust than mean)
                self.baselines[metric_name] = statistics.median(values)

    def _load_performance_data(self):
        """Load performance data from disk."""
        # Load metrics (only recent ones to avoid memory issues)
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, "r") as f:
                    data = json.load(f)
                    for metric_name, metric_list in data.items():
                        # Only load last 1000 metrics per type
                        for metric_data in metric_list[-1000:]:
                            metric = PerformanceMetric(**metric_data)
                            self.recent_metrics[metric_name].append(metric)
            except Exception as e:
                print(f"Error loading performance metrics: {e}")

        # Load alerts
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, "r") as f:
                    data = json.load(f)
                    self.performance_alerts = [PerformanceAlert(**alert) for alert in data[-200:]]
            except Exception as e:
                print(f"Error loading performance alerts: {e}")

    def _save_performance_data(self):
        """Save performance data to disk."""
        try:
            # Save metrics
            data = {}
            for metric_name, metrics in self.recent_metrics.items():
                data[metric_name] = [asdict(m) for m in list(metrics)[-1000:]]

            with open(self.metrics_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Error saving performance metrics: {e}")

    def _save_alerts(self):
        """Save performance alerts to disk."""
        try:
            # Keep only last 200 alerts
            data = [asdict(a) for a in self.performance_alerts[-200:]]

            with open(self.alerts_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Error saving performance alerts: {e}")

    def clear_old_alerts(self, age_hours: int = 24):
        """Clear alerts older than specified age.

        Args:
            age_hours: Age threshold in hours
        """
        cutoff_time = time.time() - (age_hours * 3600)
        before_count = len(self.performance_alerts)

        self.performance_alerts = [a for a in self.performance_alerts if a.created_at > cutoff_time]

        after_count = len(self.performance_alerts)
        if before_count > after_count:
            self._save_alerts()

        return before_count - after_count
