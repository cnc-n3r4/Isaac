"""
Fallback Python implementations for C++ core components.
Used when C++ extensions are not available or fail to build.
"""

from dataclasses import dataclass
from typing import Optional
import subprocess
import os
import platform

@dataclass
class CommandResult:
    """Result from shell command execution."""
    success: bool
    output: str
    exit_code: int

class TierValidator:
    """Python fallback for tier validation."""

    def __init__(self):
        self.tier_defaults = self._load_tier_defaults()

    def _load_tier_defaults(self):
        """Load default tier classifications."""
        return {
            "1": [
                "ls", "cd", "clear", "cls", "pwd", "echo", "cat", "type",
                "Get-ChildItem", "Set-Location", "Get-Location"
            ],
            "2": ["grep", "Select-String", "head", "tail", "sort", "uniq"],
            "2.5": ["find", "sed", "awk", "Where-Object", "ForEach-Object"],
            "3": [
                "cp", "mv", "git", "npm", "pip", "reset",
                "Copy-Item", "Move-Item", "New-Item", "Remove-Item"
            ],
            "4": ["rm", "del", "format", "dd", "Remove-Item", "Format-Volume", "Clear-Disk"]
        }

    def get_tier(self, command: str) -> float:
        """Get safety tier for a command."""
        if not command or not command.strip():
            return 3.0

        # Extract base command (first word) - keep original case for case-sensitive matching
        base_cmd = command.strip().split()[0]

        for tier_str, commands in self.tier_defaults.items():
            if base_cmd in commands:
                return float(tier_str) if "." in tier_str else int(tier_str)

        return 3.0

    def is_safe(self, command: str) -> bool:
        return self.get_tier(command) <= 2.0

    def requires_confirmation(self, command: str) -> bool:
        return self.get_tier(command) == 2.5

    def requires_validation(self, command: str) -> bool:
        return self.get_tier(command) >= 3.0

class ShellAdapter:
    """Python fallback for shell execution."""

    def __init__(self):
        self.system = platform.system().lower()

    def execute(self, command: str) -> CommandResult:
        """Execute shell command."""
        try:
            if self.system == "windows":
                # Use subprocess with shell=True for Windows
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                # Use subprocess with shell=True for Unix-like systems
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout + result.stderr,
                exit_code=result.returncode
            )

        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                output="Isaac > Command timed out after 30 seconds",
                exit_code=-1
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output=f"Isaac > Execution error: {str(e)}",
                exit_code=-1
            )

    def execute_with_timeout(self, command: str, timeout_seconds: int) -> CommandResult:
        """Execute with custom timeout."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )

            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout + result.stderr,
                exit_code=result.returncode
            )

        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                output=f"Isaac > Command timed out after {timeout_seconds} seconds",
                exit_code=-1
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output=f"Isaac > Execution error: {str(e)}",
                exit_code=-1
            )

    def get_shell_name(self) -> str:
        """Get shell name."""
        if self.system == "windows":
            return "PowerShell/cmd"
        else:
            return os.environ.get("SHELL", "bash")

    def is_available(self) -> bool:
        """Check if shell is available."""
        return True  # Basic subprocess should always be available

class SessionManager:
    """Python fallback for session management."""

    def __init__(self):
        pass

    def get_user_id(self) -> str:
        return os.environ.get("USER", os.environ.get("USERNAME", "default_user"))

    def is_authenticated(self) -> bool:
        return True  # Fallback - always authenticated

class CommandRouter:
    """Python fallback for command routing."""

    def __init__(self, session_mgr, shell):
        self.session = session_mgr
        self.shell = shell
        self.validator = TierValidator()

    def route_command(self, input_text: str) -> CommandResult:
        """Route command through basic validation."""
        # Simple routing logic
        input_lower = input_text.lower().strip()

        if input_lower in ["exit", "quit", "q"]:
            return CommandResult(True, "Isaac > Goodbye!", 0)
        elif input_lower.startswith("/help"):
            return CommandResult(True, "Isaac > Help: Basic command routing active (Python fallback)", 0)
        elif input_lower.startswith("isaac"):
            query = input_text[5:].strip()
            return CommandResult(True, f"Isaac > AI query: {query} (Python processing)", 0)
        elif input_text.startswith("/"):
            return CommandResult(False, "Isaac > Meta command not implemented in fallback", -1)
        else:
            # Execute with basic validation
            tier = self.validator.get_tier(input_text)
            if tier >= 4.0:
                return CommandResult(False, "Isaac > Command blocked (Tier 4 - lockdown)", -1)
            elif tier >= 3.0:
                result = self.shell.execute(input_text)
                result.output = "Isaac > Warning: Tier 3 command executed\n" + result.output
                return result
            else:
                return self.shell.execute(input_text)

    def get_help(self) -> str:
        return "Isaac Command Router (Python Fallback)\nBasic routing with safety validation"