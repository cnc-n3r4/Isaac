"""
Web Interface - Browser-based access to Isaac

Provides full terminal emulation in web browsers with real-time command execution,
workspace visualization, and navigation.
"""

from .terminal_emulator import TerminalEmulator
from .web_server import WebServer
from .web_terminal import WebTerminal

__all__ = ["WebTerminal", "WebServer", "TerminalEmulator"]
