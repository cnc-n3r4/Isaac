#!/usr/bin/env python3#!/usr/bin/env python3

""""""

Quick test script for /togrok command integrationQuick test script for /togrok command integration

""""""



import sysimport sys

import osimport os

sys.path.insert(0, os.path.dirname(__file__))sys.path.insert(0, os.path.dirname(__file__))



from isaac.commands.togrok_handler import TogrokHandlerfrom isaac.ui.permanent_shell import PermanentShell

from isaac.core.session_manager import SessionManagerfrom isaac.core.session_manager import SessionManager



def test_togrok_integration():def test_togrok_integration():

    """Test that /togrok commands work correctly."""    """Test that /togrok commands are properly routed."""

    print("Testing /togrok command integration...")    print("Testing /togrok command integration...")



    # Create session manager and handler    # Create a mock session manager and shell

    session_manager = SessionManager()    session_manager = SessionManager()

    handler = TogrokHandler(session_manager)

    # Create shell instance (but don't start the interactive loop)

    # Test command parsing and handling    shell = PermanentShell.__new__(PermanentShell)

    test_commands = [    shell.session_manager = session_manager

        "/togrok help",    shell.togrok_handler = None  # We'll test the handler separately

        "/togrok list",

        "/togrok grokbug testproject"    # Test command parsing

    ]    test_commands = [

        "/togrok help",

    for cmd in test_commands:        "/togrok list",

        print(f"\nTesting command: {cmd}")        "/togrok grokbug testproject"

        parts = cmd.strip().split()    ]

        if parts and parts[0].lower() == "/togrok":

            args = parts[1:]  # Remove "/togrok" prefix    for cmd in test_commands:

        else:        print(f"\nTesting command: {cmd}")

            args = parts        parts = cmd.strip().split()

        print(f"Parsed args: {args}")        if parts and parts[0].lower() == "/togrok":

            args = parts[1:]  # Remove "/togrok" prefix

        try:        else:

            result = handler.handle_command(args)            args = parts

            print(f"Handler result: {result[:200]}..." if len(result) > 200 else f"Handler result: {result}")        print(f"Parsed args: {args}")

        except Exception as e:

            print(f"Error: {e}")        # Test with actual handler

        if shell.togrok_handler is None:

if __name__ == "__main__":            from isaac.commands.togrok_handler import TogrokHandler

    test_togrok_integration()            shell.togrok_handler = TogrokHandler(session_manager)

        try:
            result = shell.togrok_handler.handle_command(args)
            print(f"Handler result: {result[:100]}..." if len(result) > 100 else f"Handler result: {result}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_togrok_integration()