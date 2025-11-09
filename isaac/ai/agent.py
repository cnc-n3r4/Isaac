"""
Isaac AI Agent
Integrates AI router with tool calling for autonomous task execution
"""

import json
from typing import Any, Dict, List, Optional

from ..tools import EditTool, GlobTool, GrepTool, ReadTool, ShellTool, WriteTool
from .router import AIRouter


class IsaacAgent:
    """
    AI Agent with tool execution capabilities

    Combines AI router with file operation tools for autonomous coding assistance
    """

    def __init__(self, router: Optional[AIRouter] = None):
        """
        Initialize agent

        Args:
            router: AIRouter instance (creates default if None)
        """
        self.router = router or AIRouter()

        # Initialize tools
        self.tools = {
            "read": ReadTool(),
            "write": WriteTool(),
            "edit": EditTool(),
            "grep": GrepTool(),
            "glob": GlobTool(),
            "shell": ShellTool(),
        }

        # Get tool schemas for AI
        self.tool_schemas = [tool.get_parameters_schema() for tool in self.tools.values()]

        # Conversation history
        self.messages: List[Dict[str, Any]] = []

        # System prompts
        self.system_prompts = {
            "code_assistant": """You are Isaac, an AI code assistant with access to powerful file operation and shell execution tools.

Available Tools:
- read: Read file contents with line numbers
- write: Create new files with content
- edit: Make exact string replacements in files
- grep: Search for patterns across files
- glob: Find files matching patterns
- shell: Execute shell commands safely with tier-based validation

You can use these tools to:
1. Read and analyze code
2. Make precise edits
3. Search for specific patterns
4. Find files by pattern
5. Create new files
6. Execute safe shell commands (package management, system queries, etc.)

For shell commands, use the 'shell' tool which automatically validates safety using Isaac's tier system:
- Tier 1-2: Safe commands (ls, cd, grep) - execute immediately
- Tier 2.5-3: Moderate commands (pip, git, npm) - validated but allowed
- Tier 4: Dangerous commands (rm, format) - blocked

When users ask to update dependencies, install packages, or run system commands, use the shell tool to execute them safely.""",
            "file_ops": """You are Isaac, a file operations specialist.
Use the available tools to read, write, edit, search, and find files.
Be precise with file paths and edits. Always verify before making changes.""",
        }

    def set_system_prompt(self, prompt_type: str = "code_assistant"):
        """
        Set system prompt for conversation

        Args:
            prompt_type: Type of prompt ('code_assistant', 'file_ops', or custom string)
        """
        if prompt_type in self.system_prompts:
            prompt = self.system_prompts[prompt_type]
        else:
            prompt = prompt_type  # Use as custom prompt

        # Clear existing system messages
        self.messages = [msg for msg in self.messages if msg["role"] != "system"]

        # Add new system message at start
        self.messages.insert(0, {"role": "system", "content": prompt})

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with given arguments

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        tool = self.tools.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        try:
            result = tool.execute(**arguments)
            return result
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}

    def chat(self, user_message: str, max_iterations: int = 5, **kwargs) -> Dict[str, Any]:
        """
        Chat with agent (with automatic tool execution)

        Args:
            user_message: User's message
            max_iterations: Maximum tool execution iterations
            **kwargs: Additional parameters for AI router

        Returns:
            Dict with response and execution details
        """
        # Add user message to history
        self.messages.append({"role": "user", "content": user_message})

        # Initialize system prompt if not set
        if not any(msg["role"] == "system" for msg in self.messages):
            self.set_system_prompt("code_assistant")

        tool_executions = []
        iterations = 0

        # Iterative tool execution loop
        while iterations < max_iterations:
            iterations += 1

            # Get AI response
            response = self.router.chat(messages=self.messages, tools=self.tool_schemas, **kwargs)

            if not response.success:
                return {
                    "success": False,
                    "error": response.error,
                    "iterations": iterations,
                    "tool_executions": tool_executions,
                }

            # Check if AI wants to use tools
            if not response.has_tool_calls:
                # No more tools to execute, we're done
                self.messages.append({"role": "assistant", "content": response.content})

                return {
                    "success": True,
                    "response": response.content,
                    "provider": response.provider,
                    "model": response.model,
                    "usage": response.usage,
                    "iterations": iterations,
                    "tool_executions": tool_executions,
                }

            # Execute tool calls
            for tool_call in response.tool_calls:
                # Execute tool
                tool_result = self.execute_tool(tool_call.name, tool_call.arguments)

                # Track execution
                tool_executions.append(
                    {
                        "tool": tool_call.name,
                        "arguments": tool_call.arguments,
                        "result": tool_result,
                    }
                )

                # Add tool result to conversation
                # Format depends on provider
                if response.provider == "claude":
                    self.messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_call.id,
                                    "content": json.dumps(tool_result),
                                }
                            ],
                        }
                    )
                else:
                    # OpenAI/Grok format
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.name,
                            "content": json.dumps(tool_result),
                        }
                    )

        # Max iterations reached
        return {
            "success": False,
            "error": f"Max iterations ({max_iterations}) reached",
            "iterations": iterations,
            "tool_executions": tool_executions,
        }

    def reset_conversation(self):
        """Clear conversation history"""
        self.messages = []

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history"""
        return self.messages.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        return self.router.get_stats()
