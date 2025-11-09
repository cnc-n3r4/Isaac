"""
Cost Optimizer - Advanced budget tracking and cost optimization for AI routing

Features:
- Real-time cost tracking per provider
- Daily/monthly budget management with alerts
- Cost forecasting based on usage patterns
- Automatic provider switching when approaching limits
- Usage analytics and reporting
- Cost history and trending

Part of Phase 3: Enhanced AI Routing
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class CostOptimizer:
    """
    Manages cost tracking and optimization for AI provider usage.

    Tracks costs in real-time, enforces budgets, provides forecasting,
    and suggests optimizations to stay within budget.
    """

    def __init__(self, config_manager=None, storage_path: Optional[Path] = None):
        """
        Initialize the cost optimizer.

        Args:
            config_manager: Optional RoutingConfigManager instance
            storage_path: Optional path for cost tracking data
        """
        # Load configuration
        if config_manager is None:
            from isaac.ai.routing_config import RoutingConfigManager
            self.config_manager = RoutingConfigManager()
        else:
            self.config_manager = config_manager

        # Set storage path
        if storage_path is None:
            storage_path = Path.home() / '.isaac' / 'cost_tracking.json'
        self.storage_path = storage_path

        # Load or initialize cost data
        self.cost_data = self._load_cost_data()

        # Cache for quick access
        self._today = datetime.now().date()
        self._current_month = self._today.strftime('%Y-%m')

    def _load_cost_data(self) -> Dict[str, Any]:
        """Load cost tracking data from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load cost data: {e}")
                return self._initialize_cost_data()
        else:
            return self._initialize_cost_data()

    def _initialize_cost_data(self) -> Dict[str, Any]:
        """Initialize empty cost tracking structure"""
        return {
            'version': '1.0.0',
            'daily_costs': {},      # {date: {provider: cost}}
            'monthly_costs': {},    # {month: {provider: cost}}
            'usage_history': [],    # [{timestamp, provider, tokens, cost, task_type}]
            'alerts': [],           # [{timestamp, type, message}]
            'last_updated': datetime.now().isoformat()
        }

    def _save_cost_data(self) -> None:
        """Save cost tracking data to storage"""
        self.cost_data['last_updated'] = datetime.now().isoformat()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.cost_data, f, indent=2)

    def track_usage(
        self,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        task_type: str = 'unknown',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track a single API usage and calculate cost.

        Args:
            provider: AI provider name
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            task_type: Type of task (for analytics)
            metadata: Optional additional metadata

        Returns:
            Dict with cost information and budget status
        """
        # Get pricing from config
        provider_config = self.config_manager.get_provider_config(provider)
        if not provider_config:
            return {'error': f'Unknown provider: {provider}'}

        pricing = provider_config['pricing']
        input_cost_per_1m = pricing['input_per_1m']
        output_cost_per_1m = pricing['output_per_1m']

        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * output_cost_per_1m
        total_cost = input_cost + output_cost

        # Track in daily/monthly aggregates
        today_str = self._today.isoformat()
        month_str = self._current_month

        # Initialize if needed
        if today_str not in self.cost_data['daily_costs']:
            self.cost_data['daily_costs'][today_str] = {}
        if month_str not in self.cost_data['monthly_costs']:
            self.cost_data['monthly_costs'][month_str] = {}

        # Add to aggregates
        daily_provider_cost = self.cost_data['daily_costs'][today_str].get(provider, 0.0)
        monthly_provider_cost = self.cost_data['monthly_costs'][month_str].get(provider, 0.0)

        self.cost_data['daily_costs'][today_str][provider] = daily_provider_cost + total_cost
        self.cost_data['monthly_costs'][month_str][provider] = monthly_provider_cost + total_cost

        # Add to usage history
        usage_entry = {
            'timestamp': datetime.now().isoformat(),
            'provider': provider,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost,
            'task_type': task_type
        }
        if metadata:
            usage_entry['metadata'] = metadata

        self.cost_data['usage_history'].append(usage_entry)

        # Trim old usage history (keep last 10000 entries)
        if len(self.cost_data['usage_history']) > 10000:
            self.cost_data['usage_history'] = self.cost_data['usage_history'][-10000:]

        # Save data
        self._save_cost_data()

        # Check budget status
        budget_status = self.check_budget_status()

        # Generate alerts if needed
        self._check_and_generate_alerts(budget_status)

        return {
            'cost': total_cost,
            'input_cost': input_cost,
            'output_cost': output_cost,
            'daily_total': sum(self.cost_data['daily_costs'][today_str].values()),
            'monthly_total': sum(self.cost_data['monthly_costs'][month_str].values()),
            'budget_status': budget_status
        }

    def check_budget_status(self) -> Dict[str, Any]:
        """
        Check current budget status against limits.

        Returns:
            Dict with budget information and alerts
        """
        cost_limits = self.config_manager.get_cost_limits()

        if not cost_limits.get('enabled', True):
            return {
                'enabled': False,
                'message': 'Cost limits disabled'
            }

        # Get current totals
        today_str = self._today.isoformat()
        month_str = self._current_month

        daily_total = sum(self.cost_data['daily_costs'].get(today_str, {}).values())
        monthly_total = sum(self.cost_data['monthly_costs'].get(month_str, {}).values())

        # Get limits
        daily_limit = cost_limits.get('daily_limit_usd', 10.0)
        monthly_limit = cost_limits.get('monthly_limit_usd', 100.0)
        alert_threshold = cost_limits.get('alert_threshold', 0.8)

        # Calculate percentages
        daily_pct = (daily_total / daily_limit) * 100 if daily_limit > 0 else 0
        monthly_pct = (monthly_total / monthly_limit) * 100 if monthly_limit > 0 else 0

        # Determine status
        daily_status = self._get_limit_status(daily_pct, alert_threshold * 100)
        monthly_status = self._get_limit_status(monthly_pct, alert_threshold * 100)

        return {
            'enabled': True,
            'daily': {
                'spent': daily_total,
                'limit': daily_limit,
                'remaining': max(0, daily_limit - daily_total),
                'percentage': daily_pct,
                'status': daily_status
            },
            'monthly': {
                'spent': monthly_total,
                'limit': monthly_limit,
                'remaining': max(0, monthly_limit - monthly_total),
                'percentage': monthly_pct,
                'status': monthly_status
            },
            'alert_threshold': alert_threshold,
            'overall_status': daily_status if daily_status != 'ok' else monthly_status
        }

    def _get_limit_status(self, percentage: float, alert_threshold: float) -> str:
        """Determine status based on percentage used"""
        if percentage >= 100:
            return 'exceeded'
        elif percentage >= alert_threshold:
            return 'warning'
        else:
            return 'ok'

    def _check_and_generate_alerts(self, budget_status: Dict[str, Any]) -> None:
        """Generate alerts based on budget status"""
        if not budget_status.get('enabled'):
            return

        alerts = []

        # Check daily budget
        daily = budget_status['daily']
        if daily['status'] == 'exceeded':
            alerts.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'daily_exceeded',
                'severity': 'critical',
                'message': f"Daily budget exceeded! Spent ${daily['spent']:.2f} of ${daily['limit']:.2f}"
            })
        elif daily['status'] == 'warning':
            alerts.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'daily_warning',
                'severity': 'warning',
                'message': f"Daily budget at {daily['percentage']:.1f}%! Spent ${daily['spent']:.2f} of ${daily['limit']:.2f}"
            })

        # Check monthly budget
        monthly = budget_status['monthly']
        if monthly['status'] == 'exceeded':
            alerts.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'monthly_exceeded',
                'severity': 'critical',
                'message': f"Monthly budget exceeded! Spent ${monthly['spent']:.2f} of ${monthly['limit']:.2f}"
            })
        elif monthly['status'] == 'warning':
            alerts.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'monthly_warning',
                'severity': 'warning',
                'message': f"Monthly budget at {monthly['percentage']:.1f}%! Spent ${monthly['spent']:.2f} of ${monthly['limit']:.2f}"
            })

        # Add alerts to history
        for alert in alerts:
            self.cost_data['alerts'].append(alert)

        # Trim old alerts (keep last 1000)
        if len(self.cost_data['alerts']) > 1000:
            self.cost_data['alerts'] = self.cost_data['alerts'][-1000:]

    def can_afford_request(
        self,
        provider: str,
        estimated_tokens: Dict[str, int]
    ) -> Tuple[bool, str]:
        """
        Check if a request can be afforded within budget.

        Args:
            provider: AI provider name
            estimated_tokens: Dict with 'input' and 'output' token estimates

        Returns:
            (can_afford: bool, reason: str)
        """
        cost_limits = self.config_manager.get_cost_limits()

        if not cost_limits.get('enabled', True):
            return (True, 'Cost limits disabled')

        # Estimate cost
        provider_config = self.config_manager.get_provider_config(provider)
        if not provider_config:
            return (False, f'Unknown provider: {provider}')

        pricing = provider_config['pricing']
        estimated_cost = (
            (estimated_tokens['input'] / 1_000_000) * pricing['input_per_1m'] +
            (estimated_tokens['output'] / 1_000_000) * pricing['output_per_1m']
        )

        # Check daily limit
        today_str = self._today.isoformat()
        daily_total = sum(self.cost_data['daily_costs'].get(today_str, {}).values())
        daily_limit = cost_limits.get('daily_limit_usd', 10.0)

        if daily_total + estimated_cost > daily_limit:
            return (False, f'Would exceed daily budget (${daily_total:.2f} + ${estimated_cost:.4f} > ${daily_limit:.2f})')

        # Check monthly limit
        month_str = self._current_month
        monthly_total = sum(self.cost_data['monthly_costs'].get(month_str, {}).values())
        monthly_limit = cost_limits.get('monthly_limit_usd', 100.0)

        if monthly_total + estimated_cost > monthly_limit:
            return (False, f'Would exceed monthly budget (${monthly_total:.2f} + ${estimated_cost:.4f} > ${monthly_limit:.2f})')

        return (True, 'Within budget')

    def suggest_cheaper_provider(
        self,
        complexity: str,
        estimated_tokens: Dict[str, int]
    ) -> Optional[str]:
        """
        Suggest the cheapest provider that can handle the complexity.

        Args:
            complexity: Task complexity level
            estimated_tokens: Token estimates

        Returns:
            Cheapest provider name or None
        """
        enabled_providers = self.config_manager.get_enabled_providers()

        # Get all providers that can handle this complexity
        from isaac.ai.task_analyzer import TaskComplexity
        try:
            TaskComplexity(complexity)
        except ValueError:
            return None

        affordable_providers = []

        for provider in enabled_providers:
            # Check if can afford
            can_afford, _ = self.can_afford_request(provider, estimated_tokens)
            if not can_afford:
                continue

            # Calculate cost
            provider_config = self.config_manager.get_provider_config(provider)
            if not provider_config:
                continue

            pricing = provider_config['pricing']
            cost = (
                (estimated_tokens['input'] / 1_000_000) * pricing['input_per_1m'] +
                (estimated_tokens['output'] / 1_000_000) * pricing['output_per_1m']
            )

            affordable_providers.append((provider, cost))

        if not affordable_providers:
            return None

        # Sort by cost and return cheapest
        affordable_providers.sort(key=lambda x: x[1])
        return affordable_providers[0][0]

    def get_cost_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate cost report for the last N days.

        Args:
            days: Number of days to include

        Returns:
            Detailed cost report
        """
        report = {
            'period_days': days,
            'start_date': (self._today - timedelta(days=days-1)).isoformat(),
            'end_date': self._today.isoformat(),
            'daily_breakdown': [],
            'provider_totals': defaultdict(float),
            'task_type_totals': defaultdict(float),
            'total_cost': 0.0,
            'total_tokens': 0,
            'alerts': []
        }

        # Collect daily data
        for i in range(days):
            date = (self._today - timedelta(days=i)).isoformat()
            daily_data = self.cost_data['daily_costs'].get(date, {})

            daily_total = sum(daily_data.values())
            report['total_cost'] += daily_total

            report['daily_breakdown'].append({
                'date': date,
                'costs': daily_data,
                'total': daily_total
            })

            # Aggregate by provider
            for provider, cost in daily_data.items():
                report['provider_totals'][provider] += cost

        # Analyze usage history
        start_time = datetime.now() - timedelta(days=days)

        for entry in reversed(self.cost_data['usage_history']):
            entry_time = datetime.fromisoformat(entry['timestamp'])
            if entry_time < start_time:
                break

            report['total_tokens'] += entry['total_tokens']
            report['task_type_totals'][entry['task_type']] += entry['total_cost']

        # Recent alerts
        recent_alerts = [
            alert for alert in self.cost_data['alerts']
            if datetime.fromisoformat(alert['timestamp']) >= start_time
        ]
        report['alerts'] = recent_alerts[-10:]  # Last 10 alerts

        # Convert defaultdicts to regular dicts
        report['provider_totals'] = dict(report['provider_totals'])
        report['task_type_totals'] = dict(report['task_type_totals'])

        # Reverse daily breakdown (oldest first)
        report['daily_breakdown'].reverse()

        return report

    def forecast_monthly_cost(self) -> Dict[str, Any]:
        """
        Forecast monthly cost based on current usage patterns.

        Returns:
            Forecast with projections
        """
        month_str = self._current_month
        monthly_data = self.cost_data['monthly_costs'].get(month_str, {})
        monthly_total = sum(monthly_data.values())

        # Calculate days in month and days elapsed
        today = datetime.now()
        days_in_month = (datetime(today.year, today.month + 1, 1) - timedelta(days=1)).day if today.month < 12 else 31
        days_elapsed = today.day

        # Simple linear projection
        if days_elapsed > 0:
            daily_avg = monthly_total / days_elapsed
            projected_total = daily_avg * days_in_month
        else:
            projected_total = 0.0

        cost_limits = self.config_manager.get_cost_limits()
        monthly_limit = cost_limits.get('monthly_limit_usd', 100.0)

        return {
            'month': month_str,
            'days_elapsed': days_elapsed,
            'days_remaining': days_in_month - days_elapsed,
            'current_spend': monthly_total,
            'daily_average': monthly_total / days_elapsed if days_elapsed > 0 else 0,
            'projected_total': projected_total,
            'monthly_limit': monthly_limit,
            'projected_overage': max(0, projected_total - monthly_limit),
            'on_track': projected_total <= monthly_limit,
            'provider_breakdown': monthly_data
        }

    def reset_period(self, period: str = 'daily') -> None:
        """
        Reset cost tracking for a period (for testing/admin).

        Args:
            period: 'daily' or 'monthly'
        """
        if period == 'daily':
            today_str = self._today.isoformat()
            if today_str in self.cost_data['daily_costs']:
                self.cost_data['daily_costs'][today_str] = {}
        elif period == 'monthly':
            month_str = self._current_month
            if month_str in self.cost_data['monthly_costs']:
                self.cost_data['monthly_costs'][month_str] = {}

        self._save_cost_data()

    def get_recent_alerts(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent cost alerts"""
        return self.cost_data['alerts'][-count:]

    def clear_old_data(self, days_to_keep: int = 90) -> None:
        """
        Clear old cost tracking data.

        Args:
            days_to_keep: Number of days of data to retain
        """
        cutoff_date = (self._today - timedelta(days=days_to_keep)).isoformat()

        # Clean daily costs
        self.cost_data['daily_costs'] = {
            date: costs for date, costs in self.cost_data['daily_costs'].items()
            if date >= cutoff_date
        }

        # Clean usage history
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        self.cost_data['usage_history'] = [
            entry for entry in self.cost_data['usage_history']
            if datetime.fromisoformat(entry['timestamp']) >= cutoff_time
        ]

        # Clean alerts
        self.cost_data['alerts'] = [
            alert for alert in self.cost_data['alerts']
            if datetime.fromisoformat(alert['timestamp']) >= cutoff_time
        ]

        self._save_cost_data()
