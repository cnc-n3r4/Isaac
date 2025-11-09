"""
Conflict Resolver - Resolve synchronization conflicts
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import difflib


class ConflictResolver:
    """
    Resolves conflicts between local and remote data
    """

    def __init__(self):
        self.resolution_strategies = {
            'local_wins': self._resolve_local_wins,
            'remote_wins': self._resolve_remote_wins,
            'timestamp': self._resolve_by_timestamp,
            'merge': self._resolve_merge,
            'manual': self._resolve_manual
        }

        self.pending_conflicts: List[Dict[str, Any]] = []

    def detect_conflict(
        self,
        local_data: Dict[str, Any],
        remote_data: Dict[str, Any],
        resource_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if there's a conflict between local and remote data

        Args:
            local_data: Local version of data
            remote_data: Remote version of data
            resource_id: Identifier for the resource

        Returns:
            Conflict information if detected, None otherwise
        """
        # Check if both have been modified
        local_modified = local_data.get('modified_at')
        remote_modified = remote_data.get('modified_at')

        if not local_modified or not remote_modified:
            return None

        # Check if content differs
        local_content = local_data.get('content')
        remote_content = remote_data.get('content')

        if local_content == remote_content:
            return None

        # Conflict detected
        conflict = {
            'id': f"conflict_{resource_id}_{datetime.utcnow().timestamp()}",
            'resource_id': resource_id,
            'local_data': local_data,
            'remote_data': remote_data,
            'detected_at': datetime.utcnow().isoformat(),
            'resolved': False,
            'resolution': None
        }

        self.pending_conflicts.append(conflict)

        return conflict

    def resolve_conflict(
        self,
        conflict_id: str,
        strategy: str = 'timestamp',
        manual_resolution: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve a conflict using specified strategy

        Args:
            conflict_id: Conflict identifier
            strategy: Resolution strategy
            manual_resolution: Manual resolution data

        Returns:
            Resolved data
        """
        # Find conflict
        conflict = None
        for c in self.pending_conflicts:
            if c['id'] == conflict_id:
                conflict = c
                break

        if not conflict:
            raise ValueError(f"Conflict {conflict_id} not found")

        # Get resolution function
        resolver = self.resolution_strategies.get(strategy)

        if not resolver:
            raise ValueError(f"Unknown strategy: {strategy}")

        # Resolve conflict
        if strategy == 'manual':
            resolution = resolver(conflict, manual_resolution)
        else:
            resolution = resolver(conflict)

        # Mark as resolved
        conflict['resolved'] = True
        conflict['resolution'] = resolution
        conflict['resolved_at'] = datetime.utcnow().isoformat()
        conflict['strategy'] = strategy

        return resolution

    def _resolve_local_wins(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Always choose local version"""
        return conflict['local_data']

    def _resolve_remote_wins(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Always choose remote version"""
        return conflict['remote_data']

    def _resolve_by_timestamp(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Choose version with most recent timestamp"""
        local_time = datetime.fromisoformat(
            conflict['local_data'].get('modified_at', '2000-01-01T00:00:00')
        )
        remote_time = datetime.fromisoformat(
            conflict['remote_data'].get('modified_at', '2000-01-01T00:00:00')
        )

        if local_time > remote_time:
            return conflict['local_data']
        else:
            return conflict['remote_data']

    def _resolve_merge(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to merge both versions"""
        local = conflict['local_data']
        remote = conflict['remote_data']

        # Create merged version
        merged = {
            **remote,  # Start with remote as base
            'modified_at': datetime.utcnow().isoformat(),
            'merge_source': 'automatic'
        }

        # Try to merge content
        local_content = local.get('content', '')
        remote_content = remote.get('content', '')

        if isinstance(local_content, str) and isinstance(remote_content, str):
            # For text content, try three-way merge
            merged['content'] = self._merge_text(local_content, remote_content)
        else:
            # For other types, prefer local
            merged['content'] = local_content

        return merged

    def _merge_text(self, local: str, remote: str) -> str:
        """
        Merge text content

        Args:
            local: Local text
            remote: Remote text

        Returns:
            Merged text
        """
        # If one is empty, return the other
        if not local:
            return remote
        if not remote:
            return local

        # If identical, return as-is
        if local == remote:
            return local

        # Split into lines
        local_lines = local.splitlines()
        remote_lines = remote.splitlines()

        # Use difflib to merge
        merged_lines = []
        matcher = difflib.SequenceMatcher(None, local_lines, remote_lines)

        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == 'equal':
                merged_lines.extend(local_lines[i1:i2])
            elif op == 'replace':
                # Include both versions with conflict markers
                merged_lines.append('<<<<<<< LOCAL')
                merged_lines.extend(local_lines[i1:i2])
                merged_lines.append('=======')
                merged_lines.extend(remote_lines[j1:j2])
                merged_lines.append('>>>>>>> REMOTE')
            elif op == 'delete':
                # Content deleted in remote, keep local
                merged_lines.extend(local_lines[i1:i2])
            elif op == 'insert':
                # Content added in remote, include it
                merged_lines.extend(remote_lines[j1:j2])

        return '\n'.join(merged_lines)

    def _resolve_manual(
        self,
        conflict: Dict[str, Any],
        manual_resolution: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Use manually provided resolution"""
        if not manual_resolution:
            raise ValueError("Manual resolution required")

        return manual_resolution

    def get_pending_conflicts(self) -> List[Dict[str, Any]]:
        """Get all pending conflicts"""
        return [c for c in self.pending_conflicts if not c['resolved']]

    def get_conflict(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        """Get specific conflict"""
        for conflict in self.pending_conflicts:
            if conflict['id'] == conflict_id:
                return conflict

        return None

    def clear_resolved(self):
        """Remove resolved conflicts"""
        self.pending_conflicts = [
            c for c in self.pending_conflicts
            if not c['resolved']
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get conflict statistics"""
        total = len(self.pending_conflicts)
        resolved = sum(1 for c in self.pending_conflicts if c['resolved'])

        return {
            'total_conflicts': total,
            'pending': total - resolved,
            'resolved': resolved
        }
