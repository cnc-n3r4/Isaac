"""
Time Machine command for timeline navigation and snapshots.
Usage: /timemachine <action> [args...]
"""

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from isaac.timemachine.time_machine import TimeMachine
from isaac.timemachine.timeline_browser import TimelineBrowser
from isaac.bubbles.manager import BubbleManager


class TimeMachineCommand:
    """Command interface for time machine functionality."""

    def __init__(self):
        """Initialize time machine command."""
        self.bubble_manager = BubbleManager()
        self.time_machine = TimeMachine(self.bubble_manager)
        self.browser = TimelineBrowser(self.time_machine)

    def execute(self, args: List[str]) -> Dict[str, Any]:
        """Execute time machine command.

        Args:
            args: Command arguments

        Returns:
            Command result
        """
        if not args:
            return self._show_help()

        action = args[0].lower()

        try:
            if action == 'snapshot':
                return self._create_snapshot(args[1:])
            elif action == 'timeline':
                return self._show_timeline(args[1:])
            elif action == 'restore':
                return self._restore_to_time(args[1:])
            elif action == 'browse':
                return self._interactive_browse(args[1:])
            elif action == 'playback':
                return self._playback_mode(args[1:])
            elif action == 'search':
                return self._search_timeline(args[1:])
            elif action == 'stats':
                return self._show_stats(args[1:])
            elif action == 'graph':
                return self._show_graph(args[1:])
            else:
                return {
                    'success': False,
                    'output': f"Unknown action: {action}\n{self._get_help_text()}",
                    'exit_code': 1
                }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error executing time machine command: {e}",
                'exit_code': 1
            }

    def _create_snapshot(self, args: List[str]) -> Dict[str, Any]:
        """Create a manual snapshot."""
        parser = argparse.ArgumentParser(prog='/timemachine snapshot', exit_on_error=False)
        parser.add_argument('-d', '--description', help='Snapshot description')
        parser.add_argument('-f', '--force', action='store_true', help='Force snapshot even if recent')

        try:
            parsed = parser.parse_args(args)
        except SystemExit:
            return {
                'success': False,
                'output': "Usage: /timemachine snapshot [-d description] [-f]",
                'exit_code': 1
            }

        try:
            bubble = self.time_machine.create_snapshot(
                description=parsed.description or "Manual snapshot",
                change_type="manual",
                force=parsed.force
            )

            if bubble:
                output = f"Created timeline snapshot '{bubble.name}'\n"
                output += f"Bubble ID: {bubble.bubble_id}\n"
                output += f"Timestamp: {bubble.timestamp}\n"
                if parsed.description:
                    output += f"Description: {parsed.description}\n"
                return {
                    'success': True,
                    'output': output,
                    'exit_code': 0
                }
            else:
                return {
                    'success': False,
                    'output': "Snapshot not created (too recent, use -f to force)",
                    'exit_code': 1
                }
        except Exception as e:
            return {
                'success': False,
                'output': f"Failed to create snapshot: {e}",
                'exit_code': 1
            }

    def _show_timeline(self, args: List[str]) -> Dict[str, Any]:
        """Show timeline entries."""
        parser = argparse.ArgumentParser(prog='/timemachine timeline', exit_on_error=False)
        parser.add_argument('-f', '--filter', choices=['all', 'auto', 'manual', 'restore', 'branch_switch'],
                          default='all', help='Filter by change type')
        parser.add_argument('-s', '--search', help='Search query')
        parser.add_argument('-l', '--limit', type=int, default=20, help='Limit results')

        try:
            parsed = parser.parse_args(args)
        except SystemExit:
            return {
                'success': False,
                'output': "Usage: /timemachine timeline [-f filter] [-s search] [-l limit]",
                'exit_code': 1
            }

        try:
            entries = self.time_machine.get_timeline(limit=parsed.limit)

            if parsed.filter != 'all':
                entries = [e for e in entries if e.change_type == parsed.filter]

            if parsed.search:
                query_lower = parsed.search.lower()
                entries = [e for e in entries if query_lower in
                          f"{e.description} {e.change_type}".lower()]

            if not entries:
                return {
                    'success': True,
                    'output': "No timeline entries found.",
                    'exit_code': 0
                }

            output = f"Timeline ({len(entries)} entries):\n\n"
            for i, entry in enumerate(entries):
                dt = datetime.fromtimestamp(entry.timestamp)
                time_str = dt.strftime("%m/%d %H:%M")
                age = self._format_age(time.time() - entry.timestamp)

                output += f"{i:2d}. [{entry.change_type}] {time_str} ({age}) {entry.description}\n"

                if entry.metadata.get('git_branch'):
                    output += f"    Branch: {entry.metadata['git_branch']}\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Failed to show timeline: {e}",
                'exit_code': 1
            }

    def _restore_to_time(self, args: List[str]) -> Dict[str, Any]:
        """Restore to a specific time."""
        if not args:
            return {
                'success': False,
                'output': "Usage: /timemachine restore <timestamp|index>\n\n"
                         "Examples:\n"
                         "  /timemachine restore 1640995200  # Unix timestamp\n"
                         "  /timemachine restore 5           # Timeline index\n"
                         "  /timemachine restore \"2024-01-01 12:00:00\"  # Date string",
                'exit_code': 1
            }

        time_spec = args[0]

        try:
            # Try as timeline index first
            if time_spec.isdigit():
                index = int(time_spec)
                success = self.time_machine.restore_to_entry(index)
                action = f"timeline entry {index}"
            else:
                # Try to parse as timestamp or datetime string
                try:
                    # Try unix timestamp
                    timestamp = float(time_spec)
                except ValueError:
                    # Try datetime string
                    dt = datetime.strptime(time_spec, "%Y-%m-%d %H:%M:%S")
                    timestamp = dt.timestamp()

                success = self.time_machine.restore_to_timestamp(timestamp)
                action = f"timestamp {time_spec}"

            if success:
                return {
                    'success': True,
                    'output': f"Successfully restored workspace to {action}",
                    'exit_code': 0
                }
            else:
                return {
                    'success': False,
                    'output': f"Failed to restore to {action}",
                    'exit_code': 1
                }
        except Exception as e:
            return {
                'success': False,
                'output': f"Invalid time specification: {e}",
                'exit_code': 1
            }

    def _interactive_browse(self, args: List[str]) -> Dict[str, Any]:
        """Launch interactive timeline browser."""
        try:
            self.browser.interactive_browse()
            return {
                'success': True,
                'output': "Timeline browser closed.",
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Failed to launch timeline browser: {e}",
                'exit_code': 1
            }

    def _playback_mode(self, args: List[str]) -> Dict[str, Any]:
        """Show playback mode."""
        parser = argparse.ArgumentParser(prog='/timemachine playback', exit_on_error=False)
        parser.add_argument('--start', type=int, default=0, help='Starting entry index')
        parser.add_argument('--end', type=int, help='Ending entry index')

        try:
            parsed = parser.parse_args(args)
        except SystemExit:
            return {
                'success': False,
                'output': "Usage: /timemachine playback [--start index] [--end index]",
                'exit_code': 1
            }

        try:
            self.browser.show_playback_mode(parsed.start, parsed.end)
            return {
                'success': True,
                'output': "Playback completed.",
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Failed to start playback: {e}",
                'exit_code': 1
            }

    def _search_timeline(self, args: List[str]) -> Dict[str, Any]:
        """Search timeline."""
        if not args:
            return {
                'success': False,
                'output': "Usage: /timemachine search <query>",
                'exit_code': 1
            }

        query = " ".join(args)

        try:
            results = self.time_machine.search_timeline(query, limit=20)

            if not results:
                return {
                    'success': True,
                    'output': f"No timeline entries found matching: {query}",
                    'exit_code': 0
                }

            output = f"Timeline search results for '{query}' ({len(results)} matches):\n\n"
            for i, result in enumerate(results):
                entry = result['entry']
                bubble_info = result['bubble_info']

                dt = datetime.fromtimestamp(entry.timestamp)
                time_str = dt.strftime("%m/%d %H:%M")
                age = bubble_info['age_formatted']

                output += f"{i+1}. [{entry.change_type}] {time_str} ({age})\n"
                output += f"   {entry.description}\n"
                if entry.metadata.get('git_branch'):
                    output += f"   Branch: {entry.metadata['git_branch']}\n"
                output += "\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Failed to search timeline: {e}",
                'exit_code': 1
            }

    def _show_stats(self, args: List[str]) -> Dict[str, Any]:
        """Show timeline statistics."""
        try:
            stats = self.time_machine.get_timeline_stats()

            output = "Time Machine Statistics:\n"
            output += "=" * 30 + "\n"
            output += f"Total Snapshots: {stats['total_snapshots']}\n"

            if stats['total_snapshots'] > 0:
                output += f"Date Range: {stats['oldest']} to {stats['newest']}\n"
                output += f"Time Span: {stats['span_days']:.1f} days\n\n"

                output += "Snapshots by Type:\n"
                for change_type, count in stats['change_types'].items():
                    output += f"  {change_type}: {count}\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Failed to get stats: {e}",
                'exit_code': 1
            }

    def _show_graph(self, args: List[str]) -> Dict[str, Any]:
        """Show timeline activity graph."""
        try:
            self.browser.show_timeline_graph()
            return {
                'success': True,
                'output': "Timeline graph displayed.",
                'exit_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'output': f"Failed to show graph: {e}",
                'exit_code': 1
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
        return """Time Machine - Navigate workspace history and create snapshots

USAGE:
  /timemachine <action> [arguments...]

ACTIONS:
  snapshot [-d desc] [-f]           Create manual snapshot
  timeline [-f type] [-s query]     Show timeline entries
  restore <time>                   Restore to timestamp/index
  browse                           Interactive timeline browser
  playback [--start n] [--end n]   Playback timeline evolution
  search <query>                   Search timeline entries
  stats                            Show timeline statistics
  graph                            Show activity graph

EXAMPLES:
  /timemachine snapshot -d "Before major refactor"
  /timemachine timeline -f manual -l 10
  /timemachine restore 1640995200
  /timemachine restore "2024-01-01 12:00:00"
  /timemachine search "database"
  /timemachine browse

Automatic snapshots are created every 30 minutes by default.
Use --help with any action for detailed options."""

    def _format_age(self, seconds: float) -> str:
        """Format age in human-readable form."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h"
        else:
            return f"{int(seconds / 86400)}d"