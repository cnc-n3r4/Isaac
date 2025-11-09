"""
Base Classes for Isaac Command Standardization

Provides standardized interfaces for command implementations to ensure
consistency, maintainability, and predictability across the codebase.

Created as part of Task 2.5: Command Schema Standardization
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import sys
import json


@dataclass
class CommandManifest:
    """
    Metadata for a command.

    Defines the command's name, description, usage pattern, examples,
    and safety tier for consistent help generation and command registration.
    """
    name: str
    description: str
    usage: str
    examples: List[str]
    tier: int  # 1=safe, 2=needs validation, 3=AI validation, 4=dangerous
    aliases: List[str] = field(default_factory=list)
    category: str = "general"  # general, file, ai, system, etc.


class CommandResponse:
    """
    Standard response format for all commands.

    Provides consistent success/error handling and output formatting
    across all command implementations.
    """

    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize command response.

        Args:
            success: Whether the command executed successfully
            data: The result data (can be any type)
            error: Error message if success=False
            metadata: Additional metadata about the execution
        """
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format"""
        result = {
            'success': self.success,
        }

        if self.data is not None:
            result['data'] = self.data

        if self.error is not None:
            result['error'] = self.error

        if self.metadata:
            result['metadata'] = self.metadata

        return result

    def to_envelope(self) -> Dict[str, Any]:
        """
        Convert to dispatcher envelope format.

        Returns envelope in format: {"ok": bool, "stdout": str, "error": dict}
        """
        if self.success:
            # Convert data to string for stdout
            stdout = self.data
            if not isinstance(stdout, str):
                stdout = json.dumps(self.data, indent=2) if self.data else ""

            return {"ok": True, "stdout": stdout}
        else:
            return {
                "ok": False,
                "error": {
                    "code": self.metadata.get("error_code", "EXECUTION_ERROR"),
                    "message": self.error or "Unknown error"
                }
            }

    def to_blob(self, command: str = "") -> Dict[str, Any]:
        """
        Convert to blob format (for piping).

        Returns blob in format: {"kind": str, "content": str, "meta": dict}
        """
        if self.success:
            # Determine kind based on data type
            kind = self.metadata.get("kind", "text")

            # Convert data to string for content
            content = self.data
            if not isinstance(content, str):
                content = json.dumps(self.data, indent=2) if self.data else ""

            return {
                "kind": kind,
                "content": content,
                "meta": {
                    "command": command,
                    **self.metadata
                }
            }
        else:
            return {
                "kind": "error",
                "content": f"Error: {self.error}",
                "meta": {
                    "command": command,
                    **self.metadata
                }
            }


class FlagParser:
    """
    Unified flag parsing for all commands.

    Provides consistent argument and flag parsing across command implementations.
    Handles both -- flags and positional arguments.
    """

    def __init__(self, args: List[str]):
        """
        Initialize parser with arguments.

        Args:
            args: List of command-line arguments (typically sys.argv[1:])
        """
        self.args = args
        self.flags: Dict[str, Any] = {}
        self.positional: List[str] = []
        self._parse()

    def _parse(self):
        """Parse arguments into flags and positional arguments"""
        i = 0
        while i < len(self.args):
            arg = self.args[i]

            # Check for flags
            if arg.startswith('--'):
                # Long flag (e.g., --output, --replace-all)
                flag_name = arg[2:]

                # Check if next arg is a value or another flag
                if i + 1 < len(self.args) and not self.args[i + 1].startswith('-'):
                    # Has value
                    self.flags[flag_name] = self.args[i + 1]
                    i += 2
                else:
                    # Boolean flag
                    self.flags[flag_name] = True
                    i += 1

            elif arg.startswith('-') and len(arg) == 2:
                # Short flag (e.g., -i, -C)
                flag_name = arg[1:]

                # Check if next arg is a value
                if i + 1 < len(self.args) and not self.args[i + 1].startswith('-'):
                    # Has value
                    self.flags[flag_name] = self.args[i + 1]
                    i += 2
                else:
                    # Boolean flag
                    self.flags[flag_name] = True
                    i += 1

            else:
                # Positional argument
                self.positional.append(arg)
                i += 1

    def get_flag(self, name: str, default: Any = None, aliases: Optional[List[str]] = None) -> Any:
        """
        Get flag value by name.

        Args:
            name: Flag name (without -- prefix)
            default: Default value if flag not present
            aliases: Alternative names for the flag (e.g., ['i', 'ignore-case'])

        Returns:
            Flag value or default
        """
        # Check main name
        if name in self.flags:
            return self.flags[name]

        # Check aliases
        if aliases:
            for alias in aliases:
                if alias in self.flags:
                    return self.flags[alias]

        return default

    def get_positional(self, index: int, default: Any = None) -> Any:
        """
        Get positional argument by index.

        Args:
            index: Positional argument index (0-based)
            default: Default value if not present

        Returns:
            Argument value or default
        """
        if 0 <= index < len(self.positional):
            return self.positional[index]
        return default

    def has_flag(self, name: str, aliases: Optional[List[str]] = None) -> bool:
        """
        Check if a flag is present.

        Args:
            name: Flag name
            aliases: Alternative names for the flag

        Returns:
            True if flag is present
        """
        if name in self.flags:
            return True

        if aliases:
            for alias in aliases:
                if alias in self.flags:
                    return True

        return False

    def get_all_positional(self) -> List[str]:
        """Get all positional arguments"""
        return self.positional.copy()

    def get_all_flags(self) -> Dict[str, Any]:
        """Get all flags as dictionary"""
        return self.flags.copy()


class BaseCommand(ABC):
    """
    Base class for all Isaac commands.

    Provides standard interface for command execution, help generation,
    and output formatting. All commands should inherit from this class.
    """

    @abstractmethod
    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute the command with given arguments.

        Args:
            args: Command-line arguments (excluding command name)
            context: Optional execution context (session, config, etc.)

        Returns:
            CommandResponse with result or error
        """
        pass

    @abstractmethod
    def get_manifest(self) -> CommandManifest:
        """
        Get command metadata.

        Returns:
            CommandManifest with name, description, usage, examples, tier
        """
        pass

    def get_help(self) -> str:
        """
        Generate help text from manifest.

        Automatically generates formatted help text based on the command's manifest.
        Override this method for custom help formatting.

        Returns:
            Formatted help text
        """
        manifest = self.get_manifest()

        help_text = f"""
{manifest.name} - {manifest.description}

Usage: {manifest.usage}

Examples:
{chr(10).join(f"  {ex}" for ex in manifest.examples)}

Safety Tier: {manifest.tier}"""

        if manifest.aliases:
            help_text += f"\nAliases: {', '.join(manifest.aliases)}"

        return help_text

    def run_standalone(self, args: Optional[List[str]] = None) -> None:
        """
        Run command in standalone mode (direct execution).

        Handles argument parsing, execution, and output formatting for
        standalone command execution (not through dispatcher).

        Args:
            args: Command arguments (defaults to sys.argv[1:])
        """
        if args is None:
            args = sys.argv[1:]

        # Check for help flag
        if not args or '--help' in args or '-h' in args:
            print(self.get_help())
            sys.exit(0)

        try:
            # Execute command
            result = self.execute(args)

            # Output result
            if result.success:
                # Print data
                if isinstance(result.data, str):
                    print(result.data)
                elif result.data is not None:
                    print(json.dumps(result.data, indent=2))

                sys.exit(0)
            else:
                # Print error
                print(f"Error: {result.error}", file=sys.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def run_dispatcher(self, payload: Dict[str, Any]) -> None:
        """
        Run command through dispatcher (envelope format).

        Handles dispatcher payload parsing, execution, and envelope output.

        Args:
            payload: Dispatcher payload with command and metadata
        """
        try:
            # Extract command and arguments
            command_str = payload.get("command", "")
            manifest = self.get_manifest()

            # Parse arguments (remove command name)
            args = command_str.split()[1:] if " " in command_str else []

            # Execute command
            result = self.execute(args, context=payload)

            # Output envelope
            print(json.dumps(result.to_envelope()))

        except Exception as e:
            envelope = {
                "ok": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": str(e)
                }
            }
            print(json.dumps(envelope))

    def run_piped(self, blob: Dict[str, Any]) -> None:
        """
        Run command with piped input (blob format).

        Handles blob input parsing, execution, and blob output.

        Args:
            blob: Input blob with piped data
        """
        try:
            # Extract command and piped content
            command_str = blob.get("meta", {}).get("command", "")
            piped_content = blob.get("content", "")

            # Parse arguments
            args = command_str.split()[1:] if " " in command_str else []

            # Add piped content to context
            context = {
                "piped_input": piped_content,
                "piped_kind": blob.get("kind", "text"),
                "piped_meta": blob.get("meta", {})
            }

            # Execute command
            result = self.execute(args, context=context)

            # Output blob
            print(json.dumps(result.to_blob(command_str)))

        except Exception as e:
            error_blob = {
                "kind": "error",
                "content": f"Error: {e}",
                "meta": blob.get("meta", {})
            }
            print(json.dumps(error_blob))


