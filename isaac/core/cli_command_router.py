"""
Command Router - Parse and route commands to appropriate handlers.

Handles:
- Internal commands (--help, --version, etc.)
- Shell commands (cd, ls, cp, etc.)
- Natural language commands (via AI translator)
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
import shlex


class CommandType(Enum):
    """Types of commands Isaac can handle."""
    INTERNAL = "internal"      # --help, --version, etc.
    SHELL = "shell"            # cd, ls, cp, etc.
    NATURAL = "natural"        # AI-translated commands
    TASK = "task"              # isaac task: description
    UNKNOWN = "unknown"


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    message: str
    status_symbol: str  # '✓' / '✗' / '⊘'
    suggestion: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __str__(self):
        """Format result for display."""
        output = f"{self.status_symbol} {self.message}"
        if self.suggestion:
            output += f"\n   💡 {self.suggestion}"
        return output


class CommandRouter:
    """
    Parse and route commands to appropriate handlers.

    Identifies command type and delegates to handlers:
    - Internal commands: --help, --version
    - Shell commands: cd, ls, cp, etc.
    - Natural language: Requires AI translation
    """

    # Internal commands that Isaac handles directly
    INTERNAL_COMMANDS = {
        '--help', '-h',
        '--version', '-v',
        '--show-log',
        '--config',
        'help'
    }

    # Common shell commands (basic validation)
    SHELL_COMMANDS = {
        'cd', 'ls', 'dir', 'pwd', 'cat', 'echo',
        'cp', 'mv', 'rm', 'mkdir', 'rmdir',
        'grep', 'find', 'chmod', 'chown'
    }

    def __init__(self, session_manager):
        """
        Initialize router with session manager.

        Args:
            session_manager: SessionManager instance for logging
        """
        self.session = session_manager

    def parse(self, command_string: str) -> Tuple[CommandType, List[str]]:
        """
        Parse command string and identify type.

        Args:
            command_string: Raw command input from user

        Returns:
            Tuple of (CommandType, parsed_arguments)

        Examples:
            "backup my documents" → (NATURAL, ["backup", "my", "documents"])
            "--help" → (INTERNAL, ["--help"])
            "cd /home" → (SHELL, ["cd", "/home"])
        """
        # Handle empty input
        if not command_string or command_string.strip() == "":
            return (CommandType.UNKNOWN, [])

        # Parse command into tokens (respects quotes)
        try:
            tokens = shlex.split(command_string)
        except ValueError as e:
            # Handle unclosed quotes gracefully
            tokens = command_string.split()

        if not tokens:
            return (CommandType.UNKNOWN, [])

        # Check for internal commands
        first_token = tokens[0].lower()
        if first_token in self.INTERNAL_COMMANDS:
            return (CommandType.INTERNAL, tokens)

        # Check for task mode
        if first_token == 'task' and len(tokens) > 1:
            if tokens[1] == ':':
                # Format: isaac task : do something
                task_desc = ' '.join(tokens[2:])
                return (CommandType.TASK, [task_desc])
            else:
                # Format: isaac task: do something
                task_desc = ' '.join(tokens[1:])
                if task_desc.startswith(':'):
                    task_desc = task_desc[1:].strip()
                return (CommandType.TASK, [task_desc])

        # Check for shell commands
        if first_token in self.SHELL_COMMANDS:
            return (CommandType.SHELL, tokens)

        # Default to natural language (needs AI translation)
        return (CommandType.NATURAL, tokens)

    def execute(self, command_string: str) -> CommandResult:
        """
        Execute command after parsing and routing.

        Args:
            command_string: Command to execute

        Returns:
            CommandResult with status and message
        """
        # Log command attempt
        self.session.log_command(command_string)

        # Parse command
        cmd_type, tokens = self.parse(command_string)

        # P0-1: Check for natural language prefix requirement
        if cmd_type == CommandType.NATURAL:
            first_word = tokens[0].lower() if tokens else ""
            # Allow direct commands through (backup, restore, list)
            direct_commands = {'backup', 'restore', 'list'}
            if first_word not in direct_commands and not command_string.lower().startswith("isaac "):
                return CommandResult(
                    success=False,
                    status_symbol='⊘',
                    message="I have a name, use it.",
                    suggestion=f"Try: isaac {command_string}",
                    metadata={
                        "error_type": "missing_prefix",
                        "hint": "Natural language commands require the 'isaac' prefix"
                    }
                )

        # Route to appropriate handler
        if cmd_type == CommandType.INTERNAL:
            return self._handle_internal(tokens)
        elif cmd_type == CommandType.SHELL:
            return self._handle_shell(tokens)
        elif cmd_type == CommandType.NATURAL:
            return self._handle_natural(tokens, command_string)
        elif cmd_type == CommandType.TASK:
            return self._handle_task(tokens)
        else:
            return CommandResult(
                success=False,
                message=f"Unknown command: {command_string}",
                status_symbol='✗',
                suggestion="Type 'help' or '--help' for available commands"
            )

    def _handle_internal(self, tokens: List[str]) -> CommandResult:
        """
        Handle internal Isaac commands.

        Placeholder - actual handlers imported from commands/ package.
        """
        command = tokens[0].lower()

        if command in ['--help', '-h', 'help']:
            # Import and delegate to help handler
            from isaac.commands.help import HelpHandler
            handler = HelpHandler(self.session)
            return handler.execute(tokens[1:])

        elif command in ['--version', '-v']:
            return CommandResult(
                success=True,
                message="Isaac v0.1.0",
                status_symbol='✓'
            )

        elif command == '--show-log':
            # Import and delegate to list handler
            from isaac.commands.list import ListHandler
            handler = ListHandler(self.session)
            return handler.execute(['history'])

        else:
            return CommandResult(
                success=False,
                message=f"Internal command not implemented: {command}",
                status_symbol='✗',
                suggestion="Type '--help' for available commands"
            )

    def _handle_shell(self, tokens: List[str]) -> CommandResult:
        """
        Handle shell command execution.

        Placeholder - will integrate with SessionManager's execution layer.
        """
        command = ' '.join(tokens)

        # For now, return placeholder result
        # TODO: Integrate with actual shell execution
        return CommandResult(
            success=False,
            message=f"Shell execution not yet implemented: {command}",
            status_symbol='✗',
            suggestion="Shell commands coming in next phase"
        )

    def _handle_natural(self, tokens: List[str], original: str) -> CommandResult:
        """
        Handle natural language command (requires AI translation).
        """
        # Check if it looks like a direct command first
        first_word = tokens[0].lower()

        if first_word == 'backup':
            from isaac.commands.backup import BackupHandler
            handler = BackupHandler(self.session)
            return handler.execute(tokens[1:])

        elif first_word == 'restore':
            from isaac.commands.restore import RestoreHandler
            handler = RestoreHandler(self.session)
            return handler.execute(tokens[1:])

        elif first_word == 'list':
            from isaac.commands.list import ListHandler
            handler = ListHandler(self.session)
            return handler.execute(tokens[1:])

        else:
            # Try AI translation (Phase 2)
            from isaac.core.ai_translator import create_translator
            translator = create_translator()

            # P0-2: Strip "isaac " prefix before translation
            stripped_input = original
            if original.lower().startswith("isaac "):
                # Remove first occurrence only, preserve rest of string
                stripped_input = original[6:].strip()  # len("isaac ") = 6

            translation = translator.translate(stripped_input)
            if translation:
                # Show translation to user
                print(f"\nAI Translation:")
                print(f"  {translation.original}")
                print(f"  → {translation.translated}")
                print(f"  Confidence: {translation.confidence:.0%}\n")

                # Handle different translation types
                translated_cmd = translation.translated
                if translated_cmd in ["chat", "query", "info"] or translated_cmd.startswith("query "):
                    # These are conversational responses, not commands to execute
                    return CommandResult(
                        success=True,
                        message=f"Understood: {translation.original}",
                        status_symbol='✓',
                        metadata=translation.metadata
                    )
                elif translation.needs_confirmation:
                    confirm = input("Execute? (y/n): ").strip().lower()
                    if confirm not in ['y', 'yes']:
                        return CommandResult(
                            success=False,
                            message="Cancelled by user",
                            status_symbol='⊘'
                        )

                # Re-execute with translated command
                return self.execute(translation.translated)
            else:
                # No translation available
                return CommandResult(
                    success=False,
                    message=f"Unable to translate: {original}",
                    status_symbol='✗',
                    suggestion="Try being more specific or use explicit commands"
                )

    def _handle_task(self, tokens: List[str]) -> CommandResult:
        """
        Handle task mode commands.

        Placeholder - will integrate with AI task planner.
        """
        task_description = tokens[0] if tokens else ""

        return CommandResult(
            success=False,
            message=f"Task mode not yet implemented: {task_description}",
            status_symbol='✗',
            suggestion="Task mode coming in next phase"
        )


def create_router(session_manager):
    """
    Factory function to create CommandRouter instance.

    Args:
        session_manager: SessionManager for logging

    Returns:
        CommandRouter instance
    """
    return CommandRouter(session_manager)