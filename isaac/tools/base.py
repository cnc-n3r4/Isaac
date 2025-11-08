"""
Base Tool Interface for Isaac Tools
Provides standard interface for all file operation tools
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """Base class for all Isaac tools"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (e.g., 'read', 'write', 'edit')"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of what the tool does"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.

        Returns:
            dict: Result in standard format:
            {
                'success': bool,
                'content': str (optional),
                'error': str (optional),
                ... (tool-specific fields)
            }
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tool to dictionary format for AI tool calling.

        Returns:
            dict: Tool definition in Claude/OpenAI tool format
        """
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.get_parameters_schema()
        }

    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for tool parameters.

        Returns:
            dict: JSON schema for parameters
        """
        pass

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate tool execution result format.

        Args:
            result: Result from execute()

        Returns:
            bool: True if result is valid
        """
        return isinstance(result, dict) and 'success' in result
