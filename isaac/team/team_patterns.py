"""Team pattern sharing for collaborative code patterns."""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from .models import SharedResource, ResourceType


class TeamPatternSharing:
    """Share code patterns with teams."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize team pattern sharing.

        Args:
            base_dir: Base directory for team patterns (default: ~/.isaac/team_patterns/)
        """
        self.base_dir = Path(base_dir or os.path.expanduser("~/.isaac/team_patterns"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def share_pattern(self, team_id: str, pattern_data: Dict,
                     shared_by: str, name: str = "", description: str = "") -> SharedResource:
        """Share a pattern with a team.

        Args:
            team_id: Team ID
            pattern_data: Pattern data from pattern library
            shared_by: User ID sharing the pattern
            name: Pattern name
            description: Pattern description

        Returns:
            SharedResource object
        """
        # Generate resource ID
        import uuid
        pattern_id = pattern_data.get('pattern_id', str(uuid.uuid4()))

        # Save pattern data
        pattern_file = self.base_dir / team_id / f"{pattern_id}.json"
        pattern_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pattern_file, 'w') as f:
            json.dump(pattern_data, f, indent=2)

        # Create shared resource
        resource = SharedResource(
            resource_id=pattern_id,
            resource_type=ResourceType.PATTERN,
            team_id=team_id,
            shared_by=shared_by,
            name=name or pattern_data.get('name', 'Unnamed Pattern'),
            description=description or pattern_data.get('description', ''),
            metadata={
                'pattern_type': pattern_data.get('pattern_type'),
                'language': pattern_data.get('language'),
                'usage_count': pattern_data.get('usage_count', 0),
                'quality_score': pattern_data.get('quality_score', 0),
            }
        )

        return resource

    def get_pattern(self, team_id: str, pattern_id: str) -> Optional[Dict]:
        """Get pattern data.

        Args:
            team_id: Team ID
            pattern_id: Pattern ID

        Returns:
            Pattern data dictionary or None if not found
        """
        pattern_file = self.base_dir / team_id / f"{pattern_id}.json"
        if not pattern_file.exists():
            return None

        with open(pattern_file) as f:
            return json.load(f)

    def import_pattern(self, team_id: str, pattern_id: str, pattern_library) -> bool:
        """Import a team pattern into local pattern library.

        Args:
            team_id: Team ID
            pattern_id: Pattern ID
            pattern_library: PatternLibrary instance

        Returns:
            True if imported, False on error
        """
        pattern_data = self.get_pattern(team_id, pattern_id)
        if not pattern_data:
            return False

        try:
            # Import into pattern library
            # This would integrate with isaac/patterns/pattern_learner.py
            pattern_library.add_pattern(pattern_data)
            return True
        except Exception:
            return False

    def list_patterns(self, team_id: str, pattern_type: Optional[str] = None,
                     language: Optional[str] = None) -> List[Dict]:
        """List patterns shared with a team.

        Args:
            team_id: Team ID
            pattern_type: Optional pattern type filter
            language: Optional language filter

        Returns:
            List of pattern metadata
        """
        patterns = []
        team_dir = self.base_dir / team_id

        if not team_dir.exists():
            return patterns

        for pattern_file in team_dir.glob("*.json"):
            try:
                with open(pattern_file) as f:
                    pattern_data = json.load(f)

                # Apply filters
                if pattern_type and pattern_data.get('pattern_type') != pattern_type:
                    continue
                if language and pattern_data.get('language') != language:
                    continue

                patterns.append({
                    'pattern_id': pattern_file.stem,
                    'name': pattern_data.get('name', 'Unnamed'),
                    'description': pattern_data.get('description', ''),
                    'pattern_type': pattern_data.get('pattern_type'),
                    'language': pattern_data.get('language'),
                    'quality_score': pattern_data.get('quality_score', 0),
                    'usage_count': pattern_data.get('usage_count', 0),
                    'shared_at': pattern_data.get('shared_at'),
                })
            except Exception:
                continue

        # Sort by quality score
        patterns.sort(key=lambda p: p.get('quality_score', 0), reverse=True)

        return patterns

    def update_pattern_usage(self, team_id: str, pattern_id: str,
                           used_by: str) -> bool:
        """Update pattern usage count and tracking.

        Args:
            team_id: Team ID
            pattern_id: Pattern ID
            used_by: User ID using the pattern

        Returns:
            True if updated, False on error
        """
        pattern_data = self.get_pattern(team_id, pattern_id)
        if not pattern_data:
            return False

        # Update usage tracking
        pattern_data['usage_count'] = pattern_data.get('usage_count', 0) + 1
        pattern_data['last_used_at'] = datetime.now().isoformat()
        pattern_data['last_used_by'] = used_by

        if 'usage_history' not in pattern_data:
            pattern_data['usage_history'] = []

        pattern_data['usage_history'].append({
            'used_by': used_by,
            'used_at': datetime.now().isoformat(),
        })

        # Save updated pattern
        pattern_file = self.base_dir / team_id / f"{pattern_id}.json"
        try:
            with open(pattern_file, 'w') as f:
                json.dump(pattern_data, f, indent=2)
            return True
        except Exception:
            return False

    def search_patterns(self, team_id: str, query: str) -> List[Dict]:
        """Search patterns by name, description, or code.

        Args:
            team_id: Team ID
            query: Search query

        Returns:
            List of matching patterns
        """
        results = []
        team_dir = self.base_dir / team_id

        if not team_dir.exists():
            return results

        query_lower = query.lower()

        for pattern_file in team_dir.glob("*.json"):
            try:
                with open(pattern_file) as f:
                    pattern_data = json.load(f)

                # Search in name, description, and code
                searchable_text = (
                    f"{pattern_data.get('name', '')} "
                    f"{pattern_data.get('description', '')} "
                    f"{pattern_data.get('code', '')}"
                ).lower()

                if query_lower in searchable_text:
                    results.append({
                        'pattern_id': pattern_file.stem,
                        'name': pattern_data.get('name', 'Unnamed'),
                        'description': pattern_data.get('description', ''),
                        'pattern_type': pattern_data.get('pattern_type'),
                        'language': pattern_data.get('language'),
                        'quality_score': pattern_data.get('quality_score', 0),
                    })
            except Exception:
                continue

        # Sort by quality score
        results.sort(key=lambda p: p.get('quality_score', 0), reverse=True)

        return results

    def delete_pattern(self, team_id: str, pattern_id: str) -> bool:
        """Delete a shared pattern.

        Args:
            team_id: Team ID
            pattern_id: Pattern ID

        Returns:
            True if deleted, False if not found
        """
        pattern_file = self.base_dir / team_id / f"{pattern_id}.json"
        if pattern_file.exists():
            pattern_file.unlink()
            return True
        return False

    def get_pattern_stats(self, team_id: str) -> Dict:
        """Get statistics about team patterns.

        Args:
            team_id: Team ID

        Returns:
            Dictionary with pattern statistics
        """
        patterns = self.list_patterns(team_id)

        stats = {
            'total_patterns': len(patterns),
            'by_type': {},
            'by_language': {},
            'average_quality': 0,
            'total_usage': 0,
            'top_patterns': [],
        }

        if not patterns:
            return stats

        for pattern in patterns:
            # Count by type
            ptype = pattern.get('pattern_type', 'unknown')
            stats['by_type'][ptype] = stats['by_type'].get(ptype, 0) + 1

            # Count by language
            lang = pattern.get('language', 'unknown')
            stats['by_language'][lang] = stats['by_language'].get(lang, 0) + 1

            # Sum quality and usage
            stats['total_usage'] += pattern.get('usage_count', 0)

        # Calculate average quality
        quality_sum = sum(p.get('quality_score', 0) for p in patterns)
        stats['average_quality'] = quality_sum / len(patterns) if patterns else 0

        # Get top patterns by usage
        stats['top_patterns'] = sorted(
            patterns,
            key=lambda p: p.get('usage_count', 0),
            reverse=True
        )[:10]

        return stats
