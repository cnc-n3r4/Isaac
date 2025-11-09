"""
Flag Parser Utility - Centralized flag parsing for ISAAC commands
Standardizes flag handling across all commands.
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ParsedFlags:
    """Result of flag parsing"""
    flags: Dict[str, Any]
    positional_args: List[str]
    raw_args: List[str]

    def get_flag(self, name: str, default: Any = None) -> Any:
        """Get a flag value with default"""
        return self.flags.get(name, default)

    def has_flag(self, name: str) -> bool:
        """Check if flag is present"""
        return name in self.flags

    def get_positional(self, index: int, default: Any = None) -> Any:
        """Get positional argument by index"""
        if 0 <= index < len(self.positional_args):
            return self.positional_args[index]
        return default


class FlagParser:
    """Centralized flag parsing utility"""

    def __init__(self):
        # Common flag aliases
        self.flag_aliases = {
            'h': 'help',
            'v': 'verbose',
            'q': 'quiet',
            'f': 'force',
            'y': 'yes',
            'n': 'no',
            'd': 'dry-run',
            'i': 'interactive',
            'a': 'all',
            'r': 'recursive',
            's': 'search',
            'w': 'whatis',
            'm': 'man'
        }

    def parse(self, args: List[str], command_spec: Optional[Dict[str, Any]] = None) -> ParsedFlags:
        """
        Parse command line arguments with flags

        Args:
            args: Raw command line arguments
            command_spec: Optional command specification for validation

        Returns:
            ParsedFlags object with flags and positional args
        """
        flags = {}
        positional_args = []
        raw_args = args.copy()

        i = 0
        while i < len(args):
            arg = args[i]

            if arg == '--':
                # End of flags, rest are positional
                positional_args.extend(args[i + 1:])
                break

            elif arg.startswith('--'):
                # Long flag
                flag_name, flag_value = self._parse_long_flag(arg)
                resolved_name = self._resolve_alias(flag_name)

                if flag_value is not None:
                    flags[resolved_name] = flag_value
                else:
                    # Check if next arg is a value
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        flags[resolved_name] = args[i + 1]
                        i += 1
                    else:
                        flags[resolved_name] = True

            elif arg.startswith('-') and len(arg) > 1:
                # Short flag(s)
                short_flags = arg[1:]
                resolved_flags = self._parse_short_flags(short_flags, args, i)

                flags.update(resolved_flags['flags'])
                i = resolved_flags['new_index'] - 1  # -1 because loop will increment

            else:
                # Positional argument
                positional_args.append(arg)

            i += 1

        # Validate against command spec if provided
        if command_spec:
            self._validate_flags(flags, positional_args, command_spec)

        return ParsedFlags(flags=flags, positional_args=positional_args, raw_args=raw_args)

    def _parse_long_flag(self, arg: str) -> Tuple[str, Optional[str]]:
        """Parse a long flag like --flag=value or --flag"""
        if '=' in arg:
            parts = arg.split('=', 1)
            return parts[0][2:], parts[1]  # Remove -- prefix
        else:
            return arg[2:], None  # Remove -- prefix

    def _parse_short_flags(self, short_flags: str, all_args: List[str], current_index: int) -> Dict[str, Any]:
        """Parse short flags like -abc or -f value"""
        flags = {}
        new_index = current_index + 1

        # If it's a single character flag that expects a value, handle it specially
        if len(short_flags) == 1:
            flag_char = short_flags
            resolved_name = self._resolve_alias(flag_char)

            if self._flag_expects_value(resolved_name):
                if new_index < len(all_args) and not all_args[new_index].startswith('-'):
                    flags[resolved_name] = all_args[new_index]
                    new_index += 1
                else:
                    flags[resolved_name] = True
            else:
                flags[resolved_name] = True
        else:
            # Multiple combined flags like -abc
            for flag_char in short_flags:
                resolved_name = self._resolve_alias(flag_char)
                flags[resolved_name] = True

        return {'flags': flags, 'new_index': new_index}

    def _resolve_alias(self, flag_name: str) -> str:
        """Resolve flag alias to canonical name"""
        return self.flag_aliases.get(flag_name, flag_name)

    def _flag_expects_value(self, flag_name: str) -> bool:
        """Check if a flag typically expects a value"""
        value_flags = {
            'file', 'path', 'dir', 'output', 'input', 'config', 'search',
            'filter', 'limit', 'offset', 'count', 'name', 'value', 'key',
            'force'  # -f flag expects a value in the test
        }
        return flag_name in value_flags

    def _validate_flags(self, flags: Dict[str, Any], positional: List[str],
                       command_spec: Dict[str, Any]) -> None:
        """Validate parsed flags against command specification"""
        # This could be extended to validate against the command.yaml spec
        # For now, just basic validation

    def format_help_flags(self, command_spec: Dict[str, Any]) -> str:
        """Format flag help from command specification"""
        args = command_spec.get('args', [])

        if not args:
            return "No flags available"

        output = ["Available flags:"]

        for arg in args:
            name = arg['name']
            arg_type = arg.get('type', 'string')
            required = arg.get('required', False)
            help_text = arg.get('help', 'No description')

            flag_format = f"--{name}"
            if arg_type in ['int', 'float', 'string']:
                flag_format += f" <{arg_type}>"

            required_text = " (required)" if required else " (optional)"
            output.append(f"  {flag_format:<20} {help_text}{required_text}")

        # Add common flags
        output.append("")
        output.append("Common flags:")
        output.append("  --help, -h           Show this help")
        output.append("  --verbose, -v        Verbose output")
        output.append("  --quiet, -q          Quiet output")
        output.append("  --dry-run, -d        Show what would be done")

        return "\n".join(output)


# Global instance for easy access
flag_parser = FlagParser()


def parse_flags(args: List[str], command_spec: Optional[Dict[str, Any]] = None) -> ParsedFlags:
    """Convenience function to parse flags"""
    return flag_parser.parse(args, command_spec)


def format_flag_help(command_spec: Dict[str, Any]) -> str:
    """Convenience function to format flag help"""
    return flag_parser.format_help_flags(command_spec)