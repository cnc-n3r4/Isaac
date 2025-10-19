"""
PowerShell adapter for Windows execution.
Prefers PowerShell 7+ (pwsh) over Windows PowerShell 5.1 (powershell.exe).
"""

import subprocess
import shutil
from isaac.adapters.base_adapter import BaseShellAdapter, CommandResult


class PowerShellAdapter(BaseShellAdapter):
    """Execute commands via PowerShell (Windows)."""
    
    def __init__(self):
        """Initialize PowerShell adapter, detect best available version."""
        self.ps_exe = self._detect_powershell()
    
    @property
    def name(self) -> str:
        """Return shell name."""
        return 'PowerShell'
    
    def execute(self, command: str) -> CommandResult:
        """
        Execute PowerShell command.
        
        Args:
            command: PowerShell command to execute
            
        Returns:
            CommandResult with output and exit code
        """
        try:
            result = subprocess.run(
                [self.ps_exe, '-NoProfile', '-Command', command],
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
        Check if PowerShell is available.
        
        Returns:
            bool: True if PowerShell can be executed
        """
        try:
            result = subprocess.run(
                [self.ps_exe, '-NoProfile', '-Command', 'echo test'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _detect_powershell(self) -> str:
        """
        Detect best available PowerShell version.
        Preference: pwsh (PowerShell 7+) > powershell.exe (5.1)
        
        Returns:
            str: Path to PowerShell executable
        """
        # Try PowerShell 7+ (pwsh)
        if shutil.which('pwsh'):
            return 'pwsh'
        
        # Fall back to Windows PowerShell 5.1
        if shutil.which('powershell'):
            return 'powershell'
        
        # Default to powershell.exe (will fail if not found, but better error)
        return 'powershell.exe'