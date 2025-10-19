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