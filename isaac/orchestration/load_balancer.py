#!/usr/bin/env python3
"""
Load Balancing System for Multi-Machine Orchestration
Provides intelligent task distribution across registered machines
"""

import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from isaac.orchestration.registry import MachineRegistry, Machine


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOAD = "least_load"
    WEIGHTED_LEAST_LOAD = "weighted_least_load"
    RANDOM = "random"
    RESOURCE_AWARE = "resource_aware"
    PERFORMANCE_BASED = "performance_based"


@dataclass
class LoadScore:
    """Load score for a machine"""
    machine: Machine
    score: float
    factors: Dict[str, float]  # Breakdown of scoring factors


class LoadBalancer:
    """Intelligent load balancer for distributing tasks across machines"""

    def __init__(self, registry: MachineRegistry):
        self.registry = registry
        self.round_robin_index: Dict[str, int] = {}  # group_name -> index
        self.performance_history: Dict[str, List[float]] = {}  # machine_id -> execution times

    def select_machine(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOAD,
                      group_name: Optional[str] = None,
                      required_tags: Optional[List[str]] = None,
                      min_cpu_cores: int = 0,
                      min_memory_gb: float = 0.0,
                      command_complexity: str = "normal") -> Optional[Machine]:
        """
        Select the best machine using the specified load balancing strategy

        Args:
            strategy: Load balancing algorithm to use
            group_name: Limit selection to machines in this group
            required_tags: Machines must have all these tags
            min_cpu_cores: Minimum CPU cores required
            min_memory_gb: Minimum memory in GB required
            command_complexity: "low", "normal", "high" - affects selection criteria

        Returns:
            Selected machine or None if no suitable machine found
        """

        # Get candidate machines
        candidates = self._get_candidates(group_name, required_tags, min_cpu_cores, min_memory_gb)

        if not candidates:
            return None

        # Apply load balancing strategy
        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(candidates, group_name or "default")
        elif strategy == LoadBalancingStrategy.LEAST_LOAD:
            return self._least_load_selection(candidates)
        elif strategy == LoadBalancingStrategy.WEIGHTED_LEAST_LOAD:
            return self._weighted_least_load_selection(candidates, command_complexity)
        elif strategy == LoadBalancingStrategy.RANDOM:
            return self._random_selection(candidates)
        elif strategy == LoadBalancingStrategy.RESOURCE_AWARE:
            return self._resource_aware_selection(candidates, command_complexity)
        elif strategy == LoadBalancingStrategy.PERFORMANCE_BASED:
            return self._performance_based_selection(candidates, command_complexity)
        else:
            return self._least_load_selection(candidates)  # Default fallback

    def distribute_tasks(self, tasks: List[Dict[str, Any]],
                        strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOAD,
                        group_name: Optional[str] = None,
                        required_tags: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Distribute tasks across available machines

        Args:
            tasks: List of task dictionaries
            strategy: Load balancing strategy
            group_name: Limit to machines in this group
            required_tags: Machines must have all these tags

        Returns:
            Dict mapping machine_id to list of assigned tasks
        """

        candidates = self._get_candidates(group_name, required_tags)
        if not candidates:
            return {}

        distribution = {machine.machine_id: [] for machine in candidates}

        for task in tasks:
            machine = self.select_machine(
                strategy=strategy,
                group_name=group_name,
                required_tags=required_tags,
                command_complexity=task.get('complexity', 'normal')
            )

            if machine:
                distribution[machine.machine_id].append(task)

        return distribution

    def get_load_scores(self, machines: List[Machine],
                       command_complexity: str = "normal") -> List[LoadScore]:
        """
        Calculate load scores for machines

        Args:
            machines: List of machines to score
            command_complexity: "low", "normal", "high"

        Returns:
            List of LoadScore objects with detailed scoring breakdown
        """

        scores = []

        for machine in machines:
            if not machine.status.is_online:
                continue

            factors = {}
            total_score = 0.0

            # CPU utilization (0-100, lower is better)
            cpu_factor = machine.status.current_load / 100.0
            factors['cpu'] = cpu_factor
            total_score += cpu_factor * 0.3

            # Memory utilization (0-100, lower is better)
            memory_factor = machine.status.memory_usage / 100.0
            factors['memory'] = memory_factor
            total_score += memory_factor * 0.3

            # Current load (0-100, lower is better)
            load_factor = machine.status.current_load / 100.0
            factors['load'] = load_factor
            total_score += load_factor * 0.2

            # Performance history (recent execution times, lower is better)
            perf_factor = self._get_performance_factor(machine.machine_id)
            factors['performance'] = perf_factor
            total_score += perf_factor * 0.1

            # Resource availability bonus (higher capacity gives slight preference)
            capacity_factor = self._calculate_capacity_factor(machine, command_complexity)
            factors['capacity'] = capacity_factor
            total_score -= capacity_factor * 0.1  # Subtract because higher capacity is better

            scores.append(LoadScore(
                machine=machine,
                score=max(0.0, total_score),  # Ensure non-negative
                factors=factors
            ))

        return sorted(scores, key=lambda x: x.score)

    def record_execution_time(self, machine_id: str, execution_time: float):
        """Record execution time for performance-based load balancing"""
        if machine_id not in self.performance_history:
            self.performance_history[machine_id] = []

        self.performance_history[machine_id].append(execution_time)

        # Keep only last 10 measurements
        if len(self.performance_history[machine_id]) > 10:
            self.performance_history[machine_id] = self.performance_history[machine_id][-10:]

    def _get_candidates(self, group_name: Optional[str] = None,
                       required_tags: Optional[List[str]] = None,
                       min_cpu_cores: int = 0,
                       min_memory_gb: float = 0.0) -> List[Machine]:
        """Get candidate machines based on filters"""

        if group_name:
            candidates = self.registry.get_group_machines(group_name)
        else:
            candidates = self.registry.list_machines(filter_online=True)

        # Apply filters
        if required_tags:
            candidates = [m for m in candidates if m.tags and all(tag in m.tags for tag in required_tags)]

        candidates = [m for m in candidates
                     if m.capabilities.cpu_cores >= min_cpu_cores
                     and m.capabilities.memory_gb >= min_memory_gb]

        return candidates

    def _round_robin_selection(self, candidates: List[Machine], group_key: str) -> Optional[Machine]:
        """Round-robin selection"""
        if not candidates:
            return None

        if group_key not in self.round_robin_index:
            self.round_robin_index[group_key] = 0

        index = self.round_robin_index[group_key]
        machine = candidates[index % len(candidates)]
        self.round_robin_index[group_key] = (index + 1) % len(candidates)

        return machine

    def _least_load_selection(self, candidates: List[Machine]) -> Optional[Machine]:
        """Select machine with least current load"""
        if not candidates:
            return None

        return min(candidates, key=lambda m: m.status.current_load)

    def _weighted_least_load_selection(self, candidates: List[Machine],
                                     command_complexity: str) -> Optional[Machine]:
        """Weighted least load considering command complexity"""
        if not candidates:
            return None

        # Adjust weights based on command complexity
        weights = {
            'low': {'cpu': 0.2, 'memory': 0.2, 'load': 0.6},
            'normal': {'cpu': 0.3, 'memory': 0.3, 'load': 0.4},
            'high': {'cpu': 0.4, 'memory': 0.4, 'load': 0.2}
        }

        weight = weights.get(command_complexity, weights['normal'])

        def calculate_weighted_load(machine: Machine) -> float:
            return (machine.status.current_load * weight['cpu'] +
                   machine.status.memory_usage * weight['memory'] +
                   machine.status.current_load * weight['load'])

        return min(candidates, key=calculate_weighted_load)

    def _random_selection(self, candidates: List[Machine]) -> Optional[Machine]:
        """Random selection"""
        return random.choice(candidates) if candidates else None

    def _resource_aware_selection(self, candidates: List[Machine],
                                command_complexity: str) -> Optional[Machine]:
        """Resource-aware selection considering machine capabilities"""
        if not candidates:
            return None

        # Score based on resource availability relative to requirements
        complexity_requirements = {
            'low': {'cpu_weight': 0.3, 'memory_weight': 0.3, 'gpu_weight': 0.0},
            'normal': {'cpu_weight': 0.4, 'memory_weight': 0.4, 'gpu_weight': 0.1},
            'high': {'cpu_weight': 0.5, 'memory_weight': 0.4, 'gpu_weight': 0.2}
        }

        req = complexity_requirements.get(command_complexity, complexity_requirements['normal'])

        def resource_score(machine: Machine) -> float:
            cpu_score = machine.capabilities.cpu_cores / max(1, machine.status.current_load)
            memory_score = machine.capabilities.memory_gb / max(0.1, machine.status.memory_usage / 100.0)
            gpu_score = machine.capabilities.gpu_count if req['gpu_weight'] > 0 else 1.0

            return (cpu_score * req['cpu_weight'] +
                   memory_score * req['memory_weight'] +
                   gpu_score * req['gpu_weight'])

        return max(candidates, key=resource_score)

    def _performance_based_selection(self, candidates: List[Machine],
                                   command_complexity: str) -> Optional[Machine]:
        """Performance-based selection using historical execution times"""
        if not candidates:
            return None

        # Use performance history to predict execution time
        def performance_score(machine: Machine) -> float:
            history = self.performance_history.get(machine.machine_id, [])
            if not history:
                return machine.status.current_load  # Fallback to current load

            # Use average of recent executions
            avg_time = sum(history[-5:]) / len(history[-5:])  # Last 5 executions
            return avg_time

        return min(candidates, key=performance_score)

    def _get_performance_factor(self, machine_id: str) -> float:
        """Get performance factor (0-1, lower is better)"""
        history = self.performance_history.get(machine_id, [])
        if not history:
            return 0.5  # Neutral factor

        # Normalize recent performance (lower execution time is better)
        recent_avg = sum(history[-3:]) / len(history[-3:])
        # Convert to 0-1 scale (assuming 0-60 seconds range)
        return min(1.0, recent_avg / 60.0)

    def _calculate_capacity_factor(self, machine: Machine, command_complexity: str) -> float:
        """Calculate capacity factor (0-1, higher is better)"""
        # Higher capacity machines get slight preference
        cpu_factor = min(1.0, machine.capabilities.cpu_cores / 8.0)  # Normalize to 8 cores
        memory_factor = min(1.0, machine.capabilities.memory_gb / 16.0)  # Normalize to 16GB

        # Adjust based on command complexity
        complexity_multiplier = {'low': 0.7, 'normal': 1.0, 'high': 1.3}
        multiplier = complexity_multiplier.get(command_complexity, 1.0)

        return (cpu_factor + memory_factor) / 2.0 * multiplier