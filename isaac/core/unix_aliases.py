"""
Unix Alias Translation System
Translate Unix commands to PowerShell equivalents for cross-platform convenience
"""

import json
import re
from pathlib import Path
from typing import Optional, Dict, List


class UnixAliasTranslator:
    """Translate Unix commands to PowerShell equivalents"""

    def __init__(self, config_path: Path = None):
        """Load alias configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'data' / 'unix_aliases.json'

        with open(config_path) as f:
            self.aliases = json.load(f)

        self.enabled = True
        self.show_translation = True

    def translate(self, command: str) -> Optional[str]:
        """
        Translate Unix command to PowerShell equivalent.
        Returns None if no translation available.
        """
        if not self.enabled:
            return None

        # Parse command
        parts = command.split()
        if not parts:
            return None

        cmd_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # Check if we have an alias for this command
        if cmd_name not in self.aliases:
            return None

        alias_config = self.aliases[cmd_name]
        powershell_cmd = alias_config['powershell']

        # Simple case: no args or no arg mapping
        if not args or 'arg_mapping' not in alias_config:
            return f"{powershell_cmd} {' '.join(args)}"

        # Complex case: map Unix args to PowerShell args
        return self._translate_with_arg_mapping(
            powershell_cmd,
            args,
            alias_config['arg_mapping']
        )

    def _translate_with_arg_mapping(
        self,
        powershell_cmd: str,
        args: List[str],
        arg_mapping: Dict[str, str]
    ) -> str:
        """Translate command with argument mapping"""
        translated_args = []
        skip_next = False

        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue

            # Check if this is a flag we need to map
            if arg in arg_mapping:
                mapped = arg_mapping[arg]
                if mapped:
                    translated_args.append(mapped)
                    # Check if next arg is the value for this flag
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        translated_args.append(args[i + 1])
                        skip_next = True
            else:
                # No mapping, use default
                if 'default' in arg_mapping:
                    translated_args.append(f"{arg_mapping['default']} {arg}")
                else:
                    translated_args.append(arg)

        return f"{powershell_cmd} {' '.join(translated_args)}".strip()

    def get_description(self, command: str) -> Optional[str]:
        """Get description for a command"""
        parts = command.split()
        if not parts:
            return None

        cmd_name = parts[0]
        if cmd_name in self.aliases:
            return self.aliases[cmd_name]['description']

        return None

    def get_examples(self, command: str) -> List[Dict]:
        """Get examples for a command"""
        parts = command.split()
        if not parts:
            return []

        cmd_name = parts[0]
        if cmd_name in self.aliases:
            return self.aliases[cmd_name].get('examples', [])

        return []

    def list_aliases(self) -> Dict[str, str]:
        """List all available aliases with descriptions"""
        return {cmd: config['description'] for cmd, config in self.aliases.items()}

    def set_enabled(self, enabled: bool):
        """Enable or disable translation"""
        self.enabled = enabled

    def set_show_translation(self, show: bool):
        """Show or hide translation messages"""
        self.show_translation = show