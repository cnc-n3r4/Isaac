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

    def __init__(self, config_path: Optional[Path] = None):
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
            result = f"{powershell_cmd} {' '.join(args)}".strip()
            return result if result != powershell_cmd else powershell_cmd

        # Complex case: map Unix args to PowerShell args
        if '|' in powershell_cmd:
            base_cmd, pipe_cmd = powershell_cmd.split(' | ', 1)
            return self._translate_piped_command(
                base_cmd,
                pipe_cmd,
                args,
                alias_config['arg_mapping'],
                cmd_name
            )
        else:
            return self._translate_with_arg_mapping(
                powershell_cmd,
                args,
                alias_config['arg_mapping'],
                cmd_name
            )

    def _translate_with_arg_mapping(
        self,
        powershell_cmd: str,
        args: List[str],
        arg_mapping: Dict[str, str],
        cmd_name: str
    ) -> str:
        """Translate command with argument mapping"""
        # Special handling for commands that need piping
        if '|' in powershell_cmd:
            # Commands like "Get-Content | Measure-Object" need special handling
            base_cmd, pipe_cmd = powershell_cmd.split(' | ', 1)
            return self._translate_piped_command(base_cmd, pipe_cmd, args, arg_mapping, cmd_name)

        # Handle flag mappings
        translated_args = []
        skip_next = False
        remaining_args = []
        pipe_operation = None

        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue

            if arg in arg_mapping:
                mapped = arg_mapping[arg]
                if mapped:
                    if mapped.startswith('| '):
                        # This flag adds a pipe operation
                        pipe_operation = mapped[2:]  # Remove '| '
                        if arg == '-la':
                            # Special case: -la implies both -a (hidden files) and -l (long listing)
                            translated_args.append('-Force')
                    elif arg == '-a':
                        translated_args.append('-Force')
                    else:
                        translated_args.append(mapped)
                        # Only consume next arg as value if this flag actually takes a value
                        # For now, assume flags like -9, -l, -a don't take values
                        if arg not in ['-9', '-l', '-la', '-a'] and i + 1 < len(args) and not args[i + 1].startswith('-'):
                            translated_args.append(args[i + 1])
                            skip_next = True
            else:
                # This is not a mapped flag, keep for default processing
                remaining_args.append(arg)

        # Apply default mapping to remaining args
        if 'default' in arg_mapping and remaining_args:
            default_flag = arg_mapping['default']
            for arg in remaining_args:
                translated_args.append(f"{default_flag} {arg}")

        # Build the result
        result = f"{powershell_cmd} {' '.join(translated_args)}".strip()
        if pipe_operation:
            result = f"{result} | {pipe_operation}".strip()

        return result

    def _translate_piped_command(
        self,
        base_cmd: str,
        pipe_cmd: str,
        args: List[str],
        arg_mapping: Dict[str, str],
        cmd_name: str
    ) -> str:
        """Translate commands that use piping like Get-Content | Measure-Object"""
        flag_args = []
        file_args = []
        skip_next = False

        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue

            if arg.startswith('-'):
                # Handle numeric arguments like -10 (should be -n 10 for head/tail)
                if arg[1:].isdigit() and len(arg) > 1:
                    # Convert -10 to appropriate flag based on command
                    num = arg[1:]
                    if "Select-Object" in pipe_cmd:
                        if cmd_name == "head":
                            flag_args.extend(["-First", num])
                        elif cmd_name == "tail":
                            flag_args.extend(["-Last", num])
                        else:
                            # Default to -First for other commands
                            flag_args.extend(["-First", num])
                    continue

                if arg in arg_mapping:
                    mapped = arg_mapping[arg]
                    if mapped:
                        flag_args.append(mapped)
                        # Check if this flag takes a value
                        if arg not in ['-9', '-l', '-la', '-a'] and i + 1 < len(args) and not args[i + 1].startswith('-'):
                            flag_args.append(args[i + 1])
                            skip_next = True
            else:
                file_args.append(arg)

        if not file_args:
            return f"{base_cmd} | {pipe_cmd} {' '.join(flag_args)}".strip()

        # Apply to first file
        file_arg = file_args[0]
        result = f"{base_cmd} {file_arg} | {pipe_cmd} {' '.join(flag_args)}".strip()
        return result

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
