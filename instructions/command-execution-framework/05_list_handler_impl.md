# Implementation: List Handler

## Goal
Create list command handler that displays command history, available backups, and session information.

**Time Estimate:** 30 minutes

---

## Architecture Reminder

**Purpose:** Handle `isaac list <target>` commands
- List command history with status symbols
- List available backups
- Display session information
- Format output for readability

**User expects:**
```bash
isaac list history
Command History:
✓ cd /home [2025-10-19 14:30]
✗ backup invalid [2025-10-19 14:31]
✓ backup docs to /mnt [2025-10-19 14:32]
```

---

## File to Create

**Path:** `isaac/commands/list.py`

**Lines:** ~100

---

## Complete Implementation

```python
"""
List Handler - Display command history and backups.

Handles:
- Listing command history with status symbols
- Listing available backups
- Displaying session information
- Formatted output
"""

from typing import List
from isaac.core.command_router import CommandResult


class ListHandler:
    """
    Handle list command execution.
    
    Expected format:
        list history      - Show command history
        list backups      - Show available backups
        list              - Show recent history (default)
    """
    
    def __init__(self, session_manager):
        """
        Initialize handler with session manager.
        
        Args:
            session_manager: SessionManager for accessing history
        """
        self.session = session_manager
    
    def execute(self, args: List[str]) -> CommandResult:
        """
        Execute list command.
        
        Args:
            args: Command arguments (everything after 'list')
            
        Returns:
            CommandResult with formatted listing
        """
        # Determine what to list
        target = args[0].lower() if args else "history"
        
        if target == "history":
            return self._list_history()
        elif target == "backups":
            return self._list_backups()
        else:
            return CommandResult(
                success=False,
                message=f"Unknown list target: {target}",
                status_symbol='✗',
                suggestion="Usage: isaac list [history|backups]"
            )
    
    def _list_history(self) -> CommandResult:
        """
        List command history from session.
        
        Returns:
            CommandResult with formatted history
        """
        # Get command history from session
        # For now, return placeholder until SessionManager implements history storage
        
        history_lines = [
            "Command History:",
            "",
            "✓ cd /home [2025-10-19 14:30]",
            "✗ backup invalid-path [2025-10-19 14:31] - Path not found",
            "✓ backup documents to /mnt/external [2025-10-19 14:32]",
            "⊘ restore sensitive-data [2025-10-19 14:33] - Cancelled by user",
            "",
            "Tip: Commands logged to session for learning"
        ]
        
        return CommandResult(
            success=True,
            message="\n".join(history_lines),
            status_symbol='✓',
            suggestion=None
        )
    
    def _list_backups(self) -> CommandResult:
        """
        List available backups.
        
        Returns:
            CommandResult with formatted backup list
        """
        # Get backup list from session
        # For now, return placeholder until backup tracking implemented
        
        backup_lines = [
            "Available Backups:",
            "",
            "📁 documents (2025-10-19 14:00) → /mnt/external/documents",
            "📁 projects (2025-10-19 13:30) → /backup/projects",
            "📄 config.json (2025-10-19 12:00) → /backup/config.json",
            "",
            "Tip: Use 'isaac restore <name> from <backup_path>' to restore"
        ]
        
        return CommandResult(
            success=True,
            message="\n".join(backup_lines),
            status_symbol='✓',
            suggestion=None
        )
```

---

## Verification Steps

After implementation, verify:

- [ ] File exists at `isaac/commands/list.py`
- [ ] No syntax errors on import
- [ ] Can instantiate: `handler = ListHandler(session)`
- [ ] Execute list history: `handler.execute(["history"])` returns formatted history
- [ ] Execute list backups: `handler.execute(["backups"])` returns formatted backup list
- [ ] Default behavior: `handler.execute([])` lists history

## Test Manually

```python
# In Python REPL at project root
from isaac.core.session_manager import SessionManager
from isaac.commands.list import ListHandler

session = SessionManager()
handler = ListHandler(session)

# Test list history
result = handler.execute(["history"])
print(result.message)
# Expected: Formatted command history with status symbols

# Test list backups
result = handler.execute(["backups"])
print(result.message)
# Expected: Formatted backup list

# Test default (no args)
result = handler.execute([])
print(result.message)
# Expected: Command history (default behavior)
```

---

## Common Pitfalls

- ⚠️ **History storage** - This handler returns placeholder data until SessionManager implements actual history storage. Integration point marked for future work.

- ⚠️ **Backup tracking** - Similarly, backup list is placeholder. Real implementation requires backup metadata storage.

- ⚠️ **Status symbols** - Use consistent symbols: ✓ (success), ✗ (failed), ⊘ (cancelled)

- ⚠️ **Formatting** - Use newlines and indentation for readability. Include helpful tips at bottom.

---

## Integration Notes

**Future SessionManager Integration:**

When SessionManager implements history storage, update these methods:

```python
def _list_history(self) -> CommandResult:
    # Get actual history from session
    history = self.session.get_command_history()  # Add this method to SessionManager
    
    history_lines = ["Command History:", ""]
    for entry in history:
        symbol = entry['status_symbol']  # ✓/✗/⊘
        cmd = entry['command']
        timestamp = entry['timestamp']
        note = entry.get('note', '')
        
        line = f"{symbol} {cmd} [{timestamp}]"
        if note:
            line += f" - {note}"
        history_lines.append(line)
    
    return CommandResult(...)
```

**Backup Metadata Storage:**

Consider adding backup tracking to SessionManager:

```python
# In SessionManager
def track_backup(self, source, destination, timestamp):
    """Store backup metadata for listing"""
    pass

def get_backup_list(self):
    """Retrieve list of tracked backups"""
    pass
```

---

**END OF IMPLEMENTATION**
