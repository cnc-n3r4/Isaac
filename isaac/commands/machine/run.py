#!/usr/bin/env python3
"""
Machine Registry Command - Multi-machine orchestration
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add the isaac package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.orchestration import MachineRegistry, Machine, MachineStatus


class MachineCommand:
    """Machine registry management command"""

    def __init__(self):
        self.registry = MachineRegistry()

    def execute(self, args: Dict[str, Any]) -> str:
        """Execute the machine command"""

        # Normalize argument names (convert dashes to underscores)
        normalized_args = {}
        for key, value in args.items():
            normalized_key = key.replace('-', '_')
            normalized_args[normalized_key] = value

        action = normalized_args.get('action')

        if action == 'register':
            return self._register_machine(normalized_args)
        elif action == 'unregister':
            return self._unregister_machine(normalized_args)
        elif action == 'list':
            return self._list_machines()
        elif action == 'show':
            return self._show_machine(normalized_args)
        elif action == 'status':
            return self._update_status(normalized_args)
        elif action == 'group':
            return self._create_group(normalized_args)
        elif action == 'groups':
            return self._list_groups()
        elif action == 'discover':
            return self._discover_machines()
        elif action == 'find':
            return self._find_machines(normalized_args)
        else:
            return "❌ Invalid action. Use: register, unregister, list, show, status, group, groups, discover, find"

    def _register_machine(self, args: Dict[str, Any]) -> str:
        """Register a new machine"""
        hostname = args.get('hostname')
        ip_address = args.get('ip_address')
        port = args.get('port', 8080)
        tags_str = args.get('tags', '')

        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(',')] if tags_str else []

        if not hostname or not ip_address:
            return "❌ Hostname and IP address required. Use: /machine register --hostname <host> --ip-address <ip> [--port <port>] [--tags <tags>]"

        # Create machine instance
        import uuid
        from isaac.orchestration.registry import MachineCapabilities, MachineStatus

        machine_id = str(uuid.uuid4())[:8]
        capabilities = MachineCapabilities.detect()  # This will detect local capabilities
        status = MachineStatus(is_online=True, last_seen=time.time())

        machine = Machine(
            machine_id=machine_id,
            hostname=hostname,
            ip_address=ip_address,
            port=port,
            capabilities=capabilities,
            status=status,
            tags=tags
        )

        if self.registry.register_machine(machine):
            return f"✅ Registered machine '{hostname}' ({machine_id}) with {capabilities.cpu_cores} CPU cores, {capabilities.memory_gb}GB RAM"
        else:
            return "❌ Failed to register machine"

    def _unregister_machine(self, args: Dict[str, Any]) -> str:
        """Unregister a machine"""
        machine_id = args.get('machine_id')
        if not machine_id:
            return "❌ Machine ID required. Use: /machine unregister --machine-id <id>"

        if self.registry.unregister_machine(machine_id):
            return f"✅ Unregistered machine '{machine_id}'"
        else:
            return f"❌ Machine '{machine_id}' not found"

    def _list_machines(self) -> str:
        """List all registered machines"""
        machines = self.registry.list_machines()

        if not machines:
            return "🖥️ No machines registered. Register one with: /machine register --hostname <host> --ip-address <ip>"

        result = f"🖥️ Registered Machines ({len(machines)}):\n\n"

        for machine in machines:
            status_icon = "🟢" if machine.status.is_online else "🔴"
            result += f"{status_icon} {machine.hostname} ({machine.machine_id})\n"
            result += f"  IP: {machine.ip_address}:{machine.port}\n"
            result += f"  CPU: {machine.capabilities.cpu_cores} cores, RAM: {machine.capabilities.memory_gb}GB\n"
            if machine.capabilities.gpu_count > 0:
                result += f"  GPU: {machine.capabilities.gpu_count} GPUs ({machine.capabilities.gpu_memory_gb}GB)\n"
            if machine.tags:
                result += f"  Tags: {', '.join(machine.tags)}\n"
            result += f"  Status: {machine.status.status_message}\n"
            result += "\n"

        return result

    def _show_machine(self, args: Dict[str, Any]) -> str:
        """Show detailed machine information"""
        machine_id = args.get('machine_id')
        if not machine_id:
            return "❌ Machine ID required. Use: /machine show --machine-id <id>"

        machine = self.registry.get_machine(machine_id)
        if not machine:
            return f"❌ Machine '{machine_id}' not found"

        result = f"🖥️ Machine: {machine.hostname} ({machine.machine_id})\n"
        result += f"IP Address: {machine.ip_address}:{machine.port}\n"
        result += f"Status: {'Online' if machine.status.is_online else 'Offline'}\n"
        result += f"Last Seen: {self._format_timestamp(machine.status.last_seen)}\n\n"

        # Capabilities
        caps = machine.capabilities
        result += "Capabilities:\n"
        result += f"  OS: {caps.os}\n"
        result += f"  Architecture: {caps.architecture}\n"
        result += f"  Python: {caps.python_version}\n"
        result += f"  CPU: {caps.cpu_cores} cores ({caps.cpu_threads} threads)\n"
        result += f"  Memory: {caps.memory_gb}GB\n"
        result += f"  Disk: {caps.disk_gb}GB\n"
        if caps.gpu_count > 0:
            result += f"  GPU: {caps.gpu_count} GPUs ({caps.gpu_memory_gb}GB)\n"
        result += f"  Docker: {'Yes' if caps.has_docker else 'No'}\n"
        result += f"  Kubernetes: {'Yes' if caps.has_kubernetes else 'No'}\n\n"

        # Current status
        status = machine.status
        result += "Current Status:\n"
        result += f"  CPU Load: {status.current_load}%\n"
        result += f"  Memory Usage: {status.memory_usage}%\n"
        result += f"  Active Tasks: {status.active_tasks}\n"
        result += f"  Message: {status.status_message}\n\n"

        # Tags and metadata
        if machine.tags:
            result += f"Tags: {', '.join(machine.tags)}\n"

        if machine.metadata:
            result += f"Metadata: {machine.metadata}\n"

        return result

    def _update_status(self, args: Dict[str, Any]) -> str:
        """Update machine status"""
        machine_id = args.get('machine_id')
        if not machine_id:
            return "❌ Machine ID required. Use: /machine status --machine-id <id>"

        machine = self.registry.get_machine(machine_id)
        if not machine:
            return f"❌ Machine '{machine_id}' not found"

        # Update with current system status
        import psutil
        status = MachineStatus(
            is_online=True,
            last_seen=time.time(),
            current_load=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent,
            status_message="Status updated"
        )

        if self.registry.update_machine_status(machine_id, status):
            return f"✅ Updated status for machine '{machine.hostname}'"
        else:
            return f"❌ Failed to update status for machine '{machine_id}'"

    def _create_group(self, args: Dict[str, Any]) -> str:
        """Create a machine group"""
        group_name = args.get('group_name')
        members_str = args.get('group_members', '')

        if not group_name or not members_str:
            return "❌ Group name and members required. Use: /machine group --group-name <name> --group-members <id1,id2,id3>"

        members = [mid.strip() for mid in members_str.split(',') if mid.strip()]

        if self.registry.create_group(group_name, members):
            return f"✅ Created group '{group_name}' with {len(members)} machines"
        else:
            return f"❌ Failed to create group '{group_name}' (invalid machine IDs?)"

    def _list_groups(self) -> str:
        """List all machine groups"""
        groups = self.registry.list_groups()

        if not groups:
            return "📁 No machine groups defined. Create one with: /machine group --group-name <name> --group-members <ids>"

        result = f"📁 Machine Groups ({len(groups)}):\n\n"

        for group_name, machines in groups.items():
            result += f"• {group_name} ({len(machines)} machines)\n"
            for machine in machines:
                result += f"  - {machine.hostname} ({machine.machine_id})\n"
            result += "\n"

        return result

    def _discover_machines(self) -> str:
        """Discover machines on the network"""
        discovered = self.registry.discover_machines()

        if not discovered:
            return "🔍 No machines discovered on network (discovery not yet implemented)"

        result = f"🔍 Discovered Machines ({len(discovered)}):\n\n"
        for machine in discovered:
            result += f"• {machine.hostname} ({machine.ip_address})\n"

        return result

    def _find_machines(self, args: Dict[str, Any]) -> str:
        """Find machines by criteria"""
        filter_tags_str = args.get('filter_tags', '')
        min_cpu = args.get('min_cpu', 0)
        min_memory = args.get('min_memory', 0.0)

        # Parse filter tags
        filter_tags = [tag.strip() for tag in filter_tags_str.split(',')] if filter_tags_str else []

        # Find machines by tags
        if filter_tags:
            machines = self.registry.find_machines_by_tags(filter_tags)
        else:
            machines = self.registry.list_machines(filter_online=True)

        # Filter by capabilities
        machines = [m for m in machines
                   if m.capabilities.cpu_cores >= min_cpu
                   and m.capabilities.memory_gb >= min_memory]

        if not machines:
            criteria = []
            if filter_tags:
                criteria.append(f"tags: {', '.join(filter_tags)}")
            if min_cpu > 0:
                criteria.append(f"min CPU: {min_cpu} cores")
            if min_memory > 0:
                criteria.append(f"min memory: {min_memory}GB")

            criteria_str = ", ".join(criteria) if criteria else "online status"
            return f"🔍 No machines found matching criteria: {criteria_str}"

        # Find best machine
        best_machine = self.registry.find_best_machine(filter_tags, min_cpu, min_memory)

        result = f"🔍 Found Machines ({len(machines)}):\n\n"

        for machine in machines:
            marker = " ⭐ BEST" if machine == best_machine else ""
            result += f"• {machine.hostname} ({machine.machine_id}){marker}\n"
            result += f"  CPU: {machine.capabilities.cpu_cores} cores, Load: {machine.status.current_load}%\n"
            result += f"  Memory: {machine.capabilities.memory_gb}GB, Usage: {machine.status.memory_usage}%\n"
            if machine.tags:
                result += f"  Tags: {', '.join(machine.tags)}\n"
            result += "\n"

        return result

    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp for display"""
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Main entry point"""
    import sys

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python run.py <action> [options]")
        print("Actions: register, unregister, list, show, status, group, groups, discover, find")
        print("Options:")
        print("  --machine-id <id>        Machine ID for operations")
        print("  --hostname <host>        Hostname for registration")
        print("  --ip-address <ip>        IP address for registration")
        print("  --port <port>            Port for registration (default: 8080)")
        print("  --tags <tags>            Comma-separated tags")
        print("  --group-name <name>      Group name")
        print("  --group-members <ids>    Comma-separated machine IDs")
        print("  --filter-tags <tags>     Tags to filter by")
        print("  --min-cpu <cores>        Minimum CPU cores")
        print("  --min-memory <gb>        Minimum memory GB")
        return

    action = sys.argv[1]
    args = {'action': action}

    # Parse additional arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith('--'):
            key = arg[2:]  # Remove --
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                value = sys.argv[i + 1]
                args[key] = value
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1

    command = MachineCommand()
    result = command.execute(args)
    print(result)


if __name__ == "__main__":
    main()