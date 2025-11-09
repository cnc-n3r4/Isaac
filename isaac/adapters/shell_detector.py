"""
Shell detection logic.
Auto-detects best available shell based on platform.
"""

import platform

from isaac.adapters.bash_adapter import BashAdapter
from isaac.adapters.powershell_adapter import PowerShellAdapter


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

    if system == "Windows":
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
        raise RuntimeError("Isaac > No compatible shell found. bash required on Linux/macOS.")
