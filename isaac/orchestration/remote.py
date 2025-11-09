#!/usr/bin/env python3
"""
Remote Execution System for Multi-Machine Orchestration
"""

import time
import threading
import subprocess
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass

from isaac.orchestration.registry import MachineRegistry, Machine
from isaac.orchestration.load_balancer import LoadBalancer, LoadBalancingStrategy


@dataclass
class RemoteCommand:
    """Represents a command to be executed on a remote machine"""
    command_id: str
    target_machine: str
    command: str
    working_directory: Optional[str] = None
    environment: Optional[Dict[str, str]] = None
    timeout: int = 30
    priority: str = "normal"  # low, normal, high, urgent


@dataclass
class RemoteResult:
    """Result of a remote command execution"""
    command_id: str
    success: bool
    output: str
    exit_code: int
    execution_time: float
    error_message: Optional[str] = None
    machine_id: Optional[str] = None


class RemoteExecutor:
    """Handles remote command execution across registered machines"""

    def __init__(self, registry: MachineRegistry, port: int = 8080):
        self.registry = registry
        self.port = port
        self.active_commands: Dict[str, RemoteCommand] = {}
        self.command_results: Dict[str, RemoteResult] = {}
        self.load_balancer = LoadBalancer(registry)
        self._lock = threading.Lock()

    def execute_on_machine(self, machine_id: str, command: str,
                          working_directory: Optional[str] = None,
                          environment: Optional[Dict[str, str]] = None,
                          timeout: int = 30) -> RemoteResult:
        """Execute a command on a specific machine"""

        machine = self.registry.get_machine(machine_id)
        if not machine:
            return RemoteResult(
                command_id="",
                success=False,
                output="",
                exit_code=1,
                execution_time=0.0,
                error_message=f"Machine '{machine_id}' not found",
                machine_id=machine_id
            )

        if not machine.status.is_online:
            return RemoteResult(
                command_id="",
                success=False,
                output="",
                exit_code=1,
                execution_time=0.0,
                error_message=f"Machine '{machine.hostname}' is offline",
                machine_id=machine_id
            )

        # Create remote command
        import uuid
        command_id = str(uuid.uuid4())[:8]

        remote_cmd = RemoteCommand(
            command_id=command_id,
            target_machine=machine_id,
            command=command,
            working_directory=working_directory,
            environment=environment,
            timeout=timeout
        )

        # Store active command
        with self._lock:
            self.active_commands[command_id] = remote_cmd

        try:
            # Execute remotely
            result = self._execute_remote_command(remote_cmd, machine)

            # Store result
            with self._lock:
                self.command_results[command_id] = result
                del self.active_commands[command_id]

            return result

        except Exception as e:
            error_result = RemoteResult(
                command_id=command_id,
                success=False,
                output="",
                exit_code=1,
                execution_time=0.0,
                error_message=f"Remote execution failed: {str(e)}",
                machine_id=machine_id
            )

            with self._lock:
                self.command_results[command_id] = error_result
                if command_id in self.active_commands:
                    del self.active_commands[command_id]

            return error_result

    def execute_on_group(self, group_name: str, command: str,
                        working_directory: Optional[str] = None,
                        environment: Optional[Dict[str, str]] = None,
                        timeout: int = 30,
                        parallel: bool = True) -> List[RemoteResult]:
        """Execute a command on all machines in a group"""

        machines = self.registry.get_group_machines(group_name)
        if not machines:
            return [RemoteResult(
                command_id="",
                success=False,
                output="",
                exit_code=1,
                execution_time=0.0,
                error_message=f"Group '{group_name}' not found or empty"
            )]

        results = []

        if parallel:
            # Execute in parallel
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(machines)) as executor:
                futures = []
                for machine in machines:
                    future = executor.submit(
                        self.execute_on_machine,
                        machine.machine_id,
                        command,
                        working_directory,
                        environment,
                        timeout
                    )
                    futures.append(future)

                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append(RemoteResult(
                            command_id="",
                            success=False,
                            output="",
                            exit_code=1,
                            execution_time=0.0,
                            error_message=f"Execution failed: {str(e)}"
                        ))
        else:
            # Execute sequentially
            for machine in machines:
                result = self.execute_on_machine(
                    machine.machine_id,
                    command,
                    working_directory,
                    environment,
                    timeout
                )
                results.append(result)

        return results

    def find_best_machine(self, command: str, required_tags: Optional[List[str]] = None,
                         min_cpu: int = 0, min_memory: float = 0.0) -> Optional[Machine]:
        """Find the best machine for executing a command"""
        return self.registry.find_best_machine(required_tags, min_cpu, min_memory)

    def select_optimal_machine(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOAD,
                              group_name: Optional[str] = None,
                              required_tags: Optional[List[str]] = None,
                              min_cpu_cores: int = 0,
                              min_memory_gb: float = 0.0,
                              command_complexity: str = "normal") -> Optional[Machine]:
        """
        Select the optimal machine using intelligent load balancing

        Args:
            strategy: Load balancing strategy to use
            group_name: Limit selection to machines in this group
            required_tags: Machines must have all these tags
            min_cpu_cores: Minimum CPU cores required
            min_memory_gb: Minimum memory in GB required
            command_complexity: "low", "normal", "high" - affects selection criteria

        Returns:
            Selected machine or None if no suitable machine found
        """
        return self.load_balancer.select_machine(
            strategy=strategy,
            group_name=group_name,
            required_tags=required_tags,
            min_cpu_cores=min_cpu_cores,
            min_memory_gb=min_memory_gb,
            command_complexity=command_complexity
        )

    def execute_with_load_balancing(self, command: str,
                                   strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOAD,
                                   group_name: Optional[str] = None,
                                   required_tags: Optional[List[str]] = None,
                                   command_complexity: str = "normal",
                                   working_directory: Optional[str] = None,
                                   environment: Optional[Dict[str, str]] = None,
                                   timeout: int = 30) -> RemoteResult:
        """
        Execute a command on the optimal machine selected by load balancing

        Args:
            command: Command to execute
            strategy: Load balancing strategy
            group_name: Limit selection to machines in this group
            required_tags: Machines must have all these tags
            command_complexity: "low", "normal", "high"
            working_directory: Working directory for command
            environment: Environment variables
            timeout: Command timeout in seconds

        Returns:
            RemoteResult from the execution
        """

        # Select optimal machine
        machine = self.select_optimal_machine(
            strategy=strategy,
            group_name=group_name,
            required_tags=required_tags,
            command_complexity=command_complexity
        )

        if not machine:
            return RemoteResult(
                command_id="",
                success=False,
                output="",
                exit_code=1,
                execution_time=0.0,
                error_message="No suitable machine found for load balancing"
            )

        # Execute on selected machine
        result = self.execute_on_machine(
            machine.machine_id,
            command,
            working_directory,
            environment,
            timeout
        )

        # Record execution time for performance tracking
        if result.success:
            self.load_balancer.record_execution_time(machine.machine_id, result.execution_time)

        return result

    def _execute_remote_command(self, remote_cmd: RemoteCommand, machine: Machine) -> RemoteResult:
        """Execute command on remote machine via HTTP API"""

        start_time = time.time()

        try:
            # Prepare request payload
            payload = {
                "command": remote_cmd.command,
                "command_id": remote_cmd.command_id,
                "timeout": remote_cmd.timeout
            }

            if remote_cmd.working_directory:
                payload["working_directory"] = remote_cmd.working_directory

            if remote_cmd.environment:
                payload["environment"] = remote_cmd.environment

            # Make HTTP request to remote machine
            url = f"http://{machine.ip_address}:{machine.port}/execute"
            headers = {"Content-Type": "application/json"}

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=remote_cmd.timeout + 5  # Add buffer for network
            )

            execution_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                return RemoteResult(
                    command_id=remote_cmd.command_id,
                    success=data.get("success", False),
                    output=data.get("output", ""),
                    exit_code=data.get("exit_code", 0),
                    execution_time=execution_time,
                    machine_id=machine.machine_id
                )
            else:
                return RemoteResult(
                    command_id=remote_cmd.command_id,
                    success=False,
                    output="",
                    exit_code=1,
                    execution_time=execution_time,
                    error_message=f"HTTP {response.status_code}: {response.text}",
                    machine_id=machine.machine_id
                )

        except requests.exceptions.RequestException as e:
            execution_time = time.time() - start_time
            return RemoteResult(
                command_id=remote_cmd.command_id,
                success=False,
                output="",
                exit_code=1,
                execution_time=execution_time,
                error_message=f"Network error: {str(e)}",
                machine_id=machine.machine_id
            )

    def get_active_commands(self) -> List[RemoteCommand]:
        """Get list of currently active remote commands"""
        with self._lock:
            return list(self.active_commands.values())

    def get_command_result(self, command_id: str) -> Optional[RemoteResult]:
        """Get result of a completed command"""
        with self._lock:
            return self.command_results.get(command_id)

    def cancel_command(self, command_id: str) -> bool:
        """Cancel an active remote command"""
        with self._lock:
            if command_id in self.active_commands:
                del self.active_commands[command_id]
                return True
        return False


