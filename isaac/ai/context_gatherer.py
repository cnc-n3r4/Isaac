"""ContextGatherer scaffold.

Gathers file and git context for AI queries. This is a small, testable
scaffold rather than a full implementation.
"""
from pathlib import Path
from typing import List, Dict
from isaac.collections.git_sync import GitSync


class ContextGatherer:
    def __init__(self, workspace: Path = Path('.')):
        self.workspace = Path(workspace)
        self.git = GitSync(self.workspace)

    def gather_file_list(self, limit: int = 100) -> List[str]:
        files = []
        for p in self.workspace.rglob('*'):
            if p.is_file():
                files.append(str(p))
                if len(files) >= limit:
                    break
        return files

    def gather_git_info(self) -> Dict:
        return {
            'root': str(self.git.repo_root()) if self.git.repo_root() else None,
            'branch': self.git.current_branch(),
            'diff': self.git.diff_files()
        }
