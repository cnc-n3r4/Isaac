"""
AI Router
Intelligent routing with fallback: Grok -> Claude -> OpenAI
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from .base import BaseAIClient, AIResponse
from .grok_client import GrokClient
from .claude_client import ClaudeClient
from .openai_client import OpenAIClient


class AIRouter:
    """
    Routes AI requests with intelligent fallback
    
    Primary: Grok (fast, cheap)
    Fallback: Claude (complex tasks)
    Backup: OpenAI (reliable)
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize router with configuration
        
        Args:
            config_path: Path to AI config file (defaults to ~/.isaac/ai_config.json)
        """
        if config_path is None:
            config_path = Path.home() / '.isaac' / 'ai_config.json'
        
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize clients
        self.clients: Dict[str, Optional[BaseAIClient]] = {
            'grok': None,
            'claude': None,
            'openai': None
        }
        
        self._init_clients()
        
        # Usage tracking
        self.usage_stats = {
            'grok': {'calls': 0, 'tokens': 0, 'cost': 0.0, 'failures': 0},
            'claude': {'calls': 0, 'tokens': 0, 'cost': 0.0, 'failures': 0},
            'openai': {'calls': 0, 'tokens': 0, 'cost': 0.0, 'failures': 0}
        }

    def _load_config(self) -> Dict[str, Any]:
        """Load AI configuration"""
        default_config = {
            'providers': {
                'grok': {
                    'enabled': True,
                    'api_key_env': 'XAI_API_KEY',
                    'model': 'grok-beta',
                    'timeout': 60,
                    'max_retries': 2
                },
                'claude': {
                    'enabled': True,
                    'api_key_env': 'ANTHROPIC_API_KEY',
                    'model': 'claude-3-5-sonnet-20241022',
                    'timeout': 60,
                    'max_retries': 1
                },
                'openai': {
                    'enabled': True,
                    'api_key_env': 'OPENAI_API_KEY',
                    'model': 'gpt-4o-mini',
                    'timeout': 60,
                    'max_retries': 1
                }
            },
            'routing': {
                'strategy': 'fallback',  # 'fallback' or 'cost_optimized'
                'prefer_provider': 'grok',  # Primary provider
                'cost_limit_daily': 10.0,  # Daily cost limit in USD
                'enable_tracking': True
            },
            'defaults': {
                'temperature': 0.7,
                'max_tokens': 4096
            }
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                for key in default_config:
                    if key not in loaded_config:
                        loaded_config[key] = default_config[key]
                return loaded_config
            except Exception as e:
                print(f"Warning: Failed to load AI config: {e}")
                return default_config
        else:
            # Save default config
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config

    def _init_clients(self):
        """Initialize AI clients from config"""
        for provider, settings in self.config['providers'].items():
            if not settings['enabled']:
                continue
            
            # Get API key from environment
            api_key_env = settings['api_key_env']
            api_key = os.environ.get(api_key_env)
            
            if not api_key:
                print(f"Warning: {api_key_env} not set, {provider} disabled")
                continue
            
            # Initialize client
            client_config = {
                'timeout': settings['timeout'],
                'model': settings['model']
            }
            
            try:
                if provider == 'grok':
                    self.clients['grok'] = GrokClient(api_key, client_config)
                elif provider == 'claude':
                    self.clients['claude'] = ClaudeClient(api_key, client_config)
                elif provider == 'openai':
                    self.clients['openai'] = OpenAIClient(api_key, client_config)
            except Exception as e:
                print(f"Warning: Failed to initialize {provider}: {e}")

    def _get_fallback_order(self, prefer: Optional[str] = None) -> List[str]:
        """Get provider fallback order"""
        prefer = prefer or self.config['routing']['prefer_provider']
        
        # Default order
        default_order = ['grok', 'claude', 'openai']
        
        # Move preferred to front
        if prefer in default_order:
            order = [prefer]
            order.extend([p for p in default_order if p != prefer])
            return order
        
        return default_order

    def _update_stats(self, provider: str, response: AIResponse, success: bool):
        """Update usage statistics"""
        stats = self.usage_stats[provider]
        stats['calls'] += 1
        
        if success:
            tokens = response.usage.get('prompt_tokens', 0) + response.usage.get('completion_tokens', 0)
            stats['tokens'] += tokens
            
            client = self.clients[provider]
            if client:
                cost = client.get_cost_estimate(response.usage)
                stats['cost'] += cost
        else:
            stats['failures'] += 1

    def _check_cost_limit(self) -> bool:
        """Check if daily cost limit exceeded"""
        if not self.config['routing']['enable_tracking']:
            return True
        
        total_cost = sum(stats['cost'] for stats in self.usage_stats.values())
        limit = self.config['routing']['cost_limit_daily']
        
        return total_cost < limit

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        prefer_provider: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """
        Send chat request with intelligent routing
        
        Args:
            messages: Conversation messages
            tools: Optional tool schemas
            prefer_provider: Override preferred provider
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            AIResponse from successful provider
        """
        # Check cost limit
        if not self._check_cost_limit():
            return AIResponse(
                content='',
                error='Daily cost limit exceeded',
                provider='router'
            )
        
        # Get fallback order
        fallback_order = self._get_fallback_order(prefer_provider)
        
        # Try each provider in order
        last_error = None
        for provider in fallback_order:
            client = self.clients.get(provider)
            if not client:
                continue
            
            try:
                # Get provider-specific settings
                provider_config = self.config['providers'][provider]
                model = kwargs.get('model') or provider_config['model']
                temperature = kwargs.get('temperature') or self.config['defaults']['temperature']
                max_tokens = kwargs.get('max_tokens') or self.config['defaults']['max_tokens']
                
                # Make request
                response = client.chat(
                    messages=messages,
                    model=model,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **{k: v for k, v in kwargs.items() if k not in ['model', 'temperature', 'max_tokens']}
                )
                
                # Update stats
                self._update_stats(provider, response, response.success)
                
                # Return if successful
                if response.success:
                    return response
                
                # Store error for potential retry
                last_error = response.error
                
            except Exception as e:
                last_error = f"{provider} exception: {str(e)}"
                self._update_stats(provider, AIResponse(content='', error=last_error, provider=provider), False)
                continue
        
        # All providers failed
        return AIResponse(
            content='',
            error=f'All providers failed. Last error: {last_error}',
            provider='router'
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            'usage': self.usage_stats.copy(),
            'total_cost': sum(stats['cost'] for stats in self.usage_stats.values()),
            'total_calls': sum(stats['calls'] for stats in self.usage_stats.values()),
            'total_tokens': sum(stats['tokens'] for stats in self.usage_stats.values()),
            'cost_limit': self.config['routing']['cost_limit_daily'],
            'cost_remaining': self.config['routing']['cost_limit_daily'] - sum(stats['cost'] for stats in self.usage_stats.values())
        }

    def reset_stats(self):
        """Reset usage statistics (call daily)"""
        for provider in self.usage_stats:
            self.usage_stats[provider] = {
                'calls': 0,
                'tokens': 0,
                'cost': 0.0,
                'failures': 0
            }

    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return [name for name, client in self.clients.items() if client is not None]

    def update_config(self, updates: Dict[str, Any]):
        """Update configuration and save"""
        # Deep merge updates
        def deep_merge(base, updates):
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(self.config, updates)
        
        # Save to file
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        # Reinitialize clients if provider settings changed
        if 'providers' in updates:
            self._init_clients()
