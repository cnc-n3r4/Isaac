"""Integration tests for team collaboration system."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from isaac.team import (
    TeamManager,
    WorkspaceSharer,
    TeamCollections,
    TeamPatternSharing,
    TeamPipelineSharing,
    TeamMemory,
    PermissionSystem,
    TeamMember,
    PermissionLevel,
    ResourceType,
    Permission,
)


class TestTeamCollaboration:
    """Test team collaboration features."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    @pytest.fixture
    def team_manager(self, temp_dir):
        """Create a team manager."""
        return TeamManager(base_dir=str(Path(temp_dir) / "teams"))

    @pytest.fixture
    def workspace_sharer(self, temp_dir):
        """Create a workspace sharer."""
        return WorkspaceSharer(base_dir=str(Path(temp_dir) / "workspaces"))

    @pytest.fixture
    def collections(self, temp_dir):
        """Create team collections."""
        return TeamCollections(base_dir=str(Path(temp_dir) / "collections"))

    @pytest.fixture
    def patterns(self, temp_dir):
        """Create team pattern sharing."""
        return TeamPatternSharing(base_dir=str(Path(temp_dir) / "patterns"))

    @pytest.fixture
    def pipelines(self, temp_dir):
        """Create team pipeline sharing."""
        return TeamPipelineSharing(base_dir=str(Path(temp_dir) / "pipelines"))

    @pytest.fixture
    def memory(self, temp_dir):
        """Create team memory."""
        return TeamMemory(base_dir=str(Path(temp_dir) / "memory"))

    @pytest.fixture
    def permissions(self, temp_dir):
        """Create permission system."""
        return PermissionSystem(base_dir=str(Path(temp_dir) / "permissions"))

    def test_create_team(self, team_manager):
        """Test creating a team."""
        team = team_manager.create_team(
            name="Test Team",
            description="A test team",
            owner_id="user1",
            owner_username="testuser",
            owner_email="test@example.com"
        )

        assert team.name == "Test Team"
        assert team.description == "A test team"
        assert team.owner_id == "user1"
        assert len(team.members) == 1
        assert team.members[0].role == PermissionLevel.OWNER

    def test_add_member(self, team_manager):
        """Test adding a member to a team."""
        team = team_manager.create_team(
            name="Test Team",
            description="A test team",
            owner_id="user1"
        )

        member = TeamMember(
            user_id="user2",
            username="user2",
            email="user2@example.com",
            role=PermissionLevel.WRITE,
            invited_by="user1"
        )

        assert team_manager.add_member(team.team_id, member)

        # Verify member was added
        updated_team = team_manager.get_team(team.team_id)
        assert len(updated_team.members) == 2

    def test_remove_member(self, team_manager):
        """Test removing a member from a team."""
        team = team_manager.create_team(
            name="Test Team",
            description="A test team",
            owner_id="user1"
        )

        member = TeamMember(
            user_id="user2",
            username="user2",
            email="user2@example.com",
            role=PermissionLevel.READ
        )

        team_manager.add_member(team.team_id, member)
        assert team_manager.remove_member(team.team_id, "user2")

        # Verify member was removed
        updated_team = team_manager.get_team(team.team_id)
        assert len(updated_team.members) == 1

    def test_update_member_role(self, team_manager):
        """Test updating a member's role."""
        team = team_manager.create_team(
            name="Test Team",
            description="A test team",
            owner_id="user1"
        )

        member = TeamMember(
            user_id="user2",
            username="user2",
            email="user2@example.com",
            role=PermissionLevel.READ
        )

        team_manager.add_member(team.team_id, member)
        assert team_manager.update_member_role(team.team_id, "user2", PermissionLevel.WRITE)

        # Verify role was updated
        updated_team = team_manager.get_team(team.team_id)
        member = updated_team.get_member("user2")
        assert member.role == PermissionLevel.WRITE

    def test_workspace_sharing(self, team_manager, workspace_sharer):
        """Test workspace sharing."""
        team = team_manager.create_team(
            name="Test Team",
            description="A test team",
            owner_id="user1"
        )

        workspace_data = {
            'git_branch': 'main',
            'open_files': ['file1.py', 'file2.py'],
            'processes': [],
        }

        resource = workspace_sharer.share_workspace(
            team_id=team.team_id,
            workspace_data=workspace_data,
            shared_by="user1",
            name="Test Workspace"
        )

        assert resource.resource_type == ResourceType.WORKSPACE
        assert resource.name == "Test Workspace"

        # Verify workspace can be retrieved
        retrieved = workspace_sharer.get_workspace(resource.resource_id)
        assert retrieved is not None
        assert retrieved['git_branch'] == 'main'

    def test_team_collections(self, team_manager, collections):
        """Test team collections."""
        team = team_manager.create_team(
            name="Test Team",
            description="A test team",
            owner_id="user1"
        )

        # Share a collection
        collection_data = {
            'items': [
                {'title': 'Item 1', 'content': 'Content 1'},
                {'title': 'Item 2', 'content': 'Content 2'},
            ],
            'tags': ['test', 'example'],
        }

        resource = collections.share_collection(
            team_id=team.team_id,
            collection_id="coll1",
            shared_by="user1",
            name="Test Collection",
            content=collection_data
        )

        assert resource.name == "Test Collection"

        # Add an item
        assert collections.add_item(
            team_id=team.team_id,
            collection_id="coll1",
            item={'title': 'Item 3', 'content': 'Content 3'},
            added_by="user1"
        )

        # Verify collection
        retrieved = collections.get_collection(team.team_id, "coll1")
        assert len(retrieved['items']) == 3

    def test_team_patterns(self, team_manager, patterns):
        """Test team pattern sharing."""
        team = team_manager.create_team(
            name="Test Team",
            description="A test team",
            owner_id="user1"
        )

        pattern_data = {
            'pattern_id': 'pat1',
            'name': 'Test Pattern',
            'description': 'A test pattern',
            'pattern_type': 'function',
            'language': 'python',
            'quality_score': 85,
            'usage_count': 0,
        }

        resource = patterns.share_pattern(
            team_id=team.team_id,
            pattern_data=pattern_data,
            shared_by="user1"
        )

        assert resource.name == "Test Pattern"

        # List patterns
        pattern_list = patterns.list_patterns(team.team_id)
        assert len(pattern_list) == 1

        # Update usage
        assert patterns.update_pattern_usage(team.team_id, 'pat1', "user2")

        # Verify usage was updated
        retrieved = patterns.get_pattern(team.team_id, 'pat1')
        assert retrieved['usage_count'] == 1

    def test_team_pipelines(self, team_manager, pipelines):
        """Test team pipeline sharing."""
        team = team_manager.create_team(
            name="Test Team",
            description="A test team",
            owner_id="user1"
        )

        pipeline_data = {
            'pipeline_id': 'pipe1',
            'name': 'Test Pipeline',
            'description': 'A test pipeline',
            'steps': [
                {'name': 'step1', 'command': 'echo "hello"'},
                {'name': 'step2', 'command': 'echo "world"'},
            ],
            'tags': ['test', 'ci'],
            'execution_count': 0,
        }

        resource = pipelines.share_pipeline(
            team_id=team.team_id,
            pipeline_data=pipeline_data,
            shared_by="user1"
        )

        assert resource.name == "Test Pipeline"

        # List pipelines
        pipeline_list = pipelines.list_pipelines(team.team_id)
        assert len(pipeline_list) == 1

        # Get stats
        stats = pipelines.get_pipeline_stats(team.team_id)
        assert stats['total_pipelines'] == 1
        assert stats['average_steps'] == 2

    def test_team_memory(self, team_manager, memory):
        """Test team memory."""
        team = team_manager.create_team(
            name="Test Team",
            description="A test team",
            owner_id="user1"
        )

        # Add memories
        memory_id1 = memory.add_memory(
            team_id=team.team_id,
            user_id="user1",
            memory_type="context",
            content="We decided to use Python for the backend"
        )

        memory_id2 = memory.add_memory(
            team_id=team.team_id,
            user_id="user2",
            memory_type="decision",
            content="We will deploy on AWS"
        )

        assert memory_id1
        assert memory_id2

        # Get memories
        memories = memory.get_memories(team.team_id)
        assert len(memories) == 2

        # Search memories
        results = memory.search_memories(team.team_id, "Python")
        assert len(results) == 1
        assert "Python" in results[0]['content']

    def test_team_conversations(self, team_manager, memory):
        """Test team conversations."""
        team = team_manager.create_team(
            name="Test Team",
            description="A test team",
            owner_id="user1"
        )

        # Create conversation
        conv_id = memory.create_conversation(
            team_id=team.team_id,
            created_by="user1",
            title="Project Discussion"
        )

        assert conv_id

        # Add messages
        memory.add_message(
            conversation_id=conv_id,
            user_id="user1",
            role="user",
            content="What should we use for the database?"
        )

        memory.add_message(
            conversation_id=conv_id,
            user_id="user2",
            role="user",
            content="I suggest PostgreSQL"
        )

        # Get conversation
        conversation = memory.get_conversation(conv_id)
        assert conversation is not None
        assert conversation['message_count'] == 2
        assert len(conversation['messages']) == 2

    def test_permissions(self, permissions):
        """Test permission system."""
        # Grant permission
        permission = Permission(
            resource_id="res1",
            resource_type=ResourceType.WORKSPACE,
            user_id="user1",
            level=PermissionLevel.WRITE,
            granted_by="admin"
        )

        assert permissions.grant_permission(permission)

        # Check permission
        assert permissions.check_permission("res1", "user1", PermissionLevel.READ)
        assert permissions.check_permission("res1", "user1", PermissionLevel.WRITE)
        assert not permissions.check_permission("res1", "user1", PermissionLevel.ADMIN)

        # Update permission
        assert permissions.update_permission_level("res1", "user1", PermissionLevel.ADMIN)

        # Verify update
        assert permissions.check_permission("res1", "user1", PermissionLevel.ADMIN)

        # Revoke permission
        assert permissions.revoke_permission("res1", "user1")

        # Verify revocation
        assert not permissions.check_permission("res1", "user1", PermissionLevel.READ)

    def test_full_collaboration_flow(self, team_manager, workspace_sharer,
                                     collections, permissions):
        """Test a full collaboration flow."""
        # Create team
        team = team_manager.create_team(
            name="Development Team",
            description="Main development team",
            owner_id="alice"
        )

        # Add members
        bob = TeamMember(
            user_id="bob",
            username="bob",
            email="bob@example.com",
            role=PermissionLevel.WRITE,
            invited_by="alice"
        )

        charlie = TeamMember(
            user_id="charlie",
            username="charlie",
            email="charlie@example.com",
            role=PermissionLevel.READ,
            invited_by="alice"
        )

        team_manager.add_member(team.team_id, bob)
        team_manager.add_member(team.team_id, charlie)

        # Share workspace
        workspace_data = {'git_branch': 'feature/new-feature', 'open_files': []}
        workspace_resource = workspace_sharer.share_workspace(
            team_id=team.team_id,
            workspace_data=workspace_data,
            shared_by="alice",
            name="Feature Workspace"
        )

        # Grant permissions
        permissions.grant_team_permissions(
            team_manager, team.team_id,
            workspace_resource.resource_id,
            ResourceType.WORKSPACE,
            "alice"
        )

        # Verify permissions
        assert permissions.can_write(workspace_resource.resource_id, "alice")
        assert permissions.can_write(workspace_resource.resource_id, "bob")
        assert permissions.can_read(workspace_resource.resource_id, "charlie")
        assert not permissions.can_write(workspace_resource.resource_id, "charlie")

        # Share collection
        collection_data = {
            'items': [{'title': 'Design Doc', 'content': 'Architecture overview'}],
            'tags': ['docs'],
        }

        collections.share_collection(
            team_id=team.team_id,
            collection_id="docs",
            shared_by="alice",
            name="Team Documentation",
            content=collection_data
        )

        # Bob adds to collection
        collections.add_item(
            team_id=team.team_id,
            collection_id="docs",
            item={'title': 'API Spec', 'content': 'REST API specification'},
            added_by="bob"
        )

        # Verify collection
        docs = collections.get_collection(team.team_id, "docs")
        assert len(docs['items']) == 2

        # Get team info
        updated_team = team_manager.get_team(team.team_id)
        assert len(updated_team.members) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
