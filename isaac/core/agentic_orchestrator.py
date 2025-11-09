"""
Agentic Orchestrator
Main agentic execution loop with AI tool calling and streaming feedback
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable
from dataclasses import dataclass

from ..adapters.base_adapter import CommandResult
from ..ui.streaming_display import StreamingDisplay, DisplayMode
from ..ui.progress_indicator import ProgressIndicator
from .streaming_executor import StreamingExecutor, ExecutionEvent
from ..tools.registry import ToolRegistry
from ..ai import AIRouter
from ..core.session_manager import SessionManager


@dataclass
class AgenticContext:
    """Context for agentic execution"""
    user_input: str
    conversation_history: List[Dict[str, Any]]
    working_files: List[str]
    project_context: Dict[str, Any]
    execution_state: Dict[str, Any]


class AgenticOrchestrator:
    """
    Modern agentic execution with streaming, context awareness, and tool calling.

    Orchestrates the complete agentic loop from user input to tool execution.
    """

    def __init__(self, session_mgr: SessionManager, streaming_display: Optional[StreamingDisplay] = None, progress_indicator: Optional[ProgressIndicator] = None):
        self.session = session_mgr
        self.tool_registry = ToolRegistry()
        self.streaming_executor = StreamingExecutor(self.tool_registry)
        self.ai_router = AIRouter(session_mgr=session_mgr)
        
        # UI components
        self.streaming_display = streaming_display
        self.progress_indicator = progress_indicator

        # Event handling
        self.event_listeners: List[Callable] = []
        self.streaming_executor.add_event_listener(self._handle_tool_event)

    def add_event_listener(self, listener: Callable):
        """Add an event listener for execution events"""
        self.event_listeners.append(listener)

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to all listeners"""
        for listener in self.event_listeners:
            try:
                listener({"type": event_type, **data})
            except Exception as e:
                print(f"Warning: Event listener failed: {e}")

    def _handle_tool_event(self, event: ExecutionEvent):
        """Handle tool execution events"""
        event_data = {
            "tool_name": event.tool_name,
            "tool_args": event.tool_args,
            "timestamp": event.timestamp,
            "message": event.message,
            "data": event.data
        }

        if event.event_type == "start":
            self._emit_event("tool_start", event_data)
        elif event.event_type == "result":
            self._emit_event("tool_result", event_data)
        elif event.event_type == "error":
            self._emit_event("tool_error", event_data)
        elif event.event_type == "cancel":
            self._emit_event("tool_cancel", event_data)

    async def execute_agentic_task(self, user_input: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute an agentic task with streaming feedback.

        Yields real-time events as the agentic loop progresses.
        """
        # Initialize context
        context = self._build_context(user_input)

        # Emit start event
        self._emit_event("task_start", {
            "user_input": user_input,
            "context": context,
            "timestamp": time.time()
        })
        yield {"type": "task_start", "user_input": user_input}

        try:
            # Analyze task complexity and select AI
            task_analysis = await self._analyze_task(user_input)
            selected_ai = self._select_ai_for_task(task_analysis)

            self._emit_event("ai_selected", {
                "ai_provider": selected_ai,
                "task_analysis": task_analysis
            })
            yield {"type": "ai_selected", "ai_provider": selected_ai}

            # Execute agentic loop
            async for event in self._stream_agentic_loop(user_input, selected_ai, context):
                yield event

        except Exception as e:
            error_event = {
                "type": "task_error",
                "error": str(e),
                "timestamp": time.time()
            }
            self._emit_event("task_error", error_event)
            yield error_event

    def execute_agentic_task_sync(self, user_input: str) -> CommandResult:
        """
        Synchronous wrapper for agentic task execution.
        
        Returns CommandResult for integration with command router.
        """
        # Initialize UI components if available
        if self.streaming_display:
            self.streaming_display.update_mode(DisplayMode.THINKING, f"Starting agentic task: {user_input}")
        
        if self.progress_indicator:
            self.progress_indicator.start(f"Processing: {user_input}")

        # Collect all events from async execution
        events = []
        final_result = None
        
        async def collect_events():
            nonlocal events, final_result
            try:
                async for event in self.execute_agentic_task(user_input):
                    events.append(event)
                    
                    # Update UI based on event type
                    if self.streaming_display:
                        if event["type"] == "ai_selected":
                            self.streaming_display.update_mode(
                                DisplayMode.THINKING, 
                                f"Using {event['ai_provider']}"
                            )
                        elif event["type"] == "tool_start":
                            self.streaming_display.add_status_message(
                                f"Executing tool: {event.get('tool_name', 'unknown')}", 
                                "info"
                            )
                        elif event["type"] == "tool_result":
                            success = event.get("success", False)
                            level = "success" if success else "error"
                            self.streaming_display.add_status_message(
                                f"Tool completed: {event.get('tool_name', 'unknown')}", 
                                level
                            )
                        elif event["type"] == "task_complete":
                            final_result = event
                            self.streaming_display.update_mode(
                                DisplayMode.IDLE, 
                                "Task completed successfully"
                            )
                        elif event["type"] == "task_error":
                            final_result = event
                            self.streaming_display.update_mode(
                                DisplayMode.ERROR, 
                                f"Task failed: {event.get('error', 'Unknown error')}"
                            )
                    
                    if self.progress_indicator and event["type"] == "task_progress":
                        progress = event.get("progress", 0.0)
                        self.progress_indicator.update(progress, event.get("message", ""))
                
            except Exception as e:
                final_result = {"type": "task_error", "error": str(e)}
                if self.streaming_display:
                    self.streaming_display.show_error(str(e))

        # Run the async collection
        asyncio.run(collect_events())
        
        # Complete progress indicator
        if self.progress_indicator:
            if final_result and final_result.get("type") == "task_error":
                self.progress_indicator.fail("Task failed")
            else:
                self.progress_indicator.complete("Task completed")

        # Build CommandResult from final result
        if final_result and final_result.get("type") == "task_error":
            return CommandResult(
                success=False,
                output=f"Agentic task failed: {final_result.get('error', 'Unknown error')}",
                exit_code=1
            )
        else:
            # Collect output from all events
            output_lines = []
            for event in events:
                if event["type"] == "tool_result" and "output" in event:
                    output_lines.append(f"Tool output: {event['output']}")
                elif event["type"] == "ai_response" and "response" in event:
                    output_lines.append(f"AI: {event['response']}")
            
            # Add success message if no output collected
            if not output_lines:
                output_lines.append("Agentic task completed successfully")
            
            output = "\n".join(output_lines) if output_lines else "Agentic task completed successfully"
            
            return CommandResult(
                success=True,
                output=output,
                exit_code=0
            )

    def _build_context(self, user_input: str) -> AgenticContext:
        """Build execution context from user input and session state"""
        # Get recent command history
        conversation_history = self.session.get_recent_commands(limit=10)

        # Get working files (recently accessed) - for now, empty list
        working_files = []

        # Get project context
        project_context = {
            "current_directory": self.session.config.get('current_directory', '.'),
            "project_root": self.session.config.get('project_root'),
            "recent_commands": conversation_history[-5:]  # These are strings
        }

        return AgenticContext(
            user_input=user_input,
            conversation_history=conversation_history,
            working_files=working_files,
            project_context=project_context,
            execution_state={}
        )

    async def _analyze_task(self, user_input: str) -> Dict[str, Any]:
        """Analyze task complexity and requirements"""
        # Simple heuristic analysis for now
        # TODO: Use AI to analyze task complexity

        analysis = {
            "complexity": "medium",  # low, medium, high
            "requires_tools": True,
            "task_type": "coding",  # coding, analysis, search, etc.
            "estimated_steps": 2,
            "risk_level": "low"
        }

        # Analyze user input for complexity indicators
        input_lower = user_input.lower()
        if any(word in input_lower for word in ['fix', 'debug', 'refactor', 'implement']):
            analysis["complexity"] = "high"
            analysis["estimated_steps"] = 4
            analysis["risk_level"] = "medium"
        elif any(word in input_lower for word in ['read', 'show', 'list', 'find']):
            analysis["complexity"] = "low"
            analysis["estimated_steps"] = 1
            analysis["risk_level"] = "low"

        return analysis

    def _select_ai_for_task(self, task_analysis: Dict[str, Any]) -> str:
        """Select optimal AI provider for the task"""
        complexity = task_analysis.get("complexity", "medium")

        if complexity == "high":
            return "claude"  # Best for complex reasoning
        elif complexity == "low":
            return "grok"   # Fast and cheap for simple tasks
        else:
            return "claude" # Default to Claude for medium complexity

    async def _stream_agentic_loop(self, user_input: str, ai_provider: str,
                                 context: AgenticContext) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Main agentic execution loop with streaming feedback.
        """
        # Build initial messages
        messages = self._build_messages(user_input, context)

        # Get available tools for this task
        available_tools = self.tool_registry.get_tools_for_task(context.project_context.get("task_type", "coding"))

        max_iterations = 10  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Emit thinking event
            self._emit_event("ai_thinking", {
                "iteration": iteration,
                "messages_count": len(messages)
            })
            yield {"type": "ai_thinking", "iteration": iteration}

            # Get AI response with tool calling
            try:
                response = self.ai_router.chat(
                    messages=messages,
                    tools=available_tools,
                    prefer_provider=ai_provider,
                    max_tokens=4096
                )

                if not response.success:
                    yield {"type": "ai_error", "error": response.error}
                    break

                # Add AI response to conversation
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Emit AI response
                self._emit_event("ai_response", {
                    "content": response.content,
                    "provider": response.provider,
                    "usage": response.usage
                })
                yield {"type": "ai_response", "content": response.content}

                # Check for tool calls
                if response.tool_calls:
                    # Execute tools
                    tool_results = []
                    for tool_call in response.tool_calls:
                        tool_name = tool_call.name
                        tool_args = tool_call.arguments

                        # Execute tool with streaming
                        last_event = None
                        async for event in self.streaming_executor.execute_tool_streaming(
                            tool_name, tool_args
                        ):
                            last_event = event
                            yield {
                                "type": f"tool_{event.event_type}",
                                "tool_name": tool_name,
                                "data": event.data,
                                "message": event.message
                            }

                        # Get final result for conversation
                        if last_event and last_event.event_type == "result":
                            tool_results.append({
                                "tool_call_id": tool_call.id,
                                "function_name": tool_name,
                                "content": last_event.data
                            })

                    # Add tool results to conversation
                    if tool_results:
                        messages.append({
                            "role": "tool",
                            "content": str(tool_results)
                        })

                else:
                    # No tool calls - this is the final answer
                    self._emit_event("task_complete", {
                        "final_answer": response.content,
                        "iterations": iteration
                    })
                    yield {"type": "task_complete", "final_answer": response.content}
                    break

            except Exception as e:
                yield {"type": "execution_error", "error": str(e)}
                break

        if iteration >= max_iterations:
            yield {"type": "max_iterations_reached", "iterations": iteration}

    def _build_messages(self, user_input: str, context: AgenticContext) -> List[Dict[str, str]]:
        """Build conversation messages for AI"""
        messages = []

        # Add system prompt
        system_prompt = self._build_system_prompt(context)
        messages.append({"role": "system", "content": system_prompt})

        # For now, just add the current user input
        # TODO: Add proper conversation history when available
        messages.append({"role": "user", "content": user_input})

        return messages

    def _build_system_prompt(self, context: AgenticContext) -> str:
        """Build system prompt with context awareness"""
        prompt = """You are Isaac, an AI assistant integrated into a developer's workflow.

You have access to various tools to help with coding tasks. Use them appropriately:

FILE OPERATIONS:
- read: Read file contents with line numbers
- edit: Edit files by replacing exact strings
- write: Create new files
- grep: Search files for patterns
- glob: Find files matching patterns

When using tools:
1. Choose the right tool for the task
2. Provide accurate parameters
3. Use the results to inform your next steps

Be helpful, precise, and efficient. If you can complete a task without tools, do so directly.
"""

        # Add project context
        if context.project_context.get("project_root"):
            prompt += f"\nProject root: {context.project_context['project_root']}"

        if context.working_files:
            prompt += f"\nWorking files: {', '.join(context.working_files)}"

        return prompt

    def cancel_current_task(self) -> bool:
        """Cancel the currently running task"""
        # TODO: Implement task cancellation
        return False

    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status"""
        return {
            "active_executions": self.streaming_executor.get_active_executions(),
            "available_tools": len(self.tool_registry.tools),
            "ai_providers": self.ai_router.get_available_providers()
        }