class RemoteCommandServer:
    """HTTP server for receiving remote commands (runs on each Isaac instance)"""

    def __init__(self, registry: MachineRegistry, host: str = "0.0.0.0", port: int = 8080):
        self.registry = registry
        self.host = host
        self.port = port
        self.server = None
        self.running = False

    def start(self):
        """Start the remote command server"""
        try:
            from flask import Flask, request, jsonify
        except ImportError:
            print("❌ Flask not installed. Remote command server requires: pip install flask")
            return

        app = Flask(__name__)

        @app.route("/execute", methods=["POST"])
        def execute_command():
            try:
                data = request.get_json()

                if not data or "command" not in data:
                    return jsonify({"success": False, "error": "Missing command"}), 400

                command = data["command"]
                command_id = data.get("command_id", "")
                timeout = min(data.get("timeout", 30), 300)  # Max 5 minutes
                working_directory = data.get("working_directory")
                environment = data.get("environment")

                # Execute command locally
                import os

                env = os.environ.copy()
                if environment:
                    env.update(environment)

                cwd = working_directory if working_directory else None

                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=cwd,
                    env=env
                )

                return jsonify({
                    "success": result.returncode == 0,
                    "output": result.stdout + result.stderr,
                    "exit_code": result.returncode,
                    "command_id": command_id
                })

            except subprocess.TimeoutExpired:
                return jsonify({"success": False, "error": "Command timed out"}), 408
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @app.route("/status", methods=["GET"])
        def get_status():
            """Get machine status"""
            # Get local machine info
            import psutil
            import platform

            return jsonify({
                "hostname": platform.node(),
                "os": platform.system(),
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "timestamp": time.time()
            })

        # Start server in background thread
        def run_server():
            app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

        import threading
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        self.running = True
        print(f"🚀 Remote command server started on {self.host}:{self.port}")

    def stop(self):
        """Stop the remote command server"""
        self.running = False
        if self.server:
            self.server.shutdown()

    def is_running(self) -> bool:
        """Check if server is running"""
        return self.running