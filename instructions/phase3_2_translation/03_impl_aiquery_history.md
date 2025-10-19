# Implementation: AI Query History Model

## Goal
Create AIQueryHistory class to track AI translations separately from command history.

**Time Estimate:** 20 minutes

---

## File to Create

**Path:** `isaac/models/aiquery_history.py`

**Lines:** ~80

---

## Complete Implementation

```python
"""
AIQueryHistory - Track AI query translations separately from command history
Privacy-focused: Stored in separate file, marked as PRIVATE
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class AIQueryHistory:
    """Track AI natural language queries and their translations."""
    
    def __init__(self):
        """Initialize empty AI query history."""
        self.queries: List[Dict] = []
    
    def add(self, query: str, command: str, shell: str, 
            executed: bool = False, result: str = "pending") -> None:
        """
        Add AI query to history.
        
        Args:
            query: Original natural language query
            command: Translated shell command
            shell: Shell name (bash, PowerShell, etc.)
            executed: Whether command was executed
            result: Execution result (success, failed, aborted)
        """
        import platform
        
        entry = {
            'query': query,
            'command': command,
            'timestamp': datetime.now().isoformat(),
            'machine': platform.node(),
            'shell': shell,
            'executed': executed,
            'result': result
        }
        
        self.queries.append(entry)
    
    def get_recent(self, count: int = 10) -> List[Dict]:
        """
        Get most recent AI queries.
        
        Args:
            count: Number of recent queries to return
            
        Returns:
            List of query dicts (most recent first)
        """
        return self.queries[-count:][::-1]  # Last N, reversed
    
    def search(self, keyword: str) -> List[Dict]:
        """
        Search AI queries by keyword.
        
        Args:
            keyword: Search term (case-insensitive)
            
        Returns:
            List of matching query dicts
        """
        keyword_lower = keyword.lower()
        return [
            q for q in self.queries
            if keyword_lower in q['query'].lower() or
               keyword_lower in q['command'].lower()
        ]
    
    def get_by_machine(self, machine: str) -> List[Dict]:
        """
        Get queries from specific machine.
        
        Args:
            machine: Machine name/hostname
            
        Returns:
            List of query dicts from that machine
        """
        return [q for q in self.queries if q['machine'] == machine]
    
    def to_dict(self) -> Dict:
        """
        Serialize to dictionary for storage.
        
        Returns:
            dict: {'queries': [...], 'metadata': {...}}
        """
        return {
            'queries': self.queries,
            'metadata': {
                'total_count': len(self.queries),
                'privacy': 'PRIVATE',  # Mark as private data
                'description': 'AI natural language query history'
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AIQueryHistory':
        """
        Deserialize from dictionary.
        
        Args:
            data: Dictionary from to_dict()
            
        Returns:
            AIQueryHistory instance
        """
        history = cls()
        history.queries = data.get('queries', [])
        return history
    
    def save(self, filepath: Path) -> None:
        """
        Save to JSON file.
        
        Args:
            filepath: Path to save file
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: Path) -> 'AIQueryHistory':
        """
        Load from JSON file.
        
        Args:
            filepath: Path to load from
            
        Returns:
            AIQueryHistory instance (empty if file doesn't exist)
        """
        if not filepath.exists():
            return cls()
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return cls()  # Return empty on error
    
    def __len__(self) -> int:
        """Return number of queries in history."""
        return len(self.queries)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<AIQueryHistory: {len(self.queries)} queries>"
```

---

## Verification Steps

After creating `isaac/models/aiquery_history.py`, verify:

- [ ] File has ~150 lines
- [ ] AIQueryHistory class complete
- [ ] All methods implemented (add, get_recent, search, to_dict, from_dict, save, load)
- [ ] Privacy metadata included ('PRIVATE' marker)
- [ ] No syntax errors: `python -m py_compile isaac/models/aiquery_history.py`

---

## Integration with SessionManager

**File:** `isaac/core/session_manager.py`

**Add to __init__() method:**
```python
# AI query history (separate from command history)
self.ai_query_history = AIQueryHistory()
```

**Add new method:**
```python
def log_ai_query(self, query: str, command: str, 
                 executed: bool = False, result: str = "pending"):
    """
    Log AI query translation to separate history.
    
    Args:
        query: Original natural language query
        command: Translated shell command
        executed: Whether command was executed
        result: Execution result
    """
    self.ai_query_history.add(
        query=query,
        command=command,
        shell=self.shell.name,
        executed=executed,
        result=result
    )
    
    # Save to file
    aiquery_file = self.isaac_dir / 'aiquery_history.json'
    self.ai_query_history.save(aiquery_file)
```

**Add to load_from_local() method:**
```python
# Load AI query history
aiquery_file = self.isaac_dir / 'aiquery_history.json'
self.ai_query_history = AIQueryHistory.load(aiquery_file)
```

---

## File Location

**Stored in:** `~/.isaac/aiquery_history.json`

**Example content:**
```json
{
  "queries": [
    {
      "query": "find large files",
      "command": "find . -type f -size +100M",
      "timestamp": "2025-10-19T12:34:56.789",
      "machine": "DESKTOP-ABC123",
      "shell": "bash",
      "executed": true,
      "result": "success"
    },
    {
      "query": "delete old logs",
      "command": "find . -name '*.log' -mtime +30 -delete",
      "timestamp": "2025-10-19T12:35:10.123",
      "machine": "DESKTOP-ABC123",
      "shell": "bash",
      "executed": false,
      "result": "aborted"
    }
  ],
  "metadata": {
    "total_count": 2,
    "privacy": "PRIVATE",
    "description": "AI natural language query history"
  }
}
```

---

## Privacy Features

**PRIVATE Marker:**
- Metadata includes `"privacy": "PRIVATE"`
- This signals that file should NOT be synced to debug bots
- User can review/delete queries anytime

**Separate from Command History:**
- Regular commands: `command_history.json`
- AI queries: `aiquery_history.json`
- Different files = different privacy controls

**User Control:**
- User can disable AI query logging via config:
```json
{
  "log_ai_queries": false
}
```

---

## Usage Example

```python
from isaac.models.aiquery_history import AIQueryHistory

# Create history
history = AIQueryHistory()

# Add query
history.add(
    query="find large files",
    command="find . -type f -size +100M",
    shell="bash",
    executed=True,
    result="success"
)

# Get recent queries
recent = history.get_recent(5)
print(f"Recent: {len(recent)} queries")

# Search
matches = history.search("find")
print(f"Found {len(matches)} queries with 'find'")

# Save to file
from pathlib import Path
history.save(Path.home() / '.isaac' / 'aiquery_history.json')

# Load from file
loaded = AIQueryHistory.load(Path.home() / '.isaac' / 'aiquery_history.json')
print(f"Loaded {len(loaded)} queries")
```

---

## Common Pitfalls

⚠️ **Don't mix with command history:**
```python
# WRONG - adds to wrong history
self.command_history.add(query, ...)

# CORRECT - separate AI query history
self.ai_query_history.add(query, command, ...)
```

⚠️ **Always mark result after execution:**
```python
# Log query
session.log_ai_query(query, command, executed=False, result="pending")

# Execute command
result = execute(command)

# Update result
session.log_ai_query(query, command, executed=True, 
                    result="success" if result.success else "failed")
```

⚠️ **Check file exists before loading:**
```python
# CORRECT - handles missing file
history = AIQueryHistory.load(filepath)  # Returns empty if missing

# WRONG - crashes if file missing
with open(filepath) as f:
    data = json.load(f)
```

---

**END OF IMPLEMENTATION**
