"""
Claude AI Client (Anthropic)
Fallback AI provider - powerful for complex tasks
"""

from typing import Any, Dict, List, Optional

import requests

from .base import AIResponse, BaseAIClient, ToolCall


class ClaudeClient(BaseAIClient):
    """Client for Anthropic Claude API"""

    API_BASE = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"

    # Pricing per million tokens (as of 2024)
    PRICING = {
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,  # $3 per 1M input tokens
            "output": 15.00,  # $15 per 1M output tokens
        },
        "claude-3-5-haiku-20241022": {
            "input": 1.00,  # $1 per 1M input tokens
            "output": 5.00,  # $5 per 1M output tokens
        },
        "claude-3-opus-20240229": {
            "input": 15.00,  # $15 per 1M input tokens
            "output": 75.00,  # $75 per 1M output tokens
        },
    }

    @property
    def provider_name(self) -> str:
        return "claude"

    @property
    def default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"

    def supports_tool_calling(self) -> bool:
        return True

    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple:
        """
        Convert OpenAI-style messages to Claude format
        Returns: (system_prompt, messages)
        """
        system_prompt = ""
        claude_messages = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_prompt = content
            elif role == "user":
                claude_messages.append({"role": "user", "content": content})
            elif role == "assistant":
                claude_messages.append({"role": "assistant", "content": content})
            elif role == "tool":
                # Tool results go in user message
                claude_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.get("tool_call_id", ""),
                                "content": content,
                            }
                        ],
                    }
                )

        return system_prompt, claude_messages

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI-style tools to Claude format"""
        claude_tools = []
        for tool in tools:
            # OpenAI format: {"type": "function", "function": {...}}
            # Claude format: {"name": "...", "description": "...", "input_schema": {...}}
            func = tool.get("function", {})
            claude_tools.append(
                {
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {}),
                }
            )
        return claude_tools

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AIResponse:
        """Send chat completion request to Claude"""
        model = model or self.default_model
        max_tokens = max_tokens or 4096

        # Convert messages to Claude format
        system_prompt, claude_messages = self._convert_messages(messages)

        # Build request payload
        payload = {
            "model": model,
            "messages": claude_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_prompt:
            payload["system"] = system_prompt

        if tools:
            payload["tools"] = self._convert_tools(tools)

        # Add any additional kwargs
        for key, value in kwargs.items():
            if value is not None:
                payload[key] = value

        try:
            # Make API request
            response = requests.post(
                f"{self.API_BASE}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": self.API_VERSION,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.config.get("timeout", 60),
            )

            response.raise_for_status()
            data = response.json()

            # Parse response
            content_text = ""
            tool_calls = []

            for content_block in data.get("content", []):
                if content_block["type"] == "text":
                    content_text = content_block["text"]
                elif content_block["type"] == "tool_use":
                    tool_calls.append(
                        ToolCall(
                            id=content_block["id"],
                            name=content_block["name"],
                            arguments=content_block["input"],
                        )
                    )

            # Build response
            return AIResponse(
                content=content_text,
                tool_calls=tool_calls,
                model=data["model"],
                provider=self.provider_name,
                usage={
                    "prompt_tokens": data["usage"]["input_tokens"],
                    "completion_tokens": data["usage"]["output_tokens"],
                },
                finish_reason=data.get("stop_reason", ""),
            )

        except requests.exceptions.Timeout:
            return AIResponse(
                content="",
                error=f"Claude API timeout after {self.config.get('timeout', 60)}s",
                provider=self.provider_name,
            )
        except requests.exceptions.HTTPError as e:
            error_msg = f"Claude API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    error_msg += f" - {error_data['error'].get('message', '')}"
            except:
                pass
            return AIResponse(content="", error=error_msg, provider=self.provider_name)
        except Exception as e:
            return AIResponse(
                content="", error=f"Claude client error: {str(e)}", provider=self.provider_name
            )

    def get_cost_estimate(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on usage"""
        model = self.default_model
        if model not in self.PRICING:
            return 0.0

        pricing = self.PRICING[model]
        input_cost = (usage.get("prompt_tokens", 0) / 1_000_000) * pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def format_tool_result(self, tool_call: ToolCall, result: Any) -> Dict[str, Any]:
        """Format tool result for Claude (uses different format)"""
        return {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": tool_call.id, "content": str(result)}
            ],
        }
