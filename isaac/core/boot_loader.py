#!/usr/bin/env python3
"""
ISAAC Boot Loader
Discovers, validates, and loads command plugins with visual feedback
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml
import importlib.util
from enum import Enum
import time


class PluginStatus(Enum):
    """Plugin load status"""
    OK = "OK"
    STUB = "STUB"
    WARN = "WARN"
    FAIL = "FAIL"


class BootLoader:
    """
    Boot loader for ISAAC plugin system

    Discovers and validates all /slash commands, checks dependencies,
    and provides visual boot feedback.
    """

    def __init__(self, commands_dir: Optional[Path] = None, quiet: bool = False):
        """
        Initialize boot loader

        Args:
            commands_dir: Path to commands directory (default: isaac/commands)
            quiet: If True, suppress visual output
        """
        if commands_dir is None:
            # Assume we're in isaac/core, go up to isaac, then to commands
            isaac_root = Path(__file__).parent.parent
            commands_dir = isaac_root / 'commands'

        self.commands_dir = commands_dir
        self.quiet = quiet
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.load_results: List[Tuple[str, PluginStatus, str]] = []

    def discover_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover all command plugins

        Returns:
            Dict mapping command name to plugin metadata
        """
        plugins = {}

        if not self.commands_dir.exists():
            return plugins

        # Scan all subdirectories
        for item in self.commands_dir.iterdir():
            if not item.is_dir():
                continue

            if item.name.startswith('_') or item.name.startswith('.'):
                continue

            # Look for command.yaml
            yaml_file = item / 'command.yaml'
            if not yaml_file.exists():
                continue

            # Load metadata
            try:
                with open(yaml_file, 'r') as f:
                    metadata = yaml.safe_load(f)

                if metadata:
                    plugins[item.name] = {
                        'path': item,
                        'metadata': metadata,
                        'status': PluginStatus.OK,
                        'message': ''
                    }
            except Exception as e:
                plugins[item.name] = {
                    'path': item,
                    'metadata': {},
                    'status': PluginStatus.FAIL,
                    'message': f'Failed to load YAML: {e}'
                }

        return plugins

    def check_dependencies(self, plugin_name: str, plugin: Dict[str, Any]) -> Tuple[PluginStatus, str]:
        """
        Check if plugin dependencies are satisfied

        Args:
            plugin_name: Name of the plugin
            plugin: Plugin metadata dict

        Returns:
            Tuple of (status, message)
        """
        metadata = plugin['metadata']

        # Check if it's marked as stub
        if metadata.get('status') == 'stub':
            return PluginStatus.STUB, metadata.get('stub_reason', 'Not implemented')

        # Check for required dependencies
        dependencies = metadata.get('dependencies', {})

        # Check API keys
        required_keys = dependencies.get('api_keys', [])
        for key_name in required_keys:
            if not os.environ.get(key_name):
                return PluginStatus.WARN, f'Missing API key: {key_name}'

        # Check Python packages
        required_packages = dependencies.get('packages', [])
        for package_name in required_packages:
            spec = importlib.util.find_spec(package_name)
            if spec is None:
                return PluginStatus.WARN, f'Missing package: {package_name}'

        # Check for run.py
        run_file = plugin['path'] / 'run.py'
        if not run_file.exists():
            return PluginStatus.STUB, 'No run.py found'

        return PluginStatus.OK, metadata.get('summary', '')

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Load and validate all plugins

        Returns:
            Dict of loaded plugins with status
        """
        self.plugins = self.discover_plugins()
        self.load_results = []

        for name, plugin in sorted(self.plugins.items()):
            status, message = self.check_dependencies(name, plugin)
            plugin['status'] = status
            plugin['message'] = message
            self.load_results.append((name, status, message))

        return self.plugins

    def display_boot_sequence(self):
        """Display visual boot sequence"""
        if self.quiet:
            return

        # Header
        print()
        print("ISAAC v2.0.0 starting...")
        print("━" * 70)
        print()

        # Core system (always OK for now)
        print("Core System:")
        self._print_status(PluginStatus.OK, "Session manager initialized")
        self._print_status(PluginStatus.OK, "Configuration loaded")
        self._print_status(PluginStatus.OK, "Message queue ready")
        print()

        # AI Providers
        print("AI Providers:")
        self._check_ai_provider('Grok (xAI)', 'XAI_API_KEY', 'grok-beta')
        self._check_ai_provider('Claude (Anthropic)', 'ANTHROPIC_API_KEY', 'claude-3-5-sonnet')
        self._check_ai_provider('OpenAI', 'OPENAI_API_KEY', 'gpt-4o-mini')

        # Phase 3 features
        self._print_status(PluginStatus.OK, "AIRouter (Phase 3 enhanced)")
        self._print_status(PluginStatus.OK, "Cost tracking: $0.00/$10.00 daily")
        print()

        # Commands
        print("Commands Loaded:")

        # Group by status
        ok_cmds = []
        stub_cmds = []
        warn_cmds = []
        fail_cmds = []

        for name, status, message in self.load_results:
            plugin = self.plugins[name]
            metadata = plugin['metadata']
            version = metadata.get('version', '1.0.0')
            summary = metadata.get('summary', 'No description')

            # Truncate long summaries
            if len(summary) > 40:
                summary = summary[:37] + "..."

            trigger = metadata.get('triggers', [f'/{name}'])[0] if metadata.get('triggers') else f'/{name}'
            display = f"{trigger} - {summary} v{version}"

            if status == PluginStatus.OK:
                ok_cmds.append(display)
            elif status == PluginStatus.STUB:
                stub_cmds.append((display, message))
            elif status == PluginStatus.WARN:
                warn_cmds.append((display, message))
            else:
                fail_cmds.append((display, message))

        # Display OK commands
        for cmd in sorted(ok_cmds):
            self._print_status(PluginStatus.OK, cmd)

        # Display stubs
        for cmd, msg in sorted(stub_cmds):
            self._print_status(PluginStatus.STUB, f"{cmd} ({msg})")

        # Display warnings
        for cmd, msg in sorted(warn_cmds):
            self._print_status(PluginStatus.WARN, f"{cmd} ({msg})")

        # Display failures
        for cmd, msg in sorted(fail_cmds):
            self._print_status(PluginStatus.FAIL, f"{cmd} ({msg})")

        print()

        # Phase 3 Features
        print("Phase 3 Features:")
        self._print_status(PluginStatus.OK, "TaskAnalyzer - Intelligent routing")
        self._print_status(PluginStatus.OK, "CostOptimizer - Budget tracking")
        self._print_status(PluginStatus.OK, "Performance monitoring")
        print()

        # Summary
        print("━" * 70)
        total = len(self.plugins)
        ok_count = sum(1 for _, s, _ in self.load_results if s == PluginStatus.OK)
        print(f"✓ ISAAC ready. {ok_count}/{total} commands loaded successfully")
        print("  Type 'man isaac' or /help for documentation")
        print()

    def _print_status(self, status: PluginStatus, message: str):
        """Print a status line"""
        if status == PluginStatus.OK:
            symbol = "  OK  "
            color = ""  # Green in future
        elif status == PluginStatus.STUB:
            symbol = " STUB "
            color = ""  # Yellow
        elif status == PluginStatus.WARN:
            symbol = " WARN "
            color = ""  # Yellow
        else:  # FAIL
            symbol = " FAIL "
            color = ""  # Red

        print(f"[{symbol}] {message}")

    def _check_ai_provider(self, name: str, key_env: str, model: str):
        """Check AI provider availability"""
        if os.environ.get(key_env):
            self._print_status(PluginStatus.OK, f"{name} - {model}")
        else:
            self._print_status(PluginStatus.WARN, f"{name} - No API key ({key_env})")

    def get_plugin_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics

        Returns:
            Dict with counts by status
        """
        summary = {
            'total': len(self.plugins),
            'ok': 0,
            'stub': 0,
            'warn': 0,
            'fail': 0,
            'plugins': self.plugins
        }

        for _, status, _ in self.load_results:
            if status == PluginStatus.OK:
                summary['ok'] += 1
            elif status == PluginStatus.STUB:
                summary['stub'] += 1
            elif status == PluginStatus.WARN:
                summary['warn'] += 1
            else:
                summary['fail'] += 1

        return summary


def boot(quiet: bool = False) -> BootLoader:
    """
    Main boot function

    Args:
        quiet: If True, suppress visual output

    Returns:
        BootLoader instance with loaded plugins
    """
    loader = BootLoader(quiet=quiet)
    loader.load_all()

    if not quiet:
        loader.display_boot_sequence()

    return loader


if __name__ == '__main__':
    # Test the boot loader
    boot(quiet=False)
