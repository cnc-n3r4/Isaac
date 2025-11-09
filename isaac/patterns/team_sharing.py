"""
Team Pattern Sharing - Collaborative pattern libraries
Phase 3.4.3: Share patterns across team members
"""

import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class TeamPatternRepository:
    """A repository of shared team patterns."""

    id: str
    name: str
    description: str
    owner: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    patterns: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    contributors: Set[str] = field(default_factory=set)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    is_public: bool = False


@dataclass
class PatternContribution:
    """A contribution to a team pattern repository."""

    id: str
    repository_id: str
    contributor: str
    pattern_id: str
    action: str  # 'add', 'update', 'delete'
    timestamp: float = field(default_factory=time.time)
    pattern_data: Optional[Dict[str, Any]] = None
    description: str = ""


@dataclass
class PatternSyncResult:
    """Result of synchronizing patterns."""

    synced_patterns: int = 0
    new_patterns: int = 0
    updated_patterns: int = 0
    conflicts: int = 0
    errors: List[str] = field(default_factory=list)


class TeamPatternManager:
    """Manages team pattern sharing and synchronization."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize team pattern manager."""
        self.config = config or {}
        self.repositories: Dict[str, TeamPatternRepository] = {}
        self.contributions: List[PatternContribution] = []
        self.local_user = self.config.get("user_id", "anonymous")
        self.sync_interval = self.config.get("sync_interval", 3600)  # 1 hour

        # Storage paths
        self.data_dir = Path.home() / ".isaac" / "team_patterns"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Remote sync configuration
        self.remote_url = self.config.get("remote_url")
        self.api_key = self.config.get("api_key")

        # Load local data
        self._load_repositories()
        self._load_contributions()

        # Start background sync if configured
        if self.remote_url:
            self.sync_thread = threading.Thread(target=self._background_sync, daemon=True)
            self.sync_thread.start()

    def create_repository(
        self, name: str, description: str = "", is_public: bool = False, tags: List[str] = None
    ) -> str:
        """Create a new team pattern repository."""
        repo_id = str(uuid.uuid4())

        repository = TeamPatternRepository(
            id=repo_id,
            name=name,
            description=description,
            owner=self.local_user,
            contributors={self.local_user},
            is_public=is_public,
            tags=tags or [],
        )

        self.repositories[repo_id] = repository
        self._save_repositories()

        # Record contribution
        self._record_contribution(repo_id, "", "create_repo", f"Created repository '{name}'")

        return repo_id

    def add_pattern_to_repository(
        self, repo_id: str, pattern_data: Dict[str, Any], description: str = ""
    ) -> bool:
        """Add a pattern to a team repository."""
        if repo_id not in self.repositories:
            return False

        repository = self.repositories[repo_id]

        # Generate pattern ID if not provided
        pattern_id = pattern_data.get("id", str(uuid.uuid4()))
        pattern_data["id"] = pattern_id

        # Add metadata
        pattern_data["added_by"] = self.local_user
        pattern_data["added_at"] = time.time()
        pattern_data["repository_id"] = repo_id

        repository.patterns[pattern_id] = pattern_data
        repository.updated_at = time.time()
        repository.contributors.add(self.local_user)

        self._save_repositories()

        # Record contribution
        self._record_contribution(
            repo_id, pattern_id, "add", f"Added pattern '{pattern_data.get('name', 'Unknown')}'"
        )

        return True

    def update_pattern_in_repository(
        self, repo_id: str, pattern_id: str, updates: Dict[str, Any], description: str = ""
    ) -> bool:
        """Update a pattern in a team repository."""
        if repo_id not in self.repositories:
            return False

        repository = self.repositories[repo_id]
        if pattern_id not in repository.patterns:
            return False

        pattern = repository.patterns[pattern_id]

        # Apply updates
        for key, value in updates.items():
            pattern[key] = value

        pattern["updated_by"] = self.local_user
        pattern["updated_at"] = time.time()

        repository.updated_at = time.time()
        repository.contributors.add(self.local_user)

        self._save_repositories()

        # Record contribution
        self._record_contribution(
            repo_id, pattern_id, "update", f"Updated pattern '{pattern.get('name', 'Unknown')}'"
        )

        return True

    def remove_pattern_from_repository(
        self, repo_id: str, pattern_id: str, description: str = ""
    ) -> bool:
        """Remove a pattern from a team repository."""
        if repo_id not in self.repositories:
            return False

        repository = self.repositories[repo_id]
        if pattern_id not in repository.patterns:
            return False

        pattern_name = repository.patterns[pattern_id].get("name", "Unknown")
        del repository.patterns[pattern_id]

        repository.updated_at = time.time()
        repository.contributors.add(self.local_user)

        self._save_repositories()

        # Record contribution
        self._record_contribution(
            repo_id, pattern_id, "delete", f"Removed pattern '{pattern_name}'"
        )

        return True

    def get_repository_patterns(
        self, repo_id: str, category: Optional[str] = None, language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get patterns from a repository."""
        if repo_id not in self.repositories:
            return []

        repository = self.repositories[repo_id]
        patterns = list(repository.patterns.values())

        # Filter by category
        if category:
            patterns = [p for p in patterns if p.get("category") == category]

        # Filter by language
        if language:
            patterns = [p for p in patterns if p.get("language") == language]

        # Sort by usage and recency
        patterns.sort(key=lambda p: (p.get("usage_count", 0), p.get("updated_at", 0)), reverse=True)

        return patterns

    def search_repositories(
        self, query: str = "", tags: List[str] = None, owner: Optional[str] = None
    ) -> List[TeamPatternRepository]:
        """Search for repositories."""
        repositories = list(self.repositories.values())

        # Filter by query
        if query:
            query_lower = query.lower()
            repositories = [
                r
                for r in repositories
                if query_lower in r.name.lower() or query_lower in r.description.lower()
            ]

        # Filter by tags
        if tags:
            repositories = [r for r in repositories if any(tag in r.tags for tag in tags)]

        # Filter by owner
        if owner:
            repositories = [r for r in repositories if r.owner == owner]

        # Sort by recency and contributor count
        repositories.sort(key=lambda r: (r.updated_at, len(r.contributors)), reverse=True)

        return repositories

    def fork_repository(
        self, source_repo_id: str, new_name: str, new_description: str = ""
    ) -> Optional[str]:
        """Fork a repository."""
        if source_repo_id not in self.repositories:
            return None

        source_repo = self.repositories[source_repo_id]

        # Create new repository
        new_repo_id = self.create_repository(
            new_name, new_description, source_repo.is_public, source_repo.tags.copy()
        )

        new_repo = self.repositories[new_repo_id]

        # Copy patterns
        for pattern_id, pattern_data in source_repo.patterns.items():
            new_pattern_data = pattern_data.copy()
            new_pattern_data["forked_from"] = source_repo_id
            new_pattern_data["original_pattern_id"] = pattern_id
            new_repo.patterns[pattern_id] = new_pattern_data

        new_repo.contributors.update(source_repo.contributors)
        self._save_repositories()

        return new_repo_id

    def merge_repositories(
        self, source_repo_id: str, target_repo_id: str, conflict_resolution: str = "source_wins"
    ) -> bool:
        """Merge one repository into another."""
        if source_repo_id not in self.repositories or target_repo_id not in self.repositories:
            return False

        source_repo = self.repositories[source_repo_id]
        target_repo = self.repositories[target_repo_id]

        merged_count = 0
        conflicts = 0

        # Merge patterns
        for pattern_id, source_pattern in source_repo.patterns.items():
            if pattern_id in target_repo.patterns:
                # Conflict resolution
                conflicts += 1
                if conflict_resolution == "source_wins":
                    target_repo.patterns[pattern_id] = source_pattern
                elif conflict_resolution == "target_wins":
                    pass  # Keep target version
                elif conflict_resolution == "newer_wins":
                    source_time = source_pattern.get("updated_at", 0)
                    target_time = target_repo.patterns[pattern_id].get("updated_at", 0)
                    if source_time > target_time:
                        target_repo.patterns[pattern_id] = source_pattern
            else:
                target_repo.patterns[pattern_id] = source_pattern
                merged_count += 1

        # Merge contributors
        target_repo.contributors.update(source_repo.contributors)
        target_repo.updated_at = time.time()

        self._save_repositories()

        # Record merge contribution
        self._record_contribution(
            target_repo_id,
            "",
            "merge",
            f"Merged {merged_count} patterns from {source_repo.name} ({conflicts} conflicts)",
        )

        return True

    def export_repository(self, repo_id: str, file_path: str) -> bool:
        """Export a repository to a file."""
        if repo_id not in self.repositories:
            return False

        repository = self.repositories[repo_id]
        export_data = {
            "repository": asdict(repository),
            "exported_at": time.time(),
            "exported_by": self.local_user,
            "version": "1.0",
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting repository: {e}")
            return False

    def import_repository(self, file_path: str) -> Optional[str]:
        """Import a repository from a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            repository_data = import_data["repository"]

            # Create repository instance
            repository = TeamPatternRepository(**repository_data)
            repo_id = repository.id

            # Handle ID conflicts
            if repo_id in self.repositories:
                repo_id = str(uuid.uuid4())
                repository.id = repo_id

            self.repositories[repo_id] = repository
            self._save_repositories()

            # Record import contribution
            self._record_contribution(
                repo_id, "", "import", f"Imported repository '{repository.name}'"
            )

            return repo_id

        except Exception as e:
            print(f"Error importing repository: {e}")
            return None

    def sync_with_remote(self) -> PatternSyncResult:
        """Synchronize with remote pattern server."""
        if not self.remote_url or not self.api_key:
            return PatternSyncResult(errors=["Remote sync not configured"])

        result = PatternSyncResult()

        try:
            # Sync repositories
            repo_result = self._sync_repositories()
            result.synced_patterns += repo_result.get("synced", 0)
            result.new_patterns += repo_result.get("new", 0)
            result.updated_patterns += repo_result.get("updated", 0)
            result.conflicts += repo_result.get("conflicts", 0)

            # Sync contributions
            contrib_result = self._sync_contributions()
            if contrib_result.get("errors"):
                result.errors.extend(contrib_result["errors"])

        except Exception as e:
            result.errors.append(f"Sync failed: {str(e)}")

        return result

    def _sync_repositories(self) -> Dict[str, int]:
        """Sync repositories with remote server."""
        # This would implement actual HTTP sync
        # For now, return mock results
        return {"synced": 0, "new": 0, "updated": 0, "conflicts": 0}

    def _sync_contributions(self) -> Dict[str, Any]:
        """Sync contributions with remote server."""
        # This would implement actual HTTP sync
        return {"errors": []}

    def get_repository_stats(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a repository."""
        if repo_id not in self.repositories:
            return None

        repository = self.repositories[repo_id]
        patterns = list(repository.patterns.values())

        # Calculate statistics
        total_patterns = len(patterns)
        categories = {}
        languages = {}
        total_usage = 0

        for pattern in patterns:
            category = pattern.get("category", "unknown")
            language = pattern.get("language", "unknown")
            usage = pattern.get("usage_count", 0)

            categories[category] = categories.get(category, 0) + 1
            languages[language] = languages.get(language, 0) + 1
            total_usage += usage

        return {
            "repository_id": repo_id,
            "name": repository.name,
            "total_patterns": total_patterns,
            "categories": categories,
            "languages": languages,
            "total_usage": total_usage,
            "contributors": len(repository.contributors),
            "created_at": repository.created_at,
            "updated_at": repository.updated_at,
            "is_public": repository.is_public,
        }

    def get_user_contributions(self, user_id: Optional[str] = None) -> List[PatternContribution]:
        """Get contributions by a user."""
        user = user_id or self.local_user
        return [c for c in self.contributions if c.contributor == user]

    def get_recent_activity(self, limit: int = 10) -> List[PatternContribution]:
        """Get recent pattern activity."""
        contributions = sorted(self.contributions, key=lambda c: c.timestamp, reverse=True)
        return contributions[:limit]

    def cleanup_old_repositories(self, days_threshold: int = 365) -> int:
        """Remove repositories that haven't been updated recently."""
        cutoff_time = time.time() - (days_threshold * 24 * 60 * 60)
        to_remove = []

        for repo_id, repository in self.repositories.items():
            if repository.updated_at < cutoff_time and len(repository.contributors) == 1:
                to_remove.append(repo_id)

        for repo_id in to_remove:
            del self.repositories[repo_id]

        if to_remove:
            self._save_repositories()

        return len(to_remove)

    def _load_repositories(self):
        """Load repositories from disk."""
        repo_file = self.data_dir / "repositories.json"
        try:
            if repo_file.exists():
                with open(repo_file, "r", encoding="utf-8") as f:
                    repos_data = json.load(f)
                    for repo_data in repos_data:
                        repository = TeamPatternRepository(**repo_data)
                        self.repositories[repository.id] = repository
        except Exception as e:
            print(f"Error loading repositories: {e}")

    def _save_repositories(self):
        """Save repositories to disk."""
        repo_file = self.data_dir / "repositories.json"
        try:
            repos_data = [asdict(r) for r in self.repositories.values()]
            with open(repo_file, "w", encoding="utf-8") as f:
                json.dump(repos_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving repositories: {e}")

    def _load_contributions(self):
        """Load contributions from disk."""
        contrib_file = self.data_dir / "contributions.json"
        try:
            if contrib_file.exists():
                with open(contrib_file, "r", encoding="utf-8") as f:
                    contribs_data = json.load(f)
                    self.contributions = [PatternContribution(**c) for c in contribs_data]
        except Exception as e:
            print(f"Error loading contributions: {e}")

    def _save_contributions(self):
        """Save contributions to disk."""
        contrib_file = self.data_dir / "contributions.json"
        try:
            contribs_data = [asdict(c) for c in self.contributions]
            with open(contrib_file, "w", encoding="utf-8") as f:
                json.dump(contribs_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving contributions: {e}")

    def _record_contribution(self, repo_id: str, pattern_id: str, action: str, description: str):
        """Record a contribution."""
        contribution = PatternContribution(
            id=str(uuid.uuid4()),
            repository_id=repo_id,
            contributor=self.local_user,
            pattern_id=pattern_id,
            action=action,
            description=description,
        )

        self.contributions.append(contribution)
        self._save_contributions()

    def _background_sync(self):
        """Background synchronization thread."""
        while True:
            try:
                time.sleep(self.sync_interval)
                self.sync_with_remote()
            except Exception as e:
                print(f"Background sync error: {e}")
                time.sleep(60)  # Wait a minute before retrying
