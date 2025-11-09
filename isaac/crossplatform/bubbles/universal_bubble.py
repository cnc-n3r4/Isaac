"""
Universal Bubble - Cross-platform workspace state container
"""

import hashlib
import json
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class UniversalBubble:
    """
    Cross-platform workspace state container that handles OS-specific differences
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.platform_info = self._get_platform_info()
        self.state = {
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat(),
            "created_on": self.platform_info,
            "workspace": {},
            "processes": [],
            "environment": {},
            "git_state": {},
            "files": {},
            "metadata": {},
        }

    def _get_platform_info(self) -> Dict[str, str]:
        """Get current platform information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }

    def capture(self) -> Dict[str, Any]:
        """Capture current workspace state in a platform-agnostic way"""
        self.state["workspace"] = self._capture_workspace()
        self.state["processes"] = self._capture_processes()
        self.state["environment"] = self._capture_environment()
        self.state["git_state"] = self._capture_git_state()
        self.state["files"] = self._capture_file_metadata()
        self.state["metadata"] = self._capture_metadata()

        return self.state

    def _capture_workspace(self) -> Dict[str, Any]:
        """Capture workspace configuration"""
        return {
            "path": str(self.workspace_path.absolute()),
            "normalized_path": self._normalize_path(str(self.workspace_path)),
            "exists": self.workspace_path.exists(),
            "is_dir": self.workspace_path.is_dir() if self.workspace_path.exists() else False,
        }

    def _capture_processes(self) -> List[Dict[str, Any]]:
        """Capture running processes in platform-agnostic format"""
        processes = []

        try:
            import psutil

            for proc in psutil.process_iter(["pid", "name", "cwd", "cmdline"]):
                try:
                    info = proc.info
                    if info["cwd"] and self.workspace_path in Path(info["cwd"]).parents:
                        processes.append(
                            {
                                "pid": info["pid"],
                                "name": info["name"],
                                "cwd": self._normalize_path(info["cwd"]),
                                "cmdline": info["cmdline"],
                                "platform": platform.system(),
                            }
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            # psutil not available, return empty list
            pass

        return processes

    def _capture_environment(self) -> Dict[str, str]:
        """Capture environment variables in platform-agnostic way"""
        env = {}

        # Capture relevant environment variables
        relevant_vars = [
            "PATH",
            "PYTHONPATH",
            "HOME",
            "USER",
            "SHELL",
            "VIRTUAL_ENV",
            "CONDA_DEFAULT_ENV",
            "NODE_ENV",
        ]

        for var in relevant_vars:
            value = os.environ.get(var)
            if value:
                env[var] = self._normalize_env_value(var, value)

        return env

    def _capture_git_state(self) -> Dict[str, Any]:
        """Capture git repository state"""
        git_state = {
            "is_repo": False,
            "branch": None,
            "commit": None,
            "dirty": False,
            "remotes": [],
        }

        try:
            import subprocess

            # Check if it's a git repo
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                git_state["is_repo"] = True

                # Get current branch
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                )
                git_state["branch"] = result.stdout.strip()

                # Get current commit
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                )
                git_state["commit"] = result.stdout.strip()

                # Check if dirty
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                )
                git_state["dirty"] = bool(result.stdout.strip())

                # Get remotes
                result = subprocess.run(
                    ["git", "remote", "-v"], cwd=self.workspace_path, capture_output=True, text=True
                )
                git_state["remotes"] = result.stdout.strip().split("\n")

        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return git_state

    def _capture_file_metadata(self) -> Dict[str, Any]:
        """Capture file metadata for important files"""
        files = {}

        important_files = [
            "package.json",
            "requirements.txt",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            ".env",
        ]

        for filename in important_files:
            file_path = self.workspace_path / filename
            if file_path.exists():
                files[filename] = {
                    "exists": True,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "hash": self._compute_file_hash(file_path),
                }

        return files

    def _capture_metadata(self) -> Dict[str, Any]:
        """Capture additional metadata"""
        return {
            "bubble_id": self._generate_bubble_id(),
            "captured_at": datetime.utcnow().isoformat(),
            "isaac_version": "5.5.0",
            "format_version": "1.0.0",
        }

    def _normalize_path(self, path: str) -> str:
        """Normalize path for cross-platform compatibility"""
        # Convert to forward slashes
        normalized = path.replace("\\", "/")

        # Remove drive letters for Windows paths
        if ":" in normalized[:3]:
            # Windows path like C:/Users/...
            normalized = normalized[normalized.index(":") + 1 :]

        return normalized

    def _normalize_env_value(self, var: str, value: str) -> str:
        """Normalize environment variable value for cross-platform use"""
        if var == "PATH" or var == "PYTHONPATH":
            # Normalize path separators
            if platform.system() == "Windows":
                paths = value.split(";")
            else:
                paths = value.split(":")

            # Normalize each path
            normalized_paths = [self._normalize_path(p) for p in paths]
            return ":".join(normalized_paths)  # Use : as standard separator

        return value

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file"""
        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return ""

    def _generate_bubble_id(self) -> str:
        """Generate unique bubble ID"""
        content = f"{self.workspace_path}{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def save(self, output_path: str) -> str:
        """Save bubble to file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(self.state, f, indent=2)

        return str(output_file)

    @classmethod
    def load(cls, bubble_path: str) -> "UniversalBubble":
        """Load bubble from file"""
        with open(bubble_path, "r") as f:
            state = json.load(f)

        # Extract workspace path from state
        workspace_path = state.get("workspace", {}).get("path", ".")

        bubble = cls(workspace_path)
        bubble.state = state

        return bubble

    def restore(self, target_path: Optional[str] = None) -> bool:
        """Restore bubble state to current or target workspace"""
        if target_path:
            self.workspace_path = Path(target_path)

        try:
            self._restore_environment()
            self._restore_git_state()

            return True
        except Exception as e:
            print(f"Error restoring bubble: {e}")
            return False

    def _restore_environment(self):
        """Restore environment variables (with platform adaptation)"""
        for var, value in self.state.get("environment", {}).items():
            # Denormalize for current platform
            if var in ["PATH", "PYTHONPATH"]:
                value = self._denormalize_path_var(value)

            os.environ[var] = value

    def _restore_git_state(self):
        """Restore git state if possible"""
        git_state = self.state.get("git_state", {})

        if not git_state.get("is_repo"):
            return

        try:
            import subprocess

            # Check if we're on the right branch
            current_branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
            ).stdout.strip()

            target_branch = git_state.get("branch")

            if current_branch != target_branch and target_branch:
                print(
                    f"Note: Bubble was captured on branch '{target_branch}', currently on '{current_branch}'"
                )

        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    def _denormalize_path_var(self, value: str) -> str:
        """Denormalize path variable for current platform"""
        paths = value.split(":")

        if platform.system() == "Windows":
            # Add drive letter if needed
            paths = [f"C:{p}" if not p.startswith("/") and ":" not in p else p for p in paths]
            # Convert to backslashes
            paths = [p.replace("/", "\\") for p in paths]
            return ";".join(paths)
        else:
            return ":".join(paths)

    def get_compatibility_report(self) -> Dict[str, Any]:
        """Generate compatibility report for current platform"""
        current_platform = self._get_platform_info()
        created_platform = self.state.get("created_on", {})

        compatible = True
        warnings = []

        # Check if platforms differ
        if current_platform["system"] != created_platform.get("system"):
            warnings.append(
                f"Bubble created on {created_platform.get('system')}, "
                f"restoring on {current_platform['system']}"
            )

        # Check Python version compatibility
        if current_platform["python_version"] != created_platform.get("python_version"):
            warnings.append(
                f"Python version mismatch: {created_platform.get('python_version')} "
                f"-> {current_platform['python_version']}"
            )

        return {
            "compatible": compatible,
            "warnings": warnings,
            "created_platform": created_platform,
            "current_platform": current_platform,
        }
