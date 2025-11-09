"""
Tool Registry System
Dynamic tool discovery, registration, and management for agentic execution
"""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, Any, List, Type, Optional
from .base import BaseTool


class ToolRegistry:
    """
    Dynamic tool loading with capability detection and safety.

    Manages tool discovery, registration, and provides tools to AI agents.
    """

    def __init__(self):
        self.tools: Dict[str, Type[BaseTool]] = {}
        self.tool_instances: Dict[str, BaseTool] = {}
        self.capabilities: Dict[str, List[str]] = {}
        self.load_tools()

    def load_tools(self):
        """Auto-discover and load tools from isaac.tools package"""
        # Get the tools package path
        tools_package = Path(__file__).parent

        # Import all tool modules
        for _, module_name, _ in pkgutil.iter_modules([str(tools_package)]):
            if module_name in ['base', '__init__', 'registry']:  # Skip non-tool modules
                continue

            try:
                # Import the module
                module = importlib.import_module(f'isaac.tools.{module_name}')

                # Find all BaseTool subclasses in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, BaseTool) and
                        obj != BaseTool):

                        self._register_tool(obj)

            except Exception as e:
                print(f"Warning: Failed to load tools from {module_name}: {e}")

    def _register_tool(self, tool_class: Type[BaseTool]):
        """Register a tool class"""
        try:
            # Create instance to get metadata
            instance = tool_class()
            tool_name = instance.name

            # Store the class and instance
            self.tools[tool_name] = tool_class
            self.tool_instances[tool_name] = instance

            # Extract capabilities from tool description and schema
            self._extract_capabilities(tool_name, instance)

            print(f"✅ Registered tool: {tool_name}")

        except Exception as e:
            print(f"Warning: Failed to register tool {tool_class.__name__}: {e}")

    def _extract_capabilities(self, tool_name: str, instance: BaseTool):
        """Extract capabilities from tool metadata"""
        capabilities = []

        # Analyze description for keywords
        desc_lower = instance.description.lower()
        if any(word in desc_lower for word in ['read', 'view', 'display']):
            capabilities.append('read')
        if any(word in desc_lower for word in ['write', 'create', 'edit', 'modify']):
            capabilities.append('write')
        if any(word in desc_lower for word in ['search', 'find', 'grep', 'query']):
            capabilities.append('search')
        if any(word in desc_lower for word in ['analyze', 'check', 'validate']):
            capabilities.append('analyze')

        # Analyze parameters for additional capabilities
        schema = instance.get_parameters_schema()
        if 'properties' in schema:
            props = schema['properties']
            if 'file_path' in props:
                capabilities.append('file_operations')
            if 'pattern' in props or 'query' in props:
                capabilities.append('pattern_matching')
            if 'directory' in props or 'path' in props:
                capabilities.append('filesystem')

        self.capabilities[tool_name] = list(set(capabilities))  # Remove duplicates

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool instance by name"""
        return self.tool_instances.get(name)

    def get_tool_class(self, name: str) -> Optional[Type[BaseTool]]:
        """Get a tool class by name"""
        return self.tools.get(name)

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools in OpenAI format"""
        return [instance.to_dict() for instance in self.tool_instances.values()]

    def get_tools_for_capability(self, capability: str) -> List[str]:
        """Get tool names that have a specific capability"""
        return [name for name, caps in self.capabilities.items() if capability in caps]

    def get_tools_for_task(self, task_type: str) -> List[Dict[str, Any]]:
        """Return relevant tools for task type in OpenAI format"""
        if task_type == "coding":
            relevant_tools = ['read', 'grep', 'glob']
        elif task_type == "file_operations":
            relevant_tools = ['read', 'grep', 'glob']
        elif task_type == "analysis":
            relevant_tools = ['grep', 'read']
        elif task_type == "search":
            relevant_tools = ['grep', 'glob']
        else:
            # Return all tools for unknown task types
            relevant_tools = list(self.tools.keys())

        return [self.tool_instances[name].to_dict() for name in relevant_tools
                if name in self.tool_instances]

    def validate_tool_call(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """Safety validation before tool execution"""
        if tool_name not in self.tool_instances:
            return False

        tool = self.tool_instances[tool_name]

        # Basic parameter validation against schema
        schema = tool.get_parameters_schema()
        if 'required' in schema:
            for required_param in schema['required']:
                if required_param not in args:
                    return False

        # Additional safety checks can be added here
        # - Path validation
        # - Permission checks
        # - Rate limiting
        # - Resource limits

        return True

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given arguments"""
        if not self.validate_tool_call(tool_name, args):
            return {
                'success': False,
                'error': f'Invalid tool call: {tool_name} with args {args}'
            }

        tool = self.tool_instances[tool_name]
        try:
            result = tool.execute(**args)
            # Validate result format
            if not tool.validate_result(result):
                return {
                    'success': False,
                    'error': f'Tool {tool_name} returned invalid result format'
                }
            return result
        except Exception as e:
            return {
                'success': False,
                'error': f'Tool execution failed: {str(e)}'
            }

    def get_tool_info(self) -> Dict[str, Any]:
        """Get information about all registered tools"""
        return {
            'total_tools': len(self.tools),
            'tools': {
                name: {
                    'description': instance.description,
                    'capabilities': self.capabilities.get(name, [])
                }
                for name, instance in self.tool_instances.items()
            }
        }