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