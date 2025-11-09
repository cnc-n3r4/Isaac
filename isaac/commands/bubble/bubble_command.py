"""
Bubble command for workspace state management.
Usage: /bubble <action> [args...]
"""

import argparse
from pathlib import Path
from typing import List, Dict, Any
from isaac.bubbles.bubble_manager import BubbleManager
from isaac.core.session_manager import SessionManager


class BubbleCommand:
    """Command interface for workspace bubbles."""

    def __init__(self, session_manager: SessionManager):
        """Initialize bubble command.

        Args:
            session_manager: Session manager instance
        """
        self.session = session_manager
        self.bubble_manager = BubbleManager(session_manager)

    def execute(self, args: List[str]) -> Dict[str, Any]:
        """Execute bubble command.

        Args:
            args: Command arguments

        Returns:
            Command result
        """
        if not args:
            return self._show_help()

        action = args[0].lower()

        try:
            if action == 'create':
                return self._create_bubble(args[1:])
            elif action == 'list':
                return self._list_bubbles(args[1:])
            elif action == 'resume':
                return self._resume_bubble(args[1:])
            elif action == 'suspend':
                return self._suspend_bubble(args[1:])
            elif action == 'delete':
                return self._delete_bubble(args[1:])
            elif action == 'export':
                return self._export_bubble(args[1:])
            elif action == 'import':
                return self._import_bubble(args[1:])
            elif action == 'info':
                return self._show_bubble_info(args[1:])
            elif action == 'current':
                return self._show_current_bubble()
            else:
                return {
                    'success': False,
                    'output': f"Unknown action: {action}\n{self._get_help_text()}",
                    'exit_code': 1
                }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error executing bubble command: {e}",
                'exit_code': 1
            }

    def _create_bubble(self, args: List[str]) -> Dict[str, Any]:
        """Create a new bubble."""
        parser = argparse.ArgumentParser(prog='/bubble create', exit_on_error=False)
        parser.add_argument('name', help='Bubble name')
        parser.add_argument('-d', '--description', help='Bubble description')
        parser.add_argument('-t', '--tags', nargs='*', help='Tags for organization')

        try:
            parsed = parser.parse_args(args)
        except SystemExit:
            return {
                'success': False,
                'output': "Usage: /bubble create <name> [-d description] [-t tag1 tag2 ...]",
                'exit_code': 1
            }

        try:
            bubble = self.bubble_manager.create_bubble(
                name=parsed.name,
                description=parsed.description or "",
                tags=parsed.tags or []
            )

            output = f"Created bubble '{bubble.name}' (ID: {bubble.bubble_id})\n"
            output += f"Workspace: {bubble.workspace_path}\n"
            if bubble.description:
                output += f"Description: {bubble.description}\n"
            if bubble.tags:
                output += f"Tags: {', '.join(bubble.tags)}\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Failed to create bubble: {e}",
                'exit_code': 1
            }

    def _list_bubbles(self, args: List[str]) -> Dict[str, Any]:
        """List available bubbles."""
        parser = argparse.ArgumentParser(prog='/bubble list', exit_on_error=False)
        parser.add_argument('-t', '--tag', help='Filter by tag')
        parser.add_argument('-l', '--limit', type=int, default=10, help='Limit results')

        try:
            parsed = parser.parse_args(args)
        except SystemExit:
            return {
                'success': False,
                'output': "Usage: /bubble list [-t tag] [-l limit]",
                'exit_code': 1
            }

        bubbles = self.bubble_manager.list_bubbles(tag_filter=parsed.tag)

        if not bubbles:
            return {
                'success': True,
                'output': "No bubbles found.",
                'exit_code': 0
            }

        output = f"Bubbles ({len(bubbles)} total):\n\n"
        for bubble in bubbles[:parsed.limit]:
            output += f"• {bubble.name} (ID: {bubble.bubble_id})\n"
            output += f"  Created: {bubble.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            if bubble.description:
                output += f"  Description: {bubble.description}\n"
            if bubble.tags:
                output += f"  Tags: {', '.join(bubble.tags)}\n"
            output += "\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _resume_bubble(self, args: List[str]) -> Dict[str, Any]:
        """Resume a bubble."""
        if not args:
            return {
                'success': False,
                'output': "Usage: /bubble resume <bubble_id>",
                'exit_code': 1
            }

        bubble_id = args[0]
        success = self.bubble_manager.resume_bubble(bubble_id)

        if success:
            return {
                'success': True,
                'output': f"Resumed bubble '{bubble_id}'",
                'exit_code': 0
            }
        else:
            return {
                'success': False,
                'output': f"Failed to resume bubble '{bubble_id}'",
                'exit_code': 1
            }

    def _suspend_bubble(self, args: List[str]) -> Dict[str, Any]:
        """Suspend a bubble."""
        if not args:
            return {
                'success': False,
                'output': "Usage: /bubble suspend <bubble_id>",
                'exit_code': 1
            }

        bubble_id = args[0]
        success = self.bubble_manager.suspend_bubble(bubble_id)

        if success:
            return {
                'success': True,
                'output': f"Suspended bubble '{bubble_id}'",
                'exit_code': 0
            }
        else:
            return {
                'success': False,
                'output': f"Failed to suspend bubble '{bubble_id}' (may already be suspended)",
                'exit_code': 1
            }

    def _delete_bubble(self, args: List[str]) -> Dict[str, Any]:
        """Delete a bubble."""
        if not args:
            return {
                'success': False,
                'output': "Usage: /bubble delete <bubble_id>",
                'exit_code': 1
            }

        bubble_id = args[0]

        # Confirm deletion
        confirm_msg = f"Are you sure you want to delete bubble '{bubble_id}'? (y/N): "
        # Note: In a real implementation, this would prompt the user
        # For now, we'll assume confirmation

        success = self.bubble_manager.delete_bubble(bubble_id)

        if success:
            return {
                'success': True,
                'output': f"Deleted bubble '{bubble_id}'",
                'exit_code': 0
            }
        else:
            return {
                'success': False,
                'output': f"Bubble '{bubble_id}' not found",
                'exit_code': 1
            }

    def _export_bubble(self, args: List[str]) -> Dict[str, Any]:
        """Export a bubble."""
        if len(args) < 2:
            return {
                'success': False,
                'output': "Usage: /bubble export <bubble_id> <export_path>",
                'exit_code': 1
            }

        bubble_id = args[0]
        export_path = args[1]

        success = self.bubble_manager.export_bubble(bubble_id, export_path)

        if success:
            return {
                'success': True,
                'output': f"Exported bubble '{bubble_id}' to {export_path}",
                'exit_code': 0
            }
        else:
            return {
                'success': False,
                'output': f"Failed to export bubble '{bubble_id}'",
                'exit_code': 1
            }

    def _import_bubble(self, args: List[str]) -> Dict[str, Any]:
        """Import a bubble."""
        if not args:
            return {
                'success': False,
                'output': "Usage: /bubble import <import_path>",
                'exit_code': 1
            }

        import_path = args[0]

        if not Path(import_path).exists():
            return {
                'success': False,
                'output': f"Import file not found: {import_path}",
                'exit_code': 1
            }

        bubble = self.bubble_manager.import_bubble(import_path)

        if bubble:
            return {
                'success': True,
                'output': f"Imported bubble '{bubble.name}' (ID: {bubble.bubble_id})",
                'exit_code': 0
            }
        else:
            return {
                'success': False,
                'output': f"Failed to import bubble from {import_path}",
                'exit_code': 1
            }

    def _show_bubble_info(self, args: List[str]) -> Dict[str, Any]:
        """Show detailed bubble information."""
        if not args:
            return {
                'success': False,
                'output': "Usage: /bubble info <bubble_id>",
                'exit_code': 1
            }

        bubble_id = args[0]
        bubble = self.bubble_manager._load_bubble(bubble_id)

        if not bubble:
            return {
                'success': False,
                'output': f"Bubble '{bubble_id}' not found",
                'exit_code': 1
            }

        output = f"Bubble Information: {bubble.name}\n"
        output += "=" * 50 + "\n"
        output += f"ID: {bubble.bubble_id}\n"
        output += f"Created: {bubble.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += f"Workspace: {bubble.workspace_path}\n"

        if bubble.description:
            output += f"Description: {bubble.description}\n"

        if bubble.tags:
            output += f"Tags: {', '.join(bubble.tags)}\n"

        # Git state
        if bubble.git_state.get('is_git_repo'):
            output += "\nGit State:\n"
            if bubble.git_state.get('current_branch'):
                output += f"  Branch: {bubble.git_state['current_branch']}\n"
            if bubble.git_state.get('status'):
                output += f"  Status: {len(bubble.git_state['status'].splitlines())} changes\n"
            if bubble.git_state.get('recent_commits'):
                output += f"  Recent commits: {len(bubble.git_state['recent_commits'].splitlines())}\n"

        # Environment
        if bubble.environment_vars:
            output += f"\nEnvironment Variables: {len(bubble.environment_vars)}\n"

        # Processes
        if bubble.running_processes:
            output += f"\nRunning Processes: {len(bubble.running_processes)}\n"

        # Open files
        if bubble.open_files:
            output += f"\nOpen Files: {len(bubble.open_files)}\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _show_current_bubble(self) -> Dict[str, Any]:
        """Show current bubble information."""
        current = self.bubble_manager.current_bubble

        if not current:
            return {
                'success': True,
                'output': "No current bubble active",
                'exit_code': 0
            }

        output = f"Current Bubble: {current.name}\n"
        output += f"ID: {current.bubble_id}\n"
        output += f"Created: {current.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += f"Workspace: {current.workspace_path}\n"

        if current.description:
            output += f"Description: {current.description}\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _show_help(self) -> Dict[str, Any]:
        """Show help information."""
        return {
            'success': True,
            'output': self._get_help_text(),
            'exit_code': 0
        }

    def _get_help_text(self) -> str:
        """Get help text."""
        return """Workspace Bubbles - Capture and restore complete workspace states

USAGE:
  /bubble <action> [arguments...]

ACTIONS:
  create <name> [-d description] [-t tag1 tag2 ...]  Create new bubble
  list [-t tag] [-l limit]                          List bubbles
  resume <bubble_id>                                Resume bubble
  suspend <bubble_id>                               Suspend bubble
  delete <bubble_id>                                Delete bubble
  export <bubble_id> <path>                         Export bubble
  import <path>                                     Import bubble
  info <bubble_id>                                  Show bubble details
  current                                           Show current bubble
  help                                              Show this help

EXAMPLES:
  /bubble create "web-dev-session" -d "Working on API endpoints" -t web api
  /bubble list -t web
  /bubble resume web-dev-session_1640995200
  /bubble export my-bubble bubble.json
  /bubble import shared-bubble.json

Bubbles capture: git state, environment variables, running processes,
open files, shell history, and terminal state for instant workspace switching."""