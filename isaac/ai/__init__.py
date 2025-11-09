"""
AI Integration for Isaac
Multi-provider AI routing with tool calling support
"""

from .agent import IsaacAgent
from .base import AIResponse, BaseAIClient, ToolCall
from .claude_client import ClaudeClient
from .config_manager import AIConfigManager
from .grok_client import GrokClient
from .openai_client import OpenAIClient
from .router import AIRouter

__all__ = [
    "BaseAIClient",
    "AIResponse",
    "ToolCall",
    "GrokClient",
    "ClaudeClient",
    "OpenAIClient",
    "AIRouter",
    "AIConfigManager",
    "IsaacAgent",
]
