"""
Workspace Command - Standardized Implementation

Manage isolated workspaces for organizing projects and resources.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.core.sandbox_enforcer import SandboxEnforcer


class WorkspaceCommand(BaseCommand):
    """Manage isolated workspaces for organizing projects and resources"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute workspace command.

        Args:
            args: Command arguments [--subcommand [options]]
            context: Optional execution context with session data

        Returns:
            CommandResponse with workspace operation result or error
        """
        parser = FlagParser(args)

        # Initialize sandbox enforcer with session data if available
        try:
            session = self._create_mock_session(context)
            enforcer = SandboxEnforcer(session)
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error initializing workspace manager: {e}",
                metadata={"error_code": "INIT_ERROR"}
            )

        # Handle subcommands based on flags
        if parser.has_flag('list'):
            return self._list_workspaces(enforcer)
        elif parser.has_flag('create'):
            name = parser.get_flag('create')
            create_venv = parser.has_flag('venv')
            create_collection = parser.has_flag('collection')
            return self._create_workspace(enforcer, name, create_venv, create_collection)
        elif parser.has_flag('switch'):
            name = parser.get_flag('switch')
            return self._switch_workspace(enforcer, session, name)
        elif parser.has_flag('delete'):
            name = parser.get_flag('delete')
            preserve_collection = parser.has_flag('preserve-collection')
            return self._delete_workspace(enforcer, name, preserve_collection)
        elif parser.has_flag('add-collection'):
            name = parser.get_flag('add-collection')
            return self._add_collection(enforcer, name)
        else:
            # No subcommand provided, show usage
            return self._show_usage()

    def _create_mock_session(self, context: Optional[Dict[str, Any]]):
        """Create a mock session from context data"""
        class MockSession:
            def __init__(self, context_dict):
                session_data = context_dict.get("session", {}) if context_dict else {}
                self.config = session_data.get("config", {})

            def get_config(self):
                """Return the full config dict (no parameters)"""
                return self.config

        return MockSession(context)

    def _list_workspaces(self, enforcer: SandboxEnforcer) -> CommandResponse:
        """List all available workspaces"""
        try:
            workspaces = enforcer.list_workspaces()
            if workspaces:
                output = "Available workspaces:\n"
                for ws in workspaces:
                    output += f"  - {ws}\n"
            else:
                output = "No workspaces found.\n"

            return CommandResponse(
                success=True,
                data=output,
                metadata={"workspaces": workspaces, "count": len(workspaces)}
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error listing workspaces: {e}",
                metadata={"error_code": "LIST_ERROR"}
            )

    def _create_workspace(
        self,
        enforcer: SandboxEnforcer,
        name: str,
        create_venv: bool,
        create_collection: bool
    ) -> CommandResponse:
        """Create a new workspace"""
        try:
            result = enforcer.create_workspace(name, create_venv, create_collection)
            if result:
                output = f"[OK] Created workspace '{name}'\n"
                if create_venv:
                    output += f"[OK] Created virtual environment in '{name}/.venv'\n"
                    output += "  Run 'activate_venv.bat' to activate it\n"
                if create_collection:
                    output += f"[OK] Created xAI collection 'workspace-{name}'\n"

                return CommandResponse(
                    success=True,
                    data=output,
                    metadata={
                        "workspace_name": name,
                        "venv_created": create_venv,
                        "collection_created": create_collection
                    }
                )
            else:
                return CommandResponse(
                    success=False,
                    error=f"Failed to create workspace '{name}'",
                    metadata={"error_code": "CREATE_ERROR"}
                )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error creating workspace: {e}",
                metadata={"error_code": "CREATE_ERROR"}
            )

    def _switch_workspace(
        self,
        enforcer: SandboxEnforcer,
        session: Any,
        name: str
    ) -> CommandResponse:
        """Switch to a different workspace"""
        try:
            result = enforcer.switch_workspace(name, session)
            if result:
                output = f"[OK] Switched to workspace '{name}'\n"
                return CommandResponse(
                    success=True,
                    data=output,
                    metadata={"workspace_name": name}
                )
            else:
                return CommandResponse(
                    success=False,
                    error=f"Failed to switch to workspace '{name}'",
                    metadata={"error_code": "SWITCH_ERROR"}
                )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error switching workspace: {e}",
                metadata={"error_code": "SWITCH_ERROR"}
            )

    def _delete_workspace(
        self,
        enforcer: SandboxEnforcer,
        name: str,
        preserve_collection: bool
    ) -> CommandResponse:
        """Delete a workspace"""
        try:
            # Note: In a real implementation, you'd want to handle confirmation
            # For now, we'll proceed without interactive confirmation
            result = enforcer.delete_workspace(name, preserve_collection)
            if result:
                output = f"[OK] Deleted workspace '{name}'\n"
                if preserve_collection:
                    output += "[OK] Collection preserved (use /mine --claim to access it)\n"

                return CommandResponse(
                    success=True,
                    data=output,
                    metadata={
                        "workspace_name": name,
                        "collection_preserved": preserve_collection
                    }
                )
            else:
                return CommandResponse(
                    success=False,
                    error=f"Failed to delete workspace '{name}'",
                    metadata={"error_code": "DELETE_ERROR"}
                )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error deleting workspace: {e}",
                metadata={"error_code": "DELETE_ERROR"}
            )

    def _add_collection(self, enforcer: SandboxEnforcer, name: str) -> CommandResponse:
        """Add xAI collection to existing workspace"""
        try:
            result = enforcer.add_collection_to_workspace(name)
            if result:
                output = f"[OK] Added xAI collection to workspace '{name}'\n"
                return CommandResponse(
                    success=True,
                    data=output,
                    metadata={"workspace_name": name}
                )
            else:
                return CommandResponse(
                    success=False,
                    error=f"Failed to add collection to workspace '{name}'",
                    metadata={"error_code": "ADD_COLLECTION_ERROR"}
                )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error adding collection to workspace: {e}",
                metadata={"error_code": "ADD_COLLECTION_ERROR"}
            )

    def _show_usage(self) -> CommandResponse:
        """Show usage information"""
        output = "Usage: /workspace <--subcommand> [options]\n"
        output += "Subcommands:\n"
        output += "  --list                           List all workspaces\n"
        output += "  --create <name>                  Create a new workspace\n"
        output += "  --switch <name>                  Switch to workspace\n"
        output += "  --delete <name>                  Delete workspace\n"
        output += "  --add-collection <name>          Add xAI collection to existing workspace\n"
        output += "Options:\n"
        output += "  --venv                           Create virtual environment\n"
        output += "  --collection                     Create xAI collection\n"
        output += "  --preserve-collection            Preserve collection on delete\n"
        output += "\n"
        output += "Examples:\n"
        output += "  /workspace --list\n"
        output += "  /workspace --create myproject --venv --collection\n"
        output += "  /workspace --add-collection myproject\n"
        output += "  /workspace --switch myproject\n"
        output += "  /workspace --delete oldproject\n"

        return CommandResponse(
            success=False,
            error="No subcommand specified",
            metadata={"error_code": "MISSING_SUBCOMMAND"}
        )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="workspace",
            description="Manage isolated workspaces for organizing projects and resources",
            usage="/workspace <--subcommand> [options]",
            examples=[
                "/workspace --list",
                "/workspace --create myproject --venv --collection",
                "/workspace --switch myproject",
                "/workspace --add-collection myproject",
                "/workspace --delete oldproject --preserve-collection"
            ],
            tier=3,  # AI validation - modifies files and directories
            aliases=["ws"],
            category="system"
        )
