#!/usr/bin/env python3
"""
Machines Command Handler - Machine orchestration status and management
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def main():
    """Main entry point for machines command"""
    # Read payload from stdin
    payload = json.loads(sys.stdin.read())
    args = payload.get("args", {})
    session = payload.get("session", {})

    action = args.get("action", "status")
    target = args.get("target")
    verbose = args.get("verbose", False)

    try:
        if action == "status":
            output = get_orchestration_status(verbose)
        elif action == "list":
            output = list_machines(verbose)
        elif action == "groups":
            output = list_groups(verbose)
        elif action == "load":
            output = show_load_distribution(verbose)
        elif action == "register":
            output = register_machine(target, args)
        elif action == "unregister":
            output = unregister_machine(target)
        else:
            output = f"Unknown action: {action}"

        # Return envelope
        print(json.dumps({
            "ok": True,
            "kind": "text",
            "stdout": output,
            "meta": {}
        }))

    except Exception as e:
        print(json.dumps({
            "ok": False,
            "kind": "text",
            "stdout": f"Error: {str(e)}",
            "meta": {}
        }))


def get_orchestration_status(verbose: bool = False) -> str:
    """Get overall orchestration status"""
    lines = []
    lines.append("=" * 70)
    lines.append("ISAAC Machine Orchestration Status")
    lines.append("=" * 70)

    try:
        from isaac.orchestration import MachineRegistry, LoadBalancer

        registry = MachineRegistry()
        load_balancer = LoadBalancer(registry)

        machines = registry.list_machines()
        groups = registry.list_groups()

        # Summary stats
        total_machines = len(machines)
        online_machines = sum(1 for m in machines if m.status.is_online)
        total_groups = len(groups)

        lines.append(f"\n📊 Overview")
        lines.append(f"  Total Machines: {total_machines}")
        lines.append(f"  Online Machines: {online_machines}")
        lines.append(f"  Offline Machines: {total_machines - online_machines}")
        lines.append(f"  Machine Groups: {total_groups}")

        if total_machines > 0:
            # System health
            health_score = (online_machines / total_machines) * 100
            health_icon = "🟢" if health_score >= 90 else "🟡" if health_score >= 70 else "🔴"
            lines.append(f"  System Health: {health_icon} {health_score:.1f}%")

            # Load distribution
            if online_machines > 0:
                online_list = [m for m in machines if m.status.is_online]
                scores = load_balancer.get_load_scores(online_list)

                avg_load = sum(s.machine.status.current_load for s in scores) / len(scores)
                avg_memory = sum(s.machine.status.memory_usage for s in scores) / len(scores)

                lines.append(f"  Average Load: {avg_load:.1f}% CPU, {avg_memory:.1f}% Memory")

        if verbose and total_machines > 0:
            lines.append(f"\n🖥️  Machine Details")
            for machine in sorted(machines, key=lambda m: m.hostname):
                status_icon = "🟢" if machine.status.is_online else "🔴"
                load = machine.status.current_load
                memory = machine.status.memory_usage
                lines.append(f"  {status_icon} {machine.hostname}")
                lines.append(f"      ID: {machine.machine_id}")
                lines.append(f"      IP: {machine.ip_address}:{machine.port}")
                lines.append(f"      Load: {load:.1f}% CPU, {memory:.1f}% Memory")
                lines.append(f"      Tags: {', '.join(machine.tags) if machine.tags else 'none'}")

                if machine.capabilities.gpu_count > 0:
                    lines.append(f"      GPU: {machine.capabilities.gpu_count}x ({machine.capabilities.gpu_memory_gb:.1f}GB)")

        if verbose and total_groups > 0:
            lines.append(f"\n👥 Groups")
            for group_name, group_machines in groups.items():
                machine_count = len(group_machines)
                online_count = sum(1 for m in group_machines if m.status.is_online)
                lines.append(f"  {group_name}: {online_count}/{machine_count} online")

        # Load balancing stats
        if hasattr(load_balancer, 'performance_history'):
            total_executions = sum(len(times) for times in load_balancer.performance_history.values())
            if total_executions > 0:
                lines.append(f"\n⚖️  Load Balancing")
                lines.append(f"  Total Executions Tracked: {total_executions}")

                # Show performance leaders
                if load_balancer.performance_history:
                    fastest_machine = min(
                        load_balancer.performance_history.items(),
                        key=lambda x: sum(x[1]) / len(x[1]) if x[1] else float('inf')
                    )
                    if fastest_machine[1]:
                        avg_time = sum(fastest_machine[1]) / len(fastest_machine[1])
                        lines.append(f"  Fastest Machine: {fastest_machine[0]} ({avg_time:.2f}s avg)")

    except Exception as e:
        lines.append(f"\n⚠️  Error loading orchestration status: {str(e)}")

    lines.append("\n" + "=" * 70)
    return "\n".join(lines)


def list_machines(verbose: bool = False) -> str:
    """List all registered machines"""
    try:
        from isaac.orchestration import MachineRegistry

        registry = MachineRegistry()
        machines = registry.list_machines()

        if not machines:
            return "No machines registered. Use '/machines register <hostname>' to add machines."

        lines = []
        lines.append("Registered Machines")
        lines.append("-" * 50)

        for machine in sorted(machines, key=lambda m: m.hostname):
            status_icon = "🟢 ONLINE" if machine.status.is_online else "🔴 OFFLINE"
            lines.append(f"{machine.hostname} - {status_icon}")

            if verbose:
                lines.append(f"  ID: {machine.machine_id}")
                lines.append(f"  IP: {machine.ip_address}:{machine.port}")
                lines.append(f"  CPU: {machine.capabilities.cpu_cores} cores")
                lines.append(f"  Memory: {machine.capabilities.memory_gb:.1f}GB")
                lines.append(f"  Load: {machine.status.current_load:.1f}%")
                lines.append(f"  Tags: {', '.join(machine.tags) if machine.tags else 'none'}")
                lines.append("")

        return "\n".join(lines)

    except Exception as e:
        return f"Error listing machines: {str(e)}"


def list_groups(verbose: bool = False) -> str:
    """List all machine groups"""
    try:
        from isaac.orchestration import MachineRegistry

        registry = MachineRegistry()
        groups = registry.list_groups()

        if not groups:
            return "No machine groups defined. Machines are automatically grouped by tags."

        lines = []
        lines.append("Machine Groups")
        lines.append("-" * 30)

        for group_name, machines in groups.items():
            online_count = sum(1 for m in machines if m.status.is_online)
            total_count = len(machines)
            lines.append(f"{group_name}: {online_count}/{total_count} online")

            if verbose:
                for machine in machines:
                    status = "🟢" if machine.status.is_online else "🔴"
                    lines.append(f"  {status} {machine.hostname}")
                lines.append("")

        return "\n".join(lines)

    except Exception as e:
        return f"Error listing groups: {str(e)}"


def show_load_distribution(verbose: bool = False) -> str:
    """Show current load distribution across machines"""
    try:
        from isaac.orchestration import MachineRegistry, LoadBalancer

        registry = MachineRegistry()
        load_balancer = LoadBalancer(registry)

        machines = registry.list_machines(filter_online=True)

        if not machines:
            return "No online machines available."

        scores = load_balancer.get_load_scores(machines)

        lines = []
        lines.append("Load Distribution (Lower = Better)")
        lines.append("-" * 40)

        for i, score in enumerate(scores, 1):
            machine = score.machine
            rank_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            lines.append(f"{rank_icon} {machine.hostname}: {score.score:.3f}")

            if verbose:
                factors = score.factors
                lines.append(f"    CPU: {factors['cpu']:.3f}, Memory: {factors['memory']:.3f}, Load: {factors['load']:.3f}")
                if 'performance' in factors:
                    lines.append(f"    Performance: {factors['performance']:.3f}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error showing load distribution: {str(e)}"


def register_machine(target: str, args: Dict[str, Any]) -> str:
    """Register a new machine"""
    if not target:
        return "Usage: /machines register <hostname> [--ip <ip>] [--port <port>] [--tags <tag1,tag2>]"

    try:
        from isaac.orchestration import MachineRegistry
        from isaac.orchestration.registry import Machine, MachineCapabilities, MachineStatus

        registry = MachineRegistry()

        # Basic machine creation (would be enhanced with actual detection)
        ip = args.get("ip", "127.0.0.1")
        port = int(args.get("port", 8080))
        tags_str = args.get("tags", "")
        tags = [tag.strip() for tag in tags_str.split(",")] if tags_str else []

        # Create machine with default capabilities
        machine = Machine(
            machine_id=f"{target}_{ip}",
            hostname=target,
            ip_address=ip,
            port=port,
            capabilities=MachineCapabilities(),
            status=MachineStatus(),
            tags=tags
        )

        if registry.register_machine(machine):
            return f"Successfully registered machine: {target}"
        else:
            return f"Failed to register machine: {target}"

    except Exception as e:
        return f"Error registering machine: {str(e)}"


def unregister_machine(target: str) -> str:
    """Unregister a machine"""
    if not target:
        return "Usage: /machines unregister <machine_id>"

    try:
        from isaac.orchestration import MachineRegistry

        registry = MachineRegistry()

        if registry.unregister_machine(target):
            return f"Successfully unregistered machine: {target}"
        else:
            return f"Machine not found: {target}"

    except Exception as e:
        return f"Error unregistering machine: {str(e)}"


if __name__ == "__main__":
    main()