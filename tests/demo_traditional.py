#!/usr/bin/env python3
"""
Traditional Terminal Demo - Show Isaac's new terminal-like interface
Demonstrates the 3-line status bar with normal terminal behavior below
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isaac.ui.terminal_control import TerminalControl


def demo_traditional_terminal():
    """Demonstrate traditional terminal interface."""
    terminal = TerminalControl()

    print("🎯 Isaac Traditional Terminal Interface Demo")
    print("=" * 60)
    print("This demo shows Isaac's new traditional terminal experience:")
    print("• Top 3 lines: Status bar (refreshes with session/tier/connection info)")
    print("• Everything below: Normal terminal output (no fancy colors/formatting)")
    print("• Isaac responses appear as normal terminal output")
    print("=" * 60)
    print()

    # Setup terminal
    terminal.setup_terminal()

    # Show status bar
    print("✅ Status bar initialized (top 3 lines)")
    print("✅ Ready for normal terminal interaction")
    print()

    # Simulate some terminal interactions
    print("Example interactions:")
    print()

    # Example 1: Normal command
    terminal.print_normal_output("PS C:\\Users\\ndemi\\.claude> ls")
    terminal.print_normal_output("")
    terminal.print_normal_output("    Directory: C:\\Users\\ndemi\\.claude")
    terminal.print_normal_output("")
    terminal.print_normal_output("Mode                 LastWriteTime         Length Name")
    terminal.print_normal_output("----                 -------------         ------ ----")
    terminal.print_normal_output("d-----        10/16/2025   9:11 PM                debug")
    terminal.print_normal_output("d-----        10/14/2025  11:51 PM                downloads")
    terminal.print_normal_output("d-----        10/16/2025   9:15 PM                file-history")
    print()

    # Example 2: AI query
    terminal.print_normal_output("PS C:\\Users\\ndemi\\.claude> isaac who won the baseball game?")
    terminal.print_isaac_response("isaac> The Chicago Cubs won the World Series in 2016.")
    print()

    # Example 3: Unknown command with correction
    terminal.print_normal_output("PS C:\\Users\\ndemi\\.claude> ks")
    terminal.print_isaac_response("isaac> unknown command 'ks', did you mean 'ls' to list the directory? type (y/n)")
    terminal.print_normal_output("PS C:\\Users\\ndemi\\.claude> y")
    terminal.print_isaac_response("isaac> executing...")
    terminal.print_normal_output("PS C:\\Users\\ndemi\\.claude> ls")
    terminal.print_normal_output("")
    terminal.print_normal_output("    Directory: C:\\Users\\ndemi\\.claude")
    terminal.print_normal_output("")
    terminal.print_normal_output("Mode                 LastWriteTime         Length Name")
    terminal.print_normal_output("----                 -------------         ------ ----")
    terminal.print_normal_output("d-----        10/16/2025   9:11 PM                debug")
    print()

    # Example 4: AI query with whois
    terminal.print_normal_output("PS C:\\Users\\ndemi\\.claude> whois babe ruth?")
    terminal.print_isaac_response("isaac> unknown command. was this an 'AIQuery'? type (y/n)")
    terminal.print_normal_output("PS C:\\Users\\ndemi\\.claude> y")
    terminal.print_isaac_response("isaac> I have a name.")
    terminal.print_normal_output("PS C:\\Users\\ndemi\\.claude> isaac who is babe ruth?")
    terminal.print_isaac_response("isaac> Babe Ruth was a baseball player")
    print()

    print("=" * 60)
    print("✨ Traditional Terminal Experience Complete!")
    print()
    print("Key Features:")
    print("• Status bar shows session/tier/connection info")
    print("• All output looks like normal PowerShell/bash")
    print("• Isaac responses integrate seamlessly")
    print("• No colorama or fancy formatting below status lines")
    print("• Feels like a natural terminal extension")

    # Restore terminal
    terminal.restore_terminal()


if __name__ == "__main__":
    demo_traditional_terminal()