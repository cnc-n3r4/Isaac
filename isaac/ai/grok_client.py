"""
Grok AI Client (xAI)
Primary AI provider - fast and cost-effective
"""

import json
import requests
from typing import Dict, Any, List, Optional
from .base import BaseAIClient, AIResponse, ToolCall


class GrokClient(BaseAIClient):
    """Client for xAI Grok API"""

    API_BASE = "https://api.x.ai/v1"

    # Pricing per million tokens (as of 2024)
    PRICING = {
        'grok-beta': {
            'input': 5.00,   # $5 per 1M input tokens
            'output': 15.00  # $15 per 1M output tokens
        }
    }

    @property
    def provider_name(self) -> str:
        return "grok"

    @property
    def default_model(self) -> str:
        return "grok-beta"

    def supports_tool_calling(self) -> bool:
        return True

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """Send chat completion request to Grok"""
        model = model or self.default_model

        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = kwargs.get("tool_choice", "auto")

        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in ["tool_choice"] and value is not None:
                payload[key] = value

        try:
            # Make API request
            response = requests.post(
                f"{self.API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=self.config.get('timeout', 60)
            )

            response.raise_for_status()
            data = response.json()

            # Parse response
            choice = data['choices'][0]
            message = choice['message']

            # Extract tool calls if present
            tool_calls = []
            if message.get('tool_calls'):
                for tc in message['tool_calls']:
                    tool_calls.append(ToolCall(
                        id=tc['id'],
                        name=tc['function']['name'],
                        arguments=json.loads(tc['function']['arguments'])
                    ))

            # Build response
            return AIResponse(
                content=message.get('content', ''),
                tool_calls=tool_calls,
                model=data['model'],
                provider=self.provider_name,
                usage=data.get('usage', {}),
                finish_reason=choice.get('finish_reason', '')
            )

        except requests.exceptions.Timeout:
            return AIResponse(
                content='',
                error=f"Grok API timeout after {self.config.get('timeout', 60)}s",
                provider=self.provider_name
            )
        except requests.exceptions.HTTPError as e:
            error_msg = f"Grok API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if 'error' in error_data:
                    error_msg += f" - {error_data['error'].get('message', '')}"
            except:
                pass
            return AIResponse(
                content='',
                error=error_msg,
                provider=self.provider_name
            )
        except Exception as e:
            return AIResponse(
                content='',
                error=f"Grok client error: {str(e)}",
                provider=self.provider_name
            )

    def get_cost_estimate(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on usage"""
        model = self.default_model
        if model not in self.PRICING:
            return 0.0

        pricing = self.PRICING[model]
        input_cost = (usage.get('prompt_tokens', 0) / 1_000_000) * pricing['input']
        output_cost = (usage.get('completion_tokens', 0) / 1_000_000) * pricing['output']

        return input_cost + output_cost
