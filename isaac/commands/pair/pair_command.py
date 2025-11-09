"""
Pair Command - Interface for collaborative pair programming
Provides access to AI pair mode, task division, code review, and metrics
"""

import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from isaac.core.session_manager import SessionManager
from isaac.pairing import (
    PairProgrammingMode,
    TaskDivider,
    CodeReviewer,
    SuggestionSystem,
    PairingLearner,
    PairMetrics,
    PairRole,
    PairStyle,
    TaskPriority,
    TaskAssignee,
    ReviewSeverity
)


class PairCommand:
    """Command interface for collaborative pair programming."""

    def __init__(self, session_manager: Optional[SessionManager] = None):
        """Initialize pair command.

        Args:
            session_manager: Session manager instance (creates default if None)
        """
        self.session_manager = session_manager or SessionManager()

        # Initialize pairing components
        self.pair_mode = PairProgrammingMode(self.session_manager)
        self.task_divider = TaskDivider(self.session_manager)
        self.code_reviewer = CodeReviewer(self.session_manager)
        self.suggestion_system = SuggestionSystem(self.session_manager)
        self.pairing_learner = PairingLearner(self.session_manager, start_background_learning=True)
        self.metrics = PairMetrics(self.session_manager)

    def execute(self, args: List[str]) -> Dict[str, Any]:
        """Execute pair command.

        Args:
            args: Command arguments

        Returns:
            Command result
        """
        if not args:
            return self._show_status()

        subcommand = args[0].lower()

        if subcommand == 'start':
            return self._start_session(args[1:])
        elif subcommand == 'end':
            return self._end_session(args[1:])
        elif subcommand == 'switch':
            return self._switch_roles(args[1:])
        elif subcommand == 'tasks':
            return self._show_tasks(args[1:])
        elif subcommand == 'divide':
            return self._divide_task(args[1:])
        elif subcommand == 'review':
            return self._review_code(args[1:])
        elif subcommand == 'suggest':
            return self._show_suggestions(args[1:])
        elif subcommand == 'learn':
            return self._show_learning(args[1:])
        elif subcommand == 'metrics':
            return self._show_metrics(args[1:])
        elif subcommand == 'history':
            return self._show_history(args[1:])
        elif subcommand == 'help':
            return self._show_help()
        else:
            return {
                'success': False,
                'output': f"Unknown subcommand: {subcommand}\n{self._get_help_text()}",
                'exit_code': 1
            }

    def _show_status(self) -> Dict[str, Any]:
        """Show current pairing status."""
        session = self.pair_mode.get_active_session()

        output = "🤝 Pair Programming Status\n"
        output += "=" * 60 + "\n\n"

        if session:
            duration = datetime.now().timestamp() - session.start_time
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)

            output += f"📍 Active Session: {session.id[:8]}...\n"
            output += f"⏱️  Duration: {hours}h {minutes}m\n"
            output += f"🎯 Task: {session.task_description}\n"
            output += f"🎭 Style: {session.pair_style}\n"
            output += f"👤 Your Role: {session.human_role}\n"
            output += f"🤖 Isaac's Role: {session.current_role}\n"
            output += f"📝 Files Touched: {len(session.files_touched)}\n\n"

            # Show active tasks
            tasks = self.task_divider.get_session_tasks(session.id)
            if tasks:
                output += f"📋 Tasks ({len(tasks)} total):\n"
                for task in tasks[:5]:
                    status_icon = "✅" if task.status == "completed" else "🔄" if task.status == "in_progress" else "⏳"
                    output += f"   {status_icon} {task.title} ({task.assignee})\n"

                if len(tasks) > 5:
                    output += f"   ... and {len(tasks) - 5} more\n"
        else:
            output += "No active pairing session.\n"
            output += "\nStart a session with: /pair start <task-description>\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _start_session(self, args: List[str]) -> Dict[str, Any]:
        """Start a new pairing session."""
        if not args:
            return {
                'success': False,
                'output': 'Usage: /pair start <task-description> [--style <style>] [--role <role>]',
                'exit_code': 1
            }

        # Parse arguments
        task_description = args[0]
        style = PairStyle.DRIVER_NAVIGATOR
        role = PairRole.NAVIGATOR

        # Simple argument parsing
        i = 1
        while i < len(args):
            if args[i] == '--style' and i + 1 < len(args):
                style_map = {
                    'ping-pong': PairStyle.PING_PONG,
                    'driver-navigator': PairStyle.DRIVER_NAVIGATOR,
                    'collaborative': PairStyle.COLLABORATIVE,
                    'async': PairStyle.ASYNCHRONOUS
                }
                style = style_map.get(args[i + 1], PairStyle.DRIVER_NAVIGATOR)
                i += 2
            elif args[i] == '--role' and i + 1 < len(args):
                role_map = {
                    'driver': PairRole.DRIVER,
                    'navigator': PairRole.NAVIGATOR,
                    'both': PairRole.BOTH
                }
                role = role_map.get(args[i + 1], PairRole.NAVIGATOR)
                i += 2
            else:
                i += 1

        session = self.pair_mode.start_session(task_description, style, role)

        output = "🎉 Pair Programming Session Started!\n\n"
        output += f"Session ID: {session.id[:8]}...\n"
        output += f"Task: {task_description}\n"
        output += f"Style: {style.value}\n"
        output += f"Your Role: {session.human_role}\n"
        output += f"Isaac's Role: {session.current_role}\n\n"
        output += "Let's build something great together! 🚀\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _end_session(self, args: List[str]) -> Dict[str, Any]:
        """End the current pairing session."""
        session = self.pair_mode.get_active_session()

        if not session:
            return {
                'success': False,
                'output': 'No active pairing session.',
                'exit_code': 1
            }

        # Calculate metrics before ending
        session_data = {
            'start_time': session.start_time,
            'end_time': datetime.now().timestamp(),
            'files_touched': session.files_touched,
            'tasks_total': len(self.task_divider.get_session_tasks(session.id))
        }

        metrics = self.metrics.calculate_session_metrics(session.id, session_data)

        # End the session
        self.pair_mode.end_session(session.id)

        duration = session_data['end_time'] - session_data['start_time']
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)

        output = "🏁 Pair Programming Session Ended\n\n"
        output += f"Duration: {hours}h {minutes}m\n"
        output += f"Tasks Completed: {metrics.tasks_completed}/{metrics.tasks_total}\n"
        output += f"Files Modified: {metrics.files_modified}\n\n"

        output += "📊 Session Scores:\n"
        output += f"  Productivity:    {metrics.productivity_score:5.1f}/100 {self._get_score_bar(metrics.productivity_score)}\n"
        output += f"  Collaboration:   {metrics.collaboration_score:5.1f}/100 {self._get_score_bar(metrics.collaboration_score)}\n"
        output += f"  Code Quality:    {metrics.code_quality_score:5.1f}/100 {self._get_score_bar(metrics.code_quality_score)}\n"
        output += f"  Learning:        {metrics.learning_score:5.1f}/100 {self._get_score_bar(metrics.learning_score)}\n"
        output += f"  Overall:         {metrics.overall_score:5.1f}/100 {self._get_score_bar(metrics.overall_score)}\n\n"

        output += "Great work! 🎊\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _switch_roles(self, args: List[str]) -> Dict[str, Any]:
        """Switch roles between driver and navigator."""
        try:
            isaac_role, human_role = self.pair_mode.switch_roles()

            output = "🔄 Roles Switched!\n\n"
            output += f"Your New Role: {human_role}\n"
            output += f"Isaac's New Role: {isaac_role}\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except ValueError as e:
            return {
                'success': False,
                'output': str(e),
                'exit_code': 1
            }

    def _show_tasks(self, args: List[str]) -> Dict[str, Any]:
        """Show tasks for the current session."""
        session = self.pair_mode.get_active_session()

        if not session:
            return {
                'success': False,
                'output': 'No active pairing session.',
                'exit_code': 1
            }

        tasks = self.task_divider.get_session_tasks(session.id)

        output = f"📋 Tasks for Session {session.id[:8]}...\n"
        output += "=" * 60 + "\n\n"

        if not tasks:
            output += "No tasks yet. Use '/pair divide' to create tasks.\n"
        else:
            for task in tasks:
                status_icon = {
                    'completed': '✅',
                    'in_progress': '🔄',
                    'pending': '⏳',
                    'blocked': '🚫',
                    'cancelled': '❌'
                }.get(task.status, '❓')

                priority_icon = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(task.priority, '⚪')

                assignee_icon = {
                    'isaac': '🤖',
                    'human': '👤',
                    'both': '👥',
                    'unassigned': '❓'
                }.get(task.assignee, '❓')

                output += f"{status_icon} {priority_icon} {assignee_icon} {task.title}\n"
                output += f"   {task.description}\n"
                if task.dependencies:
                    output += f"   Depends on: {len(task.dependencies)} task(s)\n"
                output += "\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _divide_task(self, args: List[str]) -> Dict[str, Any]:
        """Divide a task into subtasks."""
        if not args:
            return {
                'success': False,
                'output': 'Usage: /pair divide <task-description>',
                'exit_code': 1
            }

        task_description = ' '.join(args)
        suggested_tasks = self.task_divider.suggest_task_division(task_description)

        output = "🔍 Suggested Task Division\n"
        output += "=" * 60 + "\n\n"

        for i, task in enumerate(suggested_tasks, 1):
            assignee_icon = {
                'isaac': '🤖',
                'human': '👤',
                'both': '👥'
            }.get(task.assignee, '❓')

            output += f"{i}. {assignee_icon} {task.title}\n"
            output += f"   {task.description}\n"
            output += f"   Priority: {task.priority}\n"
            if task.estimated_minutes:
                output += f"   Estimated: {task.estimated_minutes} minutes\n"
            output += "\n"

        output += f"Created {len(suggested_tasks)} tasks.\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _review_code(self, args: List[str]) -> Dict[str, Any]:
        """Review code in a file."""
        if not args:
            # Show unresolved suggestions
            suggestions = self.code_reviewer.get_unresolved_suggestions()

            output = "🔍 Code Review Suggestions\n"
            output += "=" * 60 + "\n\n"

            if not suggestions:
                output += "No unresolved suggestions. Great job! ✨\n"
            else:
                by_file = {}
                for suggestion in suggestions:
                    if suggestion.file_path not in by_file:
                        by_file[suggestion.file_path] = []
                    by_file[suggestion.file_path].append(suggestion)

                for file_path, file_suggestions in by_file.items():
                    output += f"\n📄 {file_path}\n"
                    for suggestion in file_suggestions:
                        severity_icon = {
                            'error': '🔴',
                            'warning': '🟠',
                            'suggestion': '🟡',
                            'info': '🔵'
                        }.get(suggestion.severity, '⚪')

                        output += f"  Line {suggestion.line_number}: {severity_icon} {suggestion.message}\n"
                        output += f"    {suggestion.suggestion}\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        else:
            # Review specific file
            file_path = args[0]

            if not Path(file_path).exists():
                return {
                    'success': False,
                    'output': f'File not found: {file_path}',
                    'exit_code': 1
                }

            suggestions = self.code_reviewer.review_code(file_path)

            output = f"🔍 Code Review: {file_path}\n"
            output += "=" * 60 + "\n\n"

            if not suggestions:
                output += "No issues found. Looks great! ✨\n"
            else:
                for suggestion in suggestions:
                    severity_icon = {
                        'error': '🔴',
                        'warning': '🟠',
                        'suggestion': '🟡',
                        'info': '🔵'
                    }.get(suggestion.severity, '⚪')

                    output += f"Line {suggestion.line_number}: {severity_icon} {suggestion.message}\n"
                    output += f"  Code: {suggestion.code_snippet}\n"
                    output += f"  {suggestion.suggestion}\n\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }

    def _show_suggestions(self, args: List[str]) -> Dict[str, Any]:
        """Show suggestion statistics."""
        stats = self.suggestion_system.get_suggestion_statistics(days=30)

        output = "💡 Suggestion Statistics (Last 30 Days)\n"
        output += "=" * 60 + "\n\n"

        output += f"Total Suggestions: {stats['total_suggestions']}\n"
        output += f"Accepted: {stats['accepted_suggestions']}\n"
        output += f"Rejected: {stats['rejected_suggestions']}\n"
        output += f"Pending: {stats['pending_suggestions']}\n"
        output += f"Acceptance Rate: {stats['acceptance_rate']:.1%}\n"
        output += f"Average Confidence: {stats['average_confidence']:.2f}\n\n"

        if stats['by_type']:
            output += "By Type:\n"
            for suggestion_type, count in stats['by_type'].items():
                output += f"  {suggestion_type}: {count}\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _show_learning(self, args: List[str]) -> Dict[str, Any]:
        """Show learned preferences and patterns."""
        preferences = self.pairing_learner.get_style_preferences()

        output = "🧠 Learned Coding Preferences\n"
        output += "=" * 60 + "\n\n"

        if not preferences:
            output += "No preferences learned yet. Keep pairing to help Isaac learn your style!\n"
        else:
            for category, pref in preferences.items():
                confidence_bar = self._get_score_bar(pref.confidence * 100)
                output += f"📌 {category.title()}\n"
                output += f"   {pref.preference}\n"
                output += f"   Confidence: {confidence_bar} {pref.confidence:.1%}\n"
                if pref.examples:
                    output += f"   Examples: {', '.join(pref.examples[:3])}\n"
                output += "\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _show_metrics(self, args: List[str]) -> Dict[str, Any]:
        """Show pairing metrics."""
        stats = self.metrics.get_aggregate_metrics(days=30)

        output = "📊 Pair Programming Metrics (Last 30 Days)\n"
        output += "=" * 60 + "\n\n"

        output += f"Total Sessions: {stats['total_sessions']}\n"
        output += f"Total Hours: {stats['totals']['total_hours']:.1f}h\n"
        output += f"Tasks Completed: {stats['totals']['tasks_completed']}\n"
        output += f"Suggestions Made: {stats['totals']['suggestions_made']}\n"
        output += f"Code Reviews: {stats['totals']['code_reviews_performed']}\n\n"

        output += "Average Scores:\n"
        for metric_name, score in stats['average_scores'].items():
            bar = self._get_score_bar(score)
            output += f"  {metric_name.title():15} {score:5.1f}/100 {bar}\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _show_history(self, args: List[str]) -> Dict[str, Any]:
        """Show session history."""
        sessions = self.pair_mode.get_session_history(limit=10)

        output = "📜 Pair Programming History\n"
        output += "=" * 60 + "\n\n"

        if not sessions:
            output += "No pairing sessions yet.\n"
        else:
            for session in sessions:
                start_time = datetime.fromtimestamp(session.start_time)
                if session.end_time:
                    duration = session.end_time - session.start_time
                    hours = int(duration // 3600)
                    minutes = int((duration % 3600) // 60)
                    duration_str = f"{hours}h {minutes}m"
                    status = "✅"
                else:
                    duration_str = "In Progress"
                    status = "🔄"

                output += f"{status} {start_time.strftime('%Y-%m-%d %H:%M')}\n"
                output += f"   Task: {session.task_description}\n"
                output += f"   Duration: {duration_str}\n"
                output += f"   Style: {session.pair_style}\n"
                output += f"   Files: {len(session.files_touched)}\n\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _show_help(self) -> Dict[str, Any]:
        """Show help information."""
        return {
            'success': True,
            'output': self._get_help_text(),
            'exit_code': 0
        }

    def _get_help_text(self) -> str:
        """Get help text."""
        return """
🤝 Pair Programming Command

Usage: /pair <subcommand> [options]

Subcommands:
  start <task>    Start a new pairing session
  end             End the current session
  switch          Switch roles (driver ↔ navigator)
  tasks           Show tasks for current session
  divide <task>   Divide a task into subtasks
  review [file]   Review code (or show suggestions)
  suggest         Show suggestion statistics
  learn           Show learned preferences
  metrics         Show pairing metrics
  history         Show session history
  help            Show this help

Options for 'start':
  --style <style>  Pairing style (ping-pong, driver-navigator, collaborative, async)
  --role <role>    Isaac's role (driver, navigator, both)

Examples:
  /pair start "Implement user authentication"
  /pair start "Fix bug #123" --style ping-pong --role driver
  /pair divide "Add payment integration"
  /pair review src/main.py
  /pair metrics

Learn more: https://docs.isaac.dev/pair-programming
"""

    def _get_score_bar(self, score: float) -> str:
        """Get a visual bar for a score.

        Args:
            score: Score from 0-100

        Returns:
            Visual bar
        """
        filled = int(score / 10)
        empty = 10 - filled
        return '█' * filled + '░' * empty

    def cleanup(self):
        """Cleanup resources."""
        self.pairing_learner.cleanup()
