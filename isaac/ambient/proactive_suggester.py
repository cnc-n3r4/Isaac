"""
Proactive Suggestions - Offer help before user asks
Isaac's ambient intelligence system for proactive assistance
"""

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from isaac.ambient.workflow_learner import WorkflowLearner


@dataclass
class Suggestion:
    """Represents a proactive suggestion."""

    suggestion_id: str
    type: str  # 'pipeline', 'command', 'workflow', 'fix', 'optimization'
    title: str
    description: str
    confidence: float  # 0-1
    context: Dict[str, Any]  # Additional context data
    timestamp: float
    expires_at: Optional[float] = None  # When this suggestion expires
    actions: Optional[List[Dict[str, Any]]] = None  # Available actions to take

    def is_expired(self) -> bool:
        """Check if this suggestion has expired."""
        return self.expires_at is not None and time.time() > self.expires_at


class ProactiveSuggester:
    """Provides proactive suggestions based on user behavior and context."""

    def __init__(self, workflow_learner: Optional[WorkflowLearner] = None):
        """Initialize proactive suggester.

        Args:
            workflow_learner: Workflow learner instance
        """
        self.workflow_learner = workflow_learner or WorkflowLearner()
        self.suggestions: Dict[str, Suggestion] = {}
        self.context_history: List[Dict[str, Any]] = []
        self.max_context_history = 100
        self.suggestion_timeout = 3600  # 1 hour

        # Context tracking
        self.current_context = {
            "last_command": "",
            "command_count": 0,
            "error_count": 0,
            "time_since_last_command": 0,
            "current_directory": "",
            "git_branch": "",
            "active_files": [],
        }

        # Load existing suggestions
        self._load_suggestions()

        # Start background analysis
        self.analysis_thread = threading.Thread(target=self._background_analysis, daemon=True)
        self.analysis_thread.start()

    def _load_suggestions(self) -> None:
        """Load previously generated suggestions."""
        suggestion_file = Path.home() / ".isaac" / "proactive_suggestions.json"
        if suggestion_file.exists():
            try:
                with open(suggestion_file, "r") as f:
                    data = json.load(f)
                    for suggestion_data in data.get("suggestions", []):
                        suggestion = Suggestion(**suggestion_data)
                        if not suggestion.is_expired():
                            self.suggestions[suggestion.suggestion_id] = suggestion
            except Exception as e:
                print(f"Warning: Could not load suggestions: {e}")

    def _save_suggestions(self) -> None:
        """Save suggestions to disk."""
        suggestion_file = Path.home() / ".isaac" / "proactive_suggestions.json"
        suggestion_file.parent.mkdir(exist_ok=True)

        data = {
            "suggestions": [vars(s) for s in self.suggestions.values()],
            "last_updated": time.time(),
        }

        try:
            with open(suggestion_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save suggestions: {e}")

    def update_context(self, context_update: Dict[str, Any]) -> None:
        """Update current context with new information.

        Args:
            context_update: Dictionary of context updates
        """
        self.current_context.update(context_update)
        self.current_context["time_since_last_command"] = time.time()

        # Add to history
        self.context_history.append({"timestamp": time.time(), "context": context_update.copy()})

        # Trim history
        if len(self.context_history) > self.max_context_history:
            self.context_history = self.context_history[-self.max_context_history :]

    def on_command_executed(self, command: str, success: bool, output: str = "") -> None:
        """Called when a command is executed.

        Args:
            command: The command that was executed
            success: Whether the command succeeded
            output: Command output (truncated)
        """
        self.update_context(
            {
                "last_command": command,
                "command_count": self.current_context["command_count"] + 1,
                "time_since_last_command": 0,
            }
        )

        if not success:
            self.current_context["error_count"] += 1
            # Generate error-related suggestions
            self._generate_error_suggestions(command, output)

        # Generate pattern-based suggestions
        self._generate_pattern_suggestions(command)

    def get_suggestions(self, limit: int = 5) -> List[Suggestion]:
        """Get current proactive suggestions.

        Args:
            limit: Maximum number of suggestions to return

        Returns:
            List of current suggestions, ordered by confidence
        """
        # Clean expired suggestions
        self._clean_expired_suggestions()

        # Return top suggestions by confidence
        active_suggestions = [s for s in self.suggestions.values() if not s.is_expired()]

        return sorted(active_suggestions, key=lambda s: s.confidence, reverse=True)[:limit]

    def _clean_expired_suggestions(self) -> None:
        """Remove expired suggestions."""
        expired_ids = [
            sid for sid, suggestion in self.suggestions.items() if suggestion.is_expired()
        ]

        for sid in expired_ids:
            del self.suggestions[sid]

    def _generate_error_suggestions(self, command: str, output: str) -> None:
        """Generate suggestions based on command errors."""
        suggestion_id = f"error_fix_{int(time.time())}"

        # Analyze error patterns
        if "command not found" in output.lower():
            suggestion = Suggestion(
                suggestion_id=suggestion_id,
                type="fix",
                title="Command Not Found",
                description=f"The command '{command.split()[0]}' was not found. Check if it's installed or if there's a typo.",
                confidence=0.9,
                context={"command": command, "error": "command_not_found"},
                timestamp=time.time(),
                expires_at=time.time() + self.suggestion_timeout,
                actions=[
                    {
                        "label": "Search for similar commands",
                        "command": f"/help search {command.split()[0]}",
                    },
                    {"label": "Check installation", "command": f"which {command.split()[0]}"},
                ],
            )
        elif "permission denied" in output.lower():
            suggestion = Suggestion(
                suggestion_id=suggestion_id,
                type="fix",
                title="Permission Denied",
                description=f"Permission denied for '{command}'. You may need to run with sudo or check file permissions.",
                confidence=0.8,
                context={"command": command, "error": "permission_denied"},
                timestamp=time.time(),
                expires_at=time.time() + self.suggestion_timeout,
                actions=[
                    {"label": "Try with sudo", "command": f"sudo {command}"},
                    {
                        "label": "Check permissions",
                        "command": f'ls -la {command.split()[-1] if len(command.split()) > 1 else "."}',
                    },
                ],
            )
        else:
            # Generic error suggestion
            suggestion = Suggestion(
                suggestion_id=suggestion_id,
                type="fix",
                title="Command Failed",
                description=f"The command '{command}' failed. Check the error message above for details.",
                confidence=0.6,
                context={"command": command, "error": "generic"},
                timestamp=time.time(),
                expires_at=time.time() + self.suggestion_timeout,
                actions=[
                    {"label": "Get help", "command": f"/help {command.split()[0]}"},
                    {"label": "Check logs", "command": 'echo "Check error output above"'},
                ],
            )

        self.suggestions[suggestion_id] = suggestion
        self._save_suggestions()

    def _generate_pattern_suggestions(self, command: str) -> None:
        """Generate suggestions based on command patterns."""
        # Get pattern suggestions from workflow learner
        pattern_suggestions = self.workflow_learner.get_pattern_suggestions(command)

        for i, pattern_sug in enumerate(pattern_suggestions):
            suggestion_id = f"pattern_{int(time.time())}_{i}"

            if pattern_sug["type"] == "pipeline_suggestion":
                suggestion = Suggestion(
                    suggestion_id=suggestion_id,
                    type="pipeline",
                    title="Create Pipeline for Repeated Commands",
                    description=f"You've run this sequence {pattern_sug['frequency']} times. Create a pipeline to automate it?",
                    confidence=min(pattern_sug["frequency"] / 10.0, 0.9),
                    context={"pattern": pattern_sug},
                    timestamp=time.time(),
                    expires_at=time.time()
                    + self.suggestion_timeout * 2,  # Longer timeout for pipeline suggestions
                    actions=[
                        {
                            "label": "Create Pipeline",
                            "command": f'/pipeline create "Auto {command.split()[0]}" -t custom',
                        },
                        {
                            "label": "View Pattern",
                            "command": f'/ambient patterns show {pattern_sug["pattern_id"]}',
                        },
                    ],
                )
            elif pattern_sug["type"] == "command_completion":
                next_cmds = pattern_sug.get("next_commands", [])
                if next_cmds:
                    suggestion = Suggestion(
                        suggestion_id=suggestion_id,
                        type="command",
                        title="Continue Command Sequence",
                        description=f"Based on your patterns, you might want to run: {'; '.join(next_cmds[:2])}",
                        confidence=0.7,
                        context={"pattern": pattern_sug},
                        timestamp=time.time(),
                        expires_at=time.time() + 300,  # 5 minutes for command suggestions
                        actions=[
                            {"label": f"Run {next_cmds[0]}", "command": next_cmds[0]},
                            {
                                "label": "Show full sequence",
                                "command": f'/ambient patterns show {pattern_sug["pattern"]["pattern_id"]}',
                            },
                        ],
                    )
                else:
                    continue
            else:
                continue

            self.suggestions[suggestion_id] = suggestion

        if pattern_suggestions:
            self._save_suggestions()

    def _generate_contextual_suggestions(self) -> None:
        """Generate suggestions based on current context."""
        context = self.current_context

        # High error rate detection
        if context["error_count"] > context["command_count"] * 0.3:  # >30% error rate
            suggestion_id = f"context_errors_{int(time.time())}"
            suggestion = Suggestion(
                suggestion_id=suggestion_id,
                type="optimization",
                title="High Error Rate Detected",
                description="You're experiencing many command failures. Consider checking your environment or getting help.",
                confidence=0.8,
                context={"error_rate": context["error_count"] / max(context["command_count"], 1)},
                timestamp=time.time(),
                expires_at=time.time() + self.suggestion_timeout,
                actions=[
                    {"label": "Check environment", "command": "env | head -20"},
                    {"label": "Get help", "command": "/help troubleshooting"},
                ],
            )
            self.suggestions[suggestion_id] = suggestion

        # Long idle time detection
        if context["time_since_last_command"] > 1800:  # 30 minutes
            suggestion_id = f"context_idle_{int(time.time())}"
            suggestion = Suggestion(
                suggestion_id=suggestion_id,
                type="workflow",
                title="Welcome Back!",
                description="It's been a while since your last command. Need help getting back to work?",
                confidence=0.5,
                context={"idle_time": context["time_since_last_command"]},
                timestamp=time.time(),
                expires_at=time.time() + 600,  # 10 minutes
                actions=[
                    {"label": "Show recent commands", "command": "/history recent"},
                    {"label": "Check status", "command": "/status"},
                ],
            )
            self.suggestions[suggestion_id] = suggestion

    def _background_analysis(self) -> None:
        """Background thread for continuous analysis."""
        while True:
            try:
                # Periodic analysis
                self._generate_contextual_suggestions()

                # Clean expired suggestions
                self._clean_expired_suggestions()

                # Save state periodically
                self._save_suggestions()

            except Exception as e:
                print(f"Background analysis error: {e}")

            time.sleep(60)  # Run every minute

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about what the system has learned."""
        return {
            "total_suggestions": len(self.suggestions),
            "active_suggestions": len([s for s in self.suggestions.values() if not s.is_expired()]),
            "patterns_learned": len(self.workflow_learner.patterns),
            "workflows_learned": len(self.workflow_learner.workflows),
            "context_history_size": len(self.context_history),
            "current_error_rate": self.current_context["error_count"]
            / max(self.current_context["command_count"], 1),
        }
