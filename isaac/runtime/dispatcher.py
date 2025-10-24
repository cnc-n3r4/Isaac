# isaac/runtime/dispatcher.py

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import shlex


class CommandDispatcher:
    """Core dispatcher for plugin-based command execution"""

    def __init__(self, session_manager):
        self.session = session_manager
        self.commands = {}  # trigger → manifest mapping
        self.security = SecurityEnforcer()
        self.loader = ManifestLoader()

    def load_commands(self, directories: List[Path]):
        """Scan directories for command.yaml manifests"""
        total_commands = 0
        
        for directory in directories:
            if not directory.exists():
                continue

            # Find all command.yaml files
            for yaml_file in directory.rglob('command.yaml'):
                manifest = self.loader.load_manifest(yaml_file)
                if manifest:
                    command_name = manifest.get('name', 'unknown')
                    print(f"Loading command: {command_name}")
                    
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
                    
                    total_commands += 1
        
        print(f"✓ Loaded {total_commands} commands")

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

    def execute(self, command: str, args: Optional[Dict] = None, stdin: Optional[str] = None) -> Dict:
        """Run handler and return normalized envelope"""
        try:
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
                # For payload, send args as list of strings
                args = args_raw.split() if args_raw else []

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
                "args_raw": args_raw,
                "stdin": stdin or "",
                "manifest": manifest,
                "session": {
                    "machine_id": getattr(self.session.config, 'machine_id', 'unknown'),
                    "user_prefs": getattr(self.session.preferences, 'data', {}),
                    "config": self.session.config,
                    "command_history": getattr(self.session.command_history, 'commands', [])
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
            use_stdin = manifest.get('stdin', True)
            stdout_config = manifest.get('stdout', {})
            is_streaming = stdout_config.get('streaming', False)
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE if use_stdin else None,
                stdout=None if is_streaming else subprocess.PIPE,  # Let streaming commands inherit stdout
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                env=self.security.sanitize_env()
            )

            # Send payload via stdin if supported
            payload_json = json.dumps(payload, ensure_ascii=True) if use_stdin else None
            
            if is_streaming:
                # For streaming commands, send input and let command handle its own output
                if use_stdin:
                    process.stdin.write(payload_json)
                    process.stdin.flush()
                    process.stdin.close()
                
                # Wait for process to complete (output streams directly to terminal)
                process.wait()
                stdout = ""  # Output already streamed to terminal
                stderr = process.stderr.read() if process.stderr else ""
            else:
                # For non-streaming commands, use communicate as before
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

            if is_streaming:
                # For streaming commands, return success status (output already streamed)
                return {
                    "ok": True,
                    "stdout": "",
                    "stderr": stderr,
                    "meta": {"streamed": True}
                }

            # Parse result for non-streaming commands
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

    def chain_pipe(self, cmd1: str, cmd2: str) -> Dict:
        """Connect stdout of cmd1 to stdin of cmd2"""
        # Execute first command
        result1 = self.execute(cmd1)
        if not result1.get('ok', False):
            return result1

        # Check if cmd2 accepts stdin
        resolved2 = self.resolve_trigger(cmd2)
        if not resolved2:
            return {
                "ok": False,
                "error": {
                    "code": "UNKNOWN_COMMAND",
                    "message": f"Unknown command: {cmd2}"
                },
                "meta": {}
            }

        manifest2 = resolved2['manifest']
        if not manifest2.get('stdin', False):
            return {
                "ok": False,
                "error": {
                    "code": "PIPE_NOT_SUPPORTED",
                    "message": f"Command {cmd2} does not accept stdin"
                },
                "meta": {}
            }

        # Execute second command with stdin from first
        stdin_data = result1.get('stdout', '')
        return self.execute(cmd2, stdin=stdin_data)

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