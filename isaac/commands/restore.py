"""
Restore Handler - Execute restore operations from backups.

Handles:
- Parsing restore command arguments
- Backup source validation
- User confirmation
- Restore execution (copy operations)
- Status logging
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from isaac.core.cli_command_router import CommandResult


class RestoreHandler:
    """
    Handle restore command execution.

    Expected format:
        restore <name> from <backup_source>
        restore <name>  (prompts for backup source)
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
        Execute restore command.

        Args:
            args: Command arguments (everything after 'restore')

        Returns:
            CommandResult with status
        """
        # Parse arguments
        name, backup_source = self._parse_args(args)

        if not name:
            return CommandResult(
                success=False,
                message="Restore failed: No backup name specified",
                status_symbol='✗',
                suggestion="Usage: isaac restore <name> from <backup_source>"
            )

        # Get backup source (prompt if not provided)
        if not backup_source:
            backup_source = self._prompt_backup_source()
            if not backup_source:
                return CommandResult(
                    success=False,
                    message="Restore cancelled: No backup source specified",
                    status_symbol='⊘',
                    suggestion=None
                )

        # Resolve backup source path
        resolved_source = self._resolve_path(backup_source)
        if not resolved_source or not resolved_source.exists():
            return CommandResult(
                success=False,
                message=f"Restore failed: Backup not found: {backup_source}",
                status_symbol='✗',
                suggestion="Verify backup source path and try again"
            )

        # Determine destination (current directory by default)
        destination = Path.cwd() / name

        # Confirm operation
        if not self._confirm_restore(resolved_source, destination):
            return CommandResult(
                success=False,
                message="Restore cancelled by user",
                status_symbol='⊘',
                suggestion=None
            )

        # Execute restore
        try:
            self._perform_restore(resolved_source, destination)

            # Log success
            log_msg = f"restore {name} from {resolved_source}"
            self.session._log_command(f"{log_msg} [SUCCESS]")

            return CommandResult(
                success=True,
                message=f"Restore complete: {resolved_source} → {destination}",
                status_symbol='✓',
                suggestion=None
            )

        except Exception as e:
            # Log failure
            log_msg = f"restore {name} from {resolved_source}"
            self.session._log_command(f"{log_msg} [FAILED: {str(e)}]")

            return CommandResult(
                success=False,
                message=f"Restore failed: {str(e)}",
                status_symbol='✗',
                suggestion="Check permissions and ensure destination is writable"
            )

    def _parse_args(self, args: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse restore arguments into name and backup source.

        Args:
            args: Command arguments

        Returns:
            Tuple of (name, backup_source)

        Examples:
            ["my-folder", "from", "/backup"] → ("my-folder", "/backup")
            ["my-folder"] → ("my-folder", None)
        """
        if not args:
            return (None, None)

        # Check for "from" keyword
        if "from" in args:
            from_index = args.index("from")
            name = ' '.join(args[:from_index])
            backup_source = ' '.join(args[from_index + 1:]) if from_index + 1 < len(args) else None
            return (name, backup_source)
        else:
            # No "from" keyword - only name provided
            name = ' '.join(args)
            return (name, None)

    def _resolve_path(self, path_str: str) -> Optional[Path]:
        """
        Resolve path string to actual Path object.

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

            return abs_path if abs_path.exists() else None

        except Exception:
            return None

    def _prompt_backup_source(self) -> Optional[str]:
        """
        Prompt user for backup source path.

        Returns:
            Backup source path string or None if cancelled
        """
        try:
            print("\nBackup source path: ", end='', flush=True)
            source = input().strip()
            return source if source else None
        except (KeyboardInterrupt, EOFError):
            return None

    def _confirm_restore(self, source: Path, destination: Path) -> bool:
        """
        Confirm restore operation with user.

        Args:
            source: Backup source path
            destination: Restore destination path

        Returns:
            True if confirmed, False if cancelled
        """
        print(f"\nRestore Operation:")
        print(f"  From: {source}")
        print(f"  To: {destination}")

        # Warn if destination exists
        if destination.exists():
            print(f"  ⚠️  WARNING: Destination exists and will be overwritten!")

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
            print("\nExecute restore? (y/n): ", end='', flush=True)
            response = input().strip().lower()
            return response in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            return False

    def _perform_restore(self, source: Path, destination: Path):
        """
        Perform the actual restore operation.

        Args:
            source: Backup source path
            destination: Restore destination path

        Raises:
            Exception: If restore fails
        """
        # Remove existing destination if present
        if destination.exists():
            if destination.is_file():
                destination.unlink()
            elif destination.is_dir():
                shutil.rmtree(destination)

        # Copy backup to destination
        if source.is_file():
            shutil.copy2(source, destination)
        elif source.is_dir():
            shutil.copytree(source, destination)
        else:
            raise ValueError(f"Source is neither file nor directory: {source}")