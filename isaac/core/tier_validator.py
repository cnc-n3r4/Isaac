"""
TierValidator - Safety classification system for shell commands
SAFETY-CRITICAL: Prevents dangerous commands from executing without warnings
"""

import json
from pathlib import Path
from typing import Dict, Any


class TierValidator:
    """Classifies shell commands into safety tiers (1-4)."""
    
    def __init__(self, preferences):
        """Initialize with user preferences."""
        self.preferences = preferences
        self.tier_defaults = self._load_tier_defaults()
    
    def _load_tier_defaults(self) -> Dict[str, list]:
        """Load default tier classifications."""
        # For now, hardcode the defaults from tests
        return {
            "1": ["ls", "cd", "pwd", "echo", "cat", "type", "Get-ChildItem", "Set-Location"],
            "2": ["grep", "Select-String", "head", "tail"],
            "2.5": ["find", "sed", "awk", "Where-Object"],
            "3": ["cp", "mv", "git", "npm", "pip", "Copy-Item", "Move-Item"],
            "4": ["rm", "del", "format", "dd", "Remove-Item", "Format-Volume"]
        }
    
    def get_tier(self, command: str) -> float:
        """
        Get safety tier for a command (1-4).
        
        Args:
            command: Shell command to classify
            
        Returns:
            float: Tier level (1=instant, 2=safe, 2.5=confirm, 3=validate, 4=lockdown)
        """
        # Extract base command (first word)
        base_cmd = command.strip().split()[0].lower()
        
        # Check user overrides first
        if hasattr(self.preferences, 'tier_overrides') and self.preferences.tier_overrides:
            if base_cmd in self.preferences.tier_overrides:
                return self.preferences.tier_overrides[base_cmd]
        
        # Check default tiers
        for tier_str, commands in self.tier_defaults.items():
            if base_cmd in [cmd.lower() for cmd in commands]:
                return float(tier_str) if '.' in tier_str else int(tier_str)
        
        # Unknown commands default to Tier 3 (validation required)
        return 3