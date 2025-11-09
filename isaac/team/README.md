# Team Collaboration System

The team collaboration system enables seamless sharing of workspaces, knowledge, patterns, pipelines, and AI memory across development teams.

## Features

### 1. Team Management
- Create and manage teams
- Role-based access control (owner, admin, write, read)
- Member invitation and management
- Team activity tracking

### 2. Workspace Sharing
- Share complete workspace contexts (bubbles)
- Import shared workspaces
- Preserve git branch, open files, and processes
- Export/import workspace snapshots

### 3. Team Collections
- Shared knowledge base
- Searchable content with tagging
- Collaborative editing
- Version tracking
- Import/export collections

### 4. Team Patterns
- Share code patterns across team
- Quality scoring and usage tracking
- Pattern search and filtering
- Language-specific patterns
- Pattern statistics and analytics

### 5. Team Pipelines
- Share automation pipelines
- Execution tracking
- Tag-based organization
- Pipeline statistics
- Import pipelines to local workspace

### 6. Team Memory
- Shared AI memory across team
- Team conversations with full history
- Searchable memory context
- Memory types (context, decision, fact, etc.)
- Import/export team memories

### 7. Permission System
- Granular resource permissions
- Permission levels (owner, admin, write, read)
- Expiring permissions support
- Automatic team-wide permission grants
- Resource-specific access control

## Architecture

```
isaac/team/
├── __init__.py              # Module exports
├── models.py                # Data models (Team, Member, Permission, etc.)
├── manager.py               # Team management
├── workspace_sharing.py     # Workspace/bubble sharing
├── team_collections.py      # Shared knowledge base
├── team_patterns.py         # Code pattern sharing
├── team_pipelines.py        # Pipeline sharing
├── team_memory.py           # Shared AI memory
├── permission_system.py     # Access control
└── README.md                # This file
```

## Database Schema

### Teams
- team_id (PK)
- name, description
- owner_id
- created_at
- settings, tags

### Team Members
- team_id, user_id (PK)
- username, email
- role
- joined_at, last_active
- invited_by

### Shared Resources
- resource_id, team_id (PK)
- resource_type (workspace, collection, pattern, pipeline, memory)
- shared_by, shared_at
- name, description, metadata
- version

### Permissions
- permission_id (PK)
- resource_id, user_id
- resource_type
- level (owner, admin, write, read)
- granted_by, granted_at
- expires_at

### Team Memories
- memory_id (PK)
- team_id, user_id
- memory_type
- content, metadata
- created_at, tags

### Team Conversations
- conversation_id (PK)
- team_id
- title
- created_by, created_at
- last_message_at
- message_count, participants

## Command Interface

The `/team` command provides complete access to all collaboration features:

```bash
# Team Management
/team create MyTeam "A collaborative team"
/team list
/team info <team_id>
/team delete <team_id>

# Member Management
/team invite <team_id> <user_id> <email> --role write
/team remove <team_id> <user_id>
/team members <team_id>
/team role <team_id> <user_id> admin

# Workspace Sharing
/team share-workspace <team_id> <bubble_id> --name "Feature Branch"
/team import-workspace <team_id> <resource_id>

# Collections
/team collections list <team_id>
/team collections add <team_id> <item>
/team collections search <team_id> <query>

# Patterns
/team patterns list <team_id>
/team patterns import <team_id> <pattern_id>
/team patterns stats <team_id>

# Pipelines
/team pipelines list <team_id>
/team pipelines import <team_id> <pipeline_id>
/team pipelines stats <team_id>

# Memory
/team memory add <team_id> <type> <content>
/team memory search <team_id> <query>
/team memory conversations <team_id>

# Permissions
/team permissions grant <resource_id> <user_id> read
/team permissions revoke <resource_id> <user_id>
/team permissions list <resource_id>
```

## Usage Examples

### Creating a Team
```python
from isaac.team import TeamManager

manager = TeamManager()
team = manager.create_team(
    name="Backend Team",
    description="Backend development team",
    owner_id="alice",
    owner_username="alice",
    owner_email="alice@example.com"
)
```

### Sharing a Workspace
```python
from isaac.team import WorkspaceSharer
from isaac.bubbles.manager import BubbleManager

sharer = WorkspaceSharer()
bubble_mgr = BubbleManager()

resource = sharer.share_bubble(
    team_id=team.team_id,
    bubble_id="bubble123",
    bubble_manager=bubble_mgr,
    shared_by="alice",
    name="Feature Branch Workspace"
)
```

### Managing Permissions
```python
from isaac.team import PermissionSystem, Permission, PermissionLevel, ResourceType

perms = PermissionSystem()

# Grant permission
permission = Permission(
    resource_id="resource123",
    resource_type=ResourceType.WORKSPACE,
    user_id="bob",
    level=PermissionLevel.WRITE,
    granted_by="alice"
)
perms.grant_permission(permission)

# Check permission
can_write = perms.check_permission("resource123", "bob", PermissionLevel.WRITE)
```

### Sharing Team Memory
```python
from isaac.team import TeamMemory

memory = TeamMemory()

# Add memory
memory_id = memory.add_memory(
    team_id=team.team_id,
    user_id="alice",
    memory_type="decision",
    content="We decided to use PostgreSQL for the database",
    tags=["database", "architecture"]
)

# Search memories
results = memory.search_memories(team.team_id, "PostgreSQL")
```

## Integration with Existing Systems

The team collaboration system integrates with:

- **Bubbles**: Share complete workspace states via `WorkspaceSharer`
- **Collections**: Team-wide shared knowledge base
- **Pattern Library**: Share code patterns across team members
- **Pipelines**: Share automation workflows
- **Memory System**: Extend AI memory across team
- **Command System**: `/team` command for all operations

## Storage Locations

Default storage locations:
- Teams database: `~/.isaac/teams/teams.db`
- Shared workspaces: `~/.isaac/shared_workspaces/`
- Team collections: `~/.isaac/team_collections/<team_id>/`
- Team patterns: `~/.isaac/team_patterns/<team_id>/`
- Team pipelines: `~/.isaac/team_pipelines/<team_id>/`
- Team memory: `~/.isaac/team_memory/team_memory.db`
- Permissions: `~/.isaac/permissions/permissions.db`

## Security Considerations

1. **Role-Based Access Control**: Four permission levels (owner, admin, write, read)
2. **Resource Permissions**: Granular per-resource permissions
3. **Expiring Permissions**: Optional time-based permission expiration
4. **Permission Validation**: All operations check permissions
5. **Owner Protection**: Team owners cannot be removed or demoted

## Performance

- **Database-Backed**: SQLite for efficient queries
- **Indexed Queries**: All common queries use database indexes
- **Lazy Loading**: Resources loaded on demand
- **Batch Operations**: Efficient bulk operations support
- **Caching**: Future enhancement for frequently accessed data

## Testing

Comprehensive integration tests cover:
- Team creation and management
- Member operations
- Resource sharing workflows
- Permission system
- All collaboration features
- Full end-to-end scenarios

Run tests:
```bash
pytest tests/integration/test_team_collaboration.py -v
```

## Future Enhancements

- Real-time synchronization
- Conflict resolution for concurrent edits
- Team activity feed
- Resource version history
- Advanced search with filters
- Team analytics dashboard
- Mobile companion app
- Web-based team portal
