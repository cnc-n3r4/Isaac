"""Team manager for creating and managing teams."""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import Team, TeamMember, PermissionLevel, SharedResource, ResourceType


class TeamManager:
    """Manages teams and team membership."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize team manager.

        Args:
            base_dir: Base directory for team storage (default: ~/.isaac/teams/)
        """
        self.base_dir = Path(base_dir or os.path.expanduser("~/.isaac/teams"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / "teams.db"
        self._init_db()

    def _init_db(self):
        """Initialize the database."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    team_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    settings TEXT,
                    tags TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS team_members (
                    team_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    email TEXT,
                    role TEXT NOT NULL,
                    joined_at TEXT NOT NULL,
                    invited_by TEXT,
                    last_active TEXT,
                    PRIMARY KEY (team_id, user_id),
                    FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS shared_resources (
                    resource_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    team_id TEXT NOT NULL,
                    shared_by TEXT NOT NULL,
                    shared_at TEXT NOT NULL,
                    name TEXT,
                    description TEXT,
                    metadata TEXT,
                    version INTEGER DEFAULT 1,
                    PRIMARY KEY (resource_id, team_id),
                    FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_team_members_user
                ON team_members(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_shared_resources_team
                ON shared_resources(team_id)
            """)
            conn.commit()

    def create_team(self, name: str, description: str, owner_id: str,
                   owner_username: str = "owner", owner_email: str = "") -> Team:
        """Create a new team.

        Args:
            name: Team name
            description: Team description
            owner_id: Owner user ID
            owner_username: Owner username
            owner_email: Owner email

        Returns:
            Created Team object
        """
        team_id = str(uuid.uuid4())
        team = Team(
            team_id=team_id,
            name=name,
            description=description,
            owner_id=owner_id,
            settings={
                'owner_username': owner_username,
                'owner_email': owner_email,
            }
        )

        # Save to database
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT INTO teams (team_id, name, description, owner_id, created_at, settings, tags)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (team_id, name, description, owner_id, team.created_at.isoformat(),
                 json.dumps(team.settings), json.dumps(list(team.tags)))
            )

            # Add owner as member
            owner = team.members[0]
            conn.execute(
                """INSERT INTO team_members (team_id, user_id, username, email, role, joined_at, invited_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (team_id, owner.user_id, owner.username, owner.email, owner.role.value,
                 owner.joined_at.isoformat(), owner.invited_by)
            )
            conn.commit()

        return team

    def get_team(self, team_id: str) -> Optional[Team]:
        """Get a team by ID.

        Args:
            team_id: Team ID

        Returns:
            Team object or None if not found
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM teams WHERE team_id = ?", (team_id,)
            ).fetchone()

            if not row:
                return None

            # Get team members
            member_rows = conn.execute(
                "SELECT * FROM team_members WHERE team_id = ?", (team_id,)
            ).fetchall()

            members = [
                TeamMember(
                    user_id=m['user_id'],
                    username=m['username'],
                    email=m['email'] or '',
                    role=PermissionLevel(m['role']),
                    joined_at=datetime.fromisoformat(m['joined_at']),
                    invited_by=m['invited_by'],
                    last_active=datetime.fromisoformat(m['last_active']) if m['last_active'] else None,
                )
                for m in member_rows
            ]

            team = Team(
                team_id=row['team_id'],
                name=row['name'],
                description=row['description'] or '',
                owner_id=row['owner_id'],
                created_at=datetime.fromisoformat(row['created_at']),
                members=members,
                settings=json.loads(row['settings']) if row['settings'] else {},
                tags=set(json.loads(row['tags'])) if row['tags'] else set(),
            )

            return team

    def list_teams(self, user_id: Optional[str] = None) -> List[Team]:
        """List all teams, optionally filtered by user membership.

        Args:
            user_id: Optional user ID to filter teams

        Returns:
            List of Team objects
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row

            if user_id:
                rows = conn.execute("""
                    SELECT DISTINCT t.* FROM teams t
                    JOIN team_members tm ON t.team_id = tm.team_id
                    WHERE tm.user_id = ?
                    ORDER BY t.created_at DESC
                """, (user_id,)).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM teams ORDER BY created_at DESC"
                ).fetchall()

            teams = []
            for row in rows:
                team = self.get_team(row['team_id'])
                if team:
                    teams.append(team)

            return teams

    def delete_team(self, team_id: str) -> bool:
        """Delete a team.

        Args:
            team_id: Team ID

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("DELETE FROM teams WHERE team_id = ?", (team_id,))
            conn.commit()
            return cursor.rowcount > 0

    def add_member(self, team_id: str, member: TeamMember) -> bool:
        """Add a member to a team.

        Args:
            team_id: Team ID
            member: TeamMember object

        Returns:
            True if added, False if already exists
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """INSERT INTO team_members (team_id, user_id, username, email, role, joined_at, invited_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (team_id, member.user_id, member.username, member.email, member.role.value,
                     member.joined_at.isoformat(), member.invited_by)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def remove_member(self, team_id: str, user_id: str) -> bool:
        """Remove a member from a team.

        Args:
            team_id: Team ID
            user_id: User ID

        Returns:
            True if removed, False if not found or is owner
        """
        # Check if user is owner
        team = self.get_team(team_id)
        if not team or team.owner_id == user_id:
            return False

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "DELETE FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_member_role(self, team_id: str, user_id: str, role: PermissionLevel) -> bool:
        """Update a member's role.

        Args:
            team_id: Team ID
            user_id: User ID
            role: New role

        Returns:
            True if updated, False if not found or is owner
        """
        # Check if user is owner
        team = self.get_team(team_id)
        if not team or team.owner_id == user_id:
            return False

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "UPDATE team_members SET role = ? WHERE team_id = ? AND user_id = ?",
                (role.value, team_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def share_resource(self, resource: SharedResource) -> bool:
        """Share a resource with a team.

        Args:
            resource: SharedResource object

        Returns:
            True if shared, False on error
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO shared_resources
                       (resource_id, resource_type, team_id, shared_by, shared_at, name, description, metadata, version)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (resource.resource_id, resource.resource_type.value, resource.team_id,
                     resource.shared_by, resource.shared_at.isoformat(), resource.name,
                     resource.description, json.dumps(resource.metadata), resource.version)
                )
                conn.commit()
                return True
        except Exception:
            return False

    def unshare_resource(self, resource_id: str, team_id: str) -> bool:
        """Unshare a resource from a team.

        Args:
            resource_id: Resource ID
            team_id: Team ID

        Returns:
            True if unshared, False if not found
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "DELETE FROM shared_resources WHERE resource_id = ? AND team_id = ?",
                (resource_id, team_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_shared_resources(self, team_id: str,
                            resource_type: Optional[ResourceType] = None) -> List[SharedResource]:
        """Get shared resources for a team.

        Args:
            team_id: Team ID
            resource_type: Optional resource type filter

        Returns:
            List of SharedResource objects
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row

            if resource_type:
                rows = conn.execute(
                    """SELECT * FROM shared_resources
                       WHERE team_id = ? AND resource_type = ?
                       ORDER BY shared_at DESC""",
                    (team_id, resource_type.value)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM shared_resources WHERE team_id = ? ORDER BY shared_at DESC",
                    (team_id,)
                ).fetchall()

            resources = []
            for row in rows:
                resources.append(SharedResource(
                    resource_id=row['resource_id'],
                    resource_type=ResourceType(row['resource_type']),
                    team_id=row['team_id'],
                    shared_by=row['shared_by'],
                    shared_at=datetime.fromisoformat(row['shared_at']),
                    name=row['name'] or '',
                    description=row['description'] or '',
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    version=row['version'] or 1,
                ))

            return resources

    def update_member_activity(self, team_id: str, user_id: str):
        """Update a member's last activity timestamp.

        Args:
            team_id: Team ID
            user_id: User ID
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "UPDATE team_members SET last_active = ? WHERE team_id = ? AND user_id = ?",
                (datetime.now().isoformat(), team_id, user_id)
            )
            conn.commit()
