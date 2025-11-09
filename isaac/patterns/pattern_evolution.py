"""
Pattern Evolution - Self-improving patterns
Phase 3.4.4: Patterns that learn and improve over time
"""

import json
import statistics
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PatternUsage:
    """Usage statistics for a pattern."""

    pattern_id: str
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    confidence_score: float = 0.0
    execution_time: float = 0.0
    user_feedback: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    applied_to_file: Optional[str] = None
    applied_to_lines: Optional[Tuple[int, int]] = None


@dataclass
class PatternEvolutionMetrics:
    """Evolution metrics for a pattern."""

    pattern_id: str
    total_uses: int = 0
    successful_uses: int = 0
    average_confidence: float = 0.0
    average_execution_time: float = 0.0
    success_rate: float = 0.0
    user_ratings: List[float] = field(default_factory=list)
    average_rating: float = 0.0
    last_used: Optional[float] = None
    first_used: Optional[float] = None
    evolution_score: float = 0.0
    improvement_trend: List[float] = field(default_factory=list)
    feedback_themes: Dict[str, int] = field(default_factory=dict)


@dataclass
class PatternEvolutionRule:
    """A rule for evolving patterns."""

    id: str
    name: str
    description: str
    condition: str  # Python expression to evaluate
    action: str  # What to do when condition is met
    priority: int = 1
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    trigger_count: int = 0


@dataclass
class PatternVariant:
    """A variant of a pattern with evolution data."""

    id: str
    parent_pattern_id: str
    version: int = 1
    changes: Dict[str, Any] = field(default_factory=dict)
    metrics: PatternEvolutionMetrics = field(default_factory=lambda: PatternEvolutionMetrics(""))
    created_at: float = field(default_factory=time.time)
    is_active: bool = True


