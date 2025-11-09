"""
Status Command - Standardized Implementation

System status information display.
"""

import socket
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse


class StatusCommand(BaseCommand):
    """Display Isaac system status"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute status command.

        Args:
            args: Command arguments (flags like -v for verbose)
            context: Optional execution context (includes session info)

        Returns:
            CommandResponse with status information
        """
        parser = FlagParser(args)

        # Check for verbose flag
        verbose = parser.has_flag('verbose', aliases=['v'])

        # Get session from context (dispatcher provides this)
        session = context.get("session", {}) if context else {}

        try:
            if verbose:
                # Detailed status with AI session info
                output = self._get_detailed_status(session)
            else:
                # One-line summary
                output = self._get_summary_status(session)

            return CommandResponse(
                success=True,
                data=output,
                metadata={"verbose": verbose}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "EXECUTION_ERROR"}
            )

    def _get_summary_status(self, session: Dict[str, Any]) -> str:
        """Return one-line status summary"""
        machine_id = session.get("machine_id", "unknown")[:6]

        # Check workspace status
        try:
            from isaac.core.workspace_integration import get_workspace_context

            ctx = get_workspace_context()
            context = ctx.get_current_context()

            if context["active"]:
                ws_name = context["workspace"]["name"][:10]
                ws_status = f"✓ {ws_name}"
            else:
                ws_status = "○ none"
        except Exception:
            ws_status = "?"

        # Check AI status
        ai = "✓"  # Assume available

        return f"Session: {machine_id} | Workspace: {ws_status} | AI: {ai}"

    def _get_detailed_status(self, session: Dict[str, Any]) -> str:
        """Return detailed system status with AI session info"""
        lines = []
        lines.append("=" * 60)
        lines.append("ISAAC System Status")
        lines.append("=" * 60)

        # Session info
        machine_id = session.get("machine_id", "unknown")
        lines.append(f"\n📍 Session")
        lines.append(f"  Machine ID: {machine_id}")

        # Workspace status
        lines.append(f"\n🗂️  Workspace")
        try:
            from isaac.core.workspace_integration import get_workspace_context

            ctx = get_workspace_context()
            context = ctx.get_current_context()

            if context["active"]:
                ws = context["workspace"]
                lines.append(f"  ✓ Active: {ws['name']}")
                lines.append(f"  Path: {ws['path']}")

                # AI Session info
                if "session" in context:
                    sess = context["session"]
                    lines.append(f"\n🤖 AI Session")
                    lines.append(f"  ID: {sess['id'][:32]}...")
                    if sess.get("age"):
                        lines.append(f"  Age: {sess['age']}")
                    if sess.get("remaining"):
                        lines.append(f"  Remaining: {sess['remaining']}")
                    lines.append(f"  Rotations: {sess.get('rotations', 0)}")

                # Knowledge base info
                if "knowledge_base" in context and context["knowledge_base"]:
                    kb = context["knowledge_base"]
                    lines.append(f"\n📚 Knowledge Base")
                    lines.append(
                        f"  Collection ID: {kb['collection_id'][:32] if kb.get('collection_id') else 'Not created'}..."
                    )
                    lines.append(f"  Files indexed: {kb['files_indexed']}")

                    if "chunker_stats" in kb:
                        stats = kb["chunker_stats"]
                        lines.append(f"  Chunks created: {stats.get('chunks_created', 0)}")
                        lines.append(f"  AST parsed: {stats.get('ast_parsed', 0)} files")

                    watching = kb.get("watching", False)
                    watch_status = "✓ Active" if watching else "○ Inactive"
                    lines.append(f"  File watcher: {watch_status}")
            else:
                lines.append(f"  ○ No active workspace")
                lines.append(f"  Hint: Navigate to a project directory")
        except Exception as e:
            lines.append(f"  ⚠ Error: {str(e)}")

        # Task Manager status
        lines.append(f"\n⚙️  Background Tasks")
        try:
            from isaac.core.task_manager import get_task_manager

            task_mgr = get_task_manager()
            stats = task_mgr.get_statistics()

            lines.append(f"  Total tasks: {stats['total_tasks']}")
            lines.append(f"  Max concurrent: {stats['max_concurrent']}")

            by_status = stats.get("by_status", {})
            if by_status:
                for status, count in by_status.items():
                    if count > 0:
                        lines.append(f"    {status}: {count}")
        except Exception as e:
            lines.append(f"  ⚠ Error: {str(e)}")

        # Machine orchestration status
        lines.append(f"\n🖥️  Machine Orchestration")
        try:
            from isaac.orchestration import LoadBalancer, MachineRegistry

            registry = MachineRegistry()
            load_balancer = LoadBalancer(registry)

            machines = registry.list_machines(filter_online=True)
            total_machines = len(machines)
            groups = registry.list_groups()

            lines.append(f"  Registered machines: {total_machines}")
            lines.append(f"  Machine groups: {len(groups)}")

            if total_machines > 0:
                # Show machine status summary
                online_count = sum(1 for m in machines if m.status.is_online)
                lines.append(f"  Online machines: {online_count}/{total_machines}")

                # Show top 3 machines by load
                if len(machines) > 0:
                    scores = load_balancer.get_load_scores(machines)
                    lines.append(f"  Load distribution:")
                    for i, score in enumerate(scores[:3]):
                        machine = score.machine
                        load_pct = machine.status.current_load
                        mem_pct = machine.status.memory_usage
                        lines.append(f"    {machine.hostname}: {load_pct:.1f}% CPU, {mem_pct:.1f}% MEM")

            # Show recent load balancing activity
            if hasattr(load_balancer, "performance_history") and load_balancer.performance_history:
                total_executions = sum(
                    len(times) for times in load_balancer.performance_history.values()
                )
                lines.append(f"  Total executions tracked: {total_executions}")

        except Exception as e:
            lines.append(f"  ⚠ Error: {str(e)}")

        # Network info
        lines.append(f"\n🌐 Network")
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            lines.append(f"  Hostname: {hostname}")
            lines.append(f"  IP: {ip}")
        except Exception:
            lines.append(f"  ⚠ Unable to detect network info")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="status",
            description="Display Isaac system status",
            usage="/status [-v|--verbose]",
            examples=[
                "/status",
                "/status -v",
                "/status --verbose"
            ],
            tier=1,  # Safe - read-only information
            aliases=[],
            category="system"
        )
