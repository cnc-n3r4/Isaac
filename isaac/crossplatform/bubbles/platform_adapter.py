"""
Platform Adapter - Handles OS-specific process and system operations
"""

import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


class PlatformAdapter:
    """
    Adapts operations for different operating systems
    """

    @staticmethod
    def get_platform() -> str:
        """Get current platform identifier"""
        return platform.system().lower()

    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows"""
        return platform.system() == "Windows"

    @staticmethod
    def is_macos() -> bool:
        """Check if running on macOS"""
        return platform.system() == "Darwin"

    @staticmethod
    def is_linux() -> bool:
        """Check if running on Linux"""
        return platform.system() == "Linux"

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize path for cross-platform use"""
        # Convert to Path object and back to string
        normalized = Path(path).as_posix()

        # Remove drive letters on Windows
        if ":" in normalized[:3]:
            normalized = normalized[normalized.index(":") + 1 :]

        return normalized

    @staticmethod
    def denormalize_path(path: str, target_platform: Optional[str] = None) -> str:
        """Convert normalized path to platform-specific format"""
        if target_platform is None:
            target_platform = PlatformAdapter.get_platform()

        if target_platform == "windows":
            # Add C: drive and convert to backslashes
            if not path.startswith("/"):
                path = "/" + path
            return f"C:{path}".replace("/", "\\")
        else:
            # Unix-like systems
            return path

    @staticmethod
    def get_shell() -> str:
        """Get appropriate shell for platform"""
        if PlatformAdapter.is_windows():
            return "cmd.exe"
        else:
            return os.environ.get("SHELL", "/bin/bash")

    @staticmethod
    def get_path_separator() -> str:
        """Get path separator for current platform"""
        if PlatformAdapter.is_windows():
            return ";"
        else:
            return ":"

    @staticmethod
    def suspend_process(pid: int) -> bool:
        """Suspend a process (platform-specific)"""
        try:
            if PlatformAdapter.is_windows():
                # Windows: Use pssuspend or PowerShell
                subprocess.run(["powershell", "-Command", f"Suspend-Process -Id {pid}"], check=True)
            else:
                # Unix-like: Send SIGSTOP
                import os
                import signal

                os.kill(pid, signal.SIGSTOP)

            return True
        except Exception as e:
            print(f"Failed to suspend process {pid}: {e}")
            return False

    @staticmethod
    def resume_process(pid: int) -> bool:
        """Resume a suspended process (platform-specific)"""
        try:
            if PlatformAdapter.is_windows():
                # Windows: Use pssuspend or PowerShell
                subprocess.run(["powershell", "-Command", f"Resume-Process -Id {pid}"], check=True)
            else:
                # Unix-like: Send SIGCONT
                import os
                import signal

                os.kill(pid, signal.SIGCONT)

            return True
        except Exception as e:
            print(f"Failed to resume process {pid}: {e}")
            return False

    @staticmethod
    def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
        """Get process information (cross-platform)"""
        try:
            import psutil

            proc = psutil.Process(pid)

            return {
                "pid": proc.pid,
                "name": proc.name(),
                "status": proc.status(),
                "cwd": proc.cwd(),
                "cmdline": proc.cmdline(),
                "cpu_percent": proc.cpu_percent(),
                "memory_percent": proc.memory_percent(),
            }
        except Exception:
            return None

    @staticmethod
    def list_processes(workspace_path: str) -> List[Dict[str, Any]]:
        """List all processes running in workspace"""
        processes = []

        try:
            import psutil

            workspace = Path(workspace_path)

            for proc in psutil.process_iter(["pid", "name", "cwd", "cmdline"]):
                try:
                    if proc.info["cwd"]:
                        proc_cwd = Path(proc.info["cwd"])
                        if workspace in proc_cwd.parents or proc_cwd == workspace:
                            processes.append(
                                {
                                    "pid": proc.info["pid"],
                                    "name": proc.info["name"],
                                    "cwd": str(proc.info["cwd"]),
                                    "cmdline": proc.info["cmdline"],
                                }
                            )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            pass

        return processes

    @staticmethod
    def get_env_paths() -> List[str]:
        """Get PATH environment variable as list"""
        import os

        path_var = os.environ.get("PATH", "")
        separator = PlatformAdapter.get_path_separator()

        return [p for p in path_var.split(separator) if p]

    @staticmethod
    def set_env_paths(paths: List[str]):
        """Set PATH environment variable from list"""
        import os

        separator = PlatformAdapter.get_path_separator()
        os.environ["PATH"] = separator.join(paths)

    @staticmethod
    def get_home_dir() -> str:
        """Get user home directory (cross-platform)"""
        return str(Path.home())

    @staticmethod
    def get_temp_dir() -> str:
        """Get temporary directory (cross-platform)"""
        import tempfile

        return tempfile.gettempdir()

    @staticmethod
    def execute_command(command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute command in platform-appropriate shell"""
        shell = PlatformAdapter.get_shell()

        try:
            if PlatformAdapter.is_windows():
                result = subprocess.run(
                    command, shell=True, cwd=cwd, capture_output=True, text=True
                )
            else:
                result = subprocess.run(
                    command, shell=True, cwd=cwd, capture_output=True, text=True, executable=shell
                )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            return {"success": False, "returncode": -1, "stdout": "", "stderr": str(e)}


import os
