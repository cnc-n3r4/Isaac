"""
AI Configuration Manager
Manages AI provider settings and preferences
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class AIConfigManager:
    """Manage AI configuration"""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path.home() / ".isaac" / "ai_config.json"

        self.config_path = config_path
        self.config = self._load_or_create()

    def _load_or_create(self) -> Dict[str, Any]:
        """Load existing config or create default"""
        default_config = {
            "providers": {
                "grok": {
                    "enabled": True,
                    "api_key_env": "XAI_API_KEY",
                    "model": "grok-beta",
                    "timeout": 60,
                    "max_retries": 2,
                    "description": "Primary - Fast and cost-effective",
                },
                "claude": {
                    "enabled": True,
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "model": "claude-3-5-sonnet-20241022",
                    "timeout": 60,
                    "max_retries": 1,
                    "description": "Fallback - Powerful for complex tasks",
                },
                "openai": {
                    "enabled": True,
                    "api_key_env": "OPENAI_API_KEY",
                    "model": "gpt-4o-mini",
                    "timeout": 60,
                    "max_retries": 1,
                    "description": "Backup - Reliable fallback",
                },
            },
            "routing": {
                "strategy": "fallback",
                "prefer_provider": "grok",
                "cost_limit_daily": 10.0,
                "enable_tracking": True,
            },
            "defaults": {"temperature": 0.7, "max_tokens": 4096},
            "prompts": {
                "system": {
                    "code_assistant": "You are Isaac, an AI code assistant. You help with coding tasks using available tools.",
                    "file_operations": "You can read, write, edit files and search code using the provided tools.",
                    "general": "You are a helpful AI assistant.",
                },
                "custom": {},
            },
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                # Ensure all default keys exist
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
            except Exception:
                return default_config
        else:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.save(default_config)
            return default_config

    def save(self, config: Optional[Dict[str, Any]] = None):
        """Save configuration to file"""
        if config is None:
            config = self.config

        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value by dot-separated path

        Example: config.get('providers.grok.model')
        """
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """
        Set config value by dot-separated path

        Example: config.set('providers.grok.model', 'grok-2')
        """
        keys = key_path.split(".")
        config = self.config

        # Navigate to parent
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set value
        config[keys[-1]] = value
        self.save()

    def get_provider_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific provider"""
        return self.config["providers"].get(provider)

    def enable_provider(self, provider: str):
        """Enable a provider"""
        if provider in self.config["providers"]:
            self.config["providers"][provider]["enabled"] = True
            self.save()

    def disable_provider(self, provider: str):
        """Disable a provider"""
        if provider in self.config["providers"]:
            self.config["providers"][provider]["enabled"] = False
            self.save()

    def set_preferred_provider(self, provider: str):
        """Set preferred primary provider"""
        if provider in self.config["providers"]:
            self.config["routing"]["prefer_provider"] = provider
            self.save()

    def get_system_prompt(self, prompt_type: str = "code_assistant") -> str:
        """Get system prompt by type"""
        return self.config["prompts"]["system"].get(prompt_type, "")

    def set_custom_prompt(self, name: str, content: str):
        """Set custom system prompt"""
        self.config["prompts"]["custom"][name] = content
        self.save()

    def get_custom_prompt(self, name: str) -> Optional[str]:
        """Get custom system prompt"""
        return self.config["prompts"]["custom"].get(name)

    def list_providers(self) -> Dict[str, Dict[str, Any]]:
        """List all providers with their status"""
        return {
            name: {
                "enabled": config["enabled"],
                "model": config["model"],
                "description": config.get("description", ""),
            }
            for name, config in self.config["providers"].items()
        }

    def export_config(self) -> str:
        """Export configuration as JSON string"""
        return json.dumps(self.config, indent=2)

    def import_config(self, config_json: str):
        """Import configuration from JSON string"""
        config = json.loads(config_json)
        self.config = config
        self.save()
