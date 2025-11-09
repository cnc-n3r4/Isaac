"""
Shell Execution Tool - Safe command execution for Isaac Agent
Integrates with tier validation and shell adapters for controlled command execution
"""

from typing import Any, Dict

from .base import BaseTool


class ShellTool(BaseTool):
    """Execute shell commands with safety validation"""

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Execute shell commands safely with tier-based validation. Use for package management, system queries, and safe administrative tasks."

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute (will be validated for safety)",
                },
                "working_directory": {
                    "type": "string",
                    "description": "Working directory for command execution (optional)",
                    "default": ".",
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Command timeout in seconds (optional, default 30)",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 300,
                },
            },
            "required": ["command"],
        }

    def _get_tier_validator(self):
        """Lazy load tier validator to avoid circular imports"""
        try:
            from ..core.tier_validator import TierValidator
            from ..models.preferences import Preferences

            # Create a basic preferences object for validation
            prefs = Preferences(machine_id="agent-shell-tool")
            return TierValidator(prefs)
        except ImportError:
            return None

    def _get_shell_adapter(self):
        """Lazy load appropriate shell adapter"""
        try:
            from ..adapters.shell_detector import detect_shell

            return detect_shell()
        except ImportError:
            return None

    def _is_safe_command(self, command: str) -> tuple[bool, str]:
        """
        Validate command safety using tier system

        Returns:
            tuple: (is_safe, reason)
        """
        validator = self._get_tier_validator()
        if not validator:
            return False, "Could not load tier validator"

        tier = validator.get_tier(command)

        if tier <= 2:
            return True, f"Tier {tier}: Safe command"
        elif tier == 2.5:
            return True, f"Tier {tier}: Requires confirmation (auto-approved for agent)"
        elif tier == 3:
            return True, f"Tier {tier}: Moderate risk, validated for agent use"
        else:
            return False, f"Tier {tier}: Dangerous command blocked"

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute shell command with safety validation

        Args:
            command: Shell command to execute
            working_directory: Working directory (optional)
            timeout_seconds: Timeout in seconds (optional)

        Returns:
            dict: Execution result
        """
        command = kwargs.get("command", "").strip()
        working_directory = kwargs.get("working_directory", ".")
        timeout_seconds = kwargs.get("timeout_seconds", 30)

        if not command:
            return {
                "success": False,
                "error": "No command provided",
                "tier": None,
                "executed": False,
            }

        # Validate command safety
        validator = self._get_tier_validator()
        is_safe, reason = self._is_safe_command(command)

        if not is_safe:
            tier = validator.get_tier(command) if validator else None
            return {
                "success": False,
                "error": f"Command blocked: {reason}",
                "tier": tier,
                "executed": False,
                "command": command,
            }

        # Get shell adapter
        adapter = self._get_shell_adapter()
        if not adapter:
            return {
                "success": False,
                "error": "Could not initialize shell adapter",
                "tier": None,
                "executed": False,
            }

        try:
            # Execute command
            result = adapter.execute(command)

            return {
                "success": result.success,
                "output": result.output,
                "exit_code": result.exit_code,
                "tier": validator.get_tier(command) if validator else None,
                "executed": True,
                "command": command,
                "working_directory": working_directory,
                "timeout_seconds": timeout_seconds,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "tier": validator.get_tier(command) if validator else None,
                "executed": False,
                "command": command,
            }
