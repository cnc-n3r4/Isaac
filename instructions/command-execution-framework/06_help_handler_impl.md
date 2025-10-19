# Implementation: Help Handler

## Goal
Create help command handler that displays scannable command reference with category drill-down support.

**Time Estimate:** 30 minutes

---

## Architecture Reminder

**Purpose:** Handle `isaac --help` and `isaac help <category>` commands
- Display brief command overview (≤30 lines)
- Support category drill-down
- Show examples for common tasks
- Keep output scannable

**User expects:**
```bash
isaac --help
Isaac Command Reference:

SHELL COMMANDS (Just work - no prefix):
  cd, ls, cp, mv, rm, etc.

ISAAC INTERNAL:
  --help             Show this help
  --version          Show version
  list history       Show command history
  list backups       Show available backups

NATURAL LANGUAGE (Prefix with "isaac"):
  isaac backup my-folder to /dest
  isaac restore my-folder from /backup

For detailed help: isaac help <category>
```

---

## File to Create

**Path:** `isaac/commands/help.py`

**Lines:** ~120

---

## Complete Implementation

```python
"""
Help Handler - Display command reference and usage examples.

Handles:
- Brief command overview
- Category-specific help
- Usage examples
- Scannable format (≤30 lines for overview)
"""

from typing import List
from isaac.core.command_router import CommandResult


class HelpHandler:
    """
    Handle help command execution.
    
    Expected format:
        help              - Show overview
        help backup       - Show backup-specific help
        help restore      - Show restore-specific help
    """
    
    def __init__(self, session_manager):
        """
        Initialize handler with session manager.
        
        Args:
            session_manager: SessionManager (not used, kept for consistency)
        """
        self.session = session_manager
    
    def execute(self, args: List[str]) -> CommandResult:
        """
        Execute help command.
        
        Args:
            args: Command arguments (category name or empty)
            
        Returns:
            CommandResult with formatted help text
        """
        # Determine help category
        category = args[0].lower() if args else "overview"
        
        if category == "overview":
            return self._show_overview()
        elif category == "backup":
            return self._show_backup_help()
        elif category == "restore":
            return self._show_restore_help()
        elif category == "list":
            return self._show_list_help()
        else:
            return CommandResult(
                success=False,
                message=f"Unknown help category: {category}",
                status_symbol='✗',
                suggestion="Try: isaac help [backup|restore|list]"
            )
    
    def _show_overview(self) -> CommandResult:
        """
        Show brief command overview.
        
        Returns:
            CommandResult with overview text (≤30 lines)
        """
        help_text = """
Isaac Command Reference

SHELL COMMANDS (Just work - no prefix needed):
  cd, ls, dir, pwd, cat, echo
  cp, mv, rm, mkdir, rmdir
  grep, find, chmod, chown
  
  Example: isaac cd /home/user

ISAAC INTERNAL COMMANDS:
  --help, -h         Show this help
  --version, -v      Show version info
  --show-log         Display command history
  list history       Show command history with status
  list backups       Show available backups

BACKUP & RESTORE:
  backup <source> to <dest>
    Example: isaac backup my-folder to /mnt/external
    
  restore <n> from <source>
    Example: isaac restore my-folder from /mnt/external

INTERACTIVE MODE:
  isaac              Enter interactive REPL
    isaac> backup documents
    isaac> list history
    isaac> exit

DETAILED HELP:
  isaac help backup   - Backup command details
  isaac help restore  - Restore command details
  isaac help list     - List command details

Visit: https://isaac-docs.example.com (placeholder)
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
```

---

## Verification Steps

After implementation, verify:

- [ ] File exists at `isaac/commands/help.py`
- [ ] No syntax errors on import
- [ ] Can instantiate: `handler = HelpHandler(session)`
- [ ] Show overview: `handler.execute([])` returns brief help (≤30 lines)
- [ ] Show category help: `handler.execute(["backup"])` returns detailed backup help
- [ ] Invalid category returns helpful error

## Test Manually

```python
# In Python REPL at project root
from isaac.core.session_manager import SessionManager
from isaac.commands.help import HelpHandler

session = SessionManager()
handler = HelpHandler(session)

# Test overview
result = handler.execute([])
print(result.message)
# Expected: Brief command overview, scannable format

# Test category help
result = handler.execute(["backup"])
print(result.message)
# Expected: Detailed backup command help with examples

# Test invalid category
result = handler.execute(["invalid"])
print(result)
# Expected: Error with suggestion
```

---

## Common Pitfalls

- ⚠️ **Line count** - Keep overview ≤30 lines for scannability. Use `.strip()` to remove leading/trailing whitespace.

- ⚠️ **Formatting** - Use consistent indentation and section headers for readability.

- ⚠️ **Examples** - Include real, working examples. Avoid placeholder/fake examples.

- ⚠️ **Drill-down** - Category help can be longer and more detailed than overview.

- ⚠️ **Status symbols** - Consistently use ✓/✗/⊘ in documentation.

---

**END OF IMPLEMENTATION**
