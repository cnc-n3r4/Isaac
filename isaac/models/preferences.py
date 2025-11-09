"""
Preferences - User settings and configuration
Cloud-synced user preferences for Isaac behavior
"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional
import platform


@dataclass
class Preferences:
    """User preferences and configuration settings."""

    machine_id: str
    auto_run_tier2: bool = False
    tier_overrides: Optional[Dict[str, int]] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None

    def __post_init__(self):
        """Initialize defaults after dataclass creation."""
        if self.tier_overrides is None:
            self.tier_overrides = {}
        if self.machine_id is None:
            self.machine_id = platform.node()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Preferences':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)

    def get_tier_override(self, command: str) -> Optional[int]:
        """
        Get user-defined tier override for command.

        Args:
            command: Command name to check

        Returns:
            Override tier number, or None if no override
        """
        if self.tier_overrides is None:
            return None
        return self.tier_overrides.get(command.lower())

    def set_tier_override(self, command: str, tier: int) -> None:
        """
        Set custom tier override for command.

        Args:
            command: Command name
            tier: Tier number (1-4)
        """
        if tier not in [1, 2, 2.5, 3, 4]:
            raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, 2.5, 3, or 4")
        if self.tier_overrides is None:
            self.tier_overrides = {}
        self.tier_overrides[command.lower()] = tier

    def remove_tier_override(self, command: str) -> None:
        """
        Remove custom tier override for command.

        Args:
            command: Command name
        """
        if self.tier_overrides is not None:
            self.tier_overrides.pop(command.lower(), None)

    def is_auto_run_enabled(self) -> bool:
        """Check if Tier 2 auto-execution is enabled."""
        return self.auto_run_tier2

    def set_auto_run(self, enabled: bool) -> None:
        """Enable/disable Tier 2 auto-execution."""
        self.auto_run_tier2 = enabled