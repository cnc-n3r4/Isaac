"""Git-aware collections sync scaffold.

This module provides a minimal GitSync helper that locates the repo root,
can compute diffs and (later) attach hooks. It's a scaffold for Phase 0.
"""
from pathlib import Path
import subprocess
from typing import Optional, List


class GitSync:
    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = Path(repo_path) if repo_path is not None else Path('.')

    def repo_root(self) -> Optional[Path]:
        try:
            out = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=str(self.repo_path), text=True).strip()
            return Path(out)
        except Exception:
            return None

    def current_branch(self) -> Optional[str]:
        try:
            out = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=str(self.repo_path), text=True).strip()
            return out
        except Exception:
            return None

    def diff_files(self) -> List[str]:
        """Return a list of changed files in the working tree (uncommitted)."""
        try:
            out = subprocess.check_output(['git', 'status', '--porcelain'], cwd=str(self.repo_path), text=True)
            files = []
            for line in out.splitlines():
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    files.append(parts[1])
            return files
        except Exception:
            return []

    def install_hook(self, hook_name: str, script: str) -> bool:
        """Install a simple git hook script into .git/hooks.

        Returns True on success.
        """
        root = self.repo_root()
        if not root:
            return False
        hooks_dir = root / '.git' / 'hooks'
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hooks_dir / hook_name
        try:
            with hook_path.open('w', encoding='utf-8') as fh:
                fh.write(script)
            # make executable on Unix-like systems
            try:
                hook_path.chmod(0o755)
            except Exception:
                pass
            return True
        except Exception:
            return False
