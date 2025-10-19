# Implementation: Core Logic (Part 2 - SessionManager)

## Goal
Create session_manager.py for loading/saving/syncing session data.

**Time Estimate:** 15 minutes

**Dependencies:**
- 05_impl_models.md (Preferences, CommandHistory models)
- 04_impl_shell_adapters.md (shell adapter for machine detection)

---

## File: session_manager.py

**Path:** `isaac/core/session_manager.py`

**Purpose:** Manage session data (preferences, command history) with local storage and cloud sync prep.

**Complete Implementation:**

```python
"""
Session manager for Isaac configuration and history.
Handles loading/saving session data (local for MVP, cloud in Phase 2).
"""

import json
import socket
from pathlib import Path
from datetime import datetime
from isaac.models.preferences import Preferences
from isaac.models.command_history import CommandHistory


class SessionManager:
    """Manage Isaac session data and sync."""
    
    def __init__(self, config, shell_adapter):
        """
        Initialize session manager.
        
        Args:
            config: Config dict from config_loader
            shell_adapter: Shell adapter instance
        """
        self.config = config
        self.shell = shell_adapter
        
        # Session data (6 files planned, 2 for MVP)
        self.preferences = Preferences()
        self.command_history = CommandHistory()
        
        # Local storage paths
        self.isaac_dir = Path.home() / '.isaac'
        self.isaac_dir.mkdir(parents=True, exist_ok=True)
        
        self.prefs_file = self.isaac_dir / 'preferences.json'
        self.history_file = self.isaac_dir / 'command_history.json'
        
        # Machine ID (auto-detect hostname)
        self.machine_id = self._get_machine_id()
        
        # Cloud sync client (Phase 2)
        self.cloud = None  # Will be CloudClient instance in Phase 2
    
    def load_from_local(self):
        """
        Load session data from local ~/.isaac/ directory.
        For MVP, this is the primary data source (no cloud yet).
        """
        # Load preferences
        if self.prefs_file.exists():
            with open(self.prefs_file, 'r') as f:
                prefs_data = json.load(f)
                self.preferences = Preferences.from_dict(prefs_data)
        else:
            # Create default preferences
            self.preferences = Preferences(
                machine_id=self.machine_id,
                auto_run_tier2=False,
                tier_overrides={},
                api_url=self.config.get('api_url', ''),
                api_key=self.config.get('api_key', '')
            )
            self._save_preferences()
        
        # Load command history
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                history_data = json.load(f)
                self.command_history = CommandHistory.from_dict(history_data)
        else:
            self.command_history = CommandHistory()
            self._save_history()
    
    def add_command(self, command: str, result) -> None:
        """
        Add command to history and sync.
        
        Args:
            command: Command string
            result: CommandResult from shell execution
        """
        entry = {
            'command': command,
            'machine': self.machine_id,
            'timestamp': datetime.now().isoformat(),
            'shell': self.shell.name,
            'exit_code': result.exit_code,
            'output': result.output[:500]  # Truncate long output
        }
        
        self.command_history.add(entry)
        self._save_history()
        
        # Cloud sync in Phase 2
        # if self.cloud:
        #     self.cloud.save_session_file('command_history.json', self.command_history.to_dict())
    
    def get_command_count(self, machine_id: str = None) -> int:
        """
        Get command count, optionally filtered by machine.
        
        Args:
            machine_id: Optional machine filter
            
        Returns:
            int: Number of commands
        """
        if machine_id:
            return len(self.command_history.get_by_machine(machine_id))
        return len(self.command_history.entries)
    
    def _save_preferences(self):
        """Save preferences to local file."""
        with open(self.prefs_file, 'w') as f:
            json.dump(self.preferences.to_dict(), f, indent=2)
    
    def _save_history(self):
        """Save command history to local file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.command_history.to_dict(), f, indent=2)
    
    def _get_machine_id(self) -> str:
        """
        Get machine identifier (hostname).
        
        Returns:
            str: Machine hostname
        """
        try:
            return socket.gethostname()
        except:
            return 'UNKNOWN-MACHINE'
```

---

## Verification Steps

