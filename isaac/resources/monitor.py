"""
Real-time Resource Monitoring

Tracks CPU, memory, disk, network, and process-level resources.
"""

import psutil
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    swap_percent: float
    load_average: tuple
    process_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp_readable'] = datetime.fromtimestamp(self.timestamp).isoformat()
        return data


@dataclass
class ProcessInfo:
    """Information about a process"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    num_threads: int
    status: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class ResourceMonitor:
    """
    Real-time resource monitoring with history tracking

    Features:
    - Track CPU, memory, disk, network usage
    - Process-level monitoring
    - Historical data with configurable retention
    - Threshold-based alerts
    - Background monitoring thread
    """

    def __init__(self, history_size: int = 1000, monitor_interval: float = 1.0):
        """
        Initialize resource monitor

        Args:
            history_size: Number of snapshots to keep in memory
            monitor_interval: Seconds between snapshots (for background monitoring)
        """
        self.history_size = history_size
        self.monitor_interval = monitor_interval
        self.history: List[ResourceSnapshot] = []
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[ResourceSnapshot], None]] = []
        self._initial_net_io = psutil.net_io_counters()

    def capture_snapshot(self) -> ResourceSnapshot:
        """Capture current resource state"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Memory
        mem = psutil.virtual_memory()
        memory_percent = mem.percent
        memory_used_mb = mem.used / (1024 * 1024)
        memory_available_mb = mem.available / (1024 * 1024)

        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        disk_free_gb = disk.free / (1024 * 1024 * 1024)

        # Network
        net_io = psutil.net_io_counters()
        network_sent_mb = (net_io.bytes_sent - self._initial_net_io.bytes_sent) / (1024 * 1024)
        network_recv_mb = (net_io.bytes_recv - self._initial_net_io.bytes_recv) / (1024 * 1024)

        # Swap
        swap = psutil.swap_memory()
        swap_percent = swap.percent

        # Load average
        load_average = psutil.getloadavg()

        # Process count
        process_count = len(psutil.pids())

        snapshot = ResourceSnapshot(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_free_gb=disk_free_gb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            swap_percent=swap_percent,
            load_average=load_average,
            process_count=process_count
        )

        # Add to history
        self.history.append(snapshot)
        if len(self.history) > self.history_size:
            self.history.pop(0)

        # Trigger callbacks
        for callback in self._callbacks:
            try:
                callback(snapshot)
            except Exception as e:
                print(f"Error in resource monitor callback: {e}")

        return snapshot

    def get_top_processes(self, limit: int = 10, sort_by: str = 'cpu') -> List[ProcessInfo]:
        """
        Get top processes by resource usage

        Args:
            limit: Number of processes to return
            sort_by: 'cpu' or 'memory'

        Returns:
            List of ProcessInfo objects
        """
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'num_threads', 'status']):
            try:
                info = proc.info
                memory_mb = info['memory_info'].rss / (1024 * 1024) if info.get('memory_info') else 0

                processes.append(ProcessInfo(
                    pid=info['pid'],
                    name=info['name'] or 'Unknown',
                    cpu_percent=info['cpu_percent'] or 0,
                    memory_percent=info['memory_percent'] or 0,
                    memory_mb=memory_mb,
                    num_threads=info['num_threads'] or 0,
                    status=info['status'] or 'unknown'
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort processes
        if sort_by == 'cpu':
            processes.sort(key=lambda p: p.cpu_percent, reverse=True)
        else:  # memory
            processes.sort(key=lambda p: p.memory_percent, reverse=True)

        return processes[:limit]

    def get_current_state(self) -> Dict[str, Any]:
        """Get current resource state as dictionary"""
        snapshot = self.capture_snapshot()
        top_cpu = self.get_top_processes(5, 'cpu')
        top_mem = self.get_top_processes(5, 'memory')

        return {
            'snapshot': snapshot.to_dict(),
            'top_cpu_processes': [p.to_dict() for p in top_cpu],
            'top_memory_processes': [p.to_dict() for p in top_mem],
            'history_count': len(self.history)
        }

    def get_statistics(self, minutes: int = 5) -> Dict[str, Any]:
        """
        Get statistics over recent history

        Args:
            minutes: Number of minutes to analyze

        Returns:
            Dictionary with statistics
        """
        if not self.history:
            return {
                'error': 'No history available',
                'available_snapshots': 0
            }

        cutoff_time = time.time() - (minutes * 60)
        recent_snapshots = [s for s in self.history if s.timestamp >= cutoff_time]

        if not recent_snapshots:
            recent_snapshots = self.history[-1:]  # At least use latest

        cpu_values = [s.cpu_percent for s in recent_snapshots]
        mem_values = [s.memory_percent for s in recent_snapshots]

        return {
            'period_minutes': minutes,
            'snapshots_analyzed': len(recent_snapshots),
            'cpu': {
                'current': cpu_values[-1] if cpu_values else 0,
                'average': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'max': max(cpu_values) if cpu_values else 0,
                'min': min(cpu_values) if cpu_values else 0,
            },
            'memory': {
                'current': mem_values[-1] if mem_values else 0,
                'average': sum(mem_values) / len(mem_values) if mem_values else 0,
                'max': max(mem_values) if mem_values else 0,
                'min': min(mem_values) if mem_values else 0,
            },
            'disk': {
                'used_gb': recent_snapshots[-1].disk_used_gb if recent_snapshots else 0,
                'free_gb': recent_snapshots[-1].disk_free_gb if recent_snapshots else 0,
                'percent': recent_snapshots[-1].disk_percent if recent_snapshots else 0,
            }
        }

    def start_monitoring(self):
        """Start background monitoring thread"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop background monitoring thread"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                self.capture_snapshot()
                time.sleep(self.monitor_interval)
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(self.monitor_interval)

    def register_callback(self, callback: Callable[[ResourceSnapshot], None]):
        """Register callback to be called on each snapshot"""
        self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[ResourceSnapshot], None]):
        """Unregister callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_docker_resources(self) -> Optional[Dict[str, Any]]:
        """Get Docker resource usage if Docker is available"""
        try:
            import subprocess
            result = subprocess.run(
                ['docker', 'system', 'df', '--format', '{{json .}}'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                docker_data = []
                for line in lines:
                    if line:
                        try:
                            docker_data.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                return {
                    'available': True,
                    'data': docker_data
                }
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        return {'available': False}

    def export_history(self, filepath: str):
        """Export monitoring history to JSON file"""
        data = {
            'exported_at': datetime.now().isoformat(),
            'history_size': len(self.history),
            'snapshots': [s.to_dict() for s in self.history]
        }

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
