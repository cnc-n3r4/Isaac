"""
Pipeline Execution Engine - Execute pipeline workflows
Isaac's pipeline runner with parallel execution and error handling
"""

import time
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

from isaac.pipelines.models import Pipeline, PipelineStep, PipelineExecution, PipelineStatus, StepType


class StepExecutor:
    """Executes individual pipeline steps."""

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize step executor.

        Args:
            working_dir: Working directory for command execution
        """
        self.working_dir = working_dir or Path.cwd()

    def execute_step(self, step: PipelineStep, variables: Dict[str, Any],
                    timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Execute a single pipeline step.

        Args:
            step: Step to execute
            variables: Pipeline variables
            timeout_seconds: Override timeout

        Returns:
            Execution result
        """
        start_time = time.time()

        try:
            if step.type == StepType.COMMAND:
                result = self._execute_command(step, variables, timeout_seconds or step.timeout_seconds)
            elif step.type == StepType.SCRIPT:
                result = self._execute_script(step, variables, timeout_seconds or step.timeout_seconds)
            elif step.type == StepType.CONDITION:
                result = self._execute_condition(step, variables)
            elif step.type == StepType.WAIT:
                result = self._execute_wait(step, variables)
            elif step.type == StepType.NOTIFICATION:
                result = self._execute_notification(step, variables)
            elif step.type == StepType.PARALLEL:
                result = self._execute_parallel(step, variables)
            elif step.type == StepType.LOOP:
                result = self._execute_loop(step, variables)
            else:
                result = {
                    'success': False,
                    'output': f"Unknown step type: {step.type}",
                    'exit_code': 1
                }

        except Exception as e:
            result = {
                'success': False,
                'output': f"Step execution error: {e}",
                'exit_code': 1
            }

        result['duration'] = time.time() - start_time
        result['step_id'] = step.id
        result['step_name'] = step.name

        return result

    def _execute_command(self, step: PipelineStep, variables: Dict[str, Any],
                        timeout: Optional[int]) -> Dict[str, Any]:
        """Execute a command step."""
        command = step.config.get('command', '')
        if not command:
            return {'success': False, 'output': 'No command specified', 'exit_code': 1}

        # Substitute variables
        command = self._substitute_variables(command, variables)

        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout + result.stderr,
                'exit_code': result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': f'Command timed out after {timeout} seconds',
                'exit_code': -1
            }

    def _execute_script(self, step: PipelineStep, variables: Dict[str, Any],
                       timeout: Optional[int]) -> Dict[str, Any]:
        """Execute a script step."""
        script_path = step.config.get('script_path', '')
        if not script_path:
            return {'success': False, 'output': 'No script path specified', 'exit_code': 1}

        script_path = Path(script_path)
        if not script_path.exists():
            return {'success': False, 'output': f'Script not found: {script_path}', 'exit_code': 1}

        # Make script executable
        script_path.chmod(0o755)

        try:
            result = subprocess.run(
                [str(script_path)],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout + result.stderr,
                'exit_code': result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': f'Script timed out after {timeout} seconds',
                'exit_code': -1
            }

    def _execute_condition(self, step: PipelineStep, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a condition step."""
        condition = step.config.get('condition', '')
        if not condition:
            return {'success': False, 'output': 'No condition specified', 'exit_code': 1}

        # Evaluate condition (simple for now)
        try:
            # Basic variable substitution and evaluation
            condition = self._substitute_variables(condition, variables)
            result = eval(condition, {"__builtins__": {}}, variables)

            return {
                'success': bool(result),
                'output': f'Condition "{condition}" evaluated to {result}',
                'exit_code': 0 if result else 1
            }

        except Exception as e:
            return {
                'success': False,
                'output': f'Condition evaluation error: {e}',
                'exit_code': 1
            }

    def _execute_wait(self, step: PipelineStep, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a wait step."""
        wait_seconds = step.config.get('seconds', 0)
        wait_seconds = self._substitute_variables(str(wait_seconds), variables)

        try:
            wait_time = float(wait_seconds)
            time.sleep(wait_time)

            return {
                'success': True,
                'output': f'Waited {wait_time} seconds',
                'exit_code': 0
            }

        except ValueError:
            return {
                'success': False,
                'output': f'Invalid wait time: {wait_seconds}',
                'exit_code': 1
            }

    def _execute_notification(self, step: PipelineStep, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a notification step."""
        message = step.config.get('message', '')
        message = self._substitute_variables(message, variables)

        # For now, just print the notification
        print(f"🔔 PIPELINE NOTIFICATION: {message}")

        return {
            'success': True,
            'output': f'Notification sent: {message}',
            'exit_code': 0
        }

    def _execute_parallel(self, step: PipelineStep, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parallel steps (placeholder for now)."""
        return {
            'success': True,
            'output': 'Parallel execution not yet implemented',
            'exit_code': 0
        }

    def _execute_loop(self, step: PipelineStep, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute loop steps (placeholder for now)."""
        return {
            'success': True,
            'output': 'Loop execution not yet implemented',
            'exit_code': 0
        }

    def _substitute_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in text."""
        for key, value in variables.items():
            text = text.replace(f"${{{key}}}", str(value))
            text = text.replace(f"${key}", str(value))
        return text