"""Permission system for team collaboration access control."""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import os

from .models import Permission, PermissionLevel, ResourceType


class PermissionSystem:
    """Manages permissions for team resources."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize permission system.

        Args:
            base_dir: Base directory for permissions (default: ~/.isaac/permissions/)
        """
        self.base_dir = Path(base_dir or os.path.expanduser("~/.isaac/permissions"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / "permissions.db"
        self._init_db()

    def _init_db(self):
        """Initialize the database."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS permissions (
                    permission_id TEXT PRIMARY KEY,
                    resource_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    level TEXT NOT NULL,
                    granted_by TEXT NOT NULL,
                    granted_at TEXT NOT NULL,
                    expires_at TEXT,
                    UNIQUE(resource_id, user_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_permissions_resource
                ON permissions(resource_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_permissions_user
                ON permissions(user_id)
            """)
            conn.commit()

    def grant_permission(self, permission: Permission) -> bool:
        """Grant a permission.

        Args:
            permission: Permission object

        Returns:
            True if granted, False on error
        """
        import uuid
        permission_id = str(uuid.uuid4())

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO permissions
                       (permission_id, resource_id, resource_type, user_id, level, granted_by, granted_at, expires_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (permission_id, permission.resource_id, permission.resource_type.value,
                     permission.user_id, permission.level.value, permission.granted_by,
                     permission.granted_at.isoformat(),
                     permission.expires_at.isoformat() if permission.expires_at else None)
                )
                conn.commit()
                return True
        except Exception:
            return False

    def revoke_permission(self, resource_id: str, user_id: str) -> bool:
        """Revoke a permission.

        Args:
            resource_id: Resource ID
            user_id: User ID

        Returns:
            True if revoked, False if not found
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "DELETE FROM permissions WHERE resource_id = ? AND user_id = ?",
                (resource_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_permission(self, resource_id: str, user_id: str) -> Optional[Permission]:
        """Get a specific permission.

        Args:
            resource_id: Resource ID
            user_id: User ID

        Returns:
            Permission object or None if not found
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM permissions WHERE resource_id = ? AND user_id = ?",
                (resource_id, user_id)
            ).fetchone()

            if not row:
                return None

            permission = Permission(
                resource_id=row['resource_id'],
                resource_type=ResourceType(row['resource_type']),
                user_id=row['user_id'],
                level=PermissionLevel(row['level']),
                granted_by=row['granted_by'],
                granted_at=datetime.fromisoformat(row['granted_at']),
                expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
            )

            return permission

    def check_permission(self, resource_id: str, user_id: str,
                        required_level: PermissionLevel) -> bool:
        """Check if a user has the required permission level.

        Args:
            resource_id: Resource ID
            user_id: User ID
            required_level: Required permission level

        Returns:
            True if user has permission, False otherwise
        """
        permission = self.get_permission(resource_id, user_id)
        if not permission:
            return False

        # Check if permission is valid
        if not permission.is_valid():
            return False

        # Check permission level hierarchy
        level_hierarchy = {
            PermissionLevel.NONE: 0,
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.ADMIN: 3,
            PermissionLevel.OWNER: 4,
        }

        user_level = level_hierarchy.get(permission.level, 0)
        required = level_hierarchy.get(required_level, 0)

        return user_level >= required

    def list_permissions(self, resource_id: Optional[str] = None,
                        user_id: Optional[str] = None,
                        resource_type: Optional[ResourceType] = None) -> List[Permission]:
        """List permissions.

        Args:
            resource_id: Optional resource ID filter
            user_id: Optional user ID filter
            resource_type: Optional resource type filter

        Returns:
            List of Permission objects
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM permissions WHERE 1=1"
            params = []

            if resource_id:
                query += " AND resource_id = ?"
                params.append(resource_id)

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            if resource_type:
                query += " AND resource_type = ?"
                params.append(resource_type.value)

            rows = conn.execute(query, params).fetchall()

            permissions = []
            for row in rows:
                permission = Permission(
                    resource_id=row['resource_id'],
                    resource_type=ResourceType(row['resource_type']),
                    user_id=row['user_id'],
                    level=PermissionLevel(row['level']),
                    granted_by=row['granted_by'],
                    granted_at=datetime.fromisoformat(row['granted_at']),
                    expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
                )

                # Only include valid permissions
                if permission.is_valid():
                    permissions.append(permission)

            return permissions

    def update_permission_level(self, resource_id: str, user_id: str,
                               new_level: PermissionLevel) -> bool:
        """Update a permission level.

        Args:
            resource_id: Resource ID
            user_id: User ID
            new_level: New permission level

        Returns:
            True if updated, False if not found
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "UPDATE permissions SET level = ? WHERE resource_id = ? AND user_id = ?",
                (new_level.value, resource_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def cleanup_expired_permissions(self) -> int:
        """Remove expired permissions.

        Returns:
            Number of permissions removed
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "DELETE FROM permissions WHERE expires_at IS NOT NULL AND expires_at < ?",
                (datetime.now().isoformat(),)
            )
            conn.commit()
            return cursor.rowcount

    def get_resource_permissions(self, resource_id: str) -> Dict[str, PermissionLevel]:
        """Get all permissions for a resource.

        Args:
            resource_id: Resource ID

        Returns:
            Dictionary mapping user IDs to permission levels
        """
        permissions = self.list_permissions(resource_id=resource_id)
        return {p.user_id: p.level for p in permissions}

    def get_user_permissions(self, user_id: str,
                            resource_type: Optional[ResourceType] = None) -> Dict[str, PermissionLevel]:
        """Get all permissions for a user.

        Args:
            user_id: User ID
            resource_type: Optional resource type filter

        Returns:
            Dictionary mapping resource IDs to permission levels
        """
        permissions = self.list_permissions(user_id=user_id, resource_type=resource_type)
        return {p.resource_id: p.level for p in permissions}

    def grant_team_permissions(self, team_manager, team_id: str, resource_id: str,
                              resource_type: ResourceType, granted_by: str,
                              default_level: PermissionLevel = PermissionLevel.READ) -> int:
        """Grant permissions to all team members for a resource.

        Args:
            team_manager: TeamManager instance
            team_id: Team ID
            resource_id: Resource ID
            resource_type: Resource type
            granted_by: User ID granting permissions
            default_level: Default permission level for members

        Returns:
            Number of permissions granted
        """
        team = team_manager.get_team(team_id)
        if not team:
            return 0

        count = 0
        for member in team.members:
            # Grant permission based on member role
            if member.role == PermissionLevel.OWNER:
                level = PermissionLevel.OWNER
            elif member.role == PermissionLevel.ADMIN:
                level = PermissionLevel.ADMIN
            elif member.role == PermissionLevel.WRITE:
                level = PermissionLevel.WRITE
            else:
                level = default_level

            permission = Permission(
                resource_id=resource_id,
                resource_type=resource_type,
                user_id=member.user_id,
                level=level,
                granted_by=granted_by,
            )

            if self.grant_permission(permission):
                count += 1

        return count

    def can_read(self, resource_id: str, user_id: str) -> bool:
        """Check if user can read a resource."""
        permission = self.get_permission(resource_id, user_id)
        return permission.can_read() if permission else False

    def can_write(self, resource_id: str, user_id: str) -> bool:
        """Check if user can write to a resource."""
        permission = self.get_permission(resource_id, user_id)
        return permission.can_write() if permission else False

    def can_admin(self, resource_id: str, user_id: str) -> bool:
        """Check if user can administer a resource."""
        permission = self.get_permission(resource_id, user_id)
        return permission.can_admin() if permission else False
