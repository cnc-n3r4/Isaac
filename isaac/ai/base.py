"""
Base AI Client Interface
Provides standard interface for all AI providers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    """Represents a tool/function call from AI"""

    id: str
    name: str
    arguments: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "arguments": self.arguments}


@dataclass
class AIResponse:
    """Standard AI response format"""

    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None  # Phase 3: Enhanced metadata

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "content": self.content,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
        }

        # Phase 3: Include metadata if present
        if self.metadata:
            result["metadata"] = self.metadata

        return result


class BaseAIClient(ABC):
    """Base class for all AI provider clients"""

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize AI client

        Args:
            api_key: API key for the provider
            config: Optional configuration dict
        """
        self.api_key = api_key
        self.config = config or {}
        self._setup()

    def _setup(self):
        """Provider-specific setup (override if needed)"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'grok', 'claude', 'openai')"""

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this provider"""

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """
        Send chat completion request

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to default_model)
            tools: Optional list of tool schemas for function calling
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            AIResponse object
        """

    @abstractmethod
    def supports_tool_calling(self) -> bool:
        """Whether this provider supports tool/function calling"""

    def get_cost_estimate(self, usage: Dict[str, int]) -> float:
        """
        Estimate cost for usage (override in subclass with real pricing)

        Args:
            usage: Dict with 'prompt_tokens' and 'completion_tokens'

        Returns:
            Estimated cost in USD
        """
        return 0.0

    def format_tool_result(self, tool_call: ToolCall, result: Any) -> Dict[str, Any]:
        """
        Format tool execution result for next API call

        Args:
            tool_call: The original tool call
            result: The tool execution result

        Returns:
            Message dict to append to conversation
        """
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_call.name,
            "content": str(result),
        }
