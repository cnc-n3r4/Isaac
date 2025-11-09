"""UnifiedFileSystem scaffold.

Provides a simple local-first API with a placeholder cloud fallback.
This is intentionally minimal and suitable for iterative enhancement.
"""

from pathlib import Path
from typing import Optional


class UnifiedFileSystem:
    """Simple local-first filesystem abstraction.

    Methods:
        read(path) -> str
        write(path, data)
        exists(path) -> bool
        listdir(path) -> list[str]
    """

    def __init__(self, cloud_client: Optional[object] = None):
        self.cloud_client = cloud_client

    def _local_path(self, path) -> Path:
        return Path(path)

    def read(self, path) -> str:
        p = self._local_path(path)
        with p.open("r", encoding="utf-8") as fh:
            return fh.read()

    def write(self, path, data: str) -> None:
        p = self._local_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            fh.write(data)

    def exists(self, path) -> bool:
        return self._local_path(path).exists()

    def listdir(self, path) -> list:
        p = self._local_path(path)
        if not p.exists():
            return []
        return [str(child) for child in p.iterdir()]

    # Placeholder for cloud fallback - implementation-specific
    def read_from_cloud(self, path) -> Optional[str]:
        if self.cloud_client:
            try:
                return self.cloud_client.read(path)
            except Exception:
                return None
        return None
