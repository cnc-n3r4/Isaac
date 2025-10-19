# Implementation: Data Models

## Goal
Create data models for Preferences and CommandHistory using dataclasses.

**Time Estimate:** 20 minutes

**Dependencies:** 02_impl_bootstrap.md (directory structure)

---

## File 1: preferences.py

**Path:** `isaac/models/preferences.py`

**Purpose:** User preferences and settings (tier overrides, API config, behavior flags).

**Complete Implementation:**

```python
"""
Preferences data model.
Stores user configuration, tier overrides, and API credentials.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict
import json


@dataclass
class Preferences:
    """User preferences for Isaac configuration."""
    
    machine_id: str = ''
    auto_run_tier2: bool = False
    tier_overrides: Dict[str, int] = field(default_factory=dict)
    api_url: str = ''
    api_key: str = ''
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Preferences':
        """
        Create Preferences from dictionary.
        
        Args:
            data: Dictionary with preference keys
            
        Returns:
            Preferences instance
        """
        return cls(
            machine_id=data.get('machine_id', ''),
            auto_run_tier2=data.get('auto_run_tier2', False),
            tier_overrides=data.get('tier_overrides', {}),
            api_url=data.get('api_url', ''),
            api_key=data.get('api_key', '')
        )
    
    def to_dict(self) -> dict:
        """
        Convert Preferences to dictionary.
        
        Returns:
            Dictionary representation
        """
        return asdict(self)
    
    def to_json(self) -> str:
        """
        Convert Preferences to JSON string.
        
        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Preferences':
        """
        Create Preferences from JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            Preferences instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
```

---

## File 2: command_history.py

**Path:** `isaac/models/command_history.py`

**Purpose:** Command history tracking with machine-aware entries.

**Complete Implementation:**

```python
"""
Command history data model.
Stores command logs with machine tagging for multi-machine sync.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
import json
from datetime import datetime


@dataclass
class CommandEntry:
    """Single command history entry."""
    
    command: str
    machine: str
    timestamp: str
    shell: str
    exit_code: int
    output: str = ''
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CommandEntry':
        """Create CommandEntry from dictionary."""
        return cls(
            command=data.get('command', ''),
            machine=data.get('machine', ''),
            timestamp=data.get('timestamp', ''),
            shell=data.get('shell', ''),
            exit_code=data.get('exit_code', 0),
            output=data.get('output', '')
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CommandHistory:
    """Collection of command history entries."""
    
    entries: List[CommandEntry] = field(default_factory=list)
    
    def add(self, entry: Dict) -> None:
        """
        Add command entry to history.
        
        Args:
            entry: Dictionary with command details
        """
        cmd_entry = CommandEntry.from_dict(entry)
        self.entries.append(cmd_entry)
    
    def get_by_machine(self, machine_id: str) -> List[CommandEntry]:
        """
        Filter entries by machine.
        
        Args:
            machine_id: Machine identifier
            
        Returns:
            List of entries from specified machine
        """
        return [e for e in self.entries if e.machine == machine_id]
    
    def get_last_n(self, n: int, machine_id: Optional[str] = None) -> List[CommandEntry]:
        """
        Get last N entries, optionally filtered by machine.
        
        Args:
            n: Number of entries to return
            machine_id: Optional machine filter
            
        Returns:
            Last N entries (or fewer if history is shorter)
        """
        if machine_id:
            entries = self.get_by_machine(machine_id)
        else:
            entries = self.entries
        
        return entries[-n:]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CommandHistory':
        """
        Create CommandHistory from dictionary.
        
        Args:
            data: Dictionary with 'entries' key
            
        Returns:
            CommandHistory instance
        """
        entries_data = data.get('entries', [])
        entries = [CommandEntry.from_dict(e) for e in entries_data]
        return cls(entries=entries)
    
    def to_dict(self) -> dict:
        """
        Convert CommandHistory to dictionary.
        
        Returns:
            Dictionary with 'entries' list
        """
        return {
            'entries': [e.to_dict() for e in self.entries]
        }
    
    def to_json(self) -> str:
        """
        Convert to JSON string.
        
        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CommandHistory':
        """
        Create from JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            CommandHistory instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
```

---

## Verification Steps

### 1. Test Preferences Model
```python
from isaac.models.preferences import Preferences

# Create default preferences
prefs = Preferences()
print(f"Default machine_id: '{prefs.machine_id}'")
print(f"Default auto_run_tier2: {prefs.auto_run_tier2}")

# Create from dict
data = {
    'machine_id': 'TEST-MACHINE',
    'auto_run_tier2': True,
    'tier_overrides': {'find': 1, 'grep': 1},
    'api_url': 'https://example.com/api',
    'api_key': 'test_key'
}
prefs = Preferences.from_dict(data)
print(f"Loaded machine_id: {prefs.machine_id}")
print(f"Tier overrides: {prefs.tier_overrides}")

# Convert to dict
prefs_dict = prefs.to_dict()
print(f"Dict keys: {list(prefs_dict.keys())}")

# JSON serialization
json_str = prefs.to_json()
print(f"JSON length: {len(json_str)} chars")
prefs_loaded = Preferences.from_json(json_str)
print(f"Roundtrip machine_id: {prefs_loaded.machine_id}")
```