def detect_execution_mode() -> str:
    """
    Detect how the command is being executed.

    Returns:
        "standalone", "dispatcher", or "piped"
    """
    if sys.stdin.isatty():
        return "standalone"

    try:
        # Try to read stdin
        stdin_data = sys.stdin.read()
        if not stdin_data:
            return "standalone"

        # Try to parse as JSON
        data = json.loads(stdin_data)

        # Check format
        if isinstance(data, dict):
            if "kind" in data:
                return "piped"
            elif "manifest" in data or "command" in data:
                return "dispatcher"

        return "standalone"

    except (json.JSONDecodeError, Exception):
        return "standalone"


def run_command(command_instance: BaseCommand, args: Optional[List[str]] = None) -> None:
    """
    Universal command runner.

    Detects execution mode and runs the command appropriately.
    Use this as the main entry point in command run.py files.

    Args:
        command_instance: Instance of a BaseCommand subclass
        args: Optional arguments (defaults to sys.argv[1:])
    """
    mode = detect_execution_mode()

    if mode == "standalone":
        command_instance.run_standalone(args)
    elif mode == "dispatcher":
        stdin_data = sys.stdin.read()
        payload = json.loads(stdin_data)
        command_instance.run_dispatcher(payload)
    elif mode == "piped":
        stdin_data = sys.stdin.read()
        blob = json.loads(stdin_data)
        command_instance.run_piped(blob)
