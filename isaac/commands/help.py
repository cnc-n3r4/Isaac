"""
Help Handler - Unified help system (consolidates /man, /apropos, /whatis)

Handles:
- Brief command overview
- Detailed command help (man pages)
- Keyword search (apropos)
- One-line summaries (whatis)
- Category-specific help
- Usage examples
"""

from typing import List
from isaac.core.cli_command_router import CommandResult

# Try to import man_pages generator for advanced help
try:
    from isaac.core.man_pages import get_generator
    MAN_PAGES_AVAILABLE = True
except ImportError:
    MAN_PAGES_AVAILABLE = False
    get_generator = None


class HelpHandler:
    """
    Handle help command execution with man/apropos/whatis functionality.

    Expected format:
        help                  - Show overview
        help <command>        - Show detailed help for command (man)
        help --search <word>  - Search commands by keyword (apropos)
        help --whatis <cmd>   - Show one-line summary (whatis)
        help <category>       - Show category-specific help
    """

    def __init__(self, session_manager):
        """
        Initialize handler with session manager.

        Args:
            session_manager: SessionManager (not used, kept for consistency)
        """
        self.session = session_manager
        self.man_generator = get_generator() if MAN_PAGES_AVAILABLE else None

    def execute(self, args: List[str]) -> CommandResult:
        """
        Execute help command with man/apropos/whatis support.

        Args:
            args: Command arguments

        Returns:
            CommandResult with formatted help text
        """
        # Handle special flags
        if args and args[0] == '--search' and len(args) > 1:
            # Apropos mode: search by keyword
            return self._search_commands(args[1])
        elif args and args[0] == '--whatis' and len(args) > 1:
            # Whatis mode: one-line summary
            return self._show_whatis(args[1])
        elif not args or args[0] == "overview":
            # Overview mode
            return self._show_overview()
        elif args[0] in ["backup", "restore", "list"]:
            # Legacy category help
            return self._show_category_help(args[0])
        else:
            # Man page mode: detailed command help
            return self._show_man_page(args[0])

    def _show_overview(self) -> CommandResult:
        """
        Show brief command overview with consolidated commands.

        Returns:
            CommandResult with overview text
        """
        help_text = """
Isaac Command Reference - Phase 9 (Consolidated Commands)

════════════════════════════════════════════════════════════
6 CORE COMMANDS (Unified Interface):
════════════════════════════════════════════════════════════

  /help [command]         Unified help (man/apropos/whatis)
    /help --search <word>   Search commands by keyword
    /help --whatis <cmd>    One-line command summary
    /help backup            Detailed help for command

  /file <operation>       All file operations
    /file read <path>       Read files
    /file write <path>      Write/create files
    /file edit <path>       Edit with string replacement
    /file append <path>     Append to files
    /file <path>            Smart mode (auto-detect)

  /search <query>         Universal search
    /search "*.py"          Find Python files (glob)
    /search "TODO"          Search for TODO (grep)
    /search "TODO" in "*.py" Search TODO in Python files

  /task <operation>       Background task management
    /task list              List all tasks
    /task show <id>         Show task details
    /task cancel <id>       Cancel running task

  /status [mode]          System status dashboard
    /status                 Quick status
    /status -v              Detailed status
    /status --session       Session info

  /config <setting>       Configuration
    /config ai              AI provider settings
    /config show            Show all settings

════════════════════════════════════════════════════════════
SHELL COMMANDS (Just work - no prefix needed):
════════════════════════════════════════════════════════════
  cd, ls, dir, pwd, cat, echo, cp, mv, rm, mkdir, grep, find

════════════════════════════════════════════════════════════
BACKUP & RESTORE (Legacy):
════════════════════════════════════════════════════════════
  backup <source> to <dest>
  restore <n> from <source>
  list backups

════════════════════════════════════════════════════════════
NATURAL LANGUAGE (Primary Interface):
════════════════════════════════════════════════════════════
  isaac fix the authentication bug
  isaac find all TODOs in Python files
  isaac explain how the login system works

════════════════════════════════════════════════════════════
ADVANCED HELP:
════════════════════════════════════════════════════════════
  /help <command>         Detailed command help (man page)
  /help --search <word>   Search by keyword (apropos)
  /help --whatis <cmd>    One-line summary
  /help backup            Legacy category help

Note: Legacy commands (/read, /write, /grep, /glob, /man, /apropos,
/whatis) still work but are deprecated in favor of unified commands.
        """.strip()

        return CommandResult(
            success=True,
            message=help_text,
            status_symbol='✓',
            suggestion=None
        )

    def _show_backup_help(self) -> CommandResult:
        """
        Show detailed backup command help.

        Returns:
            CommandResult with backup-specific help
        """
        help_text = """
Backup Command - Detailed Help

USAGE:
  isaac backup <source> to <destination>
  isaac backup <source>  (prompts for destination)

EXAMPLES:
  # Backup folder to external drive
  isaac backup my-documents to /mnt/external

  # Backup with path containing spaces (use quotes)
  isaac backup "My Documents" to /backup

  # Backup to specific location
  isaac backup ~/projects to /backup/projects-$(date +%Y%m%d)

BEHAVIOR:
  1. Resolves source path (supports ~ and relative paths)
  2. Validates destination is writable
  3. Shows backup size and confirms operation
  4. Copies source to destination (preserves timestamps)
  5. Logs result to command history

STATUS SYMBOLS:
  ✓ Backup successful
  ✗ Backup failed (check permissions and disk space)
  ⊘ Backup cancelled by user

NOTES:
  - Destination must be explicitly specified (no magic backup locations)
  - For folders: Creates folder at destination
  - For files: Copies file to destination
  - Existing files at destination will be overwritten after confirmation
        """.strip()

        return CommandResult(
            success=True,
            message=help_text,
            status_symbol='✓',
            suggestion=None
        )

    def _show_restore_help(self) -> CommandResult:
        """
        Show detailed restore command help.

        Returns:
            CommandResult with restore-specific help
        """
        help_text = """
Restore Command - Detailed Help

USAGE:
  isaac restore <n> from <backup_source>
  isaac restore <n>  (prompts for backup source)

EXAMPLES:
  # Restore from external drive
  isaac restore my-documents from /mnt/external/my-documents

  # Restore to current directory
  isaac restore project from /backup/project

  # With spaces in name (use quotes)
  isaac restore "My Documents" from "/backup/My Documents"

BEHAVIOR:
  1. Validates backup source exists
  2. Determines restore destination (current directory by default)
  3. Warns if destination exists (will overwrite!)
  4. Shows restore size and confirms operation
  5. Copies backup to destination
  6. Logs result to command history

STATUS SYMBOLS:
  ✓ Restore successful
  ✗ Restore failed (check source path and permissions)
  ⊘ Restore cancelled by user

NOTES:
  - Backup source must be explicitly specified
  - Restores to current directory/<n>
  - Existing files at destination WILL BE OVERWRITTEN
  - Always confirms before overwriting
        """.strip()

        return CommandResult(
            success=True,
            message=help_text,
            status_symbol='✓',
            suggestion=None
        )

    def _show_list_help(self) -> CommandResult:
        """
        Show detailed list command help.

        Returns:
            CommandResult with list-specific help
        """
        help_text = """
List Command - Detailed Help

USAGE:
  isaac list [history|backups]
  isaac list  (defaults to history)

EXAMPLES:
  # Show command history
  isaac list history

  # Show available backups
  isaac list backups

COMMAND HISTORY OUTPUT:
  Shows all commands with:
  - Status symbol (✓/✗/⊘)
  - Command text
  - Timestamp
  - Error note (if failed)

BACKUP LIST OUTPUT:
  Shows tracked backups with:
  - Backup name
  - Timestamp
  - Destination path

NOTES:
  - All commands are logged (success/fail/cancelled)
  - History helps learning system improve suggestions
  - Use --show-log for quick history view
        """.strip()

        return CommandResult(
            success=True,
            message=help_text,
            status_symbol='✓',
            suggestion=None
        )

    def _show_meta_commands_help(self) -> CommandResult:
        """
        Show help for meta-commands.

        Returns:
            CommandResult with meta-command help
        """
        help_text = """
Available Commands:
  /help              - Show this help
  /status            - Quick system status
  /status -v         - Detailed status
  /config            - Configuration overview
  /config status     - System status check
  /config ai         - AI provider details
  /config cloud      - Cloud sync status
  /config plugins    - List plugins
  /config set <k> <v> - Change setting
  /clear             - Clear screen
  /exit, /quit       - Exit ISAAC

Natural Language:
  isaac <query>      - AI query or command translation
""".strip()

        return CommandResult(
            success=True,
            message=help_text,
            status_symbol='✓',
            suggestion=None
        )

    def _show_category_help(self, category: str) -> CommandResult:
        """
        Show legacy category-specific help.

        Args:
            category: Category name (backup, restore, list)

        Returns:
            CommandResult with category help
        """
        if category == "backup":
            return self._show_backup_help()
        elif category == "restore":
            return self._show_restore_help()
        elif category == "list":
            return self._show_list_help()
        else:
            return CommandResult(
                success=False,
                message=f"Unknown category: {category}",
                status_symbol='✗',
                suggestion="Try: help [backup|restore|list]"
            )

    def _show_man_page(self, command: str) -> CommandResult:
        """
        Show detailed man page for a command (man functionality).

        Args:
            command: Command name (with or without /)

        Returns:
            CommandResult with man page
        """
        if not MAN_PAGES_AVAILABLE or not self.man_generator:
            return CommandResult(
                success=False,
                message="Man pages not available. Using basic help.",
                status_symbol='⚠',
                suggestion="Install man page system for detailed help"
            )

        # Normalize command name
        if not command.startswith('/'):
            command = '/' + command

        try:
            man_page = self.man_generator.generate(command)
            if man_page:
                return CommandResult(
                    success=True,
                    message=man_page,
                    status_symbol='✓',
                    suggestion=None
                )
            else:
                return CommandResult(
                    success=False,
                    message=f"No manual entry for {command}",
                    status_symbol='✗',
                    suggestion="Try: /help --search <keyword> to find commands"
                )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Error retrieving man page: {e}",
                status_symbol='✗',
                suggestion="Use /help for basic help"
            )

    def _search_commands(self, keyword: str) -> CommandResult:
        """
        Search commands by keyword (apropos functionality).

        Args:
            keyword: Keyword to search for

        Returns:
            CommandResult with search results
        """
        if not MAN_PAGES_AVAILABLE or not self.man_generator:
            return CommandResult(
                success=False,
                message="Command search not available.",
                status_symbol='⚠',
                suggestion="Use /help for basic command list"
            )

        try:
            results = self.man_generator.search(keyword)

            if not results:
                return CommandResult(
                    success=False,
                    message=f"No commands found matching '{keyword}'",
                    status_symbol='✗',
                    suggestion="Try a different keyword or /help for overview"
                )

            # Format results
            output = [f"Commands matching '{keyword}':", "=" * 70, ""]
            for result in results:
                trigger = result['trigger']
                version = result.get('version', '1.0.0')
                summary = result['summary']

                # Truncate long summaries
                if len(summary) > 50:
                    summary = summary[:47] + "..."

                output.append(f"{trigger:<20} ({version})  - {summary}")

            output.append("")
            output.append(f"Found {len(results)} match(es)")
            output.append(f"Use '/help <command>' for detailed information")

            return CommandResult(
                success=True,
                message="\n".join(output),
                status_symbol='✓',
                suggestion=None
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Error searching commands: {e}",
                status_symbol='✗',
                suggestion="Use /help for basic help"
            )

    def _show_whatis(self, command: str) -> CommandResult:
        """
        Show one-line summary for command (whatis functionality).

        Args:
            command: Command name (with or without /)

        Returns:
            CommandResult with one-line summary
        """
        if not MAN_PAGES_AVAILABLE or not self.man_generator:
            return CommandResult(
                success=False,
                message="Whatis not available.",
                status_symbol='⚠',
                suggestion="Use /help for basic command list"
            )

        # Normalize command name
        if not command.startswith('/'):
            command = '/' + command

        try:
            summary = self.man_generator.whatis(command)

            if summary:
                return CommandResult(
                    success=True,
                    message=summary,
                    status_symbol='✓',
                    suggestion=None
                )
            else:
                return CommandResult(
                    success=False,
                    message=f"{command}: nothing appropriate",
                    status_symbol='✗',
                    suggestion="Use /help --search <keyword> to find commands"
                )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Error: {e}",
                status_symbol='✗',
                suggestion="Use /help for basic help"
            )