"""
Ambient Command - Isaac's ambient intelligence interface
Provides access to proactive suggestions and learning features
"""

import time
from typing import Any, Dict, List

from isaac.ambient.proactive_suggester import ProactiveSuggester
from isaac.ambient.workflow_learner import WorkflowLearner
from isaac.logging import StructuredLogger


class AmbientCommand:
    """Command interface for ambient intelligence features."""

    def __init__(self):
        """Initialize ambient command."""
        self.workflow_learner = WorkflowLearner()
        self.proactive_suggester = ProactiveSuggester(self.workflow_learner)
        self.logger = StructuredLogger()

    def execute(self, args: List[str]) -> Dict[str, Any]:
        """Execute ambient command.

        Args:
            args: Command arguments

        Returns:
            Command result
        """
        if not args:
            return self._show_help()

        subcommand = args[0].lower()

        if subcommand == "analyze":
            return self._analyze_history(args[1:])
        elif subcommand == "suggestions":
            return self._show_suggestions(args[1:])
        elif subcommand == "patterns":
            return self._manage_patterns(args[1:])
        elif subcommand == "stats":
            return self._show_stats(args[1:])
        elif subcommand == "learn":
            return self._learn_from_history(args[1:])
        elif subcommand == "logs":
            return self._show_logs(args[1:])
        else:
            return {
                "success": False,
                "output": f"Unknown subcommand: {subcommand}\n{self._get_help_text()}",
                "exit_code": 1,
            }

    def _show_help(self) -> Dict[str, Any]:
        """Show help information."""
        return {"success": True, "output": self._get_help_text(), "exit_code": 0}

    def _get_help_text(self) -> str:
        """Get help text."""
        return """Isaac Ambient Intelligence System

USAGE:
  /ambient <subcommand> [options]

SUBCOMMANDS:
  analyze              Analyze command history for patterns
  suggestions          Show proactive suggestions
  patterns             Manage learned patterns
  stats                Show learning statistics
  learn                Force learning from recent history
  logs                 View Isaac's learning logs and self-awareness

EXAMPLES:
  /ambient analyze                    # Analyze command history
  /ambient suggestions                # Show current suggestions
  /ambient patterns list              # List learned patterns
  /ambient stats                      # Show learning statistics
  /ambient learn                      # Learn from recent commands
  /ambient logs patterns              # View learned patterns
  /ambient logs suggestions           # View generated suggestions
  /ambient logs summary               # View learning summary

The ambient system learns from your behavior and provides proactive assistance."""

    def _analyze_history(self, args: List[str]) -> Dict[str, Any]:
        """Analyze command history for patterns."""
        try:
            results = self.workflow_learner.analyze_command_history()

            output = "🎯 Command History Analysis Complete\n\n"

            if "error" in results:
                output += f"❌ Error: {results['error']}\n"
                return {"success": False, "output": output, "exit_code": 1}

            output += f"📊 Patterns Found: {results['patterns_found']}\n"
            output += f"🔄 Workflows Found: {results['workflows_found']}\n"
            output += f"✨ New Patterns: {results['new_patterns']}\n"
            output += f"🚀 New Workflows: {results['new_workflows']}\n\n"

            if results["suggestions"]:
                output += "💡 Suggestions:\n"
                for i, suggestion in enumerate(results["suggestions"][:5], 1):
                    output += f"  {i}. {suggestion['description']}\n"
                    if suggestion["type"] == "pipeline_suggestion":
                        output += f"     Frequency: {suggestion['frequency']} times\n"
                        output += f"     Commands: {' → '.join(suggestion['commands'][:3])}\n"
                    output += "\n"

            return {"success": True, "output": output, "exit_code": 0}

        except Exception as e:
            return {"success": False, "output": f"❌ Analysis failed: {e}", "exit_code": 1}

    def _show_suggestions(self, args: List[str]) -> Dict[str, Any]:
        """Show proactive suggestions."""
        try:
            suggestions = self.proactive_suggester.get_suggestions(limit=10)

            if not suggestions:
                output = "🤔 No proactive suggestions available at the moment.\n\n"
                output += "Suggestions appear when:\n"
                output += "• You repeat command sequences frequently\n"
                output += "• Commands fail with common errors\n"
                output += "• You're idle for extended periods\n"
                output += "• High error rates are detected\n\n"
                output += (
                    "Try running '/ambient analyze' to generate suggestions from your history."
                )
            else:
                output = f"💡 Proactive Suggestions ({len(suggestions)})\n\n"

                for i, suggestion in enumerate(suggestions, 1):
                    confidence_pct = int(suggestion.confidence * 100)
                    output += f"{i}. {suggestion.title} ({confidence_pct}% confidence)\n"
                    output += f"   {suggestion.description}\n"

                    if suggestion.actions:
                        output += "   Actions:\n"
                        for action in suggestion.actions:
                            output += f"   • {action['label']}: {action['command']}\n"

                    output += "\n"

            return {"success": True, "output": output, "exit_code": 0}

        except Exception as e:
            return {
                "success": False,
                "output": f"❌ Failed to get suggestions: {e}",
                "exit_code": 1,
            }

    def _manage_patterns(self, args: List[str]) -> Dict[str, Any]:
        """Manage learned patterns."""
        if not args:
            return {
                "success": False,
                "output": "Usage: /ambient patterns <list|show|delete> [pattern_id]",
                "exit_code": 1,
            }

        subcommand = args[0].lower()

        if subcommand == "list":
            return self._list_patterns()
        elif subcommand == "show" and len(args) > 1:
            return self._show_pattern(args[1])
        elif subcommand == "delete" and len(args) > 1:
            return self._delete_pattern(args[1])
        else:
            return {
                "success": False,
                "output": "Usage: /ambient patterns <list|show|delete> [pattern_id]",
                "exit_code": 1,
            }

    def _list_patterns(self) -> Dict[str, Any]:
        """List all learned patterns."""
        patterns = list(self.workflow_learner.patterns.values())
        workflows = list(self.workflow_learner.workflows.values())

        output = f"🎯 Learned Patterns ({len(patterns)} command patterns, {len(workflows)} workflows)\n\n"

        if patterns:
            output += "Command Patterns:\n"
            for pattern in sorted(patterns, key=lambda p: p.frequency, reverse=True)[:10]:
                confidence_pct = int(pattern.confidence * 100)
                output += f"• {pattern.pattern_id}: {' → '.join(pattern.commands[:3])}{'...' if len(pattern.commands) > 3 else ''}\n"
                output += f"  Frequency: {pattern.frequency}, Confidence: {confidence_pct}%\n\n"

        if workflows:
            output += "Workflow Patterns:\n"
            for workflow in sorted(workflows, key=lambda w: w.frequency, reverse=True)[:5]:
                output += f"• {workflow.workflow_id}: {len(workflow.steps)} steps\n"
                output += f"  Tags: {', '.join(workflow.tags)}\n"
                output += f"  Frequency: {workflow.frequency}, Success Rate: {int(workflow.success_rate * 100)}%\n\n"

        if not patterns and not workflows:
            output += "No patterns learned yet. Try running '/ambient analyze' to discover patterns in your command history."

        return {"success": True, "output": output, "exit_code": 0}

    def _show_pattern(self, pattern_id: str) -> Dict[str, Any]:
        """Show details of a specific pattern."""
        pattern = self.workflow_learner.patterns.get(pattern_id)
        workflow = self.workflow_learner.workflows.get(pattern_id)

        if not pattern and not workflow:
            return {"success": False, "output": f"Pattern '{pattern_id}' not found", "exit_code": 1}

        output = f"📋 Pattern Details: {pattern_id}\n\n"

        if pattern:
            output += f"Type: Command Pattern\n"
            output += f"Commands: {' → '.join(pattern.commands)}\n"
            output += f"Frequency: {pattern.frequency} times\n"
            output += f"Confidence: {int(pattern.confidence * 100)}%\n"
            output += f"Average Interval: {pattern.avg_interval:.1f} seconds\n"
            output += f"First Seen: {time.ctime(pattern.first_seen)}\n"
            output += f"Last Seen: {time.ctime(pattern.last_seen)}\n"
            output += f"Description: {pattern.description}\n"

        elif workflow:
            output += f"Type: Workflow Pattern\n"
            output += f"Steps: {len(workflow.steps)}\n"
            for i, step in enumerate(workflow.steps, 1):
                output += f"  {i}. {step}\n"
            output += f"Frequency: {workflow.frequency} times\n"
            output += f"Success Rate: {int(workflow.success_rate * 100)}%\n"
            output += f"Average Duration: {workflow.avg_duration:.1f} seconds\n"
            output += f"Tags: {', '.join(workflow.tags)}\n"
            output += f"Last Executed: {time.ctime(workflow.last_executed)}\n"

        return {"success": True, "output": output, "exit_code": 0}

    def _delete_pattern(self, pattern_id: str) -> Dict[str, Any]:
        """Delete a learned pattern."""
        if pattern_id in self.workflow_learner.patterns:
            del self.workflow_learner.patterns[pattern_id]
            self.workflow_learner._save_patterns()
            return {
                "success": True,
                "output": f"Deleted command pattern '{pattern_id}'",
                "exit_code": 0,
            }
        elif pattern_id in self.workflow_learner.workflows:
            del self.workflow_learner.workflows[pattern_id]
            self.workflow_learner._save_patterns()
            return {
                "success": True,
                "output": f"Deleted workflow pattern '{pattern_id}'",
                "exit_code": 0,
            }
        else:
            return {"success": False, "output": f"Pattern '{pattern_id}' not found", "exit_code": 1}

    def _show_stats(self, args: List[str]) -> Dict[str, Any]:
        """Show learning statistics."""
        try:
            self.workflow_learner.get_pattern_suggestions()
            suggester_stats = self.proactive_suggester.get_learning_stats()

            output = "📊 Ambient Intelligence Statistics\n\n"

            output += "Pattern Learning:\n"
            output += f"• Command Patterns: {len(self.workflow_learner.patterns)}\n"
            output += f"• Workflow Patterns: {len(self.workflow_learner.workflows)}\n"
            output += (
                f"• Command Sequences Analyzed: {len(self.workflow_learner.command_sequences)}\n\n"
            )

            output += "Proactive Suggestions:\n"
            output += f"• Total Suggestions: {suggester_stats['total_suggestions']}\n"
            output += f"• Active Suggestions: {suggester_stats['active_suggestions']}\n"
            output += f"• Context History Size: {suggester_stats['context_history_size']}\n"
            output += f"• Current Error Rate: {suggester_stats['current_error_rate']:.1%}\n\n"

            output += "Current Context:\n"
            context = self.proactive_suggester.current_context
            output += f"• Commands Executed: {context['command_count']}\n"
            output += f"• Errors Encountered: {context['error_count']}\n"
            output += f"• Last Command: {context['last_command'] or 'None'}\n"
            output += (
                f"• Time Since Last Command: {context['time_since_last_command']:.0f} seconds\n"
            )

            return {"success": True, "output": output, "exit_code": 0}

        except Exception as e:
            return {"success": False, "output": f"❌ Failed to get statistics: {e}", "exit_code": 1}

    def _learn_from_history(self, args: List[str]) -> Dict[str, Any]:
        """Force learning from recent command history."""
        try:
            # Re-analyze history
            results = self.workflow_learner.analyze_command_history()

            output = "🧠 Learning from Recent History\n\n"

            if "error" in results:
                output += f"❌ Error: {results['error']}\n"
                return {"success": False, "output": output, "exit_code": 1}

            output += f"✅ Analysis complete!\n"
            output += (
                f"📊 Patterns: {results['patterns_found']} total ({results['new_patterns']} new)\n"
            )
            output += f"🔄 Workflows: {results['workflows_found']} total ({results['new_workflows']} new)\n\n"

            if results["suggestions"]:
                output += f"💡 Generated {len(results['suggestions'])} new suggestions\n"
                output += "Run '/ambient suggestions' to see them."

            return {"success": True, "output": output, "exit_code": 0}

        except Exception as e:
            return {"success": False, "output": f"❌ Learning failed: {e}", "exit_code": 1}

    def _show_logs(self, args: List[str]) -> Dict[str, Any]:
        """Show Isaac's learning logs."""
        try:
            if not args:
                # Show default summary
                args = ["summary"]

            log_type = args[0].lower()

            if log_type == "patterns":
                return self._show_pattern_logs(args[1:])
            elif log_type == "suggestions":
                return self._show_suggestion_logs(args[1:])
            elif log_type == "summary":
                return self._show_log_summary(args[1:])
            elif log_type == "warnings":
                return self._show_warning_logs(args[1:])
            else:
                return {
                    "success": False,
                    "output": f"Unknown log type: {log_type}\nAvailable: patterns, suggestions, summary, warnings",
                    "exit_code": 1,
                }

        except Exception as e:
            return {"success": False, "output": f"❌ Failed to show logs: {e}", "exit_code": 1}

    def _show_pattern_logs(self, args: List[str]) -> Dict[str, Any]:
        """Show recently learned patterns."""
        limit = int(args[0]) if args and args[0].isdigit() else 10
        patterns = self.logger.get_recent_patterns(limit=limit)

        if not patterns:
            return {
                "success": True,
                "output": "No learned patterns yet. Isaac is still observing...",
                "exit_code": 0,
            }

        output = f"🧠 Recently Learned Patterns (showing {len(patterns)} of {limit})\n\n"

        for event in patterns:
            data = event.data
            output += f"Pattern ID: {data.get('pattern_id', 'N/A')}\n"
            output += f"  Type: {data.get('pattern_type', 'N/A')}\n"
            output += f"  Description: {data.get('description', 'N/A')}\n"
            output += f"  Confidence: {data.get('confidence', 0):.2%}\n"
            output += f"  Learned: {event.timestamp}\n"
            if data.get('correction_action'):
                output += f"  Action: {data['correction_action']}\n"
            output += "\n"

        return {"success": True, "output": output, "exit_code": 0}

    def _show_suggestion_logs(self, args: List[str]) -> Dict[str, Any]:
        """Show recently generated suggestions."""
        limit = int(args[0]) if args and args[0].isdigit() else 10
        suggestions = self.logger.get_recent_suggestions(limit=limit)

        if not suggestions:
            return {
                "success": True,
                "output": "No suggestions generated yet.",
                "exit_code": 0,
            }

        output = f"💡 Recently Generated Suggestions (showing {len(suggestions)} of {limit})\n\n"

        for event in suggestions:
            data = event.data
            output += f"Suggestion: {data.get('title', 'N/A')}\n"
            output += f"  Type: {data.get('suggestion_type', 'N/A')}\n"
            output += f"  Description: {data.get('description', 'N/A')}\n"
            output += f"  Confidence: {data.get('confidence', 0):.2%}\n"
            output += f"  Generated: {event.timestamp}\n"
            output += "\n"

        return {"success": True, "output": output, "exit_code": 0}

    def _show_warning_logs(self, args: List[str]) -> Dict[str, Any]:
        """Show recent warnings."""
        limit = int(args[0]) if args and args[0].isdigit() else 10
        warnings = self.logger.get_recent_warnings(limit=limit)

        if not warnings:
            return {
                "success": True,
                "output": "No warnings. Isaac is running smoothly! ✅",
                "exit_code": 0,
            }

        output = f"⚠️  Recent Warnings (showing {len(warnings)} of {limit})\n\n"

        for event in warnings:
            data = event.data
            output += f"{event.event_type.upper()}: {data.get('message', 'N/A')}\n"
            output += f"  Source: {data.get('source', 'N/A')}\n"
            output += f"  Time: {event.timestamp}\n"
            if data.get('details'):
                output += f"  Details: {data['details']}\n"
            output += "\n"

        return {"success": True, "output": output, "exit_code": 0}

    def _show_log_summary(self, args: List[str]) -> Dict[str, Any]:
        """Show learning summary."""
        days = int(args[0]) if args and args[0].isdigit() else 7
        summary = self.logger.get_learning_summary(days=days)

        output = f"📊 Isaac's Learning Summary (Last {days} days)\n\n"

        output += "🧠 Learning Activity:\n"
        output += f"  • Patterns Learned: {summary['patterns_learned']}\n"
        output += f"  • Suggestions Generated: {summary['suggestions_generated']}\n"
        output += f"  • Mistakes Recorded: {summary['mistakes_recorded']}\n\n"

        if summary.get('pattern_types'):
            output += "📈 Pattern Types:\n"
            for ptype, count in summary['pattern_types'].items():
                output += f"  • {ptype}: {count}\n"
            output += "\n"

        if summary.get('suggestion_types'):
            output += "💡 Suggestion Types:\n"
            for stype, count in summary['suggestion_types'].items():
                output += f"  • {stype}: {count}\n"
            output += "\n"

        if summary.get('avg_pattern_confidence'):
            output += f"🎯 Average Pattern Confidence: {summary['avg_pattern_confidence']:.2%}\n"

        if summary.get('avg_suggestion_confidence'):
            output += f"💪 Average Suggestion Confidence: {summary['avg_suggestion_confidence']:.2%}\n"

        output += "\n✨ Isaac is continuously learning and improving!"

        return {"success": True, "output": output, "exit_code": 0}
