# Implementation: Shell Adapters

## Goal
Create shell abstraction layer with base interface and platform-specific implementations (PowerShell, bash).

**Time Estimate:** 30 minutes

**Dependencies:** 02_impl_bootstrap.md (directory structure)

---

## Architecture Overview

```
BaseShellAdapter (abstract interface)
    ├─ PowerShellAdapter (Windows: pwsh > powershell.exe)
    ├─ BashAdapter (Linux: bash -c)
    └─ shell_detector.py (auto-detect at runtime)

All return: CommandResult(success, output, exit_code)
```

---

## File 1: base_adapter.py

**Path:** `isaac/adapters/base_adapter.py`

**Purpose:** Abstract interface all shell adapters implement.

**Complete Implementation:**

```python
"""
Base shell adapter interface.
All platform-specific shells must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result from shell command execution."""
    success: bool
    output: str
    exit_code: int


class BaseShellAdapter(ABC):
    """Abstract interface for shell execution."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Shell name for display purposes.
        
        Returns:
            str: Shell name (e.g., "PowerShell", "bash")
        """
        pass
    
    @abstractmethod
    def execute(self, command: str) -> CommandResult:
        """
        Execute shell command and return result.
        
        Args:
            command: Shell command to execute
            
        Returns:
            CommandResult with success status, output, and exit code
        """
        pass
    
    @abstractmethod
    def detect_available(self) -> bool:
        """
        Check if this shell is available on the system.
        
        Returns:
            bool: True if shell can be used, False otherwise
        """
        pass
```

---

## File 2: powershell_adapter.py

**Path:** `isaac/adapters/powershell_adapter.py`

**Purpose:** PowerShell execution for Windows (pwsh preferred, fallback to powershell.exe).

**Complete Implementation:**

```python
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
```

---

## File 3: bash_adapter.py

**Path:** `isaac/adapters/bash_adapter.py`

**Purpose:** Bash execution for Linux/macOS.

**Complete Implementation:**

```python
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
```

---

## File 4: shell_detector.py

**Path:** `isaac/adapters/shell_detector.py`

**Purpose:** Auto-detect best available shell at runtime.

**Complete Implementation:**

```python
"""
Shell detection logic.
Auto-detects best available shell based on platform.
"""

import platform
from isaac.adapters.powershell_adapter import PowerShellAdapter
from isaac.adapters.bash_adapter import BashAdapter


def detect_shell():
    """
    Detect and return best available shell adapter.
    
    Windows: PowerShell (pwsh > powershell.exe)
    Linux/macOS: bash
    
    Returns:
        BaseShellAdapter: Shell adapter instance
        
    Raises:
        RuntimeError: If no compatible shell found
    """
    system = platform.system()
    
    if system == 'Windows':
        # Try PowerShell
        ps_adapter = PowerShellAdapter()
        if ps_adapter.detect_available():
            return ps_adapter
        
        # No PowerShell found
        raise RuntimeError(
            "Isaac > No compatible shell found. PowerShell required on Windows.\n"
            "Install PowerShell 7+: https://github.com/PowerShell/PowerShell"
        )
    
    else:  # Linux, Darwin (macOS), etc.
        # Try bash
        bash_adapter = BashAdapter()
        if bash_adapter.detect_available():
            return bash_adapter
        
        # No bash found (rare on Linux/macOS)
        raise RuntimeError(
            "Isaac > No compatible shell found. bash required on Linux/macOS."
        )
```

---

## Verification Steps

### 1. Test Base Adapter (Import Check)
```python
from isaac.adapters.base_adapter import BaseShellAdapter, CommandResult

# Test CommandResult
result = CommandResult(success=True, output='test', exit_code=0)
print(f"✅ CommandResult created: {result}")

# Test BaseShellAdapter is abstract
try:
    adapter = BaseShellAdapter()  # Should fail
    print("❌ BaseShellAdapter should be abstract")
except TypeError:
    print("✅ BaseShellAdapter is properly abstract")
```

### 2. Test PowerShell Adapter (Windows Only)
```python
from isaac.adapters.powershell_adapter import PowerShellAdapter

adapter = PowerShellAdapter()
print(f"Shell: {adapter.name}")
print(f"Executable: {adapter.ps_exe}")
print(f"Available: {adapter.detect_available()}")

# Test simple command
result = adapter.execute('echo test')
print(f"Output: {result.output}")
print(f"Success: {result.success}")
print(f"Exit code: {result.exit_code}")

# Should print:
# Shell: PowerShell
# Executable: pwsh (or powershell)
# Available: True
# Output: test
# Success: True
# Exit code: 0
```

### 3. Test Bash Adapter (Linux/macOS Only)
```python
from isaac.adapters.bash_adapter import BashAdapter

adapter = BashAdapter()
print(f"Shell: {adapter.name}")
print(f"Available: {adapter.detect_available()}")

# Test simple command
result = adapter.execute('echo test')
print(f"Output: {result.output.strip()}")
print(f"Success: {result.success}")
print(f"Exit code: {result.exit_code}")

# Should print:
# Shell: bash
# Available: True
# Output: test
# Success: True
# Exit code: 0
```

### 4. Test Shell Detector
```python
from isaac.adapters.shell_detector import detect_shell

shell = detect_shell()
print(f"Detected shell: {shell.name}")

# Test execution
result = shell.execute('echo hello')
print(f"Output: {result.output.strip()}")

# Windows: Detected shell: PowerShell
# Linux: Detected shell: bash
```

### 5. Test Timeout Handling
```python
from isaac.adapters.shell_detector import detect_shell

shell = detect_shell()

# Command that takes too long (sleep 60)
result = shell.execute('sleep 60')  # bash
# OR
result = shell.execute('Start-Sleep -Seconds 60')  # PowerShell

print(result.output)  # Should say "timed out after 30 seconds"
print(result.success)  # Should be False
print(result.exit_code)  # Should be -1
```

---

## Common Pitfalls

⚠️ **PowerShell Not Found on Windows**
- **Symptom:** `RuntimeError: No compatible shell found`
- **Fix:** Install PowerShell 7+ or ensure powershell.exe is in PATH

⚠️ **Timeout Not Working**
- **Symptom:** Commands hang indefinitely
- **Fix:** Ensure `timeout=30` parameter in subprocess.run()

⚠️ **Mixed stdout/stderr**
- **Symptom:** Error messages not visible
- **Fix:** Always combine `result.stdout + result.stderr` in output

⚠️ **Shell Detection Fails**
- **Symptom:** `RuntimeError` on startup
- **Fix:** Check platform.system() returns expected value

⚠️ **Commands with Quotes**
- **Symptom:** Commands fail with syntax errors
- **Fix:** Use proper escaping in command strings

---

## Success Signals

✅ BaseShellAdapter is abstract (cannot instantiate)  
✅ CommandResult dataclass works  
✅ PowerShellAdapter detects pwsh or powershell.exe  
✅ BashAdapter detects bash  
✅ detect_shell() returns correct adapter for platform  
✅ `execute('echo test')` returns "test"  
✅ Timeout works (commands stop after 30s)  
✅ Error handling returns CommandResult with success=False  
✅ Ready for next step (data models)

---

**Next Step:** 05_impl_models.md (Create Preferences and CommandHistory models)

---

**END OF SHELL ADAPTERS IMPLEMENTATION**
