"""
Query Classifier - Determine if query is geographic, file lookup, or shell command.

Uses heuristics + optional AI classification for edge cases.
"""
import re
from typing import Literal

QueryType = Literal['geographic', 'file_lookup', 'shell_command', 'general_info']


class QueryClassifier:
    """Classify natural language queries by intent."""
    
    # File extension patterns
    FILE_EXTENSIONS = r'\.(exe|dll|txt|log|csv|json|xml|py|js|md|bat|ps1|sh|pdf|doc|docx|zip|tar|gz)$'
    
    # Geographic indicators
    GEOGRAPHIC_KEYWORDS = [
        'where is', 'location of', 'capital of', 'population of',
        'country', 'city', 'state', 'province', 'continent',
        'what country', 'which country', 'located in'
    ]
    
    # General info indicators
    INFO_KEYWORDS = [
        'what is', 'explain', 'how does', 'why does', 'tell me about',
        'define', 'describe', 'difference between', 'what are',
        'how to', 'when did', 'who is', 'who was'
    ]
    
    # Shell command indicators
    COMMAND_KEYWORDS = [
        'list', 'show', 'find', 'search', 'delete', 'remove',
        'copy', 'move', 'create', 'make', 'run', 'execute',
        'kill', 'stop', 'start', 'restart'
    ]
    
    def classify(self, query: str) -> QueryType:
        """
        Classify query type.
        
        Args:
            query: Natural language query
        
        Returns:
            Query type classification
        """
        query_lower = query.lower().strip()
        
        # Check for file extensions (strong signal for file_lookup)
        if re.search(self.FILE_EXTENSIONS, query_lower, re.IGNORECASE):
            return 'file_lookup'
        
        # Check for file path patterns
        if self._looks_like_path(query):
            return 'file_lookup'
        
        # Check for geographic keywords
        if any(kw in query_lower for kw in self.GEOGRAPHIC_KEYWORDS):
            # But exclude if it ends with file extension
            if not re.search(self.FILE_EXTENSIONS, query_lower):
                return 'geographic'
        
        # Check for general info keywords
        if any(kw in query_lower for kw in self.INFO_KEYWORDS):
            # Exclude if followed by file/command indicators
            if not any(cmd in query_lower for cmd in self.COMMAND_KEYWORDS):
                return 'general_info'
        
        # Check for explicit command keywords
        if any(cmd in query_lower for cmd in self.COMMAND_KEYWORDS):
            return 'shell_command'
        
        # Default: shell command translation
        return 'shell_command'
    
    def _looks_like_path(self, query: str) -> bool:
        """Check if query contains path-like patterns."""
        # Windows paths: C:\, \\server\, D:\
        if re.search(r'[A-Z]:\\|\\\\[\w-]+\\', query, re.IGNORECASE):
            return True
        
        # Unix paths: /usr/, ~/
        if re.search(r'^/[\w/]+|^~/[\w/]+', query):
            return True
        
        # Relative paths with slashes
        if re.search(r'[\\/][\w.-]+[\\/]', query):
            return True
        
        return False
    
    def is_chat_mode_query(self, query: str) -> bool:
        """
        Determine if query should route to chat mode (vs translation).
        
        Returns:
            True if query should use chat mode (geographic/general_info)
            False if query should translate to shell command
        """
        query_type = self.classify(query)
        return query_type in ('geographic', 'general_info')
