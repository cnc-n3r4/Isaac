"""Git Status Plugin - Displays git repository information.

This plugin demonstrates file system access and external process execution.
"""

import subprocess
from pathlib import Path

from isaac.plugins.plugin_api import Plugin, PluginMetadata, PluginContext, PluginHook


class GitStatusPlugin(Plugin):
    """Shows git repository status before commands."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="git-status",
            version="1.0.0",
            author="Isaac Team",
            description="Displays git repository information and status",
            license="MIT",
            tags=["git", "vcs", "status"],
            hooks=[PluginHook.STARTUP],
            commands=[],
            permissions=["file:read", "subprocess"],
        )

    def initialize(self, context: PluginContext) -> None:
        """Initialize the plugin.

        Args:
            context: Plugin context
        """
        self._context = context
        self.workspace = Path(context.workspace_path)

        # Register hooks
        self.register_hook(PluginHook.STARTUP, self.on_startup)

    def shutdown(self) -> None:
        """Clean up plugin resources."""
        pass

    def on_startup(self) -> None:
        """Handle startup hook."""
        if self._is_git_repo():
            self._show_git_status()

    def _is_git_repo(self) -> bool:
        """Check if workspace is a git repository.

        Returns:
            True if git repository
        """
        git_dir = self.workspace / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def _show_git_status(self) -> None:
        """Display git status information."""
        try:
            # Get current branch
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if branch_result.returncode == 0:
                branch = branch_result.stdout.strip()
                print(f"[Git] Current branch: {branch}")

            # Get status
            status_result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if status_result.returncode == 0:
                status = status_result.stdout.strip()
                if status:
                    print(f"[Git] Uncommitted changes:")
                    status_lines = status.split("\n")
                    for line in status_lines[:5]:  # Show first 5 files
                        print(f"      {line}")
                    if len(status_lines) > 5:
                        remaining_count = len(status_lines) - 5
                        print(f"      ... and {remaining_count} more")
                else:
                    print("[Git] Working directory clean")

        except subprocess.TimeoutExpired:
            print("[Git] Git command timed out")
        except Exception as e:
            print(f"[Git] Error getting status: {e}")
