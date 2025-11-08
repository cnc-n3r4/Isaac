"""
Backup Handler - Execute backup operations.

Handles:
- Parsing backup command arguments
- Path validation
- User confirmation
- Backup execution (copy operations)
- Status logging
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from isaac.core.cli_command_router import CommandResult


class BackupHandler:
    """
    Handle backup command execution.

    Expected format:
        backup <source> to <destination>
        backup <source>  (prompts for destination)
    """

    def __init__(self, session_manager):
        """
        Initialize handler with session manager.

        Args:
            session_manager: SessionManager for logging
        """
        self.session = session_manager

    def execute(self, args: List[str]) -> CommandResult:
        """
        Execute backup command.

        Args:
            args: Command arguments (everything after 'backup')

        Returns:
            CommandResult with status

        Examples:
            args = ["my-folder", "to", "/mnt/external"]
            args = ["~/Documents"]  (prompts for destination)
        """
        # Parse arguments
        source, destination = self._parse_args(args)

        if not source:
            return CommandResult(
                success=False,
                message="Backup failed: No source specified",
                status_symbol='✗',
                suggestion="Usage: isaac backup <source> to <destination>"
            )

        # Resolve source path
        resolved_source = self._resolve_path(source)
        if not resolved_source:
            return CommandResult(
                success=False,
                message=f"Backup failed: Source not found: {source}",
                status_symbol='✗',
                suggestion=self._suggest_similar_paths(source)
            )

        # Get destination (prompt if not provided)
        if not destination:
            destination = self._prompt_destination()
            if not destination:
                return CommandResult(
                    success=False,
                    message="Backup cancelled: No destination specified",
                    status_symbol='⊘',
                    suggestion=None
                )

        # Resolve destination path
        resolved_dest = self._resolve_path(destination)
        if not resolved_dest:
            return CommandResult(
                success=False,
                message=f"Backup failed: Destination not accessible: {destination}",
                status_symbol='✗',
                suggestion="Ensure destination directory exists and is writable"
            )

        # Confirm operation
        if not self._confirm_backup(resolved_source, resolved_dest):
            return CommandResult(
                success=False,
                message="Backup cancelled by user",
                status_symbol='⊘',
                suggestion=None
            )

        # Execute backup
        try:
            self._perform_backup(resolved_source, resolved_dest)

            # Log success
            log_msg = f"backup {resolved_source} to {resolved_dest}"
            self.session._log_command(f"{log_msg} [SUCCESS]")

            return CommandResult(
                success=True,
                message=f"Backup complete: {resolved_source} → {resolved_dest}",
                status_symbol='✓',
                suggestion=None
            )

        except Exception as e:
            # Log failure
            log_msg = f"backup {resolved_source} to {resolved_dest}"
            self.session._log_command(f"{log_msg} [FAILED: {str(e)}]")

            return CommandResult(
                success=False,
                message=f"Backup failed: {str(e)}",
                status_symbol='✗',
                suggestion="Check permissions and disk space"
            )

    def _parse_args(self, args: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse backup arguments into source and destination.

        Args:
            args: Command arguments

        Returns:
            Tuple of (source, destination)

        Examples:
            ["my-folder", "to", "/dest"] → ("my-folder", "/dest")
            ["my-folder"] → ("my-folder", None)
            [] → (None, None)
        """
        if not args:
            return (None, None)

        # Check for "to" keyword
        if "to" in args:
            to_index = args.index("to")
            source = ' '.join(args[:to_index])
            destination = ' '.join(args[to_index + 1:]) if to_index + 1 < len(args) else None
            return (source, destination)
        else:
            # No "to" keyword - only source provided
            source = ' '.join(args)
            return (source, None)

    def _resolve_path(self, path_str: str) -> Optional[Path]:
        """
        Resolve path string to actual Path object.

        Handles:
        - Relative paths
        - ~ expansion
        - Path validation

        Args:
            path_str: Path string to resolve

        Returns:
            Resolved Path object or None if invalid
        """
        try:
            # Expand user home directory
            expanded = os.path.expanduser(path_str)

            # Convert to absolute path
            abs_path = Path(expanded).resolve()

            # For destination paths, parent must exist
            # For source paths, path itself must exist
            if abs_path.exists():
                return abs_path
            elif abs_path.parent.exists():
                # Destination doesn't exist yet but parent does
                return abs_path
            else:
                return None

        except Exception:
            return None

    def _suggest_similar_paths(self, path_str: str) -> str:
        """
        Generate helpful suggestions for invalid paths.

        Args:
            path_str: Invalid path string

        Returns:
            Suggestion message
        """
        # Check common variations
        suggestions = []

        # Try with quotes
        if ' ' in path_str:
            suggestions.append(f'Try quoting: isaac backup "{path_str}" to <dest>')

        # Try case variations
        lower = path_str.lower()
        if lower == "my documents" or lower == "documents":
            home = Path.home()
            docs = home / "Documents"
            if docs.exists():
                suggestions.append(f'Did you mean: "{docs}"?')

        # Try current directory
        cwd_path = Path.cwd() / path_str
        if cwd_path.exists():
            suggestions.append(f'Found in current directory: {cwd_path}')

        return ' '.join(suggestions) if suggestions else "Check the path and try again"

    def _prompt_destination(self) -> Optional[str]:
        """
        Prompt user for destination path.

        Returns:
            Destination path string or None if cancelled
        """
        try:
            print("\nDestination path: ", end='', flush=True)
            dest = input().strip()
            return dest if dest else None
        except (KeyboardInterrupt, EOFError):
            return None

    def _confirm_backup(self, source: Path, destination: Path) -> bool:
        """
        Confirm backup operation with user.

        Args:
            source: Source path
            destination: Destination path

        Returns:
            True if confirmed, False if cancelled
        """
        print(f"\nBackup Operation:")
        print(f"  Source: {source}")
        print(f"  Destination: {destination}")

        # Calculate size if possible
        try:
            if source.is_file():
                size = source.stat().st_size
                size_mb = size / (1024 * 1024)
                print(f"  Size: {size_mb:.2f} MB")
            elif source.is_dir():
                # Estimate directory size
                total_size = sum(f.stat().st_size for f in source.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                print(f"  Size: ~{size_mb:.2f} MB")
        except Exception:
            pass  # Skip size if can't calculate

        try:
            print("\nExecute backup? (y/n): ", end='', flush=True)
            response = input().strip().lower()
            return response in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            return False

    def _perform_backup(self, source: Path, destination: Path):
        """
        Perform the actual backup operation.

        Args:
            source: Source path to backup
            destination: Destination path

        Raises:
            Exception: If backup fails
        """
        # Determine if source is file or directory
        if source.is_file():
            # File backup - copy file
            dest_file = destination / source.name if destination.is_dir() else destination
            shutil.copy2(source, dest_file)

        elif source.is_dir():
            # Directory backup - recursive copy
            dest_dir = destination / source.name if destination.is_dir() else destination
            shutil.copytree(source, dest_dir, dirs_exist_ok=True)

        else:
            raise ValueError(f"Source is neither file nor directory: {source}")