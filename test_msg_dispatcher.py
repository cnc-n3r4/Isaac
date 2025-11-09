#!/usr/bin/env python3
"""
Test dispatcher with /msg filtering
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from isaac.core.session_manager import SessionManager
from isaac.runtime.dispatcher import CommandDispatcher

def test_msg_filtering():
    """Test /msg command filtering through dispatcher"""
    session = SessionManager()
    dispatcher = CommandDispatcher(session)

    # Load commands
    dispatcher.load_commands([
        Path('isaac/commands')
    ])

    print("Testing /msg --a (invalid)")
    result = dispatcher.execute('/msg --a')
    print(f"Result OK: {result.get('ok')}")
    stdout = result.get('stdout', '')
    stderr = result.get('stderr', '')
    print(f"Stdout: {repr(stdout)}")
    print(f"Stderr: {repr(stderr)}")
    print()

    print("Testing /msg --sys")
    result = dispatcher.execute('/msg --sys')
    print(f"Result OK: {result.get('ok')}")
    stdout = result.get('stdout', '')
    print(f"Output:\n{stdout}")
    print()

    print("Testing /msg --code")
    result = dispatcher.execute('/msg --code')
    print(f"Result OK: {result.get('ok')}")
    stdout = result.get('stdout', '')
    print(f"Output:\n{stdout}")
    print()

    print("Testing /msg (all)")
    result = dispatcher.execute('/msg')
    print(f"Result OK: {result.get('ok')}")
    stdout = result.get('stdout', '')
    print(f"Output:\n{stdout}")

if __name__ == "__main__":
    test_msg_filtering()