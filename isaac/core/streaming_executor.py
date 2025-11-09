"""
Streaming Execution Engine
Async tool execution with real-time feedback and progress tracking
"""

import asyncio
import time
from typing import Dict, Any, List, Callable, Optional, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum


class ExecutionState(Enum):
    """Execution states for streaming feedback"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionEvent:
    """Event emitted during tool execution"""
    event_type: str  # 'start', 'progress', 'result', 'error', 'cancel'
    tool_name: str
    tool_args: Dict[str, Any]
    timestamp: float
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class StreamingExecutor:
    """
    Async tool execution with real-time streaming feedback.

    Provides progress tracking, cancellation, and event streaming for UI updates.
    """

    def __init__(self, tool_registry, max_concurrent: int = 3):
        self.tool_registry = tool_registry
        self.max_concurrent = max_concurrent
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.event_listeners: List[Callable[[ExecutionEvent], None]] = []

    def add_event_listener(self, listener: Callable[[ExecutionEvent], None]):
        """Add an event listener for execution events"""
        self.event_listeners.append(listener)

    def remove_event_listener(self, listener: Callable[[ExecutionEvent], None]):
        """Remove an event listener"""
        if listener in self.event_listeners:
            self.event_listeners.remove(listener)

    def _emit_event(self, event: ExecutionEvent):
        """Emit event to all listeners"""
        for listener in self.event_listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"Warning: Event listener failed: {e}")

    async def execute_tool_streaming(self, tool_name: str, tool_args: Dict[str, Any],
                                   execution_id: Optional[str] = None) -> AsyncGenerator[ExecutionEvent, None]:
        """
        Execute a tool with streaming feedback.

        Yields events as execution progresses.
        """
        if execution_id is None:
            execution_id = f"{tool_name}_{int(time.time() * 1000)}"

        # Emit start event
        start_event = ExecutionEvent(
            event_type="start",
            tool_name=tool_name,
            tool_args=tool_args,
            timestamp=time.time(),
            message=f"Starting {tool_name} execution"
        )
        self._emit_event(start_event)
        yield start_event

        try:
            # Validate tool call
            if not self.tool_registry.validate_tool_call(tool_name, tool_args):
                error_event = ExecutionEvent(
                    event_type="error",
                    tool_name=tool_name,
                    tool_args=tool_args,
                    timestamp=time.time(),
                    message=f"Invalid tool call: {tool_name}",
                    data={"error": "validation_failed"}
                )
                self._emit_event(error_event)
                yield error_event
                return

            # Execute tool in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self.tool_registry.execute_tool,
                tool_name,
                tool_args
            )

            # Emit result event
            if result.get('success', False):
                result_event = ExecutionEvent(
                    event_type="result",
                    tool_name=tool_name,
                    tool_args=tool_args,
                    timestamp=time.time(),
                    message=f"Successfully executed {tool_name}",
                    data=result
                )
            else:
                result_event = ExecutionEvent(
                    event_type="error",
                    tool_name=tool_name,
                    tool_args=tool_args,
                    timestamp=time.time(),
                    message=f"Tool execution failed: {result.get('error', 'Unknown error')}",
                    data=result
                )

            self._emit_event(result_event)
            yield result_event

        except asyncio.CancelledError:
            cancel_event = ExecutionEvent(
                event_type="cancel",
                tool_name=tool_name,
                tool_args=tool_args,
                timestamp=time.time(),
                message=f"Execution cancelled: {tool_name}"
            )
            self._emit_event(cancel_event)
            yield cancel_event
            raise

        except Exception as e:
            error_event = ExecutionEvent(
                event_type="error",
                tool_name=tool_name,
                tool_args=tool_args,
                timestamp=time.time(),
                message=f"Unexpected error in {tool_name}: {str(e)}",
                data={"error": str(e)}
            )
            self._emit_event(error_event)
            yield error_event

    async def execute_multiple_tools(self, tool_calls: List[Dict[str, Any]],
                                   max_concurrent: Optional[int] = None) -> AsyncGenerator[ExecutionEvent, None]:
        """
        Execute multiple tools concurrently with streaming feedback.

        Args:
            tool_calls: List of {"tool_name": str, "tool_args": dict} items
            max_concurrent: Maximum concurrent executions (default: self.max_concurrent)
        """
        if max_concurrent is None:
            max_concurrent = self.max_concurrent

        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(tool_call: Dict[str, Any]):
            async with semaphore:
                tool_name = tool_call["tool_name"]
                tool_args = tool_call["tool_args"]
                async for event in self.execute_tool_streaming(tool_name, tool_args):
                    yield event

        # Create tasks for all tool calls
        tasks = [
            execute_with_semaphore(tool_call)
            for tool_call in tool_calls
        ]

        # Execute all tasks concurrently
        async for event in self._merge_async_generators(tasks):
            yield event

    async def _merge_async_generators(self, generators: List[AsyncGenerator]) -> AsyncGenerator[ExecutionEvent, None]:
        """Merge multiple async generators into one"""
        async def consume_generator(gen: AsyncGenerator) -> List[ExecutionEvent]:
            events = []
            async for event in gen:
                events.append(event)
            return events

        # Create tasks that consume each generator and collect all events
        tasks = [asyncio.create_task(consume_generator(gen)) for gen in generators]

        # Wait for all tasks and yield events in completion order
        for task in asyncio.as_completed(tasks):
            try:
                events = await task
                for event in events:
                    yield event
            except Exception as e:
                print(f"Warning: Generator task failed: {e}")

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        if execution_id in self.active_executions:
            task = self.active_executions[execution_id]
            if not task.done():
                task.cancel()
                return True
        return False

    def get_active_executions(self) -> List[str]:
        """Get list of active execution IDs"""
        return [eid for eid, task in self.active_executions.items() if not task.done()]

    def shutdown(self):
        """Shutdown the executor"""
        self.executor.shutdown(wait=True)

    # Context manager support
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()