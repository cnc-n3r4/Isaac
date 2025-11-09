"""
AI Routing Configuration Manager

Manages user-configurable settings for intelligent AI provider routing.
Stores configuration in ~/.isaac/ai_routing_config.json

Configuration includes:
- Provider preferences for each complexity level
- Model selections per provider
- Cost limits and budgets
- Provider capabilities and pricing
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class RoutingConfigManager:
    """
    Manages AI routing configuration with user preferences.

    Default settings favor Claude and Grok as per user preference,
    but all settings are fully configurable.
    """

    DEFAULT_CONFIG = {
        'version': '1.0.0',

        # Provider routing preferences for each complexity level
        'routing_preferences': {
            'simple': 'openai',      # Cost-optimized for simple tasks
            'medium': 'grok',        # Balanced performance
            'complex': 'claude',     # Advanced reasoning
            'expert': 'claude',      # Expert-level tasks

            # Task-type overrides (optional)
            'code_write': 'claude',  # Always use Claude for code generation
            'code_debug': 'claude',  # Always use Claude for debugging
            'tool_use': 'claude',    # Always use Claude for tool calling
        },

        # Provider configurations
        'providers': {
            'grok': {
                'enabled': True,
                'model': 'grok-beta',
                'max_complexity': 'complex',
                'strengths': ['chat', 'search', 'code_read'],
                'pricing': {
                    'input_per_1m': 5.0,
                    'output_per_1m': 15.0,
                    'currency': 'USD'
                },
                'speed': 'fast',
                'context_window': 128000
            },
            'claude': {
                'enabled': True,
                'model': 'claude-3-5-sonnet-20241022',
                'max_complexity': 'expert',
                'strengths': ['code_write', 'code_debug', 'analysis', 'planning', 'tool_use'],
                'pricing': {
                    'input_per_1m': 3.0,
                    'output_per_1m': 15.0,
                    'currency': 'USD'
                },
                'speed': 'medium',
                'context_window': 200000
            },
            'openai': {
                'enabled': True,
                'model': 'gpt-4o-mini',
                'max_complexity': 'medium',
                'strengths': ['chat', 'creative', 'search'],
                'pricing': {
                    'input_per_1m': 0.15,
                    'output_per_1m': 0.60,
                    'currency': 'USD'
                },
                'speed': 'fast',
                'context_window': 128000
            }
        },

        # Cost management
        'cost_limits': {
            'enabled': True,
            'daily_limit_usd': 10.0,
            'monthly_limit_usd': 100.0,
            'alert_threshold': 0.8,  # Alert at 80% of limit
            'auto_switch_to_cheaper': True  # Switch to cheaper provider if limit approaching
        },

        # Advanced settings
        'advanced': {
            'enable_context_preservation': True,
            'enable_performance_monitoring': True,
            'fallback_on_error': True,
            'max_retries': 2,
            'timeout_seconds': 60
        }
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize routing config manager.

        Args:
            config_path: Optional custom path for config file
        """
        if config_path is None:
            config_path = Path.home() / '.isaac' / 'ai_routing_config.json'

        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)

                # Merge with defaults to ensure all keys exist
                return self._merge_with_defaults(loaded_config)
            except Exception as e:
                print(f"Warning: Failed to load AI routing config: {e}")
                print("Using default configuration")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()

    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded config with defaults to ensure all keys exist"""
        def deep_merge(base, updates):
            """Recursively merge dictionaries"""
            result = base.copy()
            for key, value in updates.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(self.DEFAULT_CONFIG, loaded_config)

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def save(self) -> None:
        """Save current configuration"""
        self._save_config(self.config)

    def get_provider_for_complexity(self, complexity: str) -> str:
        """Get preferred provider for a complexity level"""
        return self.config['routing_preferences'].get(complexity, 'grok')

    def set_provider_for_complexity(self, complexity: str, provider: str) -> None:
        """Set provider preference for a complexity level"""
        valid_complexity = ['simple', 'medium', 'complex', 'expert']
        if complexity not in valid_complexity:
            raise ValueError(f"Invalid complexity: {complexity}. Must be one of {valid_complexity}")

        valid_providers = list(self.config['providers'].keys())
        if provider not in valid_providers:
            raise ValueError(f"Invalid provider: {provider}. Must be one of {valid_providers}")

        self.config['routing_preferences'][complexity] = provider
        self.save()

    def get_provider_for_task_type(self, task_type: str) -> Optional[str]:
        """Get preferred provider for a specific task type (if override exists)"""
        return self.config['routing_preferences'].get(task_type)

    def set_provider_for_task_type(self, task_type: str, provider: str) -> None:
        """Set provider preference for a task type"""
        valid_providers = list(self.config['providers'].keys())
        if provider not in valid_providers:
            raise ValueError(f"Invalid provider: {provider}. Must be one of {valid_providers}")

        self.config['routing_preferences'][task_type] = provider
        self.save()

    def get_provider_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific provider"""
        return self.config['providers'].get(provider)

    def set_provider_model(self, provider: str, model: str) -> None:
        """Set model for a provider"""
        if provider not in self.config['providers']:
            raise ValueError(f"Unknown provider: {provider}")

        self.config['providers'][provider]['model'] = model
        self.save()

    def set_provider_enabled(self, provider: str, enabled: bool) -> None:
        """Enable or disable a provider"""
        if provider not in self.config['providers']:
            raise ValueError(f"Unknown provider: {provider}")

        self.config['providers'][provider]['enabled'] = enabled
        self.save()

    def update_provider_pricing(self, provider: str, input_per_1m: float, output_per_1m: float) -> None:
        """Update pricing for a provider"""
        if provider not in self.config['providers']:
            raise ValueError(f"Unknown provider: {provider}")

        self.config['providers'][provider]['pricing']['input_per_1m'] = input_per_1m
        self.config['providers'][provider]['pricing']['output_per_1m'] = output_per_1m
        self.save()

    def get_cost_limits(self) -> Dict[str, Any]:
        """Get cost limit settings"""
        return self.config['cost_limits']

    def set_cost_limit(self, period: str, amount: float) -> None:
        """Set cost limit for a period (daily or monthly)"""
        if period == 'daily':
            self.config['cost_limits']['daily_limit_usd'] = amount
        elif period == 'monthly':
            self.config['cost_limits']['monthly_limit_usd'] = amount
        else:
            raise ValueError(f"Invalid period: {period}. Must be 'daily' or 'monthly'")

        self.save()

    def enable_cost_limits(self, enabled: bool) -> None:
        """Enable or disable cost limits"""
        self.config['cost_limits']['enabled'] = enabled
        self.save()

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all configuration settings"""
        return self.config.copy()

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        import copy
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        self.save()

    def export_config(self, output_path: Path) -> None:
        """Export configuration to a file"""
        with open(output_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def import_config(self, input_path: Path) -> None:
        """Import configuration from a file"""
        with open(input_path, 'r') as f:
            imported_config = json.load(f)

        self.config = self._merge_with_defaults(imported_config)
        self.save()

    def get_enabled_providers(self) -> list:
        """Get list of enabled providers"""
        return [
            name for name, config in self.config['providers'].items()
            if config.get('enabled', True)
        ]

    def validate_config(self) -> tuple[bool, list]:
        """
        Validate configuration for correctness.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Check that at least one provider is enabled
        enabled_providers = self.get_enabled_providers()
        if not enabled_providers:
            errors.append("At least one provider must be enabled")

        # Check that routing preferences point to valid providers
        for complexity, provider in self.config['routing_preferences'].items():
            if complexity in ['simple', 'medium', 'complex', 'expert']:
                if provider not in self.config['providers']:
                    errors.append(f"Routing preference '{complexity}' points to unknown provider '{provider}'")
                elif not self.config['providers'][provider].get('enabled', True):
                    errors.append(f"Routing preference '{complexity}' points to disabled provider '{provider}'")

        # Check cost limits are reasonable
        if self.config['cost_limits']['enabled']:
            daily = self.config['cost_limits']['daily_limit_usd']
            monthly = self.config['cost_limits']['monthly_limit_usd']
            if daily > monthly:
                errors.append(f"Daily cost limit (${daily}) exceeds monthly limit (${monthly})")

        return (len(errors) == 0, errors)
