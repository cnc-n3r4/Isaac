"""
Continuous Learning Coordinator - Phase 3.5 Self-Improving System
Orchestrates all learning components for seamless continuous improvement.
"""

import time
import threading
from typing import Dict, Any
import logging

from isaac.core.session_manager import SessionManager


class ContinuousLearningCoordinator:
    """
    Coordinates all learning components for continuous improvement.

    This coordinator ensures all learning systems work together harmoniously:
    - Mistake learning feeds into behavior adjustments
    - User preferences inform personalized suggestions
    - Metrics track overall learning health
    - Background processes maintain learning momentum
    """

    def __init__(self, session_manager: SessionManager):
        """Initialize the continuous learning coordinator.

        Args:
            session_manager: Session manager with learning components
        """
        self.session_manager = session_manager
        self.logger = logging.getLogger(__name__)

        # Get learning components from session manager
        self.mistake_learner = session_manager.mistake_learner
        self.behavior_engine = session_manager.behavior_engine
        self.metrics_dashboard = session_manager.metrics_dashboard
        self.preference_learner = session_manager.preference_learner

        # Coordination state
        self.learning_cycle_count = 0
        self.last_optimization = time.time()
        self.last_metrics_generation = time.time()

        # Background coordination thread
        self._stop_coordination = False
        self.coordination_thread = None

        # Configuration
        self.config = {
            'optimization_interval': 3600,  # 1 hour
            'metrics_interval': 1800,  # 30 minutes
            'pattern_consolidation_threshold': 20,  # Consolidate when >20 patterns
            'learning_health_threshold': 40.0,  # Alert when health <40
        }

    def start(self):
        """Start continuous learning coordination."""
        if self.coordination_thread and self.coordination_thread.is_alive():
            self.logger.warning("Continuous learning already running")
            return

        self._stop_coordination = False
        self.coordination_thread = threading.Thread(
            target=self._coordination_loop,
            daemon=True,
            name="ContinuousLearningCoordinator"
        )
        self.coordination_thread.start()
        self.logger.info("Continuous learning coordinator started")

    def stop(self):
        """Stop continuous learning coordination."""
        self._stop_coordination = True
        if self.coordination_thread and self.coordination_thread.is_alive():
            self.coordination_thread.join(timeout=5.0)
        self.logger.info("Continuous learning coordinator stopped")

    def _coordination_loop(self):
        """Main coordination loop running in background."""
        while not self._stop_coordination:
            try:
                # Sleep for a while between coordination cycles
                time.sleep(300)  # 5 minutes

                if self._stop_coordination:
                    break

                # Run coordination tasks
                self._run_coordination_cycle()

            except Exception as e:
                self.logger.error(f"Coordination cycle error: {e}")
                time.sleep(60)  # Wait a minute before retrying

    def _run_coordination_cycle(self):
        """Run a single coordination cycle."""
        self.learning_cycle_count += 1
        current_time = time.time()

        # Generate metrics periodically
        if current_time - self.last_metrics_generation > self.config['metrics_interval']:
            self._generate_and_analyze_metrics()
            self.last_metrics_generation = current_time

        # Run optimization periodically
        if current_time - self.last_optimization > self.config['optimization_interval']:
            self._run_learning_optimization()
            self.last_optimization = current_time

        # Check learning health
        self._check_learning_health()

        # Consolidate patterns if needed
        self._consolidate_patterns_if_needed()

        # Sync cross-component insights
        self._sync_cross_component_insights()

    def _generate_and_analyze_metrics(self):
        """Generate metrics and analyze learning progress."""
        if not self.metrics_dashboard:
            return

        try:
            # Generate current metrics
            metrics = self.metrics_dashboard.generate_current_metrics(period_days=7)

            self.logger.info(
                f"Learning health: {metrics.learning_health_score:.1f}/100 | "
                f"Patterns: {metrics.learning_patterns} | "
                f"Rate: {metrics.learning_rate:.1%}"
            )

            # Check for concerning trends
            if len(metrics.improvement_trend) >= 3:
                recent_trend = metrics.improvement_trend[-3:]
                if all(recent_trend[i] < recent_trend[i-1] for i in range(1, len(recent_trend))):
                    self.logger.warning("Learning health declining - review needed")

        except Exception as e:
            self.logger.error(f"Failed to generate metrics: {e}")

    def _run_learning_optimization(self):
        """Optimize learning systems for better performance."""
        try:
            # Trigger pattern learning from accumulated mistakes
            if self.mistake_learner:
                mistake_types = ['command_error', 'command_typo', 'ai_response']
                patterns_learned = 0

                for mistake_type in mistake_types:
                    pattern = self.mistake_learner.learn_from_mistakes(mistake_type)
                    if pattern:
                        patterns_learned += 1

                if patterns_learned > 0:
                    self.logger.info(f"Learned {patterns_learned} new patterns during optimization")

            # Analyze behavior effectiveness
            if self.behavior_engine:
                effectiveness = self.behavior_engine.analyze_behavior_effectiveness()
                if effectiveness.get('total_adjustments', 0) > 0:
                    self.logger.debug(f"Behavior adjustments: {effectiveness['total_adjustments']}")

        except Exception as e:
            self.logger.error(f"Learning optimization failed: {e}")

    def _check_learning_health(self):
        """Check overall learning health and alert if issues found."""
        if not self.metrics_dashboard:
            return

        try:
            summary = self.metrics_dashboard.get_dashboard_summary()
            health = summary.get('current_health_score', 0)

            if health < self.config['learning_health_threshold']:
                self.logger.warning(
                    f"Low learning health: {health:.1f}/100 - "
                    f"Consider increasing user interactions or reviewing patterns"
                )

                # Get insights for low health
                insights = self.metrics_dashboard.get_learning_insights(priority='high', limit=3)
                for insight in insights:
                    self.logger.info(f"Insight: {insight.title} - {insight.recommendation}")

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")

    def _consolidate_patterns_if_needed(self):
        """Consolidate similar patterns to prevent pattern explosion."""
        if not self.mistake_learner:
            return

        try:
            pattern_count = len(self.mistake_learner.learning_patterns)

            if pattern_count > self.config['pattern_consolidation_threshold']:
                self.logger.info(f"Pattern consolidation needed: {pattern_count} patterns")

                # Group patterns by type
                pattern_groups = {}
                for pattern_id, pattern in self.mistake_learner.learning_patterns.items():
                    if pattern.mistake_type not in pattern_groups:
                        pattern_groups[pattern.mistake_type] = []
                    pattern_groups[pattern.mistake_type].append((pattern_id, pattern))

                # For each type, keep only high-confidence patterns
                for mistake_type, patterns in pattern_groups.items():
                    if len(patterns) > 10:  # More than 10 patterns of same type
                        # Sort by confidence and keep top 5
                        patterns.sort(key=lambda x: x[1].confidence, reverse=True)
                        to_keep = [p[0] for p in patterns[:5]]
                        to_remove = [p[0] for p in patterns[5:] if p[1].confidence < 0.5]

                        for pattern_id in to_remove:
                            del self.mistake_learner.learning_patterns[pattern_id]

                        if to_remove:
                            self.logger.info(
                                f"Consolidated {mistake_type} patterns: "
                                f"removed {len(to_remove)} low-confidence patterns"
                            )

                # Save consolidated patterns
                self.mistake_learner._save_patterns()

        except Exception as e:
            self.logger.error(f"Pattern consolidation failed: {e}")

    def _sync_cross_component_insights(self):
        """Sync insights across learning components."""
        try:
            # Share user preferences with behavior engine
            if self.preference_learner and self.behavior_engine:
                prefs = self.preference_learner.user_preferences
                if prefs:
                    # Check if communication style preference conflicts with behavior profile
                    comm_style_prefs = prefs.get_top_preferences('communication_style', limit=1)
                    if comm_style_prefs:
                        pref_style = comm_style_prefs[0][1].preference_value
                        behavior_style = self.behavior_engine.behavior_profile.response_style

                        # If strong preference conflicts with behavior, adjust
                        if comm_style_prefs[0][1].confidence > 0.8:
                            if pref_style != behavior_style:
                                self.logger.debug(
                                    f"Syncing communication style: {behavior_style} → {pref_style}"
                                )

            # Share high-confidence patterns with metrics for better recommendations
            if self.mistake_learner and self.metrics_dashboard:
                high_conf_patterns = [
                    p for p in self.mistake_learner.learning_patterns.values()
                    if p.confidence > 0.8
                ]
                if len(high_conf_patterns) > 5:
                    self.logger.debug(f"Found {len(high_conf_patterns)} high-confidence patterns")

        except Exception as e:
            self.logger.error(f"Cross-component sync failed: {e}")

    def get_coordination_status(self) -> Dict[str, Any]:
        """Get current coordination status.

        Returns:
            Dictionary with coordination statistics
        """
        return {
            'active': self.coordination_thread and self.coordination_thread.is_alive(),
            'learning_cycles': self.learning_cycle_count,
            'last_optimization': time.time() - self.last_optimization,
            'last_metrics': time.time() - self.last_metrics_generation,
            'components': {
                'mistake_learner': self.mistake_learner is not None,
                'behavior_engine': self.behavior_engine is not None,
                'metrics_dashboard': self.metrics_dashboard is not None,
                'preference_learner': self.preference_learner is not None,
            }
        }

    def force_learning_cycle(self):
        """Force an immediate learning cycle (for testing/debugging)."""
        self.logger.info("Forcing immediate learning cycle")
        self._run_coordination_cycle()

    def adjust_config(self, key: str, value: Any):
        """Adjust coordination configuration.

        Args:
            key: Configuration key
            value: New value
        """
        if key in self.config:
            old_value = self.config[key]
            self.config[key] = value
            self.logger.info(f"Updated config: {key} = {value} (was {old_value})")
        else:
            self.logger.warning(f"Unknown config key: {key}")

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive learning summary from all components.

        Returns:
            Dictionary with complete learning system status
        """
        summary = {
            'coordination': self.get_coordination_status(),
            'components': {}
        }

        try:
            if self.mistake_learner:
                summary['components']['mistakes'] = self.mistake_learner.get_learning_stats()

            if self.behavior_engine:
                summary['components']['behavior'] = {
                    'profile': self.behavior_engine.get_current_behavior_profile(),
                    'effectiveness': self.behavior_engine.analyze_behavior_effectiveness()
                }

            if self.preference_learner:
                summary['components']['preferences'] = self.preference_learner.get_learning_stats()

            if self.metrics_dashboard:
                summary['components']['metrics'] = self.metrics_dashboard.get_dashboard_summary()

        except Exception as e:
            self.logger.error(f"Failed to generate learning summary: {e}")

        return summary
