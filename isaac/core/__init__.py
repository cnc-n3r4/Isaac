"""
Isaac Core Module - Hybrid C++/Python Implementation
Automatically uses C++ components when available, falls back to Python implementations.
"""

import sys
import os

# Try to import C++ extensions first
try:
    from isaac.isaac_core import (
        CommandResult,
        TierValidator,
        ShellAdapter,
        SessionManager,
        CommandRouter
    )
    USING_CPP_CORE = True
    print("Isaac > Using C++ core components", file=sys.stderr)

except ImportError:
    # Fall back to Python implementations
    from .isaac_core_fallback import (
        CommandResult,
        TierValidator,
        ShellAdapter,
        SessionManager,
        CommandRouter
    )
    USING_CPP_CORE = False
    print("Isaac > Using Python fallback implementations", file=sys.stderr)

__all__ = [
    'CommandResult',
    'TierValidator',
    'ShellAdapter',
    'SessionManager',
    'CommandRouter',
    'USING_CPP_CORE'
]