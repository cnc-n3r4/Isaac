"""
Command Aliases System - User-defined command shortcuts
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CommandAlias:
    """A command alias definition"""

    name: str
    command: str
    description: Optional[str] = None
    category: str = "user"
    created_at: Optional[float] = None
    usage_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            import time

            self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandAlias":
        """Create from dictionary"""
        return cls(**data)


class AliasManager:
    """Manages user-defined command aliases"""

    def __init__(self, aliases_file: Optional[Path] = None):
        if aliases_file is None:
            # Default to user's Isaac directory
            from pathlib import Path

            isaac_dir = Path.home() / ".isaac"
            isaac_dir.mkdir(exist_ok=True)
            aliases_file = isaac_dir / "aliases.json"

        self.aliases_file = aliases_file
        self.aliases: Dict[str, CommandAlias] = {}
        self._load_aliases()

    def _load_aliases(self):
        """Load aliases from file"""
        if self.aliases_file.exists():
            try:
                with open(self.aliases_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for alias_data in data.get("aliases", []):
                    alias = CommandAlias.from_dict(alias_data)
                    self.aliases[alias.name] = alias

            except Exception as e:
                print(f"Warning: Could not load aliases: {e}")

    def _save_aliases(self):
        """Save aliases to file"""
        try:
            data = {"aliases": [alias.to_dict() for alias in self.aliases.values()]}

            with open(self.aliases_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error saving aliases: {e}")

    def add_alias(self, name: str, command: str, description: Optional[str] = None) -> bool:
        """Add a new alias"""
        if name in self.aliases:
            return False  # Alias already exists

        # Validate command format
        if not command.strip():
            return False

        alias = CommandAlias(name=name, command=command.strip(), description=description)

        self.aliases[name] = alias
        self._save_aliases()
        return True

    def remove_alias(self, name: str) -> bool:
        """Remove an alias"""
        if name not in self.aliases:
            return False

        del self.aliases[name]
        self._save_aliases()
        return True

    def get_alias(self, name: str) -> Optional[CommandAlias]:
        """Get an alias by name"""
        return self.aliases.get(name)

    def resolve_alias(self, name: str) -> Optional[str]:
        """Resolve alias to command, returns None if not found"""
        alias = self.get_alias(name)
        if alias:
            alias.usage_count += 1
            self._save_aliases()
            return alias.command
        return None

    def list_aliases(self, category: Optional[str] = None) -> List[CommandAlias]:
        """List all aliases, optionally filtered by category"""
        aliases = list(self.aliases.values())

        if category:
            aliases = [a for a in aliases if a.category == category]

        return sorted(aliases, key=lambda x: x.name)

    def search_aliases(self, query: str) -> List[CommandAlias]:
        """Search aliases by name, command, or description"""
        query_lower = query.lower()
        matches = []

        for alias in self.aliases.values():
            searchable = [alias.name, alias.command, alias.description or ""]

            if any(query_lower in text.lower() for text in searchable):
                matches.append(alias)

        return sorted(matches, key=lambda x: x.name)

    def get_popular_aliases(self, limit: int = 10) -> List[CommandAlias]:
        """Get most used aliases"""
        aliases = list(self.aliases.values())
        return sorted(aliases, key=lambda x: x.usage_count, reverse=True)[:limit]

    def import_aliases(self, aliases_data: List[Dict[str, Any]], merge: bool = True) -> int:
        """Import aliases from data"""
        imported = 0

        for alias_data in aliases_data:
            try:
                name = alias_data["name"]
                if not merge and name in self.aliases:
                    continue  # Skip existing

                alias = CommandAlias.from_dict(alias_data)
                self.aliases[name] = alias
                imported += 1

            except Exception:
                continue

        if imported > 0:
            self._save_aliases()

        return imported

    def export_aliases(self) -> List[Dict[str, Any]]:
        """Export all aliases as data"""
        return [alias.to_dict() for alias in self.aliases.values()]

    def get_stats(self) -> Dict[str, Any]:
        """Get alias statistics"""
        total_aliases = len(self.aliases)
        total_usage = sum(alias.usage_count for alias in self.aliases.values())
        categories = {}

        for alias in self.aliases.values():
            categories[alias.category] = categories.get(alias.category, 0) + 1

        return {
            "total_aliases": total_aliases,
            "total_usage": total_usage,
            "categories": categories,
            "most_used": [alias.name for alias in self.get_popular_aliases(5)],
        }


# Global instance for easy access
alias_manager = AliasManager()


def add_alias(name: str, command: str, description: Optional[str] = None) -> bool:
    """Convenience function to add alias"""
    return alias_manager.add_alias(name, command, description)


def resolve_alias(name: str) -> Optional[str]:
    """Convenience function to resolve alias"""
    return alias_manager.resolve_alias(name)


def list_aliases(category: Optional[str] = None) -> List[CommandAlias]:
    """Convenience function to list aliases"""
    return alias_manager.list_aliases(category)
