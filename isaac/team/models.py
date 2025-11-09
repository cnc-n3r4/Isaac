"""Data models for team collaboration."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
import uuid


class PermissionLevel(Enum):
    """Permission levels for team members."""
    OWNER = "owner"         # Full control
    ADMIN = "admin"         # Can manage members and permissions
    WRITE = "write"         # Can share and modify team resources
    READ = "read"           # Can only view team resources
    NONE = "none"           # No access


class ResourceType(Enum):
    """Types of resources that can be shared."""
    WORKSPACE = "workspace"
    COLLECTION = "collection"
    PATTERN = "pattern"
    PIPELINE = "pipeline"
    MEMORY = "memory"
    BUBBLE = "bubble"


@dataclass
class Permission:
    """Permission for a specific resource."""
    resource_id: str
    resource_type: ResourceType
    user_id: str
    level: PermissionLevel
    granted_by: str
    granted_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        """Check if permission is still valid."""
        if self.expires_at is None:
            return True
        return datetime.now() < self.expires_at

    def can_read(self) -> bool:
        """Check if permission allows reading."""
        return self.level in [PermissionLevel.READ, PermissionLevel.WRITE,
                             PermissionLevel.ADMIN, PermissionLevel.OWNER]

    def can_write(self) -> bool:
        """Check if permission allows writing."""
        return self.level in [PermissionLevel.WRITE, PermissionLevel.ADMIN,
                             PermissionLevel.OWNER]

    def can_admin(self) -> bool:
        """Check if permission allows admin actions."""
        return self.level in [PermissionLevel.ADMIN, PermissionLevel.OWNER]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'resource_id': self.resource_id,
            'resource_type': self.resource_type.value,
            'user_id': self.user_id,
            'level': self.level.value,
            'granted_by': self.granted_by,
            'granted_at': self.granted_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }

    @staticmethod
    def from_dict(data: dict) -> 'Permission':
        """Create from dictionary."""
        return Permission(
            resource_id=data['resource_id'],
            resource_type=ResourceType(data['resource_type']),
            user_id=data['user_id'],
            level=PermissionLevel(data['level']),
            granted_by=data['granted_by'],
            granted_at=datetime.fromisoformat(data['granted_at']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
        )


@dataclass
class TeamMember:
    """Member of a team."""
    user_id: str
    username: str
    email: str
    role: PermissionLevel
    joined_at: datetime = field(default_factory=datetime.now)
    invited_by: Optional[str] = None
    last_active: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'joined_at': self.joined_at.isoformat(),
            'invited_by': self.invited_by,
            'last_active': self.last_active.isoformat() if self.last_active else None,
        }

    @staticmethod
    def from_dict(data: dict) -> 'TeamMember':
        """Create from dictionary."""
        return TeamMember(
            user_id=data['user_id'],
            username=data['username'],
            email=data['email'],
            role=PermissionLevel(data['role']),
            joined_at=datetime.fromisoformat(data['joined_at']),
            invited_by=data.get('invited_by'),
            last_active=datetime.fromisoformat(data['last_active']) if data.get('last_active') else None,
        )


@dataclass
class Team:
    """A team that can collaborate and share resources."""
    team_id: str
    name: str
    description: str
    owner_id: str
    created_at: datetime = field(default_factory=datetime.now)
    members: List[TeamMember] = field(default_factory=list)
    settings: Dict = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)

    def __post_init__(self):
        """Initialize team with owner as first member."""
        if not self.members:
            # Add owner as first member if not already present
            owner_exists = any(m.user_id == self.owner_id for m in self.members)
            if not owner_exists:
                self.members.append(TeamMember(
                    user_id=self.owner_id,
                    username=self.settings.get('owner_username', 'owner'),
                    email=self.settings.get('owner_email', ''),
                    role=PermissionLevel.OWNER,
                    joined_at=self.created_at,
                ))

    def get_member(self, user_id: str) -> Optional[TeamMember]:
        """Get a team member by user ID."""
        for member in self.members:
            if member.user_id == user_id:
                return member
        return None

    def add_member(self, member: TeamMember) -> bool:
        """Add a member to the team."""
        if self.get_member(member.user_id):
            return False
        self.members.append(member)
        return True

    def remove_member(self, user_id: str) -> bool:
        """Remove a member from the team."""
        if user_id == self.owner_id:
            return False  # Cannot remove owner

        member = self.get_member(user_id)
        if member:
            self.members.remove(member)
            return True
        return False

    def update_member_role(self, user_id: str, role: PermissionLevel) -> bool:
        """Update a member's role."""
        if user_id == self.owner_id:
            return False  # Cannot change owner role

        member = self.get_member(user_id)
        if member:
            member.role = role
            return True
        return False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'team_id': self.team_id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'created_at': self.created_at.isoformat(),
            'members': [m.to_dict() for m in self.members],
            'settings': self.settings,
            'tags': list(self.tags),
        }

    @staticmethod
    def from_dict(data: dict) -> 'Team':
        """Create from dictionary."""
        team = Team(
            team_id=data['team_id'],
            name=data['name'],
            description=data['description'],
            owner_id=data['owner_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            members=[TeamMember.from_dict(m) for m in data.get('members', [])],
            settings=data.get('settings', {}),
            tags=set(data.get('tags', [])),
        )
        return team


@dataclass
class SharedResource:
    """A resource shared with a team."""
    resource_id: str
    resource_type: ResourceType
    team_id: str
    shared_by: str
    shared_at: datetime = field(default_factory=datetime.now)
    name: str = ""
    description: str = ""
    metadata: Dict = field(default_factory=dict)
    version: int = 1

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'resource_id': self.resource_id,
            'resource_type': self.resource_type.value,
            'team_id': self.team_id,
            'shared_by': self.shared_by,
            'shared_at': self.shared_at.isoformat(),
            'name': self.name,
            'description': self.description,
            'metadata': self.metadata,
            'version': self.version,
        }

    @staticmethod
    def from_dict(data: dict) -> 'SharedResource':
        """Create from dictionary."""
        return SharedResource(
            resource_id=data['resource_id'],
            resource_type=ResourceType(data['resource_type']),
            team_id=data['team_id'],
            shared_by=data['shared_by'],
            shared_at=datetime.fromisoformat(data['shared_at']),
            name=data.get('name', ''),
            description=data.get('description', ''),
            metadata=data.get('metadata', {}),
            version=data.get('version', 1),
        )
