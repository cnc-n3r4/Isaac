"""
Environment Configuration Loader
Manages .env file loading and integration with Isaac's configuration system
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class EnvConfigLoader:
    """Load and manage environment variable configuration"""

    # Mapping of service names to environment variables
    ENV_MAPPING = {
        'xai-chat': 'XAI_CHAT_API_KEY',
        'xai-collections': 'XAI_COLLECTIONS_API_KEY',
        'xai': 'XAI_API_KEY',
        'claude': 'CLAUDE_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
    }

    # Mapping to Isaac config keys
    CONFIG_KEY_MAPPING = {
        'XAI_API_KEY': 'xai_api_key',
        'XAI_CHAT_API_KEY': 'xai.chat.api_key',
        'XAI_COLLECTIONS_API_KEY': 'xai.collections.api_key',
        'CLAUDE_API_KEY': 'claude_api_key',
        'ANTHROPIC_API_KEY': 'claude_api_key',  # Map to same key
        'OPENAI_API_KEY': 'openai_api_key',
    }

    def __init__(self, env_path: Optional[Path] = None, auto_load: bool = True):
        """
        Initialize environment configuration loader

        Args:
            env_path: Path to .env file (default: project root/.env)
            auto_load: Automatically load .env on initialization
        """
        if env_path is None:
            # Try to find .env in project root or current directory
            possible_paths = [
                Path.cwd() / '.env',
                Path(__file__).parent.parent.parent / '.env',  # Isaac project root
                Path.home() / '.isaac' / '.env',  # User config directory
            ]

            self.env_path = None
            for path in possible_paths:
                if path.exists():
                    self.env_path = path
                    break

            # If not found, use current directory as default
            if self.env_path is None:
                self.env_path = Path.cwd() / '.env'
        else:
            self.env_path = env_path

        self.loaded = False

        if auto_load and self.env_path.exists():
            self.load()

    def load(self, override: bool = False) -> bool:
        """
        Load environment variables from .env file

        Args:
            override: Override existing environment variables

        Returns:
            True if .env was loaded, False otherwise
        """
        if not self.env_path.exists():
            return False

        load_dotenv(dotenv_path=self.env_path, override=override)
        self.loaded = True
        return True

    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get API key for a service from environment variables

        Args:
            service: Service name (e.g., 'xai', 'claude', 'openai')

        Returns:
            API key if found, None otherwise
        """
        env_var = self.ENV_MAPPING.get(service)
        if not env_var:
            return None

        return os.getenv(env_var)

    def get_all_api_keys(self) -> Dict[str, str]:
        """
        Get all API keys from environment variables

        Returns:
            Dictionary mapping service names to API keys
        """
        api_keys = {}
        for service, env_var in self.ENV_MAPPING.items():
            key = os.getenv(env_var)
            if key:
                api_keys[service] = key

        return api_keys

    def export_to_isaac_config(self) -> Dict[str, Any]:
        """
        Export environment variables to Isaac config format

        Returns:
            Dictionary in Isaac config format
        """
        config = {}

        for env_var, config_key in self.CONFIG_KEY_MAPPING.items():
            value = os.getenv(env_var)
            if not value:
                continue

            # Handle nested keys (e.g., 'xai.chat.api_key')
            if '.' in config_key:
                parts = config_key.split('.')
                current = config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                config[config_key] = value

        return config

    def validate_keys(self) -> Dict[str, bool]:
        """
        Validate that API keys are present and non-empty

        Returns:
            Dictionary mapping service names to validation status
        """
        validation = {}

        for service, env_var in self.ENV_MAPPING.items():
            key = os.getenv(env_var)
            validation[service] = bool(key and len(key) > 0)

        return validation

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value from environment variables

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)

    def has_env_file(self) -> bool:
        """Check if .env file exists"""
        return self.env_path.exists()

    def create_example_env(self, output_path: Optional[Path] = None) -> bool:
        """
        Create .env.example file with template

        Args:
            output_path: Path for .env.example (default: same as .env)

        Returns:
            True if created successfully
        """
        if output_path is None:
            output_path = self.env_path.parent / '.env.example'

        template = """# Isaac AI Assistant Configuration
# Copy this file to .env and add your API keys

# xAI API Keys
# Get your keys from https://x.ai/api
XAI_API_KEY=
XAI_CHAT_API_KEY=
XAI_COLLECTIONS_API_KEY=

# Anthropic Claude API Key
# Get your key from https://console.anthropic.com/
CLAUDE_API_KEY=
ANTHROPIC_API_KEY=

# OpenAI API Key
# Get your key from https://platform.openai.com/
OPENAI_API_KEY=

# Optional: Isaac Settings
# ISAAC_DEFAULT_MODEL=grok-beta
# ISAAC_MASTER_KEY=your_master_key
# ISAAC_DEBUG=false
"""

        try:
            with open(output_path, 'w') as f:
                f.write(template)
            return True
        except Exception:
            return False

    def merge_with_isaac_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge environment variables with Isaac config
        Priority: .env < config.json (config.json takes precedence)

        Args:
            config: Existing Isaac configuration

        Returns:
            Merged configuration
        """
        env_config = self.export_to_isaac_config()

        # Merge with existing config (config takes precedence)
        merged = env_config.copy()

        # Deep merge for nested structures
        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        merged = deep_merge(merged, config)
        return merged

    def update_env_file(self, service: str, api_key: str) -> bool:
        """
        Update .env file with new API key

        Args:
            service: Service name
            api_key: New API key

        Returns:
            True if updated successfully
        """
        env_var = self.ENV_MAPPING.get(service)
        if not env_var:
            return False

        # Read existing .env file
        lines = []
        if self.env_path.exists():
            with open(self.env_path, 'r') as f:
                lines = f.readlines()

        # Update or add the key
        key_found = False
        for i, line in enumerate(lines):
            if line.startswith(f'{env_var}='):
                lines[i] = f'{env_var}={api_key}\n'
                key_found = True
                break

        if not key_found:
            lines.append(f'{env_var}={api_key}\n')

        # Write back to file
        try:
            self.env_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.env_path, 'w') as f:
                f.writelines(lines)

            # Reload environment
            self.load(override=True)
            return True
        except Exception:
            return False

    @classmethod
    def get_provider_api_key(cls, provider: str) -> Optional[str]:
        """
        Get API key for AI provider from environment
        This is a convenience method for AI clients

        Args:
            provider: Provider name ('grok', 'claude', 'openai')

        Returns:
            API key if found
        """
        provider_env_map = {
            'grok': 'XAI_API_KEY',
            'claude': 'ANTHROPIC_API_KEY',
            'openai': 'OPENAI_API_KEY',
        }

        env_var = provider_env_map.get(provider)
        if not env_var:
            return None

        return os.getenv(env_var)


def load_env_config(env_path: Optional[Path] = None) -> EnvConfigLoader:
    """
    Convenience function to load environment configuration

    Args:
        env_path: Path to .env file

    Returns:
        Configured EnvConfigLoader instance
    """
    return EnvConfigLoader(env_path=env_path, auto_load=True)
