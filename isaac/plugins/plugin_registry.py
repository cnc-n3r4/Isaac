"""Plugin Registry - Central plugin repository management."""

import json
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from isaac.plugins.plugin_api import PluginMetadata


@dataclass
class RegistryEntry:
    """Entry in the plugin registry."""

    metadata: PluginMetadata
    download_url: str
    checksum: str
    downloads: int = 0
    rating: float = 0.0
    reviews: int = 0
    featured: bool = False
    verified: bool = False
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "download_url": self.download_url,
            "checksum": self.checksum,
            "downloads": self.downloads,
            "rating": self.rating,
            "reviews": self.reviews,
            "featured": self.featured,
            "verified": self.verified,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegistryEntry":
        """Create from dictionary."""
        metadata = PluginMetadata.from_dict(data["metadata"])
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            metadata=metadata,
            download_url=data["download_url"],
            checksum=data["checksum"],
            downloads=data.get("downloads", 0),
            rating=data.get("rating", 0.0),
            reviews=data.get("reviews", 0),
            featured=data.get("featured", False),
            verified=data.get("verified", False),
            updated_at=updated_at,
        )


class PluginRegistry:
    """Central plugin registry for discovering and downloading plugins."""

    DEFAULT_REGISTRY_URL = "https://registry.isaac.dev/plugins.json"
    CACHE_DURATION = 3600  # 1 hour

    def __init__(self, cache_dir: Optional[Path] = None, registry_url: Optional[str] = None):
        """Initialize the plugin registry.

        Args:
            cache_dir: Directory to cache registry data
            registry_url: URL of the plugin registry (defaults to official registry)
        """
        self.cache_dir = cache_dir or Path.home() / ".isaac" / "plugin_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.registry_url = registry_url or self.DEFAULT_REGISTRY_URL
        self.cache_file = self.cache_dir / "registry.json"
        self._registry: Dict[str, RegistryEntry] = {}
        self._last_update: Optional[datetime] = None

        # Load from cache if available
        self._load_cache()

    def _load_cache(self) -> None:
        """Load registry from cache."""
        if not self.cache_file.exists():
            return

        try:
            with open(self.cache_file) as f:
                data = json.load(f)

            self._last_update = datetime.fromisoformat(data["updated_at"])
            self._registry = {
                name: RegistryEntry.from_dict(entry)
                for name, entry in data["entries"].items()
            }
        except Exception:
            # Ignore cache errors
            pass

    def _save_cache(self) -> None:
        """Save registry to cache."""
        try:
            data = {
                "updated_at": self._last_update.isoformat() if self._last_update else None,
                "entries": {name: entry.to_dict() for name, entry in self._registry.items()},
            }

            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            # Ignore cache errors
            pass

    def _needs_update(self) -> bool:
        """Check if registry cache needs update."""
        if not self._last_update:
            return True

        age = (datetime.now() - self._last_update).total_seconds()
        return age > self.CACHE_DURATION

    def update(self, force: bool = False) -> bool:
        """Update registry from remote source.

        Args:
            force: Force update even if cache is fresh

        Returns:
            True if update was successful
        """
        if not force and not self._needs_update():
            return True

        try:
            # In a real implementation, this would fetch from the registry URL
            # For now, we'll use a local registry or mock data
            response = self._fetch_registry()

            if response:
                self._registry = response
                self._last_update = datetime.now()
                self._save_cache()
                return True

        except Exception as e:
            print(f"Failed to update registry: {e}")

        return False

    def _fetch_registry(self) -> Optional[Dict[str, RegistryEntry]]:
        """Fetch registry from remote source.

        Returns:
            Registry entries or None if fetch failed
        """
        # For development, use a local registry file if it exists
        local_registry = self.cache_dir / "local_registry.json"
        if local_registry.exists():
            with open(local_registry) as f:
                data = json.load(f)
                return {
                    name: RegistryEntry.from_dict(entry)
                    for name, entry in data.items()
                }

        # In production, this would make an HTTP request to the registry URL
        # For now, return built-in plugins
        return self._get_builtin_registry()

    def _get_builtin_registry(self) -> Dict[str, RegistryEntry]:
        """Get built-in plugin registry.

        Returns:
            Dictionary of built-in plugins
        """
        # This will be populated with example/built-in plugins
        return {}

    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        featured: bool = False,
        verified: bool = False,
    ) -> List[RegistryEntry]:
        """Search for plugins in the registry.

        Args:
            query: Search query (searches name and description)
            tags: Filter by tags
            featured: Only show featured plugins
            verified: Only show verified plugins

        Returns:
            List of matching plugin entries
        """
        self.update()  # Auto-update if needed

        results = list(self._registry.values())

        # Filter by query
        if query:
            query_lower = query.lower()
            results = [
                entry
                for entry in results
                if query_lower in entry.metadata.name.lower()
                or query_lower in entry.metadata.description.lower()
            ]

        # Filter by tags
        if tags:
            results = [
                entry
                for entry in results
                if any(tag in entry.metadata.tags for tag in tags)
            ]

        # Filter by featured
        if featured:
            results = [entry for entry in results if entry.featured]

        # Filter by verified
        if verified:
            results = [entry for entry in results if entry.verified]

        # Sort by downloads and rating
        results.sort(key=lambda e: (e.downloads, e.rating), reverse=True)

        return results

    def get(self, name: str) -> Optional[RegistryEntry]:
        """Get a specific plugin from the registry.

        Args:
            name: Plugin name

        Returns:
            Registry entry or None if not found
        """
        self.update()  # Auto-update if needed
        return self._registry.get(name)

    def list_featured(self) -> List[RegistryEntry]:
        """List featured plugins.

        Returns:
            List of featured plugins
        """
        return self.search(featured=True)

    def list_by_tag(self, tag: str) -> List[RegistryEntry]:
        """List plugins by tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of plugins with the tag
        """
        return self.search(tags=[tag])

    def download_plugin(self, name: str, destination: Path) -> bool:
        """Download a plugin from the registry.

        Args:
            name: Plugin name
            destination: Destination directory

        Returns:
            True if download successful
        """
        entry = self.get(name)
        if not entry:
            return False

        try:
            # In a real implementation, this would download from the URL
            # For now, we'll copy from a local plugins directory
            return self._download_from_url(entry.download_url, destination, entry.checksum)
        except Exception as e:
            print(f"Failed to download plugin {name}: {e}")
            return False

    def _download_from_url(self, url: str, destination: Path, expected_checksum: str) -> bool:
        """Download file from URL and verify checksum.

        Args:
            url: Download URL
            destination: Destination path
            expected_checksum: Expected SHA256 checksum

        Returns:
            True if download and verification successful
        """
        # For development, check if it's a local path
        if url.startswith("file://"):
            local_path = Path(url[7:])
            if local_path.exists():
                import shutil

                shutil.copy2(local_path, destination)
                return self._verify_checksum(destination, expected_checksum)

        # In production, download from HTTP(S)
        # This is a placeholder for actual HTTP download logic
        return False

    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify file checksum.

        Args:
            file_path: Path to file
            expected_checksum: Expected SHA256 checksum

        Returns:
            True if checksum matches
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)

        return sha256.hexdigest() == expected_checksum

    def add_to_local_registry(self, entry: RegistryEntry) -> None:
        """Add an entry to the local registry.

        This is useful for testing or private plugins.

        Args:
            entry: Registry entry to add
        """
        self._registry[entry.metadata.name] = entry
        self._last_update = datetime.now()
        self._save_cache()

    def remove_from_local_registry(self, name: str) -> bool:
        """Remove an entry from the local registry.

        Args:
            name: Plugin name

        Returns:
            True if removed
        """
        if name in self._registry:
            del self._registry[name]
            self._last_update = datetime.now()
            self._save_cache()
            return True
        return False