class PatternEvolutionEngine:
    """Engine for evolving patterns based on usage and feedback."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize pattern evolution engine."""
        self.config = config or {}
        self.usage_history: List[PatternUsage] = []
        self.evolution_metrics: Dict[str, PatternEvolutionMetrics] = {}
        self.evolution_rules: List[PatternEvolutionRule] = []
        self.pattern_variants: Dict[str, List[PatternVariant]] = {}

        # Storage paths
        data_dir_config = self.config.get("data_dir")
        if data_dir_config:
            self.data_dir = Path(data_dir_config)
        else:
            self.data_dir = Path.home() / ".isaac" / "pattern_evolution"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Evolution settings
        self.min_uses_for_evolution = self.config.get("min_uses_for_evolution", 10)
        self.evolution_interval = self.config.get("evolution_interval", 86400)  # 24 hours
        self.max_variants_per_pattern = self.config.get("max_variants_per_pattern", 5)

        # Load data
        self._load_usage_history()
        self._load_evolution_metrics()
        self._load_evolution_rules()
        self._load_pattern_variants()

        # Initialize default evolution rules
        self._initialize_default_rules()

        # Start background evolution
        self.evolution_thread = threading.Thread(target=self._background_evolution, daemon=True)
        self.evolution_thread.start()

    def record_pattern_usage(self, usage: PatternUsage):
        """Record usage of a pattern."""
        self.usage_history.append(usage)

        # Update metrics
        self._update_metrics_for_usage(usage)

        # Save data
        self._save_usage_history()
        self._save_evolution_metrics()

    def get_pattern_metrics(self, pattern_id: str) -> Optional[PatternEvolutionMetrics]:
        """Get evolution metrics for a pattern."""
        return self.evolution_metrics.get(pattern_id)

    def get_pattern_performance_trend(
        self, pattern_id: str, days: int = 30
    ) -> List[Tuple[float, float]]:
        """Get performance trend for a pattern over time."""
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        relevant_usage = [
            u
            for u in self.usage_history
            if u.pattern_id == pattern_id and u.timestamp >= cutoff_time
        ]

        if not relevant_usage:
            return []

        # Group by day
        daily_stats = {}
        for usage in relevant_usage:
            day = datetime.fromtimestamp(usage.timestamp).date()
            if day not in daily_stats:
                daily_stats[day] = {"successes": 0, "total": 0, "confidence_sum": 0.0}

            daily_stats[day]["total"] += 1
            if usage.success:
                daily_stats[day]["successes"] += 1
            daily_stats[day]["confidence_sum"] += usage.confidence_score

        # Convert to trend data
        trend = []
        for day in sorted(daily_stats.keys()):
            stats = daily_stats[day]
            success_rate = stats["successes"] / stats["total"] if stats["total"] > 0 else 0
            avg_confidence = stats["confidence_sum"] / stats["total"] if stats["total"] > 0 else 0
            trend.append(
                (
                    datetime.combine(day, datetime.min.time()).timestamp(),
                    success_rate,
                    avg_confidence,
                )
            )

        return trend

    def suggest_pattern_improvements(self, pattern_id: str) -> List[Dict[str, Any]]:
        """Suggest improvements for a pattern based on usage data."""
        metrics = self.get_pattern_metrics(pattern_id)
        if not metrics or metrics.total_uses < self.min_uses_for_evolution:
            return []

        suggestions = []

        # Analyze success rate
        if metrics.success_rate < 0.7:
            suggestions.append(
                {
                    "type": "success_rate",
                    "severity": "high",
                    "description": f"Pattern has low success rate ({metrics.success_rate:.1%}). Consider reviewing conditions.",
                    "suggested_action": "Review pattern matching conditions and reduce false positives.",
                }
            )

        # Analyze confidence trends
        if len(metrics.improvement_trend) >= 3:
            recent_trend = metrics.improvement_trend[-3:]
            if recent_trend[-1] < recent_trend[0]:
                suggestions.append(
                    {
                        "type": "confidence_trend",
                        "severity": "medium",
                        "description": "Pattern confidence is declining over time.",
                        "suggested_action": "Update pattern to match current code patterns.",
                    }
                )

        # Analyze execution time
        if metrics.average_execution_time > 5.0:  # More than 5 seconds
            suggestions.append(
                {
                    "type": "performance",
                    "severity": "medium",
                    "description": f"Pattern execution is slow ({metrics.average_execution_time:.2f}s average).",
                    "suggested_action": "Optimize pattern matching logic or add caching.",
                }
            )

        # Analyze user feedback
        if metrics.feedback_themes:
            most_common_feedback = max(metrics.feedback_themes.items(), key=lambda x: x[1])
            if most_common_feedback[1] >= 3:  # At least 3 similar feedbacks
                suggestions.append(
                    {
                        "type": "user_feedback",
                        "severity": "medium",
                        "description": f'Common user feedback: "{most_common_feedback[0]}" ({most_common_feedback[1]} times).',
                        "suggested_action": "Address the common feedback in pattern updates.",
                    }
                )

        # Analyze usage patterns
        recent_usage = self._get_recent_usage(pattern_id, days=7)
        if len(recent_usage) < 2:
            suggestions.append(
                {
                    "type": "usage",
                    "severity": "low",
                    "description": "Pattern has low recent usage.",
                    "suggested_action": "Consider if this pattern is still relevant or needs updating.",
                }
            )

        return suggestions

    def create_pattern_variant(
        self, parent_pattern_id: str, changes: Dict[str, Any], reason: str = ""
    ) -> Optional[str]:
        """Create a variant of an existing pattern."""
        if parent_pattern_id not in self.evolution_metrics:
            return None

        # Get existing variants
        variants = self.pattern_variants.get(parent_pattern_id, [])
        if len(variants) >= self.max_variants_per_pattern:
            # Remove oldest inactive variant
            variants.sort(key=lambda v: v.created_at)
            variants = [v for v in variants if v.is_active]
            if len(variants) >= self.max_variants_per_pattern:
                return None

        # Create new variant
        variant_id = str(uuid.uuid4())
        variant = PatternVariant(
            id=variant_id,
            parent_pattern_id=parent_pattern_id,
            version=len(variants) + 1,
            changes=changes,
            metrics=PatternEvolutionMetrics(variant_id),
        )

        variants.append(variant)
        self.pattern_variants[parent_pattern_id] = variants

        self._save_pattern_variants()

        return variant_id

    def get_best_pattern_variant(self, pattern_id: str) -> Optional[PatternVariant]:
        """Get the best performing variant of a pattern."""
        variants = self.pattern_variants.get(pattern_id, [])
        if not variants:
            return None

        # Find variant with highest evolution score
        active_variants = [v for v in variants if v.is_active]
        if not active_variants:
            return None

        return max(active_variants, key=lambda v: v.metrics.evolution_score)

    def evolve_pattern(self, pattern_id: str, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evolve a pattern based on usage data and rules."""
        metrics = self.get_pattern_metrics(pattern_id)
        if not metrics or metrics.total_uses < self.min_uses_for_evolution:
            return pattern_data

        evolved_pattern = pattern_data.copy()

        # Apply evolution rules
        for rule in self.evolution_rules:
            if not rule.enabled:
                continue

            try:
                # Evaluate condition
                condition_met = self._evaluate_evolution_condition(rule.condition, metrics)
                if condition_met:
                    # Apply action
                    evolved_pattern = self._apply_evolution_action(
                        rule.action, evolved_pattern, metrics
                    )
                    rule.trigger_count += 1

            except Exception as e:
                print(f"Error applying evolution rule {rule.id}: {e}")

        # Save updated rules
        self._save_evolution_rules()

        return evolved_pattern

    def analyze_pattern_lifecycle(self, pattern_id: str) -> Dict[str, Any]:
        """Analyze the lifecycle and evolution of a pattern."""
        metrics = self.get_pattern_metrics(pattern_id)
        if not metrics:
            return {}

        variants = self.pattern_variants.get(pattern_id, [])

        lifecycle = {
            "pattern_id": pattern_id,
            "total_uses": metrics.total_uses,
            "success_rate": metrics.success_rate,
            "average_rating": metrics.average_rating,
            "evolution_score": metrics.evolution_score,
            "variants_count": len(variants),
            "active_variants": len([v for v in variants if v.is_active]),
            "first_used": metrics.first_used,
            "last_used": metrics.last_used,
            "usage_trend": self._calculate_usage_trend(pattern_id),
            "performance_trend": self._calculate_performance_trend(pattern_id),
            "recommendations": self.suggest_pattern_improvements(pattern_id),
        }

        # Calculate lifecycle stage
        if metrics.total_uses < 5:
            lifecycle["stage"] = "experimental"
        elif metrics.success_rate >= 0.8 and metrics.average_rating >= 4.0:
            lifecycle["stage"] = "mature"
        elif metrics.success_rate < 0.6:
            lifecycle["stage"] = "problematic"
        else:
            lifecycle["stage"] = "evolving"

        return lifecycle

    def cleanup_old_data(self, days_threshold: int = 365) -> Dict[str, int]:
        """Clean up old usage data and inactive variants."""
        cutoff_time = time.time() - (days_threshold * 24 * 60 * 60)

        # Remove old usage history
        old_usage_count = len([u for u in self.usage_history if u.timestamp < cutoff_time])
        self.usage_history = [u for u in self.usage_history if u.timestamp >= cutoff_time]

        # Remove inactive variants older than threshold
        variants_removed = 0
        for pattern_id, variants in self.pattern_variants.items():
            active_variants = []
            for variant in variants:
                if variant.is_active or variant.created_at >= cutoff_time:
                    active_variants.append(variant)
                else:
                    variants_removed += 1
            self.pattern_variants[pattern_id] = active_variants

        # Save cleaned data
        self._save_usage_history()
        self._save_pattern_variants()

        return {"usage_records_removed": old_usage_count, "variants_removed": variants_removed}

    def export_evolution_data(self, pattern_id: str, file_path: str) -> bool:
        """Export evolution data for a pattern."""
        metrics = self.get_pattern_metrics(pattern_id)
        variants = self.pattern_variants.get(pattern_id, [])
        usage_history = [u for u in self.usage_history if u.pattern_id == pattern_id]

        export_data = {
            "pattern_id": pattern_id,
            "metrics": asdict(metrics) if metrics else None,
            "variants": [asdict(v) for v in variants],
            "usage_history": [asdict(u) for u in usage_history],
            "exported_at": time.time(),
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting evolution data: {e}")
            return False

    def _update_metrics_for_usage(self, usage: PatternUsage):
        """Update evolution metrics for a usage record."""
        pattern_id = usage.pattern_id

        if pattern_id not in self.evolution_metrics:
            self.evolution_metrics[pattern_id] = PatternEvolutionMetrics(pattern_id)

        metrics = self.evolution_metrics[pattern_id]

        # Update basic counters
        metrics.total_uses += 1
        if usage.success:
            metrics.successful_uses += 1

        # Update timestamps
        if metrics.first_used is None:
            metrics.first_used = usage.timestamp
        metrics.last_used = usage.timestamp

        # Update averages
        metrics.average_confidence = self._update_running_average(
            metrics.average_confidence, usage.confidence_score, metrics.total_uses
        )
        metrics.average_execution_time = self._update_running_average(
            metrics.average_execution_time, usage.execution_time, metrics.total_uses
        )

        # Update success rate
        metrics.success_rate = metrics.successful_uses / metrics.total_uses

        # Update user feedback
        if usage.user_feedback:
            self._analyze_user_feedback(usage.user_feedback, metrics)

        # Update evolution score
        metrics.evolution_score = self._calculate_evolution_score(metrics)

        # Track improvement trend (confidence over time)
        metrics.improvement_trend.append(usage.confidence_score)
        if len(metrics.improvement_trend) > 20:  # Keep last 20 data points
            metrics.improvement_trend.pop(0)

    def _analyze_user_feedback(self, feedback: str, metrics: PatternEvolutionMetrics):
        """Analyze user feedback for themes."""
        feedback_lower = feedback.lower()

        # Simple keyword-based theme detection
        themes = {
            "too_broad": ["too broad", "false positive", "wrong match"],
            "too_narrow": ["too narrow", "missed", "not found"],
            "slow": ["slow", "performance", "takes too long"],
            "confusing": ["confusing", "unclear", "hard to understand"],
            "helpful": ["helpful", "good", "useful", "great"],
        }

        for theme, keywords in themes.items():
            if any(keyword in feedback_lower for keyword in keywords):
                metrics.feedback_themes[theme] = metrics.feedback_themes.get(theme, 0) + 1

    def _calculate_evolution_score(self, metrics: PatternEvolutionMetrics) -> float:
        """Calculate overall evolution score for a pattern."""
        if metrics.total_uses == 0:
            return 0.0

        # Weighted combination of factors
        success_weight = 0.4
        confidence_weight = 0.3
        usage_weight = 0.2
        rating_weight = 0.1

        success_score = metrics.success_rate
        confidence_score = min(metrics.average_confidence / 10.0, 1.0)  # Normalize to 0-1
        usage_score = min(metrics.total_uses / 100.0, 1.0)  # Normalize to 0-1
        rating_score = (metrics.average_rating / 5.0) if metrics.average_rating > 0 else 0.5

        evolution_score = (
            success_score * success_weight
            + confidence_score * confidence_weight
            + usage_score * usage_weight
            + rating_score * rating_weight
        )

        return evolution_score

    def _get_recent_usage(self, pattern_id: str, days: int) -> List[PatternUsage]:
        """Get recent usage records for a pattern."""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        return [
            u
            for u in self.usage_history
            if u.pattern_id == pattern_id and u.timestamp >= cutoff_time
        ]

    def _calculate_usage_trend(self, pattern_id: str) -> str:
        """Calculate usage trend for a pattern."""
        recent_usage = self._get_recent_usage(pattern_id, days=30)
        if len(recent_usage) < 7:
            return "insufficient_data"

        # Simple trend analysis
        recent_count = len(recent_usage)
        older_usage = self._get_recent_usage(pattern_id, days=60)[: len(recent_usage)]
        older_count = len(older_usage)

        if recent_count > older_count * 1.2:
            return "increasing"
        elif recent_count < older_count * 0.8:
            return "decreasing"
        else:
            return "stable"

    def _calculate_performance_trend(self, pattern_id: str) -> str:
        """Calculate performance trend for a pattern."""
        metrics = self.get_pattern_metrics(pattern_id)
        if not metrics or len(metrics.improvement_trend) < 5:
            return "insufficient_data"

        # Analyze confidence trend
        recent_avg = statistics.mean(metrics.improvement_trend[-3:])
        earlier_avg = statistics.mean(metrics.improvement_trend[:3])

        if recent_avg > earlier_avg * 1.1:
            return "improving"
        elif recent_avg < earlier_avg * 0.9:
            return "declining"
        else:
            return "stable"

    def _initialize_default_rules(self):
        """Initialize default evolution rules."""
        default_rules = [
            PatternEvolutionRule(
                id="success_rate_boost",
                name="Success Rate Boost",
                description="Increase confidence threshold when success rate is high",
                condition="metrics.success_rate > 0.85 and metrics.total_uses > 20",
                action="increase_confidence_threshold",
            ),
            PatternEvolutionRule(
                id="success_rate_reduction",
                name="Success Rate Reduction",
                description="Decrease confidence threshold when success rate is low",
                condition="metrics.success_rate < 0.6 and metrics.total_uses > 10",
                action="decrease_confidence_threshold",
            ),
            PatternEvolutionRule(
                id="performance_optimization",
                name="Performance Optimization",
                description="Add caching when execution time is high",
                condition="metrics.average_execution_time > 3.0 and metrics.total_uses > 15",
                action="add_performance_optimizations",
            ),
            PatternEvolutionRule(
                id="usage_promotion",
                name="Usage Promotion",
                description="Promote frequently used patterns",
                condition="metrics.total_uses > 50 and metrics.success_rate > 0.75",
                action="promote_pattern",
            ),
        ]

        # Only add rules that don't already exist
        existing_ids = {r.id for r in self.evolution_rules}
        for rule in default_rules:
            if rule.id not in existing_ids:
                self.evolution_rules.append(rule)

        self._save_evolution_rules()

    def _evaluate_evolution_condition(
        self, condition: str, metrics: PatternEvolutionMetrics
    ) -> bool:
        """Evaluate an evolution condition expression."""
        # Create a safe evaluation context
        context = {
            "metrics": metrics,
            "total_uses": metrics.total_uses,
            "success_rate": metrics.success_rate,
            "average_confidence": metrics.average_confidence,
            "average_execution_time": metrics.average_execution_time,
            "average_rating": metrics.average_rating,
        }

        try:
            return eval(condition, {"__builtins__": {}}, context)
        except Exception:
            return False

    def _apply_evolution_action(
        self, action: str, pattern: Dict[str, Any], metrics: PatternEvolutionMetrics
    ) -> Dict[str, Any]:
        """Apply an evolution action to a pattern."""
        evolved_pattern = pattern.copy()

        if action == "increase_confidence_threshold":
            current_threshold = pattern.get("confidence_threshold", 0.5)
            evolved_pattern["confidence_threshold"] = min(current_threshold + 0.1, 0.9)

        elif action == "decrease_confidence_threshold":
            current_threshold = pattern.get("confidence_threshold", 0.5)
            evolved_pattern["confidence_threshold"] = max(current_threshold - 0.1, 0.1)

        elif action == "add_performance_optimizations":
            if "optimizations" not in evolved_pattern:
                evolved_pattern["optimizations"] = []
            evolved_pattern["optimizations"].append("caching")

        elif action == "promote_pattern":
            evolved_pattern["promoted"] = True
            evolved_pattern["promotion_reason"] = "High usage and success rate"

        return evolved_pattern

    def _update_running_average(self, current_avg: float, new_value: float, count: int) -> float:
        """Update a running average with a new value."""
        return current_avg + (new_value - current_avg) / count

    def _background_evolution(self):
        """Background evolution processing."""
        while True:
            try:
                time.sleep(self.evolution_interval)

                # Clean up old data
                cleanup_stats = self.cleanup_old_data()
                if cleanup_stats["usage_records_removed"] > 0:
                    print(f"Cleaned up {cleanup_stats['usage_records_removed']} old usage records")

                # Process pattern evolution
                for pattern_id in list(self.evolution_metrics.keys()):
                    metrics = self.evolution_metrics[pattern_id]
                    if metrics.total_uses >= self.min_uses_for_evolution:
                        # This would trigger evolution logic
                        pass

            except Exception as e:
                print(f"Background evolution error: {e}")
                time.sleep(60)

    def _load_usage_history(self):
        """Load usage history from disk."""
        history_file = self.data_dir / "usage_history.json"
        try:
            if history_file.exists():
                with open(history_file, "r", encoding="utf-8") as f:
                    usage_data = json.load(f)
                    self.usage_history = [PatternUsage(**u) for u in usage_data]
        except Exception as e:
            print(f"Error loading usage history: {e}")

    def _save_usage_history(self):
        """Save usage history to disk."""
        history_file = self.data_dir / "usage_history.json"
        try:
            usage_data = [asdict(u) for u in self.usage_history[-1000:]]  # Keep last 1000 records
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(usage_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving usage history: {e}")

    def _load_evolution_metrics(self):
        """Load evolution metrics from disk."""
        metrics_file = self.data_dir / "evolution_metrics.json"
        try:
            if metrics_file.exists():
                with open(metrics_file, "r", encoding="utf-8") as f:
                    metrics_data = json.load(f)
                    for pattern_id, metrics_dict in metrics_data.items():
                        self.evolution_metrics[pattern_id] = PatternEvolutionMetrics(**metrics_dict)
        except Exception as e:
            print(f"Error loading evolution metrics: {e}")

    def _save_evolution_metrics(self):
        """Save evolution metrics to disk."""
        metrics_file = self.data_dir / "evolution_metrics.json"
        try:
            metrics_data = {pid: asdict(m) for pid, m in self.evolution_metrics.items()}
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving evolution metrics: {e}")

    def _load_evolution_rules(self):
        """Load evolution rules from disk."""
        rules_file = self.data_dir / "evolution_rules.json"
        try:
            if rules_file.exists():
                with open(rules_file, "r", encoding="utf-8") as f:
                    rules_data = json.load(f)
                    self.evolution_rules = [PatternEvolutionRule(**r) for r in rules_data]
        except Exception as e:
            print(f"Error loading evolution rules: {e}")

    def _save_evolution_rules(self):
        """Save evolution rules to disk."""
        rules_file = self.data_dir / "evolution_rules.json"
        try:
            rules_data = [asdict(r) for r in self.evolution_rules]
            with open(rules_file, "w", encoding="utf-8") as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving evolution rules: {e}")

    def _load_pattern_variants(self):
        """Load pattern variants from disk."""
        variants_file = self.data_dir / "pattern_variants.json"
        try:
            if variants_file.exists():
                with open(variants_file, "r", encoding="utf-8") as f:
                    variants_data = json.load(f)
                    for pattern_id, variants_list in variants_data.items():
                        self.pattern_variants[pattern_id] = [
                            PatternVariant(**v) for v in variants_list
                        ]
        except Exception as e:
            print(f"Error loading pattern variants: {e}")

    def _save_pattern_variants(self):
        """Save pattern variants to disk."""
        variants_file = self.data_dir / "pattern_variants.json"
        try:
            variants_data = {}
            for pattern_id, variants in self.pattern_variants.items():
                variants_data[pattern_id] = [asdict(v) for v in variants]
            with open(variants_file, "w", encoding="utf-8") as f:
                json.dump(variants_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving pattern variants: {e}")
