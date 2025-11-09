"""Team collaboration command implementation."""

import os
from typing import List

from isaac.core.flag_parser import FlagParser
from isaac.team import (
    PermissionLevel,
    PermissionSystem,
    ResourceType,
    TeamCollections,
    TeamManager,
    TeamMember,
    TeamMemory,
    TeamPatternSharing,
    TeamPipelineSharing,
    WorkspaceSharer,
)


class TeamCommand:
    """Manage team collaboration and shared resources."""

    def __init__(self):
        """Initialize team command."""
        self.user_id = os.environ.get("USER", "default_user")
        self.username = os.environ.get("USER", "default_user")
        self.email = os.environ.get("EMAIL", f"{self.user_id}@example.com")

        self.team_manager = TeamManager()
        self.workspace_sharer = WorkspaceSharer()
        self.collections = TeamCollections()
        self.patterns = TeamPatternSharing()
        self.pipelines = TeamPipelineSharing()
        self.memory = TeamMemory()
        self.permissions = PermissionSystem()

    def run(self, args: List[str]) -> str:
        """Run team command.

        Args:
            args: Command arguments

        Returns:
            Command output
        """
        if not args:
            return self._show_help()

        subcommand = args[0]
        subargs = args[1:]

        # Team management commands
        if subcommand == "create":
            return self._create_team(subargs)
        elif subcommand == "list":
            return self._list_teams(subargs)
        elif subcommand == "info":
            return self._team_info(subargs)
        elif subcommand == "delete":
            return self._delete_team(subargs)

        # Member management
        elif subcommand == "invite":
            return self._invite_member(subargs)
        elif subcommand == "remove":
            return self._remove_member(subargs)
        elif subcommand == "members":
            return self._list_members(subargs)
        elif subcommand == "role":
            return self._update_role(subargs)

        # Resource sharing
        elif subcommand == "share":
            return self._share_resource(subargs)
        elif subcommand == "unshare":
            return self._unshare_resource(subargs)
        elif subcommand == "resources":
            return self._list_resources(subargs)

        # Workspace sharing
        elif subcommand == "share-workspace":
            return self._share_workspace(subargs)
        elif subcommand == "import-workspace":
            return self._import_workspace(subargs)

        # Collections
        elif subcommand == "collections":
            return self._manage_collections(subargs)

        # Patterns
        elif subcommand == "patterns":
            return self._manage_patterns(subargs)

        # Pipelines
        elif subcommand == "pipelines":
            return self._manage_pipelines(subargs)

        # Memory
        elif subcommand == "memory":
            return self._manage_memory(subargs)

        # Permissions
        elif subcommand == "permissions":
            return self._manage_permissions(subargs)

        else:
            return f"Unknown subcommand: {subcommand}\nUse '/team help' for usage."

    def _show_help(self) -> str:
        """Show help message."""
        return """Team Collaboration Commands:

TEAM MANAGEMENT:
  /team create <name> <description>    Create a new team
  /team list                           List your teams
  /team info <team_id>                 Show team information
  /team delete <team_id>               Delete a team

MEMBER MANAGEMENT:
  /team invite <team_id> <user_id> <email> [--role ROLE]
                                       Invite a member to the team
  /team remove <team_id> <user_id>    Remove a member from the team
  /team members <team_id>              List team members
  /team role <team_id> <user_id> <role>
                                       Update a member's role

RESOURCE SHARING:
  /team share <team_id> <type> <id>   Share a resource with the team
  /team unshare <team_id> <type> <id> Unshare a resource
  /team resources <team_id> [--type TYPE]
                                       List shared resources

WORKSPACE SHARING:
  /team share-workspace <team_id> <bubble_id> [--name NAME]
                                       Share a workspace/bubble
  /team import-workspace <team_id> <resource_id> [--name NAME]
                                       Import a shared workspace

COLLECTIONS:
  /team collections list <team_id>     List team collections
  /team collections add <team_id> <item>
                                       Add item to team collection
  /team collections search <team_id> <query>
                                       Search team collections

PATTERNS:
  /team patterns list <team_id>        List team patterns
  /team patterns import <team_id> <pattern_id>
                                       Import a pattern
  /team patterns stats <team_id>       Show pattern statistics

PIPELINES:
  /team pipelines list <team_id>       List team pipelines
  /team pipelines import <team_id> <pipeline_id>
                                       Import a pipeline
  /team pipelines stats <team_id>      Show pipeline statistics

MEMORY:
  /team memory add <team_id> <type> <content>
                                       Add to team memory
  /team memory search <team_id> <query>
                                       Search team memory
  /team memory conversations <team_id> List team conversations

PERMISSIONS:
  /team permissions grant <resource_id> <user_id> <level>
                                       Grant permission
  /team permissions revoke <resource_id> <user_id>
                                       Revoke permission
  /team permissions list <resource_id> List resource permissions

ROLES: owner, admin, write, read
RESOURCE TYPES: workspace, collection, pattern, pipeline, memory
"""

    def _create_team(self, args: List[str]) -> str:
        """Create a new team."""
        if len(args) < 2:
            return "Usage: /team create <name> <description>"

        name = args[0]
        description = " ".join(args[1:])

        team = self.team_manager.create_team(
            name=name,
            description=description,
            owner_id=self.user_id,
            owner_username=self.username,
            owner_email=self.email,
        )

        return f"""✓ Team created successfully!

Team ID: {team.team_id}
Name: {team.name}
Description: {team.description}
Owner: {self.username}

Share the Team ID with others to invite them to join!
"""

    def _list_teams(self, args: List[str]) -> str:
        """List teams."""
        teams = self.team_manager.list_teams(user_id=self.user_id)

        if not teams:
            return "You are not a member of any teams.\nCreate one with: /team create <name> <description>"

        output = [f"Your Teams ({len(teams)}):\n"]

        for team in teams:
            member = team.get_member(self.user_id)
            role = member.role.value if member else "unknown"

            output.append(f"  {team.name}")
            output.append(f"    ID: {team.team_id}")
            output.append(f"    Role: {role}")
            output.append(f"    Members: {len(team.members)}")
            output.append(f"    Created: {team.created_at.strftime('%Y-%m-%d')}")
            output.append("")

        return "\n".join(output)

    def _team_info(self, args: List[str]) -> str:
        """Show team information."""
        if not args:
            return "Usage: /team info <team_id>"

        team_id = args[0]
        team = self.team_manager.get_team(team_id)

        if not team:
            return f"Team not found: {team_id}"

        # Get shared resources
        resources = self.team_manager.get_shared_resources(team_id)

        output = [f"Team: {team.name}"]
        output.append(f"ID: {team.team_id}")
        output.append(f"Description: {team.description}")
        output.append(f"Created: {team.created_at.strftime('%Y-%m-%d %H:%M')}")
        output.append(f"\nMembers ({len(team.members)}):")

        for member in team.members:
            last_active = member.last_active.strftime("%Y-%m-%d") if member.last_active else "Never"
            output.append(
                f"  • {member.username} ({member.role.value}) - Last active: {last_active}"
            )

        output.append(f"\nShared Resources ({len(resources)}):")
        resource_counts = {}
        for res in resources:
            resource_counts[res.resource_type.value] = (
                resource_counts.get(res.resource_type.value, 0) + 1
            )

        for rtype, count in resource_counts.items():
            output.append(f"  • {rtype}: {count}")

        return "\n".join(output)

    def _delete_team(self, args: List[str]) -> str:
        """Delete a team."""
        if not args:
            return "Usage: /team delete <team_id>"

        team_id = args[0]
        team = self.team_manager.get_team(team_id)

        if not team:
            return f"Team not found: {team_id}"

        # Check if user is owner
        if team.owner_id != self.user_id:
            return "Only the team owner can delete the team."

        if self.team_manager.delete_team(team_id):
            return f"✓ Team '{team.name}' deleted successfully."
        else:
            return "Failed to delete team."

    def _invite_member(self, args: List[str]) -> str:
        """Invite a member to a team."""
        parser = FlagParser()
        parsed = parser.parse(args)

        if len(parsed.positional) < 3:
            return "Usage: /team invite <team_id> <user_id> <email> [--role ROLE]"

        team_id = parsed.positional[0]
        new_user_id = parsed.positional[1]
        new_email = parsed.positional[2]
        role = PermissionLevel(parsed.flags.get("role", "read"))

        team = self.team_manager.get_team(team_id)
        if not team:
            return f"Team not found: {team_id}"

        # Check if current user is admin or owner
        current_member = team.get_member(self.user_id)
        if not current_member or current_member.role not in [
            PermissionLevel.OWNER,
            PermissionLevel.ADMIN,
        ]:
            return "Only team owners and admins can invite members."

        # Create new member
        new_member = TeamMember(
            user_id=new_user_id,
            username=new_user_id,  # Could be enhanced with actual username lookup
            email=new_email,
            role=role,
            invited_by=self.user_id,
        )

        if self.team_manager.add_member(team_id, new_member):
            return f"✓ Invited {new_user_id} to team '{team.name}' as {role.value}."
        else:
            return f"Failed to invite member. They may already be in the team."

    def _remove_member(self, args: List[str]) -> str:
        """Remove a member from a team."""
        if len(args) < 2:
            return "Usage: /team remove <team_id> <user_id>"

        team_id = args[0]
        user_id = args[1]

        team = self.team_manager.get_team(team_id)
        if not team:
            return f"Team not found: {team_id}"

        # Check if current user is admin or owner
        current_member = team.get_member(self.user_id)
        if not current_member or current_member.role not in [
            PermissionLevel.OWNER,
            PermissionLevel.ADMIN,
        ]:
            return "Only team owners and admins can remove members."

        if self.team_manager.remove_member(team_id, user_id):
            return f"✓ Removed {user_id} from team '{team.name}'."
        else:
            return "Failed to remove member. They may not be in the team or are the owner."

    def _list_members(self, args: List[str]) -> str:
        """List team members."""
        if not args:
            return "Usage: /team members <team_id>"

        team_id = args[0]
        team = self.team_manager.get_team(team_id)

        if not team:
            return f"Team not found: {team_id}"

        output = [f"Members of '{team.name}' ({len(team.members)}):\n"]

        for member in sorted(team.members, key=lambda m: m.joined_at):
            joined = member.joined_at.strftime("%Y-%m-%d")
            last_active = member.last_active.strftime("%Y-%m-%d") if member.last_active else "Never"

            output.append(f"  {member.username}")
            output.append(f"    Role: {member.role.value}")
            output.append(f"    Email: {member.email}")
            output.append(f"    Joined: {joined}")
            output.append(f"    Last Active: {last_active}")
            if member.invited_by:
                output.append(f"    Invited by: {member.invited_by}")
            output.append("")

        return "\n".join(output)

    def _update_role(self, args: List[str]) -> str:
        """Update a member's role."""
        if len(args) < 3:
            return "Usage: /team role <team_id> <user_id> <role>"

        team_id = args[0]
        user_id = args[1]
        role = PermissionLevel(args[2])

        team = self.team_manager.get_team(team_id)
        if not team:
            return f"Team not found: {team_id}"

        # Check if current user is owner
        if team.owner_id != self.user_id:
            return "Only the team owner can change member roles."

        if self.team_manager.update_member_role(team_id, user_id, role):
            return f"✓ Updated {user_id}'s role to {role.value}."
        else:
            return "Failed to update role. User may not be in the team or is the owner."

    def _share_resource(self, args: List[str]) -> str:
        """Share a resource with a team."""
        if len(args) < 3:
            return "Usage: /team share <team_id> <type> <id>"

        team_id = args[0]
        resource_type = ResourceType(args[1])
        resource_id = args[2]

        # This would integrate with actual resource managers
        from isaac.team.models import SharedResource

        resource = SharedResource(
            resource_id=resource_id,
            resource_type=resource_type,
            team_id=team_id,
            shared_by=self.user_id,
            name=f"{resource_type.value} {resource_id}",
        )

        if self.team_manager.share_resource(resource):
            # Grant permissions to all team members
            self.permissions.grant_team_permissions(
                self.team_manager, team_id, resource_id, resource_type, self.user_id
            )
            return f"✓ Shared {resource_type.value} with team."
        else:
            return "Failed to share resource."

    def _unshare_resource(self, args: List[str]) -> str:
        """Unshare a resource from a team."""
        if len(args) < 3:
            return "Usage: /team unshare <team_id> <type> <id>"

        team_id = args[0]
        resource_type = ResourceType(args[1])
        resource_id = args[2]

        if self.team_manager.unshare_resource(resource_id, team_id):
            return f"✓ Unshared {resource_type.value} from team."
        else:
            return "Failed to unshare resource."

    def _list_resources(self, args: List[str]) -> str:
        """List shared resources."""
        parser = FlagParser()
        parsed = parser.parse(args)

        if not parsed.positional:
            return "Usage: /team resources <team_id> [--type TYPE]"

        team_id = parsed.positional[0]
        resource_type = ResourceType(parsed.flags.get("type")) if "type" in parsed.flags else None

        resources = self.team_manager.get_shared_resources(team_id, resource_type)

        if not resources:
            return "No shared resources found."

        output = [f"Shared Resources ({len(resources)}):\n"]

        for res in resources:
            output.append(f"  {res.name}")
            output.append(f"    Type: {res.resource_type.value}")
            output.append(f"    ID: {res.resource_id}")
            output.append(f"    Shared by: {res.shared_by}")
            output.append(f"    Shared at: {res.shared_at.strftime('%Y-%m-%d %H:%M')}")
            if res.description:
                output.append(f"    Description: {res.description}")
            output.append("")

        return "\n".join(output)

    def _share_workspace(self, args: List[str]) -> str:
        """Share a workspace/bubble."""
        parser = FlagParser()
        parsed = parser.parse(args)

        if len(parsed.positional) < 2:
            return "Usage: /team share-workspace <team_id> <bubble_id> [--name NAME]"

        team_id = parsed.positional[0]
        bubble_id = parsed.positional[1]
        name = parsed.flags.get("name", "")

        # Would integrate with actual bubble manager
        try:
            from isaac.bubbles.manager import BubbleManager

            bubble_manager = BubbleManager()

            resource = self.workspace_sharer.share_bubble(
                team_id, bubble_id, bubble_manager, self.user_id, name
            )

            if resource:
                self.team_manager.share_resource(resource)
                return f"✓ Shared workspace '{resource.name}' with team."
            else:
                return "Bubble not found."
        except Exception as e:
            return f"Error sharing workspace: {str(e)}"

    def _import_workspace(self, args: List[str]) -> str:
        """Import a shared workspace."""
        parser = FlagParser()
        parsed = parser.parse(args)

        if len(parsed.positional) < 2:
            return "Usage: /team import-workspace <team_id> <resource_id> [--name NAME]"

        parsed.positional[0]
        resource_id = parsed.positional[1]
        name = parsed.flags.get("name")

        try:
            from isaac.bubbles.manager import BubbleManager

            bubble_manager = BubbleManager()

            bubble_id = self.workspace_sharer.import_workspace(
                resource_id, bubble_manager, self.user_id, name
            )

            if bubble_id:
                return f"✓ Imported workspace as bubble: {bubble_id}"
            else:
                return "Failed to import workspace."
        except Exception as e:
            return f"Error importing workspace: {str(e)}"

    def _manage_collections(self, args: List[str]) -> str:
        """Manage team collections."""
        if not args:
            return "Usage: /team collections <list|add|search> <team_id> ..."

        subcommand = args[0]

        if subcommand == "list":
            if len(args) < 2:
                return "Usage: /team collections list <team_id>"
            collections = self.collections.list_collections(args[1])
            if not collections:
                return "No collections found."
            output = ["Team Collections:\n"]
            for coll in collections:
                output.append(f"  {coll['name']}")
                output.append(f"    ID: {coll['collection_id']}")
                output.append(f"    Items: {coll['item_count']}")
                output.append("")
            return "\n".join(output)

        elif subcommand == "search":
            if len(args) < 3:
                return "Usage: /team collections search <team_id> <query>"
            results = self.collections.search_collections(args[1], " ".join(args[2:]))
            return f"Found {len(results)} results."

        else:
            return "Unknown collections subcommand."

    def _manage_patterns(self, args: List[str]) -> str:
        """Manage team patterns."""
        if not args:
            return "Usage: /team patterns <list|stats> <team_id>"

        subcommand = args[0]

        if subcommand == "list":
            if len(args) < 2:
                return "Usage: /team patterns list <team_id>"
            patterns = self.patterns.list_patterns(args[1])
            if not patterns:
                return "No patterns found."
            output = [f"Team Patterns ({len(patterns)}):\n"]
            for pat in patterns[:20]:  # Show first 20
                output.append(f"  {pat['name']}")
                output.append(f"    Type: {pat.get('pattern_type', 'unknown')}")
                output.append(f"    Quality: {pat.get('quality_score', 0):.1f}")
                output.append(f"    Usage: {pat.get('usage_count', 0)}")
                output.append("")
            return "\n".join(output)

        elif subcommand == "stats":
            if len(args) < 2:
                return "Usage: /team patterns stats <team_id>"
            stats = self.patterns.get_pattern_stats(args[1])
            output = ["Pattern Statistics:\n"]
            output.append(f"Total patterns: {stats['total_patterns']}")
            output.append(f"Average quality: {stats['average_quality']:.1f}")
            output.append(f"Total usage: {stats['total_usage']}")
            return "\n".join(output)

        else:
            return "Unknown patterns subcommand."

    def _manage_pipelines(self, args: List[str]) -> str:
        """Manage team pipelines."""
        if not args:
            return "Usage: /team pipelines <list|stats> <team_id>"

        subcommand = args[0]

        if subcommand == "list":
            if len(args) < 2:
                return "Usage: /team pipelines list <team_id>"
            pipelines = self.pipelines.list_pipelines(args[1])
            if not pipelines:
                return "No pipelines found."
            output = [f"Team Pipelines ({len(pipelines)}):\n"]
            for pipe in pipelines[:20]:  # Show first 20
                output.append(f"  {pipe['name']}")
                output.append(f"    Steps: {pipe['step_count']}")
                output.append(f"    Executions: {pipe.get('execution_count', 0)}")
                output.append("")
            return "\n".join(output)

        elif subcommand == "stats":
            if len(args) < 2:
                return "Usage: /team pipelines stats <team_id>"
            stats = self.pipelines.get_pipeline_stats(args[1])
            output = ["Pipeline Statistics:\n"]
            output.append(f"Total pipelines: {stats['total_pipelines']}")
            output.append(f"Total executions: {stats['total_executions']}")
            output.append(f"Average steps: {stats['average_steps']:.1f}")
            return "\n".join(output)

        else:
            return "Unknown pipelines subcommand."

    def _manage_memory(self, args: List[str]) -> str:
        """Manage team memory."""
        if not args:
            return "Usage: /team memory <add|search|conversations> <team_id> ..."

        subcommand = args[0]

        if subcommand == "add":
            if len(args) < 4:
                return "Usage: /team memory add <team_id> <type> <content>"
            team_id = args[1]
            memory_type = args[2]
            content = " ".join(args[3:])
            memory_id = self.memory.add_memory(team_id, self.user_id, memory_type, content)
            return f"✓ Added to team memory: {memory_id}"

        elif subcommand == "search":
            if len(args) < 3:
                return "Usage: /team memory search <team_id> <query>"
            results = self.memory.search_memories(args[1], " ".join(args[2:]))
            output = [f"Found {len(results)} memories:\n"]
            for mem in results[:10]:  # Show first 10
                output.append(f"  {mem['content'][:100]}...")
                output.append(f"    Type: {mem['memory_type']}")
                output.append(f"    By: {mem['user_id']}")
                output.append("")
            return "\n".join(output)

        elif subcommand == "conversations":
            if len(args) < 2:
                return "Usage: /team memory conversations <team_id>"
            conversations = self.memory.list_conversations(args[1])
            if not conversations:
                return "No conversations found."
            output = [f"Team Conversations ({len(conversations)}):\n"]
            for conv in conversations[:20]:
                output.append(f"  {conv['title']}")
                output.append(f"    Messages: {conv['message_count']}")
                output.append(f"    Participants: {len(conv['participants'])}")
                output.append("")
            return "\n".join(output)

        else:
            return "Unknown memory subcommand."

    def _manage_permissions(self, args: List[str]) -> str:
        """Manage permissions."""
        if not args:
            return "Usage: /team permissions <grant|revoke|list> ..."

        subcommand = args[0]

        if subcommand == "grant":
            if len(args) < 4:
                return "Usage: /team permissions grant <resource_id> <user_id> <level>"
            from isaac.team.models import Permission

            permission = Permission(
                resource_id=args[1],
                resource_type=ResourceType.WORKSPACE,  # Could be parameterized
                user_id=args[2],
                level=PermissionLevel(args[3]),
                granted_by=self.user_id,
            )
            if self.permissions.grant_permission(permission):
                return f"✓ Granted {args[3]} permission to {args[2]}."
            else:
                return "Failed to grant permission."

        elif subcommand == "revoke":
            if len(args) < 3:
                return "Usage: /team permissions revoke <resource_id> <user_id>"
            if self.permissions.revoke_permission(args[1], args[2]):
                return f"✓ Revoked permission from {args[2]}."
            else:
                return "Failed to revoke permission."

        elif subcommand == "list":
            if len(args) < 2:
                return "Usage: /team permissions list <resource_id>"
            perms = self.permissions.get_resource_permissions(args[1])
            if not perms:
                return "No permissions found."
            output = ["Resource Permissions:\n"]
            for user_id, level in perms.items():
                output.append(f"  {user_id}: {level.value}")
            return "\n".join(output)

        else:
            return "Unknown permissions subcommand."
