"""
Cloud Cost Tracking System

Track and estimate cloud resource costs.
"""

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CostEntry:
    """A cost tracking entry"""

    timestamp: float
    service: str  # 'compute', 'storage', 'network', 'database', etc.
    provider: str  # 'aws', 'gcp', 'azure', 'local', etc.
    resource_type: str  # 'instance', 'disk', 'bandwidth', etc.
    resource_id: str
    cost_usd: float
    units: str  # 'hours', 'gb', 'requests', etc.
    quantity: float
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp_readable"] = datetime.fromtimestamp(self.timestamp).isoformat()
        return data


@dataclass
class Budget:
    """Budget for cost tracking"""

    name: str
    limit_usd: float
    period: str  # 'daily', 'weekly', 'monthly'
    alert_threshold: float  # 0-100 percentage
    services: List[str] = field(default_factory=list)  # Empty means all services

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class CostTracker:
    """
    Track cloud resource costs and budgets

    Features:
    - Track costs by service, provider, resource
    - Budget management with alerts
    - Cost forecasting
    - Cost optimization suggestions
    - Export reports
    """

    # Pricing estimates (USD per unit) - These are rough estimates
    PRICING = {
        "aws": {
            "compute": {
                "t2.micro": 0.0116,  # per hour
                "t2.small": 0.023,
                "t2.medium": 0.0464,
                "m5.large": 0.096,
            },
            "storage": {
                "s3": 0.023,  # per GB/month
                "ebs": 0.10,  # per GB/month
            },
            "network": {
                "data_transfer": 0.09,  # per GB out
            },
        },
        "gcp": {
            "compute": {
                "n1-standard-1": 0.0475,  # per hour
                "n1-standard-2": 0.095,
            },
            "storage": {
                "standard": 0.020,  # per GB/month
            },
        },
        "azure": {
            "compute": {
                "B1S": 0.0104,  # per hour
                "B2S": 0.0416,
            },
            "storage": {
                "standard": 0.0184,  # per GB/month
            },
        },
    }

    def __init__(self, data_file: Optional[str] = None):
        """
        Initialize cost tracker

        Args:
            data_file: Path to JSON file for storing cost data
        """
        if data_file is None:
            data_file = os.path.expanduser("~/.isaac/resources/cost_data.json")

        self.data_file = data_file
        self.entries: List[CostEntry] = []
        self.budgets: List[Budget] = []
        self._load_data()

    def _load_data(self):
        """Load cost data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    data = json.load(f)

                    # Load entries
                    self.entries = [CostEntry(**entry) for entry in data.get("entries", [])]

                    # Load budgets
                    self.budgets = [Budget(**budget) for budget in data.get("budgets", [])]
            except (json.JSONDecodeError, TypeError, KeyError):
                self.entries = []
                self.budgets = []

    def _save_data(self):
        """Save cost data to file"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

        data = {
            "last_updated": datetime.now().isoformat(),
            "entries": [e.to_dict() for e in self.entries],
            "budgets": [b.to_dict() for b in self.budgets],
        }

        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_cost(
        self,
        service: str,
        provider: str,
        resource_type: str,
        resource_id: str,
        cost_usd: float,
        units: str,
        quantity: float,
        tags: Optional[Dict[str, str]] = None,
    ):
        """Add a cost entry"""
        entry = CostEntry(
            timestamp=time.time(),
            service=service,
            provider=provider,
            resource_type=resource_type,
            resource_id=resource_id,
            cost_usd=cost_usd,
            units=units,
            quantity=quantity,
            tags=tags or {},
        )

        self.entries.append(entry)
        self._save_data()

    def estimate_cost(
        self, provider: str, service: str, resource_type: str, quantity: float
    ) -> Optional[float]:
        """
        Estimate cost for a resource

        Args:
            provider: Cloud provider
            service: Service type
            resource_type: Specific resource
            quantity: Quantity (hours, GB, etc.)

        Returns:
            Estimated cost in USD or None if pricing unknown
        """
        try:
            unit_price = self.PRICING[provider][service][resource_type]
            return unit_price * quantity
        except KeyError:
            return None

    def add_budget(
        self,
        name: str,
        limit_usd: float,
        period: str = "monthly",
        alert_threshold: float = 80.0,
        services: Optional[List[str]] = None,
    ):
        """Add a budget"""
        budget = Budget(
            name=name,
            limit_usd=limit_usd,
            period=period,
            alert_threshold=alert_threshold,
            services=services or [],
        )

        self.budgets.append(budget)
        self._save_data()

    def get_costs(
        self, days: int = 30, service: Optional[str] = None, provider: Optional[str] = None
    ) -> List[CostEntry]:
        """
        Get cost entries for a time period

        Args:
            days: Number of days to look back
            service: Filter by service (optional)
            provider: Filter by provider (optional)

        Returns:
            List of CostEntry objects
        """
        cutoff_time = time.time() - (days * 24 * 3600)

        filtered = [e for e in self.entries if e.timestamp >= cutoff_time]

        if service:
            filtered = [e for e in filtered if e.service == service]

        if provider:
            filtered = [e for e in filtered if e.provider == provider]

        return filtered

    def get_total_cost(
        self, days: int = 30, service: Optional[str] = None, provider: Optional[str] = None
    ) -> float:
        """Get total cost for a period"""
        entries = self.get_costs(days, service, provider)
        return sum(e.cost_usd for e in entries)

    def get_cost_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """Get detailed cost breakdown"""
        entries = self.get_costs(days)

        # By service
        by_service: Dict[str, float] = {}
        for entry in entries:
            by_service[entry.service] = by_service.get(entry.service, 0) + entry.cost_usd

        # By provider
        by_provider: Dict[str, float] = {}
        for entry in entries:
            by_provider[entry.provider] = by_provider.get(entry.provider, 0) + entry.cost_usd

        # Daily costs
        daily_costs: Dict[str, float] = {}
        for entry in entries:
            date = datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d")
            daily_costs[date] = daily_costs.get(date, 0) + entry.cost_usd

        return {
            "period_days": days,
            "total_cost": sum(e.cost_usd for e in entries),
            "by_service": by_service,
            "by_provider": by_provider,
            "daily_costs": daily_costs,
            "entry_count": len(entries),
        }

    def check_budgets(self) -> List[Dict[str, Any]]:
        """Check budget status and return alerts"""
        alerts = []

        for budget in self.budgets:
            # Calculate period
            if budget.period == "daily":
                days = 1
            elif budget.period == "weekly":
                days = 7
            else:  # monthly
                days = 30

            # Get costs for services in budget
            total_cost = 0
            for service in budget.services or ["all"]:
                if service == "all":
                    total_cost = self.get_total_cost(days)
                    break
                else:
                    total_cost += self.get_total_cost(days, service=service)

            # Calculate percentage
            percent_used = (total_cost / budget.limit_usd * 100) if budget.limit_usd > 0 else 0

            # Check if over threshold
            if percent_used >= budget.alert_threshold:
                alerts.append(
                    {
                        "budget_name": budget.name,
                        "period": budget.period,
                        "limit_usd": budget.limit_usd,
                        "current_cost": total_cost,
                        "percent_used": percent_used,
                        "alert_threshold": budget.alert_threshold,
                        "over_budget": total_cost > budget.limit_usd,
                        "severity": "critical" if total_cost > budget.limit_usd else "warning",
                    }
                )

        return alerts

    def forecast_costs(self, days_ahead: int = 30) -> Dict[str, Any]:
        """
        Forecast future costs based on historical data

        Args:
            days_ahead: Number of days to forecast

        Returns:
            Dictionary with forecast data
        """
        # Get last 30 days of costs
        historical_entries = self.get_costs(days=30)

        if not historical_entries:
            return {"error": "No historical data available", "forecast": 0}

        # Calculate daily average
        daily_costs: Dict[str, float] = {}
        for entry in historical_entries:
            date = datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d")
            daily_costs[date] = daily_costs.get(date, 0) + entry.cost_usd

        if not daily_costs:
            avg_daily_cost = 0
        else:
            avg_daily_cost = sum(daily_costs.values()) / len(daily_costs)

        # Simple linear forecast
        forecast_total = avg_daily_cost * days_ahead

        return {
            "days_ahead": days_ahead,
            "historical_days": 30,
            "avg_daily_cost": avg_daily_cost,
            "forecast_total": forecast_total,
            "forecast_per_day": avg_daily_cost,
        }

    def get_cost_trends(self) -> Dict[str, Any]:
        """Analyze cost trends"""
        # Compare last 7 days vs previous 7 days
        last_7 = self.get_total_cost(days=7)
        prev_7 = self.get_total_cost(days=14) - last_7

        if prev_7 > 0:
            change_percent = ((last_7 - prev_7) / prev_7) * 100
        else:
            change_percent = 0

        # Monthly trend
        last_30 = self.get_total_cost(days=30)

        return {
            "last_7_days": last_7,
            "previous_7_days": prev_7,
            "change_percent": change_percent,
            "trend": (
                "increasing"
                if change_percent > 5
                else "decreasing" if change_percent < -5 else "stable"
            ),
            "last_30_days": last_30,
        }

    def export_report(self, filepath: str, days: int = 30):
        """Export cost report to JSON"""
        data = {
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "breakdown": self.get_cost_breakdown(days),
            "trends": self.get_cost_trends(),
            "budget_alerts": self.check_budgets(),
            "forecast_30_days": self.forecast_costs(30),
        }

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
