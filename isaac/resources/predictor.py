"""
Resource Prediction System

Predict future resource needs based on historical patterns.
"""

import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ResourcePrediction:
    """Prediction for future resource usage"""

    resource_type: str  # 'cpu', 'memory', 'disk'
    predicted_value: float
    predicted_time: float  # Unix timestamp
    confidence: float  # 0-100
    trend: str  # 'increasing', 'decreasing', 'stable'
    warning_level: str  # 'none', 'low', 'medium', 'high', 'critical'
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["predicted_time_readable"] = datetime.fromtimestamp(self.predicted_time).isoformat()
        return data


class ResourcePredictor:
    """
    Predict future resource usage based on historical patterns

    Features:
    - Trend analysis (linear regression)
    - Seasonality detection
    - Anomaly detection
    - Time-to-limit predictions
    - Capacity planning recommendations
    """

    def __init__(self, monitor=None):
        """
        Initialize resource predictor

        Args:
            monitor: ResourceMonitor instance to get historical data from
        """
        self.monitor = monitor

    def predict_resource_usage(
        self, resource_type: str, minutes_ahead: int = 60
    ) -> Optional[ResourcePrediction]:
        """
        Predict resource usage N minutes into the future

        Args:
            resource_type: 'cpu', 'memory', or 'disk'
            minutes_ahead: How many minutes ahead to predict

        Returns:
            ResourcePrediction or None if insufficient data
        """
        if not self.monitor or not self.monitor.history:
            return None

        # Get historical data
        history = self.monitor.history

        if len(history) < 10:
            return None  # Need at least 10 data points

        # Extract values based on resource type
        if resource_type == "cpu":
            values = [s.cpu_percent for s in history]
            limit = 100.0
        elif resource_type == "memory":
            values = [s.memory_percent for s in history]
            limit = 100.0
        elif resource_type == "disk":
            values = [s.disk_percent for s in history]
            limit = 100.0
        else:
            return None

        timestamps = [s.timestamp for s in history]

        # Calculate trend using simple linear regression
        trend_value, confidence = self._calculate_trend(timestamps, values)

        # Predict future value
        future_timestamp = time.time() + (minutes_ahead * 60)
        current_value = values[-1]
        time_delta = minutes_ahead * 60

        # Simple linear extrapolation
        predicted_value = current_value + (trend_value * time_delta / 3600)  # trend per hour

        # Clamp to reasonable range
        predicted_value = max(0, min(limit, predicted_value))

        # Determine trend direction
        if trend_value > 0.5:
            trend = "increasing"
        elif trend_value < -0.5:
            trend = "decreasing"
        else:
            trend = "stable"

        # Determine warning level
        if predicted_value >= 95:
            warning_level = "critical"
        elif predicted_value >= 85:
            warning_level = "high"
        elif predicted_value >= 75:
            warning_level = "medium"
        elif predicted_value >= 60:
            warning_level = "low"
        else:
            warning_level = "none"

        # Generate recommendation
        recommendation = self._generate_recommendation(
            resource_type, predicted_value, trend, current_value
        )

        return ResourcePrediction(
            resource_type=resource_type,
            predicted_value=predicted_value,
            predicted_time=future_timestamp,
            confidence=confidence,
            trend=trend,
            warning_level=warning_level,
            recommendation=recommendation,
        )

    def _calculate_trend(self, timestamps: List[float], values: List[float]) -> Tuple[float, float]:
        """
        Calculate trend using simple linear regression

        Returns:
            (trend_value per hour, confidence 0-100)
        """
        if len(timestamps) < 2:
            return (0.0, 0.0)

        # Normalize timestamps to hours from first timestamp
        t0 = timestamps[0]
        x = [(t - t0) / 3600 for t in timestamps]  # Hours
        y = values

        n = len(x)

        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        # Calculate slope (trend)
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return (0.0, 0.0)

        slope = numerator / denominator

        # Calculate R-squared for confidence
        y_pred = [x_mean + slope * (x[i] - x_mean) for i in range(n)]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))

        if ss_tot == 0:
            r_squared = 0
        else:
            r_squared = 1 - (ss_res / ss_tot)

        confidence = max(0, min(100, r_squared * 100))

        return (slope, confidence)

    def _generate_recommendation(
        self, resource_type: str, predicted_value: float, trend: str, current_value: float
    ) -> str:
        """Generate recommendation based on prediction"""
        if predicted_value >= 95:
            if resource_type == "cpu":
                return "Critical: CPU usage predicted to reach capacity. Consider scaling horizontally or optimizing code."
            elif resource_type == "memory":
                return "Critical: Memory usage predicted to reach capacity. Check for memory leaks or add more RAM."
            elif resource_type == "disk":
                return "Critical: Disk usage predicted to reach capacity. Clean up files or expand storage."

        elif predicted_value >= 85:
            if resource_type == "cpu":
                return "Warning: High CPU usage predicted. Monitor performance and consider optimization."
            elif resource_type == "memory":
                return "Warning: High memory usage predicted. Review memory-intensive processes."
            elif resource_type == "disk":
                return "Warning: High disk usage predicted. Plan for cleanup or expansion."

        elif trend == "increasing":
            return f"{resource_type.capitalize()} usage is steadily increasing. Monitor trends."

        elif trend == "decreasing":
            return f"{resource_type.capitalize()} usage is decreasing. No action needed."

        else:
            return f"{resource_type.capitalize()} usage is stable. No issues predicted."

    def predict_time_to_limit(
        self, resource_type: str, limit_percent: float = 90.0
    ) -> Optional[Dict[str, Any]]:
        """
        Predict when a resource will reach a certain limit

        Args:
            resource_type: 'cpu', 'memory', or 'disk'
            limit_percent: The limit to predict (default 90%)

        Returns:
            Dictionary with prediction info or None
        """
        if not self.monitor or not self.monitor.history:
            return None

        history = self.monitor.history

        if len(history) < 10:
            return None

        # Get values
        if resource_type == "cpu":
            values = [s.cpu_percent for s in history]
        elif resource_type == "memory":
            values = [s.memory_percent for s in history]
        elif resource_type == "disk":
            values = [s.disk_percent for s in history]
        else:
            return None

        timestamps = [s.timestamp for s in history]

        # Calculate trend
        trend_value, confidence = self._calculate_trend(timestamps, values)

        current_value = values[-1]

        # If trending down or stable, won't reach limit
        if trend_value <= 0:
            return {
                "will_reach_limit": False,
                "reason": "Resource usage is stable or decreasing",
                "current_value": current_value,
                "limit": limit_percent,
            }

        # Calculate hours until limit
        hours_to_limit = (limit_percent - current_value) / trend_value

        if hours_to_limit <= 0:
            return {
                "will_reach_limit": True,
                "already_at_limit": True,
                "current_value": current_value,
                "limit": limit_percent,
            }

        # Convert to timestamp (handle overflow for very large values)
        time_to_limit = time.time() + (hours_to_limit * 3600)

        try:
            time_readable = datetime.fromtimestamp(time_to_limit).isoformat()
        except (OverflowError, OSError, ValueError):
            time_readable = f"More than {hours_to_limit:.0f} hours from now"

        return {
            "will_reach_limit": True,
            "hours_to_limit": hours_to_limit,
            "time_to_limit": time_to_limit,
            "time_to_limit_readable": time_readable,
            "current_value": current_value,
            "limit": limit_percent,
            "trend": trend_value,
            "confidence": confidence,
        }

    def analyze_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze resource usage patterns over recent history

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary with pattern analysis
        """
        if not self.monitor or not self.monitor.history:
            return {"error": "No data available"}

        history = self.monitor.history
        cutoff_time = time.time() - (hours * 3600)
        recent = [s for s in history if s.timestamp >= cutoff_time]

        if not recent:
            return {"error": "Insufficient recent data"}

        # Analyze CPU
        cpu_values = [s.cpu_percent for s in recent]
        cpu_avg = statistics.mean(cpu_values)
        cpu_stdev = statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0

        # Analyze Memory
        mem_values = [s.memory_percent for s in recent]
        mem_avg = statistics.mean(mem_values)
        mem_stdev = statistics.stdev(mem_values) if len(mem_values) > 1 else 0

        # Detect anomalies (values > 2 standard deviations from mean)
        cpu_anomalies = [v for v in cpu_values if abs(v - cpu_avg) > 2 * cpu_stdev]
        mem_anomalies = [v for v in mem_values if abs(v - mem_avg) > 2 * mem_stdev]

        return {
            "period_hours": hours,
            "samples": len(recent),
            "cpu": {
                "average": cpu_avg,
                "std_dev": cpu_stdev,
                "min": min(cpu_values),
                "max": max(cpu_values),
                "anomalies": len(cpu_anomalies),
                "stability": (
                    "stable" if cpu_stdev < 10 else "variable" if cpu_stdev < 25 else "volatile"
                ),
            },
            "memory": {
                "average": mem_avg,
                "std_dev": mem_stdev,
                "min": min(mem_values),
                "max": max(mem_values),
                "anomalies": len(mem_anomalies),
                "stability": (
                    "stable" if mem_stdev < 5 else "variable" if mem_stdev < 15 else "volatile"
                ),
            },
        }

    def get_capacity_recommendations(self) -> List[str]:
        """Get capacity planning recommendations"""
        recommendations = []

        # Predict 1 hour ahead for each resource
        cpu_pred = self.predict_resource_usage("cpu", minutes_ahead=60)
        mem_pred = self.predict_resource_usage("memory", minutes_ahead=60)
        disk_pred = self.predict_resource_usage("disk", minutes_ahead=60)

        if cpu_pred and cpu_pred.warning_level in ["high", "critical"]:
            recommendations.append(f"CPU: {cpu_pred.recommendation}")

        if mem_pred and mem_pred.warning_level in ["high", "critical"]:
            recommendations.append(f"Memory: {mem_pred.recommendation}")

        if disk_pred and disk_pred.warning_level in ["high", "critical"]:
            recommendations.append(f"Disk: {disk_pred.recommendation}")

        # Check time to limits
        for resource in ["cpu", "memory", "disk"]:
            ttl = self.predict_time_to_limit(resource, limit_percent=90.0)
            if ttl and ttl.get("will_reach_limit") and not ttl.get("already_at_limit"):
                hours = ttl.get("hours_to_limit", 0)
                if hours < 24:
                    recommendations.append(
                        f"{resource.capitalize()}: Will reach 90% capacity in {hours:.1f} hours"
                    )

        return recommendations if recommendations else ["All resources within normal limits"]