**Expected output:**
```
Default machine_id: ''
Default auto_run_tier2: False
Loaded machine_id: TEST-MACHINE
Tier overrides: {'find': 1, 'grep': 1}
Dict keys: ['machine_id', 'auto_run_tier2', 'tier_overrides', 'api_url', 'api_key']
JSON length: ~200 chars
Roundtrip machine_id: TEST-MACHINE
```

### 2. Test CommandHistory Model
```python
from isaac.models.command_history import CommandHistory, CommandEntry
from datetime import datetime

# Create empty history
history = CommandHistory()
print(f"Empty history entries: {len(history.entries)}")

# Add command
entry = {
    'command': 'ls -la',
    'machine': 'DESKTOP-WIN11',
    'timestamp': datetime.now().isoformat(),
    'shell': 'PowerShell',
    'exit_code': 0,
    'output': '[directory listing]'
}
history.add(entry)
print(f"After add: {len(history.entries)} entries")

# Add more entries
history.add({
    'command': 'git status',
    'machine': 'DESKTOP-WIN11',
    'timestamp': datetime.now().isoformat(),
    'shell': 'PowerShell',
    'exit_code': 0
})
history.add({
    'command': 'pwd',
    'machine': 'PARROT-VM',
    'timestamp': datetime.now().isoformat(),
    'shell': 'bash',
    'exit_code': 0
})

# Filter by machine
win_cmds = history.get_by_machine('DESKTOP-WIN11')
print(f"Windows commands: {len(win_cmds)}")

linux_cmds = history.get_by_machine('PARROT-VM')
print(f"Linux commands: {len(linux_cmds)}")

# Get last N
last_2 = history.get_last_n(2)
print(f"Last 2 commands: {[e.command for e in last_2]}")

# JSON roundtrip
json_str = history.to_json()
history_loaded = CommandHistory.from_json(json_str)
print(f"Roundtrip entries: {len(history_loaded.entries)}")
```

**Expected output:**
```
Empty history entries: 0
After add: 1 entries
Windows commands: 2
Linux commands: 1
Last 2 commands: ['git status', 'pwd']
Roundtrip entries: 3
```

### 3. Test Machine Filtering
```python
from isaac.models.command_history import CommandHistory
from datetime import datetime

history = CommandHistory()

# Add 5 commands from two machines
for i in range(3):
    history.add({
        'command': f'cmd_{i}',
        'machine': 'WIN-DESKTOP',
        'timestamp': datetime.now().isoformat(),
        'shell': 'PowerShell',
        'exit_code': 0
    })

for i in range(2):
    history.add({
        'command': f'cmd_{i}',
        'machine': 'LINUX-VM',
        'timestamp': datetime.now().isoformat(),
        'shell': 'bash',
        'exit_code': 0
    })

# Test filtering
all_entries = history.entries
print(f"Total entries: {len(all_entries)}")

win_entries = history.get_by_machine('WIN-DESKTOP')
print(f"Windows entries: {len(win_entries)}")

linux_entries = history.get_by_machine('LINUX-VM')
print(f"Linux entries: {len(linux_entries)}")

# Test last N with filter
last_2_win = history.get_last_n(2, 'WIN-DESKTOP')
print(f"Last 2 from Windows: {len(last_2_win)}")
```

**Expected output:**
```
Total entries: 5
Windows entries: 3
Linux entries: 2
Last 2 from Windows: 2
```

---

## Common Pitfalls

⚠️ **Missing default_factory**
- **Symptom:** `TypeError: unhashable type: 'dict'`
- **Fix:** Use `field(default_factory=dict)` for mutable defaults

⚠️ **JSON Encoding Errors**
- **Symptom:** `TypeError: Object of type X is not JSON serializable`
- **Fix:** Ensure all fields are JSON-serializable types

⚠️ **from_dict Missing Keys**
- **Symptom:** `KeyError` when loading incomplete data
- **Fix:** Use `data.get('key', default)` instead of `data['key']`

⚠️ **Timestamp Format Issues**
- **Symptom:** Timestamps don't parse correctly
- **Fix:** Use `datetime.now().isoformat()` for consistent ISO 8601 format

---

## Success Signals

✅ Preferences dataclass created  
✅ from_dict() / to_dict() work  
✅ JSON serialization roundtrips correctly  
✅ CommandHistory dataclass created  
✅ CommandEntry nested dataclass works  
✅ add() appends entries  
✅ get_by_machine() filters correctly  
✅ get_last_n() returns correct count  
✅ JSON serialization preserves all data  
✅ Ready for next step (core logic)

---

**Next Step:** 06_impl_core_logic.md (TierValidator, CommandRouter, SessionManager)

---

**END OF DATA MODELS IMPLEMENTATION**
