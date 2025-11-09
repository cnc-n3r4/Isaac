"""
Resource Alert Manager

Monitor resources and trigger alerts when thresholds are exceeded.
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os


@dataclass
class Alert:
    """Resource alert"""
    alert_id: str
    timestamp: float
    severity: str  # 'info', 'warning', 'critical'
    category: str  # 'cpu', 'memory', 'disk', 'network', 'cost'
    title: str
    message: str
    threshold: float
    current_value: float
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp_readable'] = datetime.fromtimestamp(self.timestamp).isoformat()
        if self.resolved_at:
            data['resolved_at_readable'] = datetime.fromtimestamp(self.resolved_at).isoformat()
        return data


@dataclass
class AlertRule:
    """Rule for triggering alerts"""
    rule_id: str
    category: str
    metric: str  # 'cpu_percent', 'memory_percent', 'disk_percent', etc.
    threshold: float
    comparison: str  # 'greater', 'less', 'equal'
    severity: str
    title_template: str
    message_template: str
    enabled: bool = True
    cooldown_minutes: int = 5  # Don't re-alert within this period

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class AlertManager:
    """
    Manage resource alerts and notifications

    Features:
    - Configurable alert rules
    - Alert history
    - Alert acknowledgment
    - Auto-resolution when values return to normal
    - Callbacks for alert notifications
    - Alert cooldown to prevent spam
    """

    def __init__(self, data_file: Optional[str] = None, monitor=None):
        """
        Initialize alert manager

        Args:
            data_file: Path to JSON file for storing alert data
            monitor: ResourceMonitor instance to monitor
        """
        if data_file is None:
            data_file = os.path.expanduser('~/.isaac/resources/alerts.json')

        self.data_file = data_file
        self.monitor = monitor
        self.alerts: List[Alert] = []
        self.rules: List[AlertRule] = []
        self.callbacks: List[Callable[[Alert], None]] = []
        self._last_alert_times: Dict[str, float] = {}
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None

        self._load_data()
        self._create_default_rules()

    def _load_data(self):
        """Load alert data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)

                    # Load alerts
                    self.alerts = [
                        Alert(**alert) for alert in data.get('alerts', [])
                    ]

                    # Load rules
                    self.rules = [
                        AlertRule(**rule) for rule in data.get('rules', [])
                    ]
            except (json.JSONDecodeError, TypeError, KeyError):
                self.alerts = []
                self.rules = []

    def _save_data(self):
        """Save alert data to file"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

        data = {
            'last_updated': datetime.now().isoformat(),
            'alerts': [a.to_dict() for a in self.alerts],
            'rules': [r.to_dict() for r in self.rules]
        }

        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _create_default_rules(self):
        """Create default alert rules if none exist"""
        if self.rules:
            return  # Already have rules

        default_rules = [
            AlertRule(
                rule_id='cpu_high',
                category='cpu',
                metric='cpu_percent',
                threshold=80.0,
                comparison='greater',
                severity='warning',
                title_template='High CPU Usage',
                message_template='CPU usage is at {current_value:.1f}% (threshold: {threshold}%)'
            ),
            AlertRule(
                rule_id='cpu_critical',
                category='cpu',
                metric='cpu_percent',
                threshold=95.0,
                comparison='greater',
                severity='critical',
                title_template='Critical CPU Usage',
                message_template='CPU usage is at {current_value:.1f}% (threshold: {threshold}%)'
            ),
            AlertRule(
                rule_id='memory_high',
                category='memory',
                metric='memory_percent',
                threshold=80.0,
                comparison='greater',
                severity='warning',
                title_template='High Memory Usage',
                message_template='Memory usage is at {current_value:.1f}% (threshold: {threshold}%)'
            ),
            AlertRule(
                rule_id='memory_critical',
                category='memory',
                metric='memory_percent',
                threshold=95.0,
                comparison='greater',
                severity='critical',
                title_template='Critical Memory Usage',
                message_template='Memory usage is at {current_value:.1f}% (threshold: {threshold}%)'
            ),
            AlertRule(
                rule_id='disk_high',
                category='disk',
                metric='disk_percent',
                threshold=85.0,
                comparison='greater',
                severity='warning',
                title_template='High Disk Usage',
                message_template='Disk usage is at {current_value:.1f}% (threshold: {threshold}%)'
            ),
            AlertRule(
                rule_id='disk_critical',
                category='disk',
                metric='disk_percent',
                threshold=95.0,
                comparison='greater',
                severity='critical',
                title_template='Critical Disk Usage',
                message_template='Disk usage is at {current_value:.1f}% (threshold: {threshold}%)'
            ),
        ]

        self.rules.extend(default_rules)
        self._save_data()

    def add_rule(
        self,
        rule_id: str,
        category: str,
        metric: str,
        threshold: float,
        severity: str,
        title_template: str,
        message_template: str,
        comparison: str = 'greater',
        cooldown_minutes: int = 5
    ):
        """Add a new alert rule"""
        rule = AlertRule(
            rule_id=rule_id,
            category=category,
            metric=metric,
            threshold=threshold,
            comparison=comparison,
            severity=severity,
            title_template=title_template,
            message_template=message_template,
            cooldown_minutes=cooldown_minutes
        )

        self.rules.append(rule)
        self._save_data()

    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule"""
        original_len = len(self.rules)
        self.rules = [r for r in self.rules if r.rule_id != rule_id]

        if len(self.rules) < original_len:
            self._save_data()
            return True
        return False

    def enable_rule(self, rule_id: str):
        """Enable an alert rule"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.enabled = True
                self._save_data()
                return True
        return False

    def disable_rule(self, rule_id: str):
        """Disable an alert rule"""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.enabled = False
                self._save_data()
                return True
        return False

    def check_rules(self):
        """Check all rules against current state"""
        if not self.monitor:
            return

        # Get current snapshot
        snapshot = self.monitor.capture_snapshot()

        # Check each rule
        for rule in self.rules:
            if not rule.enabled:
                continue

            # Get current value
            current_value = getattr(snapshot, rule.metric, None)
            if current_value is None:
                continue

            # Check if rule is triggered
            triggered = False
            if rule.comparison == 'greater':
                triggered = current_value > rule.threshold
            elif rule.comparison == 'less':
                triggered = current_value < rule.threshold
            elif rule.comparison == 'equal':
                triggered = abs(current_value - rule.threshold) < 0.01

            if triggered:
                # Check cooldown
                last_alert_time = self._last_alert_times.get(rule.rule_id, 0)
                if time.time() - last_alert_time < (rule.cooldown_minutes * 60):
                    continue  # Still in cooldown

                # Create alert
                alert = Alert(
                    alert_id=f"{rule.rule_id}_{int(time.time())}",
                    timestamp=time.time(),
                    severity=rule.severity,
                    category=rule.category,
                    title=rule.title_template,
                    message=rule.message_template.format(
                        current_value=current_value,
                        threshold=rule.threshold
                    ),
                    threshold=rule.threshold,
                    current_value=current_value
                )

                self.alerts.append(alert)
                self._last_alert_times[rule.rule_id] = time.time()
                self._save_data()

                # Trigger callbacks
                for callback in self.callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        print(f"Error in alert callback: {e}")

            else:
                # Check if we should auto-resolve previous alerts
                for alert in self.alerts:
                    if (alert.category == rule.category and
                        not alert.resolved and
                        alert.current_value > rule.threshold and
                        current_value <= rule.threshold):

                        alert.resolved = True
                        alert.resolved_at = time.time()
                        self._save_data()

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self._save_data()
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Manually resolve an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = time.time()
                self._save_data()
                return True
        return False

    def get_active_alerts(self, category: Optional[str] = None) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        active = [a for a in self.alerts if not a.resolved]

        if category:
            active = [a for a in active if a.category == category]

        return active

    def get_alerts(
        self,
        hours: int = 24,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        include_resolved: bool = True
    ) -> List[Alert]:
        """Get alerts from recent history"""
        cutoff_time = time.time() - (hours * 3600)

        alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]

        if not include_resolved:
            alerts = [a for a in alerts if not a.resolved]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if category:
            alerts = [a for a in alerts if a.category == category]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alert state"""
        active_alerts = self.get_active_alerts()

        by_severity = {
            'critical': len([a for a in active_alerts if a.severity == 'critical']),
            'warning': len([a for a in active_alerts if a.severity == 'warning']),
            'info': len([a for a in active_alerts if a.severity == 'info']),
        }

        by_category: Dict[str, int] = {}
        for alert in active_alerts:
            by_category[alert.category] = by_category.get(alert.category, 0) + 1

        return {
            'total_active': len(active_alerts),
            'by_severity': by_severity,
            'by_category': by_category,
            'unacknowledged': len([a for a in active_alerts if not a.acknowledged])
        }

    def register_callback(self, callback: Callable[[Alert], None]):
        """Register callback to be called when alerts are triggered"""
        self.callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[Alert], None]):
        """Unregister callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def start_monitoring(self, interval: float = 60.0):
        """
        Start background monitoring thread

        Args:
            interval: Seconds between checks
        """
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop background monitoring thread"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)

    def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                self.check_rules()
                time.sleep(interval)
            except Exception as e:
                print(f"Error in alert monitor loop: {e}")
                time.sleep(interval)

    def clear_old_alerts(self, days: int = 7):
        """Clear resolved alerts older than specified days"""
        cutoff_time = time.time() - (days * 24 * 3600)

        original_len = len(self.alerts)
        self.alerts = [
            a for a in self.alerts
            if not a.resolved or a.timestamp >= cutoff_time
        ]

        if len(self.alerts) < original_len:
            self._save_data()
            return original_len - len(self.alerts)

        return 0
