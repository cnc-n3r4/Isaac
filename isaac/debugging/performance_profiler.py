"""
Performance Profiling - Identify bottlenecks and optimization opportunities
Isaac's intelligent performance analysis and optimization system
"""

import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import os
from pathlib import Path


@dataclass
class PerformanceMetric:
    """Represents a performance measurement."""
    name: str
    value: float
    unit: str
    timestamp: float
    context: Dict[str, Any]


@dataclass
class PerformanceProfile:
    """Complete performance profile for a command or process."""
    command: str
    start_time: float
    end_time: float
    duration: float
    cpu_usage: float
    memory_usage: float
    disk_io: Dict[str, int]
    network_io: Dict[str, int]
    system_load: Dict[str, float]
    bottlenecks: List[str]
    recommendations: List[str]


@dataclass
class OptimizationSuggestion:
    """Suggested optimization for performance improvement."""
    suggestion_id: str
    title: str
    description: str
    category: str  # 'cpu', 'memory', 'disk', 'network', 'command'
    impact: str  # 'high', 'medium', 'low'
    effort: str  # 'low', 'medium', 'high'
    commands: List[str]
    expected_improvement: str


class PerformanceProfiler:
    """Profiles command performance and identifies optimization opportunities."""

    def __init__(self):
        """Initialize the performance profiler."""
        self.monitoring_active = False
        self.current_profile = None
        self.baseline_metrics = {}
        self.performance_history = defaultdict(list)

    def start_profiling(self, command: str, context: Dict[str, Any] = None) -> str:
        """Start performance profiling for a command.

        Args:
            command: The command being profiled
            context: Additional context information

        Returns:
            Profile ID for tracking
        """
        profile_id = f"profile_{int(time.time() * 1000)}"

        self.current_profile = {
            'id': profile_id,
            'command': command,
            'start_time': time.time(),
            'context': context or {},
            'initial_metrics': self._capture_system_metrics(),
            'samples': []
        }

        self.monitoring_active = True

        # Start background monitoring
        self._start_background_monitoring()

        return profile_id

    def stop_profiling(self) -> Optional[PerformanceProfile]:
        """Stop profiling and return the performance profile."""
        if not self.current_profile:
            return None

        self.monitoring_active = False

        end_time = time.time()
        final_metrics = self._capture_system_metrics()

        profile = self._analyze_performance(
            self.current_profile,
            end_time,
            final_metrics
        )

        # Store in history
        self.performance_history[self.current_profile['command']].append(profile)

        self.current_profile = None

        return profile

    def _start_background_monitoring(self):
        """Start background monitoring thread."""
        def monitor():
            while self.monitoring_active:
                if self.current_profile:
                    metrics = self._capture_system_metrics()
                    self.current_profile['samples'].append({
                        'timestamp': time.time(),
                        'metrics': metrics
                    })
                time.sleep(0.1)  # Sample every 100ms

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def _capture_system_metrics(self) -> Dict[str, Any]:
        """Capture current system performance metrics."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=None),
                'cpu_count': psutil.cpu_count(),
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'percent': psutil.virtual_memory().percent,
                    'used': psutil.virtual_memory().used
                },
                'disk': {
                    'read_bytes': psutil.disk_io_counters().read_bytes if psutil.disk_io_counters() else 0,
                    'write_bytes': psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0
                },
                'network': {
                    'bytes_sent': psutil.net_io_counters().bytes_sent if psutil.net_io_counters() else 0,
                    'bytes_recv': psutil.net_io_counters().bytes_recv if psutil.net_io_counters() else 0
                },
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0],
                'process_count': len(psutil.pids())
            }
        except Exception as e:
            return {'error': str(e)}

    def _analyze_performance(self, profile_data: Dict[str, Any],
                           end_time: float, final_metrics: Dict[str, Any]) -> PerformanceProfile:
        """Analyze collected performance data."""
        start_time = profile_data['start_time']
        duration = end_time - start_time

        initial_metrics = profile_data['initial_metrics']
        samples = profile_data['samples']

        # Calculate averages and peaks
        cpu_usage = self._calculate_average_cpu(samples, initial_metrics)
        memory_usage = self._calculate_average_memory(samples, initial_metrics)
        disk_io = self._calculate_disk_io(initial_metrics, final_metrics)
        network_io = self._calculate_network_io(initial_metrics, final_metrics)
        system_load = self._calculate_system_load(samples)

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(
            cpu_usage, memory_usage, disk_io, network_io, system_load, duration
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            bottlenecks, profile_data['command'], duration
        )

        return PerformanceProfile(
            command=profile_data['command'],
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_io=disk_io,
            network_io=network_io,
            system_load=system_load,
            bottlenecks=bottlenecks,
            recommendations=recommendations
        )

    def _calculate_average_cpu(self, samples: List[Dict], initial_metrics: Dict) -> float:
        """Calculate average CPU usage during profiling."""
        if not samples:
            return initial_metrics.get('cpu_percent', 0)

        cpu_samples = [s['metrics'].get('cpu_percent', 0) for s in samples]
        return sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0

    def _calculate_average_memory(self, samples: List[Dict], initial_metrics: Dict) -> float:
        """Calculate average memory usage during profiling."""
        if not samples:
            return initial_metrics.get('memory', {}).get('percent', 0)

        mem_samples = [s['metrics'].get('memory', {}).get('percent', 0) for s in samples]
        return sum(mem_samples) / len(mem_samples) if mem_samples else 0

    def _calculate_disk_io(self, initial: Dict, final: Dict) -> Dict[str, int]:
        """Calculate disk I/O during profiling period."""
        initial_disk = initial.get('disk', {})
        final_disk = final.get('disk', {})

        return {
            'read_bytes': final_disk.get('read_bytes', 0) - initial_disk.get('read_bytes', 0),
            'write_bytes': final_disk.get('write_bytes', 0) - initial_disk.get('write_bytes', 0)
        }

    def _calculate_network_io(self, initial: Dict, final: Dict) -> Dict[str, int]:
        """Calculate network I/O during profiling period."""
        initial_net = initial.get('network', {})
        final_net = final.get('network', {})

        return {
            'bytes_sent': final_net.get('bytes_sent', 0) - initial_net.get('bytes_sent', 0),
            'bytes_recv': final_net.get('bytes_recv', 0) - initial_net.get('bytes_recv', 0)
        }

    def _calculate_system_load(self, samples: List[Dict]) -> Dict[str, float]:
        """Calculate average system load."""
        if not samples:
            return {'1min': 0, '5min': 0, '15min': 0}

        load_samples = [s['metrics'].get('load_average', [0, 0, 0]) for s in samples]
        if not load_samples:
            return {'1min': 0, '5min': 0, '15min': 0}

        avg_load = [
            sum(sample[i] for sample in load_samples) / len(load_samples)
            for i in range(3)
        ]

        return {
            '1min': avg_load[0],
            '5min': avg_load[1],
            '15min': avg_load[2]
        }

    def _identify_bottlenecks(self, cpu_usage: float, memory_usage: float,
                            disk_io: Dict[str, int], network_io: Dict[str, int],
                            system_load: Dict[str, float], duration: float) -> List[str]:
        """Identify performance bottlenecks."""
        bottlenecks = []

        # CPU bottlenecks
        if cpu_usage > 80:
            bottlenecks.append("High CPU usage (>80%)")
        elif cpu_usage > 50:
            bottlenecks.append("Moderate CPU usage (>50%)")

        # Memory bottlenecks
        if memory_usage > 90:
            bottlenecks.append("Critical memory usage (>90%)")
        elif memory_usage > 70:
            bottlenecks.append("High memory usage (>70%)")

        # Disk I/O bottlenecks
        total_disk_io = disk_io.get('read_bytes', 0) + disk_io.get('write_bytes', 0)
        if total_disk_io > 100 * 1024 * 1024:  # 100MB
            bottlenecks.append("High disk I/O activity")

        # Network bottlenecks
        total_network_io = network_io.get('bytes_sent', 0) + network_io.get('bytes_recv', 0)
        if total_network_io > 50 * 1024 * 1024:  # 50MB
            bottlenecks.append("High network activity")

        # System load bottlenecks
        if system_load.get('1min', 0) > psutil.cpu_count() * 0.8:
            bottlenecks.append("High system load")

        # Duration-based analysis
        if duration > 30:  # Commands taking longer than 30 seconds
            bottlenecks.append("Long execution time (>30s)")

        return bottlenecks

    def _generate_recommendations(self, bottlenecks: List[str], command: str,
                                duration: float) -> List[str]:
        """Generate optimization recommendations based on bottlenecks."""
        recommendations = []

        for bottleneck in bottlenecks:
            if "CPU usage" in bottleneck:
                recommendations.extend([
                    "Consider parallel processing if applicable",
                    "Optimize algorithms for better CPU efficiency",
                    "Check for CPU-intensive loops or computations"
                ])

            if "memory usage" in bottleneck:
                recommendations.extend([
                    "Implement memory-efficient data structures",
                    "Add memory cleanup and garbage collection",
                    "Consider processing data in chunks",
                    "Check for memory leaks in the application"
                ])

            if "disk I/O" in bottleneck:
                recommendations.extend([
                    "Use buffered I/O operations",
                    "Implement caching for frequently accessed data",
                    "Consider SSD storage for better performance",
                    "Optimize file access patterns"
                ])

            if "network" in bottleneck:
                recommendations.extend([
                    "Use compression for data transfer",
                    "Implement connection pooling",
                    "Cache remote data locally when possible",
                    "Check network latency and bandwidth"
                ])

            if "system load" in bottleneck:
                recommendations.extend([
                    "Schedule command during off-peak hours",
                    "Reduce system load by terminating unnecessary processes",
                    "Consider resource limits (nice, ionice)"
                ])

            if "execution time" in bottleneck:
                recommendations.extend([
                    "Profile the command to identify slow sections",
                    "Consider alternative tools or approaches",
                    "Implement progress monitoring and early termination options"
                ])

        # Command-specific recommendations
        if "grep" in command.lower():
            recommendations.append("Use ripgrep (rg) for faster text searching")
        elif "find" in command.lower():
            recommendations.append("Use fd for faster file finding")
        elif "cat" in command.lower() and "|" in command:
            recommendations.append("Consider using process substitution or named pipes")

        return list(set(recommendations))  # Remove duplicates

    def get_optimization_suggestions(self, profile: PerformanceProfile) -> List[OptimizationSuggestion]:
        """Get specific optimization suggestions for a performance profile."""
        suggestions = []

        # CPU optimization suggestions
        if profile.cpu_usage > 70:
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"cpu_opt_{int(time.time())}",
                title="Optimize CPU Usage",
                description="High CPU usage detected. Consider optimizing compute-intensive operations.",
                category="cpu",
                impact="high",
                effort="medium",
                commands=[
                    "Use parallel processing: parallel -j $(nproc) 'command {}' ::: items",
                    "Implement CPU affinity: taskset -c 0-3 command",
                    "Profile with perf: perf record -g command"
                ],
                expected_improvement="20-50% reduction in CPU usage"
            ))

        # Memory optimization suggestions
        if profile.memory_usage > 80:
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"mem_opt_{int(time.time())}",
                title="Optimize Memory Usage",
                description="High memory consumption detected. Implement memory-efficient patterns.",
                category="memory",
                impact="high",
                effort="high",
                commands=[
                    "Use memory-efficient data structures",
                    "Implement streaming processing: command | process_stream",
                    "Add memory limits: ulimit -v 1048576; command"
                ],
                expected_improvement="30-60% reduction in memory usage"
            ))

        # I/O optimization suggestions
        total_io = profile.disk_io.get('read_bytes', 0) + profile.disk_io.get('write_bytes', 0)
        if total_io > 50 * 1024 * 1024:  # 50MB
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"io_opt_{int(time.time())}",
                title="Optimize I/O Operations",
                description="High disk I/O detected. Consider I/O optimization techniques.",
                category="disk",
                impact="medium",
                effort="medium",
                commands=[
                    "Use buffered I/O: stdbuf -o 1M command",
                    "Implement caching: command | tee cache_file",
                    "Use faster storage or RAID configuration"
                ],
                expected_improvement="40-70% reduction in I/O time"
            ))

        # Long-running command optimizations
        if profile.duration > 60:  # Over 1 minute
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"duration_opt_{int(time.time())}",
                title="Reduce Execution Time",
                description="Command takes significant time. Consider optimization or alternatives.",
                category="command",
                impact="high",
                effort="low",
                commands=[
                    "Use faster alternatives (ripgrep vs grep, fd vs find)",
                    "Implement incremental processing",
                    "Add progress monitoring: command | pv -pterb"
                ],
                expected_improvement="50-80% reduction in execution time"
            ))

        return suggestions

    def compare_with_baseline(self, profile: PerformanceProfile) -> Dict[str, Any]:
        """Compare current performance with baseline metrics."""
        command = profile.command
        baseline = self.baseline_metrics.get(command)

        if not baseline:
            return {'comparison': 'no_baseline', 'message': 'No baseline available for comparison'}

        comparison = {
            'command': command,
            'baseline_duration': baseline.get('duration', 0),
            'current_duration': profile.duration,
            'duration_change': profile.duration - baseline.get('duration', 0),
            'duration_change_percent': ((profile.duration - baseline.get('duration', 0)) /
                                      baseline.get('duration', 0) * 100) if baseline.get('duration', 0) else 0,
            'baseline_cpu': baseline.get('cpu_usage', 0),
            'current_cpu': profile.cpu_usage,
            'cpu_change': profile.cpu_usage - baseline.get('cpu_usage', 0),
            'baseline_memory': baseline.get('memory_usage', 0),
            'current_memory': profile.memory_usage,
            'memory_change': profile.memory_usage - baseline.get('memory_usage', 0)
        }

        # Performance assessment
        if comparison['duration_change_percent'] > 20:
            comparison['assessment'] = 'performance_degraded'
            comparison['message'] = f"Performance degraded by {comparison['duration_change_percent']:.1f}%"
        elif comparison['duration_change_percent'] < -20:
            comparison['assessment'] = 'performance_improved'
            comparison['message'] = f"Performance improved by {abs(comparison['duration_change_percent']):.1f}%"
        else:
            comparison['assessment'] = 'performance_stable'
            comparison['message'] = "Performance stable compared to baseline"

        return comparison

    def set_baseline(self, command: str, profile: PerformanceProfile):
        """Set baseline performance metrics for a command."""
        self.baseline_metrics[command] = {
            'duration': profile.duration,
            'cpu_usage': profile.cpu_usage,
            'memory_usage': profile.memory_usage,
            'timestamp': time.time()
        }

    def get_performance_history(self, command: str, limit: int = 10) -> List[PerformanceProfile]:
        """Get performance history for a command."""
        return self.performance_history.get(command, [])[-limit:]

    def generate_performance_report(self, profile: PerformanceProfile) -> str:
        """Generate a human-readable performance report."""
        report = f"""
Performance Report for: {profile.command}
{'='*50}

Execution Time: {profile.duration:.2f} seconds
CPU Usage: {profile.cpu_usage:.1f}%
Memory Usage: {profile.memory_usage:.1f}%

Resource Usage:
- Disk Read: {profile.disk_io.get('read_bytes', 0) / 1024 / 1024:.1f} MB
- Disk Write: {profile.disk_io.get('write_bytes', 0) / 1024 / 1024:.1f} MB
- Network Sent: {profile.network_io.get('bytes_sent', 0) / 1024 / 1024:.1f} MB
- Network Received: {profile.network_io.get('bytes_recv', 0) / 1024 / 1024:.1f} MB

System Load:
- 1 minute: {profile.system_load.get('1min', 0):.2f}
- 5 minutes: {profile.system_load.get('5min', 0):.2f}
- 15 minutes: {profile.system_load.get('15min', 0):.2f}

Bottlenecks Identified:
{chr(10).join(f"- {b}" for b in profile.bottlenecks) if profile.bottlenecks else "None"}

Recommendations:
{chr(10).join(f"- {r}" for r in profile.recommendations) if profile.recommendations else "None"}
"""

        return report.strip()