"""Command Logger Plugin - Logs all commands executed.

This plugin demonstrates hook usage and state management.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from isaac.plugins.plugin_api import Plugin, PluginMetadata, PluginContext, PluginHook


class CommandLoggerPlugin(Plugin):
    """Logs all commands executed in Isaac."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="command-logger",
            version="1.0.0",
            author="Isaac Team",
            description="Logs all commands executed with timestamps and results",
            license="MIT",
            tags=["logging", "commands", "analytics"],
            hooks=[
                PluginHook.STARTUP,
                PluginHook.BEFORE_COMMAND,
                PluginHook.AFTER_COMMAND,
                PluginHook.COMMAND_ERROR,
            ],
            commands=[],
            permissions=["file:write"],
        )

    def initialize(self, context: PluginContext) -> None:
        """Initialize the plugin.

        Args:
            context: Plugin context
        """
        self._context = context

        # Initialize log file
        log_dir = Path(context.workspace_path) / ".isaac" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_dir / "command_log.json"

        # Load existing logs
        self._logs: List[Dict[str, Any]] = []
        if self.log_file.exists():
            try:
                with open(self.log_file) as f:
                    self._logs = json.load(f)
            except Exception:
                pass

        # Register hooks
        self.register_hook(PluginHook.STARTUP, self.on_startup)
        self.register_hook(PluginHook.BEFORE_COMMAND, self.on_before_command)
        self.register_hook(PluginHook.AFTER_COMMAND, self.on_after_command)
        self.register_hook(PluginHook.COMMAND_ERROR, self.on_command_error)

    def shutdown(self) -> None:
        """Clean up plugin resources."""
        self._save_logs()

    def _save_logs(self) -> None:
        """Save logs to disk."""
        try:
            with open(self.log_file, "w") as f:
                json.dump(self._logs, f, indent=2)
        except Exception as e:
            print(f"[CommandLogger] Failed to save logs: {e}")

    def on_startup(self) -> None:
        """Handle startup hook."""
        self._log_entry("startup", "Isaac started")

    def on_before_command(self) -> None:
        """Handle before_command hook."""
        if not self._context:
            return

        command = self._context.event_data.get("command", "")
        if command:
            # Store start time for duration calculation
            self.set_state("command_start", datetime.now().isoformat())
            self.set_state("current_command", command)

    def on_after_command(self) -> None:
        """Handle after_command hook."""
        if not self._context:
            return

        command = self.get_state("current_command")
        start_time = self.get_state("command_start")

        if command:
            # Calculate duration
            duration = None
            if start_time:
                start = datetime.fromisoformat(start_time)
                duration = (datetime.now() - start).total_seconds()

            result = self._context.event_data.get("result", "success")
            self._log_entry("command", command, result=result, duration=duration)

            # Clear state
            self.set_state("current_command", None)
            self.set_state("command_start", None)

    def on_command_error(self) -> None:
        """Handle command_error hook."""
        if not self._context:
            return

        command = self.get_state("current_command")
        error = self._context.event_data.get("error", "Unknown error")

        if command:
            self._log_entry("error", command, error=str(error))

            # Clear state
            self.set_state("current_command", None)
            self.set_state("command_start", None)

    def _log_entry(
        self,
        event_type: str,
        message: str,
        result: str = None,
        error: str = None,
        duration: float = None,
    ) -> None:
        """Add a log entry.

        Args:
            event_type: Type of event
            message: Log message
            result: Command result
            error: Error message
            duration: Command duration in seconds
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
        }

        if result:
            entry["result"] = result
        if error:
            entry["error"] = error
        if duration is not None:
            entry["duration"] = duration

        self._logs.append(entry)

        # Save periodically (every 10 entries)
        if len(self._logs) % 10 == 0:
            self._save_logs()
