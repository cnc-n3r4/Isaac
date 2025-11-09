"""
Streaming Display System
Real-time UI updates for agentic execution and tool feedback
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class DisplayMode(Enum):
    """Display modes for different UI states"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    STREAMING = "streaming"
    ERROR = "error"


@dataclass
class DisplayEvent:
    """Event for UI updates"""
    event_type: str  # 'status', 'progress', 'message', 'tool_start', 'tool_result', etc.
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class StreamingDisplay:
    """
    Real-time display system for agentic execution.

    Provides streaming updates, progress indicators, and tool execution feedback.
    """

    def __init__(self):
        self.current_mode = DisplayMode.IDLE
        self.active_tools: Dict[str, Dict[str, Any]] = {}
        self.event_listeners: List[Callable[[DisplayEvent], None]] = []
        self.status_messages: List[str] = []
        self.max_status_messages = 10

        # Threading for async updates
        self.update_lock = threading.Lock()

    def add_event_listener(self, listener: Callable[[DisplayEvent], None]):
        """Add an event listener"""
        self.event_listeners.append(listener)

    def _emit_event(self, event: DisplayEvent):
        """Emit event to all listeners"""
        with self.update_lock:
            for listener in self.event_listeners:
                try:
                    listener(event)
                except Exception as e:
                    print(f"Warning: Display event listener failed: {e}")

    def update_mode(self, mode: DisplayMode, message: Optional[str] = None):
        """Update the current display mode"""
        self.current_mode = mode

        event = DisplayEvent(
            event_type="mode_change",
            content=str(mode.value),
            metadata={"mode": mode.value, "message": message}
        )
        self._emit_event(event)

        if message:
            self.add_status_message(message)

    def add_status_message(self, message: str, level: str = "info"):
        """Add a status message to the display"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())

        if level == "error":
            formatted = f"❌ [{timestamp}] {message}"
        elif level == "warning":
            formatted = f"⚠️  [{timestamp}] {message}"
        elif level == "success":
            formatted = f"✅ [{timestamp}] {message}"
        else:
            formatted = f"ℹ️  [{timestamp}] {message}"

        self.status_messages.append(formatted)

        # Keep only recent messages
        if len(self.status_messages) > self.max_status_messages:
            self.status_messages = self.status_messages[-self.max_status_messages:]

        event = DisplayEvent(
            event_type="status_message",
            content=formatted,
            metadata={"level": level, "raw_message": message}
        )
        self._emit_event(event)

    def start_tool_execution(self, tool_name: str, tool_args: Dict[str, Any]):
        """Mark the start of tool execution"""
        execution_id = f"{tool_name}_{int(time.time() * 1000)}"

        self.active_tools[execution_id] = {
            "tool_name": tool_name,
            "tool_args": tool_args,
            "start_time": time.time(),
            "status": "running"
        }

        self.update_mode(DisplayMode.EXECUTING, f"Executing {tool_name}...")

        event = DisplayEvent(
            event_type="tool_start",
            content=f"Starting {tool_name}",
            metadata={
                "execution_id": execution_id,
                "tool_name": tool_name,
                "tool_args": tool_args
            }
        )
        self._emit_event(event)

        return execution_id

    def update_tool_progress(self, execution_id: str, progress: float, message: str):
        """Update progress for a running tool"""
        if execution_id in self.active_tools:
            self.active_tools[execution_id]["progress"] = progress
            self.active_tools[execution_id]["last_message"] = message

            event = DisplayEvent(
                event_type="tool_progress",
                content=message,
                metadata={
                    "execution_id": execution_id,
                    "progress": progress,
                    "tool_name": self.active_tools[execution_id]["tool_name"]
                }
            )
            self._emit_event(event)

    def complete_tool_execution(self, execution_id: str, result: Dict[str, Any]):
        """Mark tool execution as completed"""
        if execution_id in self.active_tools:
            tool_info = self.active_tools[execution_id]
            duration = time.time() - tool_info["start_time"]

            tool_info["status"] = "completed"
            tool_info["duration"] = duration
            tool_info["result"] = result

            success = result.get("success", False)
            level = "success" if success else "error"

            message = f"Completed {tool_info['tool_name']} in {duration:.2f}s"
            self.add_status_message(message, level)

            event = DisplayEvent(
                event_type="tool_complete",
                content=message,
                metadata={
                    "execution_id": execution_id,
                    "tool_name": tool_info["tool_name"],
                    "duration": duration,
                    "result": result,
                    "success": success
                }
            )
            self._emit_event(event)

            # Clean up after a delay
            def cleanup():
                time.sleep(5)  # Keep completed tools visible for 5 seconds
                if execution_id in self.active_tools:
                    del self.active_tools[execution_id]

            threading.Thread(target=cleanup, daemon=True).start()

    def fail_tool_execution(self, execution_id: str, error: str):
        """Mark tool execution as failed"""
        if execution_id in self.active_tools:
            tool_info = self.active_tools[execution_id]
            duration = time.time() - tool_info["start_time"]

            tool_info["status"] = "failed"
            tool_info["duration"] = duration
            tool_info["error"] = error

            message = f"Failed {tool_info['tool_name']} after {duration:.2f}s: {error}"
            self.add_status_message(message, "error")

            event = DisplayEvent(
                event_type="tool_error",
                content=message,
                metadata={
                    "execution_id": execution_id,
                    "tool_name": tool_info["tool_name"],
                    "duration": duration,
                    "error": error
                }
            )
            self._emit_event(event)

    def start_ai_thinking(self, iteration: int = 1):
        """Show AI thinking indicator"""
        self.update_mode(DisplayMode.THINKING, f"AI thinking (iteration {iteration})...")

    def show_ai_response(self, response: str, provider: str):
        """Display AI response"""
        self.update_mode(DisplayMode.STREAMING, f"AI ({provider}) responding...")

        # For streaming, we could break this into chunks
        # For now, show the full response
        event = DisplayEvent(
            event_type="ai_response",
            content=response,
            metadata={"provider": provider}
        )
        self._emit_event(event)

    def show_task_progress(self, task_description: str, progress: float):
        """Show overall task progress"""
        event = DisplayEvent(
            event_type="task_progress",
            content=f"{task_description}: {progress:.1%}",
            metadata={"progress": progress, "description": task_description}
        )
        self._emit_event(event)

    def show_error(self, error_message: str):
        """Display an error"""
        self.update_mode(DisplayMode.ERROR, error_message)
        self.add_status_message(error_message, "error")

    def get_display_state(self) -> Dict[str, Any]:
        """Get current display state for rendering"""
        return {
            "mode": self.current_mode.value,
            "active_tools": self.active_tools.copy(),
            "status_messages": self.status_messages.copy(),
            "stats": {
                "active_tool_count": len(self.active_tools),
                "total_messages": len(self.status_messages)
            }
        }

    def clear_status_messages(self):
        """Clear all status messages"""
        self.status_messages.clear()

        event = DisplayEvent(
            event_type="status_cleared",
            content="Status messages cleared"
        )
        self._emit_event(event)

    def reset(self):
        """Reset display to idle state"""
        self.current_mode = DisplayMode.IDLE
        self.active_tools.clear()
        self.clear_status_messages()

        event = DisplayEvent(
            event_type="reset",
            content="Display reset to idle state"
        )
        self._emit_event(event)