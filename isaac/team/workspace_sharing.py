"""Workspace sharing functionality for teams."""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from .models import SharedResource, ResourceType


class WorkspaceSharer:
    """Share complete workspace contexts with teams."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize workspace sharer.

        Args:
            base_dir: Base directory for shared workspaces (default: ~/.isaac/shared_workspaces/)
        """
        self.base_dir = Path(base_dir or os.path.expanduser("~/.isaac/shared_workspaces"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def share_workspace(self, team_id: str, workspace_data: Dict,
                       shared_by: str, name: str = "", description: str = "") -> SharedResource:
        """Share a workspace with a team.

        Args:
            team_id: Team ID
            workspace_data: Workspace state data (from bubbles)
            shared_by: User ID sharing the workspace
            name: Workspace name
            description: Workspace description

        Returns:
            SharedResource object
        """
        # Generate resource ID
        import uuid
        resource_id = str(uuid.uuid4())

        # Save workspace data
        workspace_file = self.base_dir / f"{resource_id}.json"
        with open(workspace_file, 'w') as f:
            json.dump(workspace_data, f, indent=2)

        # Create shared resource
        resource = SharedResource(
            resource_id=resource_id,
            resource_type=ResourceType.WORKSPACE,
            team_id=team_id,
            shared_by=shared_by,
            name=name or f"Workspace {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description=description,
            metadata={
                'file_path': str(workspace_file),
                'git_branch': workspace_data.get('git_branch'),
                'file_count': len(workspace_data.get('open_files', [])),
                'process_count': len(workspace_data.get('processes', [])),
            }
        )

        return resource

    def share_bubble(self, team_id: str, bubble_id: str, bubble_manager,
                    shared_by: str, name: str = "", description: str = "") -> Optional[SharedResource]:
        """Share a bubble with a team.

        Args:
            team_id: Team ID
            bubble_id: Bubble ID to share
            bubble_manager: BubbleManager instance
            shared_by: User ID sharing the bubble
            name: Bubble name
            description: Bubble description

        Returns:
            SharedResource object or None if bubble not found
        """
        # Get bubble data
        bubble = bubble_manager.get_bubble(bubble_id)
        if not bubble:
            return None

        # Export bubble to dict
        bubble_data = bubble.to_dict()

        # Share as workspace
        return self.share_workspace(
            team_id=team_id,
            workspace_data=bubble_data,
            shared_by=shared_by,
            name=name or bubble.name,
            description=description or bubble.description
        )

    def get_workspace(self, resource_id: str) -> Optional[Dict]:
        """Get workspace data by resource ID.

        Args:
            resource_id: Resource ID

        Returns:
            Workspace data dictionary or None if not found
        """
        workspace_file = self.base_dir / f"{resource_id}.json"
        if not workspace_file.exists():
            return None

        with open(workspace_file) as f:
            return json.load(f)

    def import_workspace(self, resource_id: str, bubble_manager, user_id: str,
                        name: Optional[str] = None) -> Optional[str]:
        """Import a shared workspace as a new bubble.

        Args:
            resource_id: Resource ID of shared workspace
            bubble_manager: BubbleManager instance
            user_id: User ID importing the workspace
            name: Optional name for the imported bubble

        Returns:
            New bubble ID or None on error
        """
        workspace_data = self.get_workspace(resource_id)
        if not workspace_data:
            return None

        # Import as new bubble
        from isaac.bubbles.models import Bubble
        import uuid

        bubble_id = str(uuid.uuid4())
        bubble = Bubble.from_dict({
            **workspace_data,
            'bubble_id': bubble_id,
            'name': name or workspace_data.get('name', 'Imported Workspace'),
            'created_at': datetime.now().isoformat(),
        })

        # Save bubble
        bubble_manager._save_bubble(bubble)

        return bubble_id

    def list_shared_workspaces(self, team_id: str, team_manager) -> List[SharedResource]:
        """List all workspaces shared with a team.

        Args:
            team_id: Team ID
            team_manager: TeamManager instance

        Returns:
            List of SharedResource objects
        """
        return team_manager.get_shared_resources(
            team_id,
            resource_type=ResourceType.WORKSPACE
        )

    def delete_shared_workspace(self, resource_id: str) -> bool:
        """Delete a shared workspace.

        Args:
            resource_id: Resource ID

        Returns:
            True if deleted, False if not found
        """
        workspace_file = self.base_dir / f"{resource_id}.json"
        if workspace_file.exists():
            workspace_file.unlink()
            return True
        return False
