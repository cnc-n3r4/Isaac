"""
Web Interface - Browser-based access to Isaac

Provides full terminal emulation in web browsers with real-time command execution,
workspace visualization, and navigation.
"""

from .web_terminal import WebTerminal
from .web_server import WebServer
from .terminal_emulator import TerminalEmulator

__all__ = ['WebTerminal', 'WebServer', 'TerminalEmulator']
