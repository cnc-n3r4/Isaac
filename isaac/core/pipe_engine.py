"""
Hybrid Pipe Engine for Isaac

Enables seamless mixing of Isaac commands (/cmd) with native shell commands
via pipe operator. Don't reinvent Unix/PowerShell - leverage existing tools.
"""

import json
import sys
from pathlib import Path
from typing import List, Optional

# Add isaac package to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class PipeEngine:
    """Hybrid pipe engine that mixes Isaac and shell commands."""

    def __init__(self, session_manager, shell_adapter):
        """Initialize pipe engine with session and shell adapter."""
        self.session_manager = session_manager
        self.shell_adapter = shell_adapter

    def _is_isaac_command(self, cmd: str) -> bool:
        """Check if command is Isaac plugin or shell command."""
        return cmd.strip().startswith("/")

    def _parse_pipe_segments(self, cmd: str) -> List[str]:
        """Split on | respecting quoted strings."""
        segments = []
        current = []
        in_quotes = False
        quote_char = None

        for char in cmd:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
                current.append(char)
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                current.append(char)
            elif char == "|" and not in_quotes:
                segments.append("".join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            segments.append("".join(current).strip())

        return segments

    def _execute_shell_command(self, cmd: str, stdin_blob: Optional[dict] = None) -> dict:
        """Execute native shell command with blob I/O."""
        # Extract text content from blob for shell stdin
        stdin_text = None
        if stdin_blob:
            if stdin_blob["kind"] == "text":
                stdin_text = stdin_blob["content"]
            elif stdin_blob["kind"] == "json":
                # Convert JSON to pretty-printed text
                stdin_text = json.dumps(stdin_blob["content"], indent=2)
            elif stdin_blob["kind"] == "error":
                # Propagate error, don't execute
                return stdin_blob

        # Execute via shell adapter
        result = self.shell_adapter.execute(cmd, stdin=stdin_text)

        # Wrap result as blob
        if result.success:
            return {
                "kind": "text",
                "content": result.output,
                "meta": {
                    "source_command": cmd,
                    "exit_code": result.exit_code,
                    "shell": self.shell_adapter.name,
                },
            }
        else:
            return {
                "kind": "error",
                "content": result.output or f"Command failed: {cmd}",
                "meta": {"exit_code": result.exit_code, "failed_command": cmd},
            }

    def _execute_isaac_command(self, cmd: str, stdin_blob: Optional[dict] = None) -> dict:
        """Execute Isaac plugin with blob I/O."""
        import subprocess

        # Find the command script
        cmd_name = cmd.strip("/").split()[0]
        cmd_dir = Path(__file__).parent.parent / "commands" / cmd_name
        run_script = cmd_dir / "run.py"

        if not run_script.exists():
            return {
                "kind": "error",
                "content": f"Command not found: {cmd_name}",
                "meta": {"command": cmd},
            }

        # Prepare stdin data
        stdin_data = None
        if stdin_blob:
            # Include the command in the blob meta for piped commands
            enhanced_blob = dict(stdin_blob)
            enhanced_blob["meta"] = enhanced_blob.get("meta", {})
            enhanced_blob["meta"]["command"] = cmd
            stdin_data = json.dumps(enhanced_blob)
        else:
            # For commands without input, send empty dispatcher envelope
            stdin_data = json.dumps({"command": cmd})

        try:
            # Execute the command script with stdin
            result = subprocess.run(
                [sys.executable, str(run_script)],
                input=stdin_data,
                text=True,
                capture_output=True,
                cwd=Path(__file__).parent.parent.parent,
            )

            # Parse JSON output
            try:
                output_blob = json.loads(result.stdout)
                return output_blob
            except json.JSONDecodeError:
                # Command returned plain text, wrap it
                return {
                    "kind": "text",
                    "content": result.stdout or result.stderr,
                    "meta": {"source_command": cmd, "exit_code": result.returncode},
                }

        except Exception as e:
            return {
                "kind": "error",
                "content": f"Failed to execute Isaac command: {e}",
                "meta": {"command": cmd},
            }

    def _execute_command(self, cmd: str, stdin_blob: Optional[dict] = None) -> dict:
        """Execute Isaac or shell command appropriately."""
        if self._is_isaac_command(cmd):
            # Route to Isaac plugin system
            return self._execute_isaac_command(cmd, stdin_blob)
        else:
            # Execute via shell adapter
            return self._execute_shell_command(cmd, stdin_blob)

    def execute_pipeline(self, command_string: str) -> dict:
        """Parse and execute piped command chain."""
        # 1. Split on | boundaries (respect quotes)
        segments = self._parse_pipe_segments(command_string)

        # 2. Execute first command (source)
        blob = self._execute_command(segments[0])

        # 3. Chain through transformers
        for segment in segments[1:]:
            if blob["kind"] == "error":
                break  # Stop on error
            blob = self._execute_command(segment, stdin_blob=blob)

        # 4. Return final blob
        return blob