### 1. Test SessionManager Initialization
```python
from isaac.core.session_manager import SessionManager
from isaac.adapters.shell_detector import detect_shell

# Create minimal config
config = {
    'api_url': '',
    'api_key': ''
}

# Initialize session manager
shell = detect_shell()
session = SessionManager(config, shell)

print(f"Machine ID: {session.machine_id}")
print(f"Isaac dir: {session.isaac_dir}")
print(f"Preferences file: {session.prefs_file}")
print(f"History file: {session.history_file}")

# Expected:
# Machine ID: YOUR-HOSTNAME
# Isaac dir: /home/user/.isaac (or C:\Users\user\.isaac)
# Preferences file: /home/user/.isaac/preferences.json
# History file: /home/user/.isaac/command_history.json
```

### 2. Test Load From Local
```python
from isaac.core.session_manager import SessionManager
from isaac.adapters.shell_detector import detect_shell

config = {}
shell = detect_shell()
session = SessionManager(config, shell)

# Load (will create defaults if files don't exist)
session.load_from_local()

print(f"Preferences machine_id: {session.preferences.machine_id}")
print(f"Command history entries: {len(session.command_history.entries)}")

# Check files created
assert session.prefs_file.exists()
assert session.history_file.exists()
print("✅ Files created in ~/.isaac/")
```

### 3. Test Add Command
```python
from isaac.core.session_manager import SessionManager
from isaac.adapters.shell_detector import detect_shell
from isaac.adapters.base_adapter import CommandResult

config = {}
shell = detect_shell()
session = SessionManager(config, shell)
session.load_from_local()

# Add a command
result = CommandResult(success=True, output='test output', exit_code=0)
session.add_command('ls -la', result)

print(f"Commands after add: {len(session.command_history.entries)}")
assert len(session.command_history.entries) > 0
print("✅ Command added")

# Check file updated
import json
with open(session.history_file, 'r') as f:
    data = json.load(f)
    print(f"Entries in file: {len(data['entries'])}")
```

### 4. Test Command Count
```python
from isaac.core.session_manager import SessionManager
from isaac.adapters.shell_detector import detect_shell
from isaac.adapters.base_adapter import CommandResult

config = {}
shell = detect_shell()
session = SessionManager(config, shell)
session.load_from_local()

# Add multiple commands
for i in range(3):
    result = CommandResult(True, f'output {i}', 0)
    session.add_command(f'cmd_{i}', result)

# Test counts
total = session.get_command_count()
this_machine = session.get_command_count(session.machine_id)

print(f"Total commands: {total}")
print(f"This machine: {this_machine}")
assert total == this_machine  # All from this machine for MVP
print("✅ Command counting works")
```

### 5. Test Persistence (Reload)
```python
from isaac.core.session_manager import SessionManager
from isaac.adapters.shell_detector import detect_shell

config = {}
shell = detect_shell()

# First session - add command
session1 = SessionManager(config, shell)
session1.load_from_local()
from isaac.adapters.base_adapter import CommandResult
result = CommandResult(True, 'test', 0)
session1.add_command('test_cmd', result)
count1 = session1.get_command_count()

# Second session - reload
session2 = SessionManager(config, shell)
session2.load_from_local()
count2 = session2.get_command_count()

print(f"Session 1 count: {count1}")
print(f"Session 2 count: {count2}")
assert count2 >= count1  # Should persist
print("✅ Data persists across sessions")
```

---

## Common Pitfalls

⚠️ **Permission denied creating ~/.isaac/**
- **Symptom:** `PermissionError` on directory creation
- **Fix:** Check user has write permissions to home directory

⚠️ **JSON encoding errors**
- **Symptom:** `TypeError: Object of type X is not JSON serializable`
- **Fix:** Ensure output truncation ([:500]) to avoid binary data

⚠️ **Machine ID contains invalid characters**
- **Symptom:** Hostname has special chars causing issues
- **Fix:** Sanitize hostname with `re.sub(r'[^a-zA-Z0-9-]', '_', hostname)`

⚠️ **History file grows too large**
- **Symptom:** Slow load times
- **Fix:** Implement rotation (keep last 1000 commands, archive older)

---

## Success Signals

✅ SessionManager initializes without errors  
✅ ~/.isaac/ directory created  
✅ preferences.json created with defaults  
✅ command_history.json created  
✅ load_from_local() works  
✅ add_command() appends to history  
✅ Files persist across sessions  
✅ Machine ID detected (hostname)  
✅ Command count accurate  
✅ Ready for next step (Terminal UI)

---

**Next Step:** 07_impl_terminal_ui.md (Splash, Header, Prompt, Terminal Control)

---

**END OF CORE LOGIC (COMPLETE)**
