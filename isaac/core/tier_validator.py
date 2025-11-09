"""
TierValidator - Safety classification system for shell commands
SAFETY-CRITICAL: Prevents dangerous commands from executing without warnings
"""

import json
from pathlib import Path
from typing import Any, Dict, List


class TierValidator:
    """Classifies shell commands into safety tiers (1-4)."""

    def __init__(self, preferences: Any) -> None:
        """Initialize with user preferences."""
        self.preferences = preferences
        self.tier_defaults = self._load_tier_defaults()

    def _load_tier_defaults(self) -> Dict[str, List[str]]:
        """Load default tier classifications from JSON file."""
        try:
            data_dir = Path(__file__).parent.parent / "data"
            tier_file = data_dir / "tier_defaults.json"

            if tier_file.exists():
                with open(tier_file, "r") as f:
                    data = json.load(f)
                    # Convert string keys to lists
                    return {tier: commands for tier, commands in data.items()}
            else:
                # Fallback to hardcoded defaults if file not found
                return {
                    "1": [
                        "ls",
                        "cd",
                        "clear",
                        "cls",
                        "pwd",
                        "echo",
                        "cat",
                        "type",
                        "Get-ChildItem",
                        "Set-Location",
                        "Get-Location",
                    ],
                    "2": ["grep", "Select-String", "head", "tail", "sort", "uniq"],
                    "2.5": ["find", "sed", "awk", "Where-Object", "ForEach-Object"],
                    "3": [
                        "cp",
                        "mv",
                        "git",
                        "npm",
                        "pip",
                        "reset",
                        "Copy-Item",
                        "Move-Item",
                        "New-Item",
                        "Remove-Item",
                    ],
                    "4": [
                        "rm",
                        "del",
                        "format",
                        "dd",
                        "Remove-Item",
                        "Format-Volume",
                        "Clear-Disk",
                    ],
                }
        except Exception:
            # Fallback on any error
            return {
                "1": [
                    "ls",
                    "cd",
                    "clear",
                    "cls",
                    "pwd",
                    "echo",
                    "cat",
                    "type",
                    "Get-ChildItem",
                    "Set-Location",
                    "Get-Location",
                ],
                "2": ["grep", "Select-String", "head", "tail", "sort", "uniq"],
                "2.5": ["find", "sed", "awk", "Where-Object", "ForEach-Object"],
                "3": [
                    "cp",
                    "mv",
                    "git",
                    "npm",
                    "pip",
                    "reset",
                    "Copy-Item",
                    "Move-Item",
                    "New-Item",
                    "Remove-Item",
                ],
                "4": ["rm", "del", "format", "dd", "Remove-Item", "Format-Volume", "Clear-Disk"],
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
        if hasattr(self.preferences, "tier_overrides") and self.preferences.tier_overrides:
            if base_cmd in self.preferences.tier_overrides:
                return self.preferences.tier_overrides[base_cmd]

        # Check default tiers
        for tier_str, commands in self.tier_defaults.items():
            if base_cmd in [cmd.lower() for cmd in commands]:
                return float(tier_str) if "." in tier_str else int(tier_str)

        # Unknown commands default to Tier 3 (validation required)
        return 3
