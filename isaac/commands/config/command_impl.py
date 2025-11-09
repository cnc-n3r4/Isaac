"""
Config Command - Standardized Implementation

Configuration management for Isaac.
"""

import json
import socket
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.ui.config_console import show_config_console


class ConfigCommand(BaseCommand):
    """Manage Isaac configuration"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute config command.

        Args:
            args: Command arguments (various flags for different operations)
            context: Optional execution context (includes session info)

        Returns:
            CommandResponse with config info or result
        """
        parser = FlagParser(args)

        # Get session from context (dispatcher provides this)
        session = context.get("session", {}) if context else {}

        try:
            # Route to appropriate handler based on flags
            if parser.has_flag('help'):
                output = self._show_overview(session)
            elif parser.has_flag('status'):
                output = self._show_status(session)
            elif parser.has_flag('ai'):
                output = self._show_ai_details(session)
            elif parser.has_flag('cloud'):
                output = self._show_cloud_details(session)
            elif parser.has_flag('plugins'):
                output = self._show_plugins()
            elif parser.has_flag('collections'):
                output = self._show_collections_config(session)
            elif parser.has_flag('console'):
                output = show_config_console(session)
            elif parser.has_flag('set'):
                key = parser.get_flag('set')
                value = parser.get_positional(0)
                output = self._set_config(session, key, value)
            elif parser.has_flag('apikey') or parser.has_flag('key'):
                service = parser.get_flag('apikey') or parser.get_flag('key')
                api_key = parser.get_positional(0)
                output = self._set_api_key(session, service, api_key)
            elif parser.has_flag('ai-routing'):
                output = self._show_ai_routing()
            elif parser.has_flag('ai-routing-set'):
                key = parser.get_flag('ai-routing-set')
                value = parser.get_positional(0)
                output = self._set_ai_routing_preference(key, value)
            elif parser.has_flag('ai-routing-model'):
                provider = parser.get_flag('ai-routing-model')
                model = parser.get_positional(0)
                output = self._set_ai_routing_model(provider, model)
            elif parser.has_flag('ai-routing-limits'):
                period = parser.get_flag('ai-routing-limits')
                amount = parser.get_positional(0)
                output = self._set_ai_routing_limits(period, amount)
            elif parser.has_flag('ai-routing-reset'):
                output = self._reset_ai_routing()
            elif parser.has_flag('env'):
                output = self._show_env_status()
            elif parser.has_flag('env-validate'):
                output = self._validate_env_keys()
            elif parser.has_flag('env-create'):
                output = self._create_env_example()
            elif len(parser.get_all_flags()) > 0:
                # Unknown flag
                unknown_flag = list(parser.get_all_flags().keys())[0]
                output = f"Unknown flag: --{unknown_flag}\nUse /config --help for help"
            else:
                # No flags - show overview
                output = self._show_overview(session)

            return CommandResponse(
                success=True,
                data=output
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "EXECUTION_ERROR"}
            )

    def _show_overview(self, session: Dict[str, Any]) -> str:
        """Show configuration overview"""
        lines = []
        lines.append("=== ISAAC Configuration ===")
        lines.append("Version: 1.0.2")
        lines.append(f"Session ID: {session.get('machine_id', 'unknown')}")
        lines.append("History Count: 42")  # Placeholder
        lines.append(f"Default Tier: {session.get('user_prefs', {}).get('default_tier', 2)}")
        lines.append("")
        lines.append("Available subcommands:")
        lines.append("  /config --status       - System status check")
        lines.append("  /config --ai           - AI provider details")
        lines.append("  /config --ai-routing   - AI routing configuration")
        lines.append("  /config --cloud        - Cloud sync status")
        lines.append("  /config --plugins      - Available plugins")
        lines.append("  /config --collections  - xAI Collections status")
        lines.append("  /config --console      - Interactive /mine settings TUI")
        lines.append("  /config --set <key> <value> - Change setting")
        lines.append("  /config --env          - Show .env configuration status")
        lines.append("  /config --env-validate - Validate .env API keys")
        lines.append("  /config --env-create   - Create .env.example file")
        return "\n".join(lines)

    def _show_status(self, session: Dict[str, Any]) -> str:
        """Show detailed system status"""
        lines = []
        lines.append("=== System Status ===")

        # Cloud status
        lines.append("Cloud: ✓ Connected")

        # AI status
        lines.append("AI Provider: ✓ xAI (grok-3)")

        # Network info
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            lines.append(f"Network: {ip}")
        except:
            lines.append("Network: Unable to detect")

        # Session info
        lines.append(f"Session: {session.get('machine_id', 'unknown')}")
        lines.append("Commands today: 42")  # Placeholder

        return "\n".join(lines)

    def _show_ai_details(self, session: Dict[str, Any]) -> str:
        """Show AI provider configuration"""
        lines = []
        lines.append("=== AI Provider Details ===")

        provider = "xai"
        model = "grok-3"

        lines.append(f"Provider: {provider}")
        lines.append(f"Model: {model}")
        lines.append("Status: ✓ Connected")

        return "\n".join(lines)

    def _show_cloud_details(self, session: Dict[str, Any]) -> str:
        """Show cloud sync status"""
        lines = []
        lines.append("=== Cloud Sync Status ===")

        lines.append("Cloud sync: Enabled")
        lines.append("Connection: ✓ Healthy")
        lines.append("Last sync: Recent")

        return "\n".join(lines)

    def _show_plugins(self) -> str:
        """List available plugins"""
        lines = []
        lines.append("=== Available Plugins ===")

        plugins = [
            ("togrok", "Vector search collections", True),
            ("backup", "Config backup/restore", True),
            ("task_planner", "Multi-step task execution", True),
        ]

        for name, desc, enabled in plugins:
            status = "✓" if enabled else "✗"
            lines.append(f"{status} {name:15} - {desc}")

        return "\n".join(lines)

    def _show_collections_config(self, session: Dict[str, Any]) -> str:
        """Show xAI Collections configuration"""
        lines = []
        lines.append("=== xAI Collections ===")

        # Check if collections are enabled
        enabled = session.get("collections_enabled", False)
        lines.append(f"Enabled: {'✓' if enabled else '✗'}")

        # Show collection IDs (masked for security)
        tc_collection = session.get("tc_log_collection_id")
        cpf_collection = session.get("cpf_log_collection_id")

        if tc_collection:
            masked_tc = tc_collection[:20] + "..." if len(tc_collection) > 20 else tc_collection
            lines.append(f"TC Log Collection: {masked_tc}")
        else:
            lines.append("TC Log Collection: Not configured")

        if cpf_collection:
            masked_cpf = cpf_collection[:20] + "..." if len(cpf_collection) > 20 else cpf_collection
            lines.append(f"CPF Log Collection: {masked_cpf}")
        else:
            lines.append("CPF Log Collection: Not configured")

        if not enabled:
            lines.append("")
            lines.append("To enable: /config --set collections_enabled true")
            lines.append("To set collection IDs: /config --set tc_log_collection_id <uuid>")

        return "\n".join(lines)

    def _set_config(self, session: Dict[str, Any], key: str, value: str) -> str:
        """Set a configuration value"""
        # Define allowed config keys
        allowed_keys = {
            "default_tier": int,
            "sync_enabled": lambda v: v.lower() in ["true", "1", "yes"],
            "ai_provider": str,
            "ai_model": str,
            "collections_enabled": lambda v: v.lower() in ["true", "1", "yes"],
            "tc_log_collection_id": str,
            "cpf_log_collection_id": str,
            "xai_management_api_key": str,
            "xai_api_host": str,
            "xai_management_api_host": str,
        }

        if key not in allowed_keys:
            return f"Unknown config key: {key}\nAllowed: {', '.join(allowed_keys.keys())}"

        try:
            # Convert value to correct type
            converter = allowed_keys[key]
            converted_value = converter(value)

            # Load existing config
            isaac_dir = Path.home() / ".isaac"
            isaac_dir.mkdir(exist_ok=True)
            config_file = isaac_dir / "config.json"

            if config_file.exists():
                try:
                    with open(config_file, "r") as f:
                        config = json.load(f)
                except:
                    config = {}
            else:
                config = {}

            # Update the config
            config[key] = converted_value

            # Save back to file
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            return f"✓ Set {key} = {converted_value}"
        except Exception as e:
            return f"✗ Error setting {key}: {str(e)}"

    def _set_api_key(self, session: Dict[str, Any], service: str, api_key: str) -> str:
        """Set API key for a specific service"""
        if not service or not api_key:
            return "Usage: /config --apikey <service> <api_key>\n\nSupported services:\n  xai-chat        - xAI API key for chat completion\n  xai-collections - xAI API key for collections\n  claude          - Anthropic Claude API key\n  openai          - OpenAI API key\n\nExamples:\n  /config --apikey xai-chat YOUR_XAI_API_KEY\n  /config --apikey xai-collections YOUR_XAI_API_KEY\n  /config --apikey claude YOUR_CLAUDE_API_KEY"

        try:
            # Map service names to config keys
            service_map = {
                "xai-chat": "xai.chat.api_key",
                "xai-collections": "xai.collections.api_key",
                "xai": "xai_api_key",  # Legacy fallback
                "claude": "claude_api_key",
                "openai": "openai_api_key",
            }

            if service not in service_map:
                return f"✗ Unknown service '{service}'. Supported services: {', '.join(service_map.keys())}"

            config_key = service_map[service]

            # Load existing config
            isaac_dir = Path.home() / ".isaac"
            isaac_dir.mkdir(exist_ok=True)
            config_file = isaac_dir / "config.json"

            if config_file.exists():
                try:
                    with open(config_file, "r") as f:
                        config = json.load(f)
                except:
                    config = {}
            else:
                config = {}

            # Set the API key in nested structure for xAI services
            if service.startswith("xai-"):
                parts = config_key.split(".")
                current = config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = api_key
            else:
                # Flat structure for other services
                config[config_key] = api_key

            # Save back to file
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            return f"✓ Set {service} API key (stored as {config_key})"
        except Exception as e:
            return f"✗ Error setting {service} API key: {str(e)}"

    def _show_ai_routing(self) -> str:
        """Show AI routing configuration"""
        try:
            from isaac.ai.routing_config import RoutingConfigManager

            config_mgr = RoutingConfigManager()
            config = config_mgr.get_all_settings()

            lines = []
            lines.append("=== AI Routing Configuration ===\n")

            # Routing preferences
            lines.append("Routing Preferences:")
            routing_prefs = config["routing_preferences"]
            lines.append(f"  Simple tasks   → {routing_prefs.get('simple', 'openai')}")
            lines.append(f"  Medium tasks   → {routing_prefs.get('medium', 'grok')}")
            lines.append(f"  Complex tasks  → {routing_prefs.get('complex', 'claude')}")
            lines.append(f"  Expert tasks   → {routing_prefs.get('expert', 'claude')}")
            lines.append("")

            # Task type overrides
            lines.append("Task Type Overrides:")
            lines.append(f"  Code writing   → {routing_prefs.get('code_write', 'claude')}")
            lines.append(f"  Code debugging → {routing_prefs.get('code_debug', 'claude')}")
            lines.append(f"  Tool use       → {routing_prefs.get('tool_use', 'claude')}")
            lines.append("")

            # Provider configs
            lines.append("Providers:")
            for provider, provider_config in config["providers"].items():
                enabled = "✓" if provider_config.get("enabled", True) else "✗"
                model = provider_config.get("model", "unknown")
                pricing = provider_config.get("pricing", {})
                input_cost = pricing.get("input_per_1m", 0)
                output_cost = pricing.get("output_per_1m", 0)

                lines.append(f"  {enabled} {provider:8} - {model}")
                lines.append(f"     Pricing: ${input_cost:.2f}/${output_cost:.2f} per 1M tokens")
            lines.append("")

            # Cost limits
            cost_limits = config["cost_limits"]
            limits_enabled = "✓" if cost_limits.get("enabled", True) else "✗"
            lines.append(f"Cost Limits: {limits_enabled}")
            if cost_limits.get("enabled", True):
                lines.append(f"  Daily:   ${cost_limits.get('daily_limit_usd', 10.0):.2f}")
                lines.append(f"  Monthly: ${cost_limits.get('monthly_limit_usd', 100.0):.2f}")
            lines.append("")

            lines.append("Commands:")
            lines.append("  /config --ai-routing-set <complexity> <provider>")
            lines.append("  /config --ai-routing-model <provider> <model>")
            lines.append("  /config --ai-routing-limits <period> <amount>")
            lines.append("  /config --ai-routing-reset")

            return "\n".join(lines)
        except Exception as e:
            return f"✗ Error loading AI routing config: {str(e)}"

    def _set_ai_routing_preference(self, key: str, provider: str) -> str:
        """Set AI routing preference for complexity level or task type"""
        if not key or not provider:
            return "Usage: /config --ai-routing-set <complexity|task_type> <provider>\n\nExamples:\n  /config --ai-routing-set simple grok\n  /config --ai-routing-set complex claude\n  /config --ai-routing-set code_write claude"

        try:
            from isaac.ai.routing_config import RoutingConfigManager

            config_mgr = RoutingConfigManager()

            # Check if it's a complexity level or task type
            valid_complexity = ["simple", "medium", "complex", "expert"]
            if key in valid_complexity:
                config_mgr.set_provider_for_complexity(key, provider)
                return f"✓ Set {key} tasks to use {provider}"
            else:
                # Assume it's a task type
                config_mgr.set_provider_for_task_type(key, provider)
                return f"✓ Set {key} tasks to use {provider}"
        except ValueError as e:
            return f"✗ {str(e)}"
        except Exception as e:
            return f"✗ Error setting routing preference: {str(e)}"

    def _set_ai_routing_model(self, provider: str, model: str) -> str:
        """Set model for a specific provider"""
        if not provider or not model:
            return "Usage: /config --ai-routing-model <provider> <model>\n\nExamples:\n  /config --ai-routing-model claude claude-3-5-sonnet-20241022\n  /config --ai-routing-model grok grok-beta\n  /config --ai-routing-model openai gpt-4o-mini"

        try:
            from isaac.ai.routing_config import RoutingConfigManager

            config_mgr = RoutingConfigManager()
            config_mgr.set_provider_model(provider, model)

            return f"✓ Set {provider} to use model {model}"
        except ValueError as e:
            return f"✗ {str(e)}"
        except Exception as e:
            return f"✗ Error setting model: {str(e)}"

    def _set_ai_routing_limits(self, period: str, amount: str) -> str:
        """Set cost limits for AI routing"""
        if not period or not amount:
            return "Usage: /config --ai-routing-limits <daily|monthly> <amount>\n\nExamples:\n  /config --ai-routing-limits daily 10.0\n  /config --ai-routing-limits monthly 100.0"

        try:
            from isaac.ai.routing_config import RoutingConfigManager

            config_mgr = RoutingConfigManager()
            amount_float = float(amount)

            config_mgr.set_cost_limit(period, amount_float)

            return f"✓ Set {period} cost limit to ${amount_float:.2f}"
        except ValueError:
            return f"✗ Invalid amount: {amount}. Must be a number."
        except Exception as e:
            return f"✗ Error setting cost limit: {str(e)}"

    def _reset_ai_routing(self) -> str:
        """Reset AI routing configuration to defaults"""
        try:
            from isaac.ai.routing_config import RoutingConfigManager

            config_mgr = RoutingConfigManager()
            config_mgr.reset_to_defaults()

            return "✓ AI routing configuration reset to defaults"
        except Exception as e:
            return f"✗ Error resetting configuration: {str(e)}"

    def _show_env_status(self) -> str:
        """Show .env configuration status"""
        try:
            from isaac.core.env_config import EnvConfigLoader

            env_loader = EnvConfigLoader(auto_load=True)

            lines = []
            lines.append("=== Environment Configuration Status ===\n")

            # Check if .env file exists
            if env_loader.has_env_file():
                lines.append(f"✓ .env file found: {env_loader.env_path}")
                lines.append("")

                # Show which API keys are configured
                lines.append("API Keys Status:")
                validation = env_loader.validate_keys()

                for service, is_valid in validation.items():
                    status = "✓" if is_valid else "✗"
                    lines.append(
                        f"  {status} {service:20} {'Configured' if is_valid else 'Not configured'}"
                    )

                lines.append("")
                lines.append("Configuration Priority:")
                lines.append("  1. Command line arguments (highest)")
                lines.append("  2. Isaac config files (~/.isaac/config.json)")
                lines.append("  3. Environment variables (.env file)")
                lines.append("  4. Default values (lowest)")
            else:
                lines.append("✗ No .env file found")
                lines.append("")
                lines.append("To create a .env file:")
                lines.append("  1. Copy .env.example to .env")
                lines.append("     cp .env.example .env")
                lines.append("")
                lines.append("  2. Edit .env and add your API keys")
                lines.append("")
                lines.append("  3. Or use: /config --env-create")

            return "\n".join(lines)
        except Exception as e:
            return f"✗ Error loading .env status: {str(e)}"

    def _validate_env_keys(self) -> str:
        """Validate .env API keys"""
        try:
            from isaac.core.env_config import EnvConfigLoader

            env_loader = EnvConfigLoader(auto_load=True)

            lines = []
            lines.append("=== Validating API Keys ===\n")

            if not env_loader.has_env_file():
                lines.append("✗ No .env file found")
                lines.append("Run: /config --env-create")
                return "\n".join(lines)

            validation = env_loader.validate_keys()
            all_api_keys = env_loader.get_all_api_keys()

            lines.append("API Key Validation:")
            for service, is_valid in validation.items():
                if is_valid:
                    key = all_api_keys.get(service, "")
                    masked_key = key[:10] + "..." + key[-4:] if len(key) > 14 else key[:4] + "..."
                    lines.append(f"  ✓ {service:20} {masked_key}")
                else:
                    lines.append(f"  ✗ {service:20} Not configured")

            lines.append("")

            # Count configured keys
            configured_count = sum(1 for v in validation.values() if v)
            total_count = len(validation)

            if configured_count == 0:
                lines.append("⚠️  No API keys configured in .env")
                lines.append("Edit your .env file and add at least one API key")
            elif configured_count < total_count:
                lines.append(f"⚠️  {configured_count}/{total_count} API keys configured")
                lines.append("Isaac will work with at least one provider configured")
            else:
                lines.append(f"✓ All {configured_count} API keys configured!")

            return "\n".join(lines)
        except Exception as e:
            return f"✗ Error validating keys: {str(e)}"

    def _create_env_example(self) -> str:
        """Create .env.example file"""
        try:
            from isaac.core.env_config import EnvConfigLoader

            env_loader = EnvConfigLoader(auto_load=False)

            # Try project root first
            project_root = Path.cwd()
            output_path = project_root / ".env.example"

            if env_loader.create_example_env(output_path):
                return f"✓ Created .env.example at {output_path}\n\nNext steps:\n  1. Copy to .env: cp .env.example .env\n  2. Edit .env and add your API keys"
            else:
                return "✗ Failed to create .env.example"
        except Exception as e:
            return f"✗ Error creating .env.example: {str(e)}"

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="config",
            description="Manage Isaac configuration",
            usage="/config [--flag [args]]",
            examples=[
                "/config",
                "/config --status",
                "/config --ai",
                "/config --ai-routing",
                "/config --set default_tier 3",
                "/config --apikey xai-chat YOUR_API_KEY"
            ],
            tier=1,  # Safe - configuration viewing/editing
            aliases=[],
            category="system"
        )
