"""
Bash adapter for Linux/macOS execution.
"""

import subprocess
from isaac.adapters.base_adapter import BaseShellAdapter, CommandResult


class BashAdapter(BaseShellAdapter):
    """Execute commands via bash (Linux/macOS)."""
    
    @property
    def name(self) -> str:
        """Return shell name."""
        return 'bash'
    
    def execute(self, command: str) -> CommandResult:
        """
        Execute bash command.
        
        Args:
            command: Bash command to execute
            
        Returns:
            CommandResult with output and exit code
        """
        try:
            result = subprocess.run(
                ['bash', '-c', command],
                capture_output=True,
                text=True,
                timeout=30  # Prevent hanging commands
            )
            
            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout + result.stderr,
                exit_code=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                output='Isaac > Command timed out after 30 seconds',
                exit_code=-1
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                output=f'Isaac > Execution error: {str(e)}',
                exit_code=-1
            )
    
    def detect_available(self) -> bool:
        """
        Check if bash is available.
        
        Returns:
            bool: True if bash can be executed
        """
        try:
            result = subprocess.run(
                ['bash', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False