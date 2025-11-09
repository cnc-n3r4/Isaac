"""
Multi-Machine Orchestration - Machine Registry and Coordination
"""

import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import socket
import psutil
import platform


@dataclass
class MachineCapabilities:
    """Hardware and software capabilities of a machine"""
    cpu_cores: int
    cpu_threads: int
    memory_gb: float
    disk_gb: float
    gpu_count: int = 0
    gpu_memory_gb: float = 0.0
    os: str = ""
    architecture: str = ""
    python_version: str = ""
    has_docker: bool = False
    has_kubernetes: bool = False

    @classmethod
    def detect(cls) -> 'MachineCapabilities':
        """Auto-detect machine capabilities"""
        try:
            # CPU info
            cpu_cores = psutil.cpu_count(logical=False) or 1
            cpu_threads = psutil.cpu_count(logical=True) or cpu_cores

            # Memory info
            memory = psutil.virtual_memory()
            memory_gb = round(memory.total / (1024**3), 2)

            # Disk info
            disk = psutil.disk_usage('/')
            disk_gb = round(disk.total / (1024**3), 2)

            # System info
            os_info = f"{platform.system()} {platform.release()}"
            architecture = platform.machine()
            python_version = f"{platform.python_version()}"

            # GPU detection (simplified)
            gpu_count = 0
            gpu_memory_gb = 0.0
            try:
                # Try to detect NVIDIA GPUs
                import subprocess
                result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    gpu_count = len(lines)
                    gpu_memory_gb = sum(float(line.split()[0]) / 1024 for line in lines if line.strip())
            except:
                pass

            # Docker detection
            has_docker = False
            try:
                result = subprocess.run(['docker', '--version'], capture_output=True, timeout=5)
                has_docker = result.returncode == 0
            except:
                pass

            # Kubernetes detection
            has_kubernetes = False
            try:
                result = subprocess.run(['kubectl', 'version', '--client'], capture_output=True, timeout=5)
                has_kubernetes = result.returncode == 0
            except:
                pass

            return cls(
                cpu_cores=cpu_cores,
                cpu_threads=cpu_threads,
                memory_gb=memory_gb,
                disk_gb=disk_gb,
                gpu_count=gpu_count,
                gpu_memory_gb=gpu_memory_gb,
                os=os_info,
                architecture=architecture,
                python_version=python_version,
                has_docker=has_docker,
                has_kubernetes=has_kubernetes
            )
        except Exception:
            # Fallback with basic info
            return cls(
                cpu_cores=1,
                cpu_threads=1,
                memory_gb=1.0,
                disk_gb=10.0,
                os=platform.system(),
                architecture=platform.architecture()[0],
                python_version=platform.python_version()
            )


@dataclass
class MachineStatus:
    """Current status of a machine"""
    is_online: bool = True
    last_seen: float = 0.0
    current_load: float = 0.0  # CPU usage percentage
    memory_usage: float = 0.0  # Memory usage percentage
    active_tasks: int = 0
    status_message: str = "Ready"


@dataclass
class Machine:
    """Represents an Isaac instance on a machine"""
    machine_id: str
    hostname: str
    ip_address: str
    capabilities: MachineCapabilities
    status: MachineStatus
    port: int = 8080  # Default Isaac API port
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def local_machine(cls, port: int = 8080) -> 'Machine':
        """Create a Machine instance for the local machine"""
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        machine_id = str(uuid.uuid4())[:8]

        capabilities = MachineCapabilities.detect()
        status = MachineStatus(
            is_online=True,
            last_seen=time.time(),
            current_load=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent
        )

        return cls(
            machine_id=machine_id,
            hostname=hostname,
            ip_address=ip_address,
            port=port,
            capabilities=capabilities,
            status=status,
            tags=['local'],
            metadata={'auto_detected': True}
        )


