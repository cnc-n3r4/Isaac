"""
Pipeline Runner - Orchestrate pipeline execution with dependencies
Isaac's pipeline execution orchestrator
"""

import threading
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Set

from isaac.pipelines.executor import StepExecutor
from isaac.pipelines.models import (
    Pipeline,
    PipelineExecution,
    PipelineStatus,
    PipelineStep,
)


class PipelineRunner:
    """Orchestrates pipeline execution with dependency management."""

    def __init__(self, max_workers: int = 4):
        """Initialize pipeline runner.

        Args:
            max_workers: Maximum number of concurrent step executions
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="pipeline")
        self.active_executions: Dict[str, PipelineExecution] = {}
        self.execution_lock = threading.Lock()

    def run_pipeline(
        self,
        pipeline: Pipeline,
        variables: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[PipelineExecution], None]] = None,
    ) -> str:
        """Start pipeline execution.

        Args:
            pipeline: Pipeline to execute
            variables: Override variables
            callback: Callback for execution updates

        Returns:
            Execution ID
        """
        execution_id = str(uuid.uuid4())

        # Merge variables
        execution_variables = {**pipeline.variables}
        if variables:
            execution_variables.update(variables)

        # Create execution record
        execution = PipelineExecution(
            pipeline_id=pipeline.id,
            execution_id=execution_id,
            start_time=time.time(),
            status=PipelineStatus.RUNNING,
            variables=execution_variables,
        )

        with self.execution_lock:
            self.active_executions[execution_id] = execution

        # Start execution in background
        thread = threading.Thread(
            target=self._execute_pipeline, args=(pipeline, execution, callback), daemon=True
        )
        thread.start()

        return execution_id

    def run_pipeline_sync(
        self, pipeline: Pipeline, variables: Optional[Dict[str, Any]] = None
    ) -> PipelineExecution:
        """Run pipeline synchronously and return execution result.

        Args:
            pipeline: Pipeline to execute
            variables: Override variables

        Returns:
            Completed PipelineExecution
        """
        execution_id = str(uuid.uuid4())

        # Merge variables
        execution_variables = {**pipeline.variables}
        if variables:
            execution_variables.update(variables)

        # Create execution record
        execution = PipelineExecution(
            pipeline_id=pipeline.id,
            execution_id=execution_id,
            start_time=time.time(),
            status=PipelineStatus.RUNNING,
            variables=execution_variables,
        )

        # Execute synchronously
        self._execute_pipeline(pipeline, execution, None)

        return execution

    def get_execution(self, execution_id: str) -> Optional[PipelineExecution]:
        """Get execution by ID."""
        with self.execution_lock:
            return self.active_executions.get(execution_id)

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        with self.execution_lock:
            execution = self.active_executions.get(execution_id)
            if execution and execution.status == PipelineStatus.RUNNING:
                execution.status = PipelineStatus.CANCELLED
                execution.end_time = time.time()
                return True
        return False

    def list_executions(self) -> List[PipelineExecution]:
        """List all executions."""
        with self.execution_lock:
            return list(self.active_executions.values())

    def _execute_pipeline(
        self,
        pipeline: Pipeline,
        execution: PipelineExecution,
        callback: Optional[Callable[[PipelineExecution], None]] = None,
    ) -> None:
        """Execute pipeline with dependency management."""
        try:
            # Build dependency graph
            self._build_dependency_graph(pipeline.steps)
            reverse_deps = self._build_reverse_dependencies(pipeline.steps)

            # Track completed steps
            completed_steps: Set[str] = set()
            pending_futures: Dict[str, Future] = {}
            step_executor = StepExecutor()

            # Start with root steps (no dependencies)
            ready_queue = deque(pipeline.get_roots())

            while ready_queue or pending_futures:
                # Submit ready steps
                while ready_queue:
                    step = ready_queue.popleft()
                    if step.id in completed_steps:
                        continue

                    future = self.executor.submit(
                        self._execute_step_with_retries,
                        step_executor,
                        step,
                        execution.variables,
                        step.timeout_seconds,
                    )
                    pending_futures[step.id] = future

                # Wait for completed steps
                if pending_futures:
                    for step_id, future in list(pending_futures.items()):
                        if future.done():
                            del pending_futures[step_id]

                            try:
                                result = future.result()
                                execution.steps_results[step_id] = result

                                if result["success"]:
                                    completed_steps.add(step_id)

                                    # Check if this unlocks new steps
                                    for dependent_id in reverse_deps.get(step_id, []):
                                        dependent_step = pipeline.get_step(dependent_id)
                                        if dependent_step and self._dependencies_satisfied(
                                            dependent_step, completed_steps
                                        ):
                                            ready_queue.append(dependent_step)
                                else:
                                    # Step failed - handle based on on_failure policy
                                    step = pipeline.get_step(step_id)
                                    if step and step.on_failure == "stop":
                                        execution.status = PipelineStatus.FAILED
                                        execution.error_message = (
                                            f"Step {step_id} failed: {result.get('output', '')}"
                                        )
                                        break

                            except Exception as e:
                                execution.steps_results[step_id] = {
                                    "success": False,
                                    "output": f"Execution error: {e}",
                                    "exit_code": 1,
                                    "duration": 0,
                                }

                # Small delay to prevent busy waiting
                time.sleep(0.1)

                # Check for timeout
                if (
                    pipeline.timeout_seconds
                    and (time.time() - execution.start_time) > pipeline.timeout_seconds
                ):
                    execution.status = PipelineStatus.FAILED
                    execution.error_message = (
                        f"Pipeline timed out after {pipeline.timeout_seconds} seconds"
                    )
                    break

            # Set final status
            if execution.status == PipelineStatus.RUNNING:
                execution.status = PipelineStatus.SUCCESS

        except Exception as e:
            execution.status = PipelineStatus.FAILED
            execution.error_message = f"Pipeline execution error: {e}"

        finally:
            execution.end_time = time.time()

            # Call callback if provided
            if callback:
                try:
                    callback(execution)
                except Exception:
                    pass  # Ignore callback errors

    def _execute_step_with_retries(
        self,
        executor: StepExecutor,
        step: PipelineStep,
        variables: Dict[str, Any],
        timeout: Optional[int],
    ) -> Dict[str, Any]:
        """Execute a step with retry logic."""
        last_result = None

        for attempt in range(step.retry_count + 1):
            if attempt > 0:
                time.sleep(step.retry_delay_seconds)

            result = executor.execute_step(step, variables, timeout)
            last_result = result

            if result["success"]:
                break

        return last_result

    def _build_dependency_graph(self, steps: List[PipelineStep]) -> Dict[str, List[str]]:
        """Build dependency graph (step -> dependencies)."""
        graph = {}
        for step in steps:
            graph[step.id] = step.depends_on.copy()
        return graph

    def _build_reverse_dependencies(self, steps: List[PipelineStep]) -> Dict[str, List[str]]:
        """Build reverse dependency graph (step -> dependents)."""
        reverse_deps = defaultdict(list)
        for step in steps:
            for dep in step.depends_on:
                reverse_deps[dep].append(step.id)
        return dict(reverse_deps)

    def _dependencies_satisfied(self, step: PipelineStep, completed_steps: Set[str]) -> bool:
        """Check if all dependencies of a step are satisfied."""
        return all(dep in completed_steps for dep in step.depends_on)

    def cleanup_completed_executions(self, max_age_seconds: int = 3600) -> int:
        """Clean up old completed executions.

        Args:
            max_age_seconds: Maximum age of executions to keep

        Returns:
            Number of executions cleaned up
        """
        cutoff_time = time.time() - max_age_seconds
        to_remove = []

        with self.execution_lock:
            for execution_id, execution in self.active_executions.items():
                if (
                    execution.is_complete
                    and execution.end_time
                    and execution.end_time < cutoff_time
                ):
                    to_remove.append(execution_id)

            for execution_id in to_remove:
                del self.active_executions[execution_id]

        return len(to_remove)
