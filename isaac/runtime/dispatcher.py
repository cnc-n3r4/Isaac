# isaac/runtime/dispatcher.py

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import shlex
import re


class CommandDispatcher:
    """Core dispatcher for plugin-based command execution"""

    def __init__(self, session_manager):
        self.session = session_manager
        self.commands = {}  # trigger → manifest mapping
        self.security = SecurityEnforcer()
        self.loader = ManifestLoader()
        self.task_manager = None  # Lazy loaded TaskManager for background execution

    def load_commands(self, directories: List[Path]):
        """Scan directories for command.yaml manifests"""
        for directory in directories:
            if not directory.exists():
                continue

            # Find all command.yaml files
            for yaml_file in directory.rglob('command.yaml'):
                manifest = self.loader.load_manifest(yaml_file)
                if manifest:
                    # Register all triggers and aliases
                    for trigger in manifest.get('triggers', []):
                        self.commands[trigger] = {
                            'manifest': manifest,
                            'path': yaml_file.parent
                        }

                    for alias in manifest.get('aliases', []):
                        self.commands[alias] = {
                            'manifest': manifest,
                            'path': yaml_file.parent
                        }

    def resolve_trigger(self, input_text: str) -> Optional[Dict]:
        """Match /command to loaded manifest"""
        # Extract base command (first word)
        parts = input_text.strip().split()
        if not parts:
            return None

        base_command = parts[0]

        # Check exact match first
        if base_command in self.commands:
            return self.commands[base_command]

        return None

    def parse_args(self, manifest: Dict, args_raw: str) -> Dict[str, Any]:
        """Extract and validate arguments per manifest"""
        args_spec = manifest.get('args', [])
        parsed_args = {}

        # Split args_raw into parts (simple splitting for now)
        parts = shlex.split(args_raw) if args_raw.strip() else []

        # Parse positional arguments
        for i, arg_spec in enumerate(args_spec):
            name = arg_spec['name']
            arg_type = arg_spec['type']
            required = arg_spec.get('required', False)

            if i < len(parts):
                value = parts[i]
                # Convert type
                try:
                    if arg_type == 'int':
                        parsed_args[name] = int(value)
                    elif arg_type == 'bool':
                        parsed_args[name] = value.lower() in ['true', '1', 'yes', 'on']
                    elif arg_type == 'enum':
                        enum_values = arg_spec.get('enum', [])
                        if value in enum_values:
                            parsed_args[name] = value
                        else:
                            raise ValueError(f"Invalid value for {name}: {value}")
                    else:  # string
                        parsed_args[name] = value
                except (ValueError, TypeError):
                    if required:
                        raise ValueError(f"Invalid {arg_type} value for {name}: {value}")
                    # Skip invalid optional args
            elif required:
                raise ValueError(f"Missing required argument: {name}")

        return parsed_args

    def _detect_execution_mode(self, command: str) -> Tuple[str, str]:
        """
        Detect execution mode flags and return (cleaned_command, mode)

        Modes: 'verbose' (default), 'background', 'piped'
        Flags: --background, --bg, -bg

        Returns:
            Tuple of (command without flags, execution_mode)
        """
        # Check for background execution flags
        bg_pattern = r'\s+(--background|--bg|-bg)\b'

        if re.search(bg_pattern, command):
            # Remove the flag from command
            cleaned_command = re.sub(bg_pattern, '', command)
            return (cleaned_command.strip(), 'background')

        return (command, 'verbose')

    def _get_task_manager(self):
        """Lazy load TaskManager"""
        if self.task_manager is None:
            from isaac.core.task_manager import get_task_manager
            self.task_manager = get_task_manager()
        return self.task_manager

    def _execute_background(self, command: str, args: Optional[Dict] = None, stdin: Optional[str] = None) -> Dict:
        """
        Execute command in background using TaskManager

        Returns immediate response with task ID
        """
        try:
            # Get task manager
            task_manager = self._get_task_manager()

            # Determine task type based on command
            # System commands: backup, restore, sync, workspace operations
            # Code commands: grep, read, write, edit, etc.
            system_commands = {'/backup', '/restore', '/sync', '/workspace', '/status'}
            base_cmd = command.split()[0] if command else ''
            task_type = 'system' if base_cmd in system_commands else 'code'

            # Build full command string for execution
            # For now, we'll execute commands through the shell
            # In future, this could directly call command handlers
            full_command = command

            # Spawn background task
            task_id = task_manager.spawn_task(
                command=full_command,
                task_type=task_type,
                priority='normal',
                metadata={
                    'dispatcher': 'CommandDispatcher',
                    'original_command': command,
                    'has_stdin': stdin is not None
                }
            )

            return {
                "ok": True,
                "kind": "text",
                "stdout": f"✓ Background task started: {task_id}\n\nCommand: {command}\nType: {task_type}\n\nMonitor with: /tasks --show {task_id}\nView all tasks: /tasks",
                "meta": {
                    "task_id": task_id,
                    "execution_mode": "background"
                }
            }

        except Exception as e:
            return {
                "ok": False,
                "error": {
                    "code": "BACKGROUND_EXECUTION_ERROR",
                    "message": f"Failed to spawn background task: {str(e)}"
                },
                "meta": {}
            }

    def execute(self, command: str, args: Optional[Dict] = None, stdin: Optional[str] = None) -> Dict:
        """Run handler and return normalized envelope"""
        try:
            # Detect execution mode
            cleaned_command, exec_mode = self._detect_execution_mode(command)

            # Handle background execution
            if exec_mode == 'background':
                return self._execute_background(cleaned_command, args, stdin)

            # Continue with normal execution for verbose mode
            command = cleaned_command

            # Resolve the command
            resolved = self.resolve_trigger(command)
            if not resolved:
                return {
                    "ok": False,
                    "error": {
                        "code": "UNKNOWN_COMMAND",
                        "message": f"Unknown command: {command}",
                        "hint": "Try /help for available commands"
                    },
                    "meta": {}
                }

            manifest = resolved['manifest']
            command_dir = resolved['path']

            # Validate resources
            valid, error_msg = self.security.validate_resources(manifest)
            if not valid:
                return {
                    "ok": False,
                    "error": {
                        "code": "INVALID_MANIFEST",
                        "message": f"Manifest validation failed: {error_msg}"
                    },
                    "meta": {}
                }

            # Parse args if not provided
            args_raw = ""
            if args is None:
                # Extract args from command (everything after first space)
                parts = command.split(None, 1)
                args_raw = parts[1] if len(parts) > 1 else ""
                args = self.parse_args(manifest, args_raw)

            # Check for --help flag and redirect to help command
            if isinstance(args, dict) and args.get('help'):
                # Redirect to help command
                help_command = f"/help {command.split()[0]}"
                return self.execute(help_command, None, stdin)
            elif args_raw and ('--help' in args_raw or '-h' in args_raw):
                # Also check raw args for --help or -h
                help_command = f"/help {command.split()[0]}"
                return self.execute(help_command, None, stdin)

            # Prepare execution
            runtime = manifest.get('runtime', {})
            entry_point = runtime.get('entry', 'run.py')
            interpreter = runtime.get('interpreter', 'python')

            script_path = command_dir / entry_point
            if not script_path.exists():
                return {
                    "ok": False,
                    "error": {
                        "code": "MISSING_HANDLER",
                        "message": f"Handler not found: {script_path}"
                    },
                    "meta": {}
                }

            # Create envelope payload
            payload = {
                "command": command,
                "args": args,
                "stdin": stdin or "",
                "manifest": manifest,
                "session": {
                    "machine_id": getattr(self.session.config, 'machine_id', 'unknown'),
                    "user_prefs": getattr(self.session.preferences, 'data', {}),
                    "config": self.session.get_config()
                }
            }

            # Execute handler
            result = self._run_handler(script_path, interpreter, payload, manifest)

            # Apply telemetry redaction if configured
            telemetry = manifest.get('telemetry', {})
            if telemetry.get('log_output', False):
                redact_patterns = telemetry.get('redact_patterns', [])
                if 'stdout' in result and redact_patterns:
                    result['stdout'] = self.security.redact_patterns(result['stdout'], redact_patterns)

            return result

        except Exception as e:
            return {
                "ok": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": str(e)
                },
                "meta": {}
            }

    def _run_handler(self, script_path: Path, interpreter: str, payload: Dict, manifest: Dict) -> Dict:
        """Execute the command handler script"""
        # Get resource limits
        resources = manifest.get('security', {}).get('resources', {})
        timeout_ms = resources.get('timeout_ms', 5000)
        max_stdout_kib = resources.get('max_stdout_kib', 64)

        # Prepare command
        if interpreter == 'python':
            cmd = [sys.executable, str(script_path)]
        else:
            cmd = [interpreter, str(script_path)]

        # Start process
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=self.security.sanitize_env()
            )

            # Send payload via stdin
            payload_json = json.dumps(payload)
            stdout, stderr = process.communicate(input=payload_json, timeout=(timeout_ms + 1000) / 1000)

            # Check for timeout
            if self.security.enforce_timeout(process, timeout_ms):
                return {
                    "ok": False,
                    "error": {
                        "code": "TIMEOUT",
                        "message": f"Command timed out after {timeout_ms}ms"
                    },
                    "meta": {}
                }

            # Parse result
            try:
                result = json.loads(stdout)
            except json.JSONDecodeError:
                # Handler didn't return valid JSON, wrap in envelope
                result = {
                    "ok": True,
                    "kind": "text",
                    "stdout": stdout,
                    "stderr": stderr,
                    "meta": {}
                }

            # Apply output cap
            if 'stdout' in result:
                result['stdout'], truncated = self.security.cap_stdout(result['stdout'], max_stdout_kib)
                if truncated:
                    result['meta']['truncated'] = True

            return result

        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "error": {
                    "code": "TIMEOUT",
                    "message": f"Command timed out after {timeout_ms}ms"
                },
                "meta": {}
            }
        except Exception as e:
            return {
                "ok": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": str(e)
                },
                "meta": {}
            }

    def parse_pipeline(self, input_text: str) -> List[str]:
        """
        Parse command pipeline separated by pipes (|)

        Returns list of commands to execute in sequence

        Example:
            "/glob '**/*.py' | /grep 'def main' | /read"
            Returns: ["/glob '**/*.py'", "/grep 'def main'", "/read"]
        """
        # Split by | but respect quotes
        commands = []
        current_cmd = []
        in_quotes = False
        quote_char = None

        for char in input_text:
            if char in ['"', "'"] and (not in_quotes or char == quote_char):
                in_quotes = not in_quotes
                quote_char = char if in_quotes else None
                current_cmd.append(char)
            elif char == '|' and not in_quotes:
                # End of current command
                cmd_str = ''.join(current_cmd).strip()
                if cmd_str:
                    commands.append(cmd_str)
                current_cmd = []
            else:
                current_cmd.append(char)

        # Add final command
        cmd_str = ''.join(current_cmd).strip()
        if cmd_str:
            commands.append(cmd_str)

        return commands

    def execute_pipeline(self, pipeline_input: str) -> Dict:
        """
        Execute a pipeline of commands connected by pipes

        Example:
            execute_pipeline("/glob '**/*.py' | /grep 'def main'")

        Returns result of final command in pipeline
        """
        # Parse pipeline
        commands = self.parse_pipeline(pipeline_input)

        if len(commands) == 0:
            return {
                "ok": False,
                "error": {
                    "code": "EMPTY_PIPELINE",
                    "message": "No commands in pipeline"
                },
                "meta": {}
            }

        if len(commands) == 1:
            # Single command, execute normally
            return self.execute(commands[0])

        # Execute pipeline
        stdin_data = None

        for i, cmd in enumerate(commands):
            is_first = (i == 0)
            is_last = (i == len(commands) - 1)

            # Execute command
            if is_first:
                result = self.execute(cmd)
            else:
                # Verify command accepts stdin
                resolved = self.resolve_trigger(cmd)
                if not resolved:
                    return {
                        "ok": False,
                        "error": {
                            "code": "UNKNOWN_COMMAND",
                            "message": f"Unknown command in pipeline: {cmd}"
                        },
                        "meta": {"pipeline_stage": i + 1}
                    }

                manifest = resolved['manifest']
                if not manifest.get('stdin', False):
                    return {
                        "ok": False,
                        "error": {
                            "code": "PIPE_NOT_SUPPORTED",
                            "message": f"Command '{cmd}' does not accept stdin (pipeline stage {i + 1})"
                        },
                        "meta": {"pipeline_stage": i + 1}
                    }

                result = self.execute(cmd, stdin=stdin_data)

            # Check if command succeeded
            if not result.get('ok', False):
                return result

            # Pass stdout to next command (unless this is the last command)
            if not is_last:
                stdin_data = result.get('stdout', '')

        # Return result of final command
        return result

    def chain_pipe(self, cmd1: str, cmd2: str) -> Dict:
        """Connect stdout of cmd1 to stdin of cmd2 (legacy method, use execute_pipeline instead)"""
        return self.execute_pipeline(f"{cmd1} | {cmd2}")

    def route_remote(self, alias: str, command: str) -> Dict:
        """Send command to device via cloud client"""
        # For now, just queue locally - implement cloud routing later
        return {
            "ok": True,
            "kind": "text",
            "stdout": f"Queued command '{command}' for device '{alias}'",
            "meta": {"queued": True, "device": alias}
        }


# Import here to avoid circular imports
from .security_enforcer import SecurityEnforcer
from .manifest_loader import ManifestLoader