class MachineRegistry:
    """Registry for managing Isaac instances across machines"""

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            isaac_dir = Path.home() / '.isaac'
            isaac_dir.mkdir(exist_ok=True)
            storage_path = isaac_dir / 'machines.json'

        self.storage_path = storage_path
        self.machines: Dict[str, Machine] = {}
        self.groups: Dict[str, List[str]] = {}  # group_name -> [machine_ids]

        self._load_registry()

    def register_machine(self, machine: Machine) -> bool:
        """Register a new machine"""
        self.machines[machine.machine_id] = machine
        self._save_registry()
        return True

    def unregister_machine(self, machine_id: str) -> bool:
        """Remove a machine from registry"""
        if machine_id in self.machines:
            del self.machines[machine_id]
            self._save_registry()
            return True
        return False

    def get_machine(self, machine_id: str) -> Optional[Machine]:
        """Get machine by ID"""
        return self.machines.get(machine_id)

    def list_machines(self, filter_online: bool = False) -> List[Machine]:
        """List all registered machines"""
        machines = list(self.machines.values())
        if filter_online:
            machines = [m for m in machines if m.status.is_online]
        return machines

    def update_machine_status(self, machine_id: str, status: MachineStatus) -> bool:
        """Update machine status"""
        machine = self.get_machine(machine_id)
        if machine:
            machine.status = status
            self._save_registry()
            return True
        return False

    def create_group(self, group_name: str, machine_ids: List[str]) -> bool:
        """Create a machine group"""
        # Validate all machine IDs exist
        for mid in machine_ids:
            if mid not in self.machines:
                return False

        self.groups[group_name] = machine_ids
        self._save_registry()
        return True

    def get_group(self, group_name: str) -> List[Machine]:
        """Get machines in a group"""
        machine_ids = self.groups.get(group_name, [])
        return [self.machines[mid] for mid in machine_ids if mid in self.machines]

    def list_groups(self) -> Dict[str, List[Machine]]:
        """List all groups with their machines"""
        return {name: self.get_group(name) for name in self.groups.keys()}

    def find_machines_by_tags(self, tags: List[str]) -> List[Machine]:
        """Find machines that have all specified tags"""
        return [m for m in self.machines.values()
                if m.tags and all(tag in m.tags for tag in tags)]

    def find_best_machine(self, required_tags: Optional[List[str]] = None,
                         min_cpu_cores: int = 0, min_memory_gb: float = 0.0) -> Optional[Machine]:
        """Find the best available machine for a task"""
        candidates = self.list_machines(filter_online=True)

        # Filter by tags
        if required_tags:
            candidates = [m for m in candidates if m.tags and all(tag in m.tags for tag in required_tags)]

        # Filter by capabilities
        candidates = [m for m in candidates
                     if m.capabilities.cpu_cores >= min_cpu_cores
                     and m.capabilities.memory_gb >= min_memory_gb]

        if not candidates:
            return None

        # Score machines (lower load is better)
        scored = [(m, m.status.current_load) for m in candidates]
        scored.sort(key=lambda x: x[1])  # Sort by load (ascending)

        return scored[0][0] if scored else None

    def get_group_machines(self, group_name: str) -> List[Machine]:
        """Get all machines in a group"""
        if group_name not in self.groups:
            return []

        machine_ids = self.groups[group_name]
        return [self.machines[mid] for mid in machine_ids if mid in self.machines]

    def discover_machines(self, network_range: str = "192.168.1.0/24") -> List[Machine]:
        """Discover Isaac instances on the network (placeholder)"""
        # This would implement network discovery
        # For now, return empty list
        discovered = []

        # TODO: Implement actual network discovery using:
        # - UDP broadcasts
        # - Service discovery protocols
        # - Known IP ranges scanning

        return discovered

    def _load_registry(self):
        """Load registry from disk"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)

                # Load machines
                for machine_data in data.get('machines', []):
                    # Convert nested dicts back to dataclasses
                    capabilities_data = machine_data.pop('capabilities', {})
                    status_data = machine_data.pop('status', {})

                    machine_data['capabilities'] = MachineCapabilities(**capabilities_data)
                    machine_data['status'] = MachineStatus(**status_data)

                    machine = Machine(**machine_data)
                    self.machines[machine.machine_id] = machine

                # Load groups
                self.groups = data.get('groups', {})

            except Exception as e:
                print(f"Warning: Could not load machine registry: {e}")

    def _save_registry(self):
        """Save registry to disk"""
        try:
            data = {
                'machines': [asdict(m) for m in self.machines.values()],
                'groups': self.groups
            }

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            print(f"Error saving machine registry: {e}")