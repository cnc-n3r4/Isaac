"""
Device routing strategy - handles !alias commands.
"""

from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy
from isaac.orchestration import LoadBalancingStrategy, RemoteExecutor


class DeviceRoutingStrategy(CommandStrategy):
    """Strategy for handling device routing commands (!alias)."""

    def can_handle(self, input_text: str) -> bool:
        """Check if command starts with !."""
        return input_text.startswith("!")

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Route command to device via local network or cloud."""
        # Parse device alias and command
        parts = input_text[1:].split(None, 1)  # Remove ! and split on first space
        if len(parts) != 2:
            return CommandResult(
                success=False,
                output="Usage: !device_alias /command\n       !device_alias:strategy /command",
                exit_code=1,
            )

        device_spec, device_cmd = parts

        # Parse device spec for strategy (alias:strategy)
        if ":" in device_spec:
            device_alias, strategy_name = device_spec.split(":", 1)
            # Map strategy names to enum values
            strategy_map = {
                "round_robin": LoadBalancingStrategy.ROUND_ROBIN,
                "least_load": LoadBalancingStrategy.LEAST_LOAD,
                "weighted": LoadBalancingStrategy.WEIGHTED_LEAST_LOAD,
                "random": LoadBalancingStrategy.RANDOM,
                "resource": LoadBalancingStrategy.RESOURCE_AWARE,
                "performance": LoadBalancingStrategy.PERFORMANCE_BASED,
            }
            strategy = strategy_map.get(strategy_name.lower(), LoadBalancingStrategy.LEAST_LOAD)
        else:
            device_alias = device_spec
            strategy = LoadBalancingStrategy.LEAST_LOAD

        # Initialize remote executor
        from isaac.orchestration import MachineRegistry

        registry = MachineRegistry()
        remote_executor = RemoteExecutor(registry)

        # Try local network execution first
        try:
            # Check if device_alias is a registered machine
            machine = registry.get_machine(device_alias)

            if machine:
                # Execute on specific machine
                print(f"Isaac > Executing on {device_alias}: {device_cmd}")
                result = remote_executor.execute_on_machine(machine.machine_id, device_cmd)

                if result.success:
                    return CommandResult(
                        success=True,
                        output=f"[{device_alias}] {result.output}",
                        exit_code=result.exit_code,
                    )
                else:
                    return CommandResult(
                        success=False,
                        output=f"[{device_alias}] Error: {result.error_message}",
                        exit_code=result.exit_code,
                    )

            # Check if device_alias is a group name
            group_machines = registry.get_group_machines(device_alias)
            if group_machines:
                # Use load balancing for group execution
                print(
                    f"Isaac > Load balancing across group '{device_alias}' ({len(group_machines)} machines): {device_cmd}"
                )
                result = remote_executor.execute_with_load_balancing(
                    device_cmd,
                    strategy=strategy,
                    group_name=device_alias,
                    command_complexity="normal",  # Could be inferred from command
                )

                if result.success:
                    return CommandResult(
                        success=True,
                        output=f"[{device_alias}] {result.output}",
                        exit_code=result.exit_code,
                    )
                else:
                    return CommandResult(
                        success=False,
                        output=f"[{device_alias}] Error: {result.error_message}",
                        exit_code=result.exit_code,
                    )

        except Exception as e:
            # Log error but continue to cloud routing
            print(f"Isaac > Local execution failed: {e}")

        # Try cloud routing (fallback)
        try:
            if self.session.cloud and self.session.cloud.is_available():
                success = self.session.cloud.route_command(device_alias, device_cmd)
                if success:
                    return CommandResult(
                        success=True,
                        output=f"Command routed to {device_alias} via cloud",
                        exit_code=0,
                    )
        except Exception:
            pass  # Fall through to queuing

        # Queue for later sync if all else fails
        validator = context.get("validator")
        tier = validator.get_tier(device_cmd) if validator else 3

        queue_id = self.session.queue.enqueue(
            command=device_cmd,
            command_type="device_route",
            target_device=device_alias,
            metadata={"tier": tier},
        )

        return CommandResult(
            success=True,
            output=f"Command queued (#{queue_id}) - will sync when online",
            exit_code=0,
        )

    def get_help(self) -> str:
        """Get help text for device routing."""
        return "Device routing: !device_alias <command> - Route command to remote device"

    def get_priority(self) -> int:
        """Medium-high priority."""
        return 35
