"""
Timeline Browser - Simple terminal interface for navigating workspace history
Isaac's time machine interface
"""

import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from isaac.timemachine.time_machine import TimeMachine, TimelineEntry


class TimelineBrowser:
    """Simple terminal-based timeline browser for workspace history."""

    def __init__(self, time_machine: TimeMachine):
        """Initialize timeline browser.

        Args:
            time_machine: Time machine instance
        """
        self.time_machine = time_machine

    def show_timeline(self, filter_type: str = "all", search_query: str = "") -> None:
        """Display the timeline in a simple table format.

        Args:
            filter_type: Filter by change type ('all', 'auto', 'manual', 'restore', etc.)
            search_query: Search query to filter entries
        """
        # Get timeline entries
        all_entries = self.time_machine.get_timeline(limit=1000)

        # Apply filters
        filtered_entries = self._filter_entries(all_entries, filter_type, search_query)

        # Show stats
        stats = self.time_machine.get_timeline_stats()
        print("ðŸ• Workspace Timeline")
        print("=" * 50)
        print(f"Total: {stats['total_snapshots']} | "
              f"Span: {stats['span_days']:.1f} days | "
              f"Auto: {stats.get('auto_snapshots', 0)} | "
              f"Manual: {stats.get('manual_snapshots', 0)}")
        print()

        if not filtered_entries:
            print("No timeline entries found.")
            return

        # Header
        print(f"{'#':<3} {'Time':<12} {'Type':<8} {'Description':<40} {'Branch':<15} {'Age':<8}")
        print("-" * 90)

        # Show entries
        for i, entry in enumerate(filtered_entries):
            # Format timestamp
            dt = datetime.fromtimestamp(entry.timestamp)
            time_str = dt.strftime("%H:%M")

            # Format age
            age_seconds = time.time() - entry.timestamp
            age_str = self._format_age(age_seconds)

            # Get branch info
            branch = entry.metadata.get('git_branch', 'N/A')
            if len(branch) > 12:
                branch = branch[:9] + "..."

            # Format description
            desc = entry.description
            if len(desc) > 37:
                desc = desc[:34] + "..."

            # Type indicator
            type_indicator = entry.change_type[:7]  # Truncate if needed

            print(f"{i:<3} {time_str:<12} {type_indicator:<8} {desc:<40} {branch:<15} {age_str:<8}")

    def interactive_browse(self) -> None:
        """Launch simple interactive timeline browser."""
        current_filter = "all"
        current_search = ""

        while True:
            self.show_timeline(current_filter, current_search)

            # Show commands
            print("\nCommands:")
            print("  r <index>  - Restore to timeline entry")
            print("  i <index>  - Show detailed info for entry")
            print("  f <type>   - Filter by type (all/auto/manual/restore)")
            print("  s <query>  - Search timeline")
            print("  c          - Clear filters")
            print("  q          - Quit timeline browser")

            # Get command
            try:
                command = input("\ntimeline> ").strip()

                if not command:
                    continue

                if command.lower() == 'q':
                    break

                parts = command.split(None, 1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == 'r' and arg.isdigit():
                    # Restore to entry
                    index = int(arg)
                    if self._confirm_restore(index):
                        success = self.time_machine.restore_to_entry(index)
                        if success:
                            print("âœ“ Successfully restored to timeline entry")
                        else:
                            print("âœ— Failed to restore")
                        time.sleep(2)

                elif cmd == 'i' and arg.isdigit():
                    # Show info
                    index = int(arg)
                    self._show_entry_info(index)
                    input("\nPress Enter to continue...")

                elif cmd == 'f':
                    # Filter
                    current_filter = arg.lower() if arg else "all"
                    current_search = ""  # Clear search when filtering

                elif cmd == 's':
                    # Search
                    current_search = arg
                    current_filter = "all"  # Clear filter when searching

                elif cmd == 'c':
                    # Clear
                    current_filter = "all"
                    current_search = ""

                else:
                    print(f"Unknown command: {cmd}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

    def _filter_entries(self, entries: List[TimelineEntry], filter_type: str,
                       search_query: str) -> List[TimelineEntry]:
        """Filter timeline entries."""
        filtered = entries

        # Apply type filter
        if filter_type != "all":
            filtered = [e for e in filtered if e.change_type == filter_type]

        # Apply search filter
        if search_query:
            query_lower = search_query.lower()
            filtered = [e for e in filtered if query_lower in
                       f"{e.description} {e.change_type} {e.metadata.get('bubble_name', '')}".lower()]

        return filtered

    def _show_entry_info(self, index: int) -> None:
        """Show detailed information for a timeline entry."""
        entries = self.time_machine.get_timeline(limit=1000)

        if index < 0 or index >= len(entries):
            print(f"Invalid entry index: {index}")
            return

        entry = entries[index]
        bubble_info = self.time_machine.get_snapshot_info(entry.bubble_id)

        if not bubble_info:
            print(f"No bubble information found for entry {index}")
            return

        bubble = bubble_info['bubble']

        # Show info
        print(f"Entry Index: {index}")
        print(f"Timestamp: {datetime.fromtimestamp(entry.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Change Type: {entry.change_type}")
        print(f"Description: {entry.description}")
        print(f"Bubble ID: {entry.bubble_id}")
        print(f"Age: {bubble_info['age_formatted']}")
        print("\nBubble Details:")
        print(f"  Name: {bubble.name}")
        print(f"  Directory: {bubble.cwd}")
        print(f"  Git Branch: {bubble.git_branch or 'N/A'}")
        print(f"  Processes: {len(bubble.running_processes)}")
        print(f"  Open Files: {len(bubble.open_files)}")

        if bubble.tags:
            print(f"  Tags: {', '.join(bubble.tags)}")

    def _confirm_restore(self, index: int) -> bool:
        """Confirm restoration to a timeline entry."""
        entries = self.time_machine.get_timeline(limit=1000)

        if index < 0 or index >= len(entries):
            return False

        entry = entries[index]
        dt = datetime.fromtimestamp(entry.timestamp)

        message = f"Restore workspace to {dt.strftime('%Y-%m-%d %H:%M:%S')}?\n"
        message += f"Description: {entry.description}\n"
        message += f"Type: {entry.change_type}\n"
        message += "Continue? (y/N): "

        response = input(message).strip().lower()
        return response in ['y', 'yes']

    def _format_age(self, seconds: float) -> str:
        """Format age in compact form."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h"
        else:
            return f"{int(seconds / 86400)}d"

    def show_playback_mode(self, start_index: int = 0, end_index: Optional[int] = None) -> None:
        """Show simple playback mode for watching timeline evolution."""
        entries = self.time_machine.get_timeline(limit=1000)

        if not entries:
            print("No timeline entries to play back")
            return

        start_index = max(0, min(start_index, len(entries) - 1))
        end_index = min(len(entries) - 1, end_index) if end_index is not None else len(entries) - 1

        print(f"Starting playback from entry {start_index} to {end_index}")
        print("Press Ctrl+C to stop playback\n")

        try:
            for i in range(start_index, end_index + 1):
                entry = entries[i]

                # Clear and show current state
                print("\033[2J\033[H", end="")  # Clear screen

                # Show current entry info
                dt = datetime.fromtimestamp(entry.timestamp)
                print(f"Entry {i}/{len(entries)} | {dt.strftime('%Y-%m-%d %H:%M:%S')} | {entry.change_type}")
                print("-" * 50)

                # Show bubble info if available
                bubble_info = self.time_machine.get_snapshot_info(entry.bubble_id)
                if bubble_info:
                    bubble = bubble_info['bubble']
                    info = f"Branch: {bubble.git_branch or 'N/A'} | Processes: {len(bubble.running_processes)} | Files: {len(bubble.open_files)}"
                    print(info)

                print(f"Description: {entry.description}")

                # Wait before next entry
                time.sleep(2)

        except KeyboardInterrupt:
            print("\nPlayback stopped")

    def show_timeline_graph(self) -> None:
        """Show a simple activity graph."""
        entries = self.time_machine.get_timeline(limit=100)

        if not entries:
            print("No timeline entries to display")
            return

        # Group by date
        date_groups = {}
        for entry in reversed(entries):  # Most recent first
            date = datetime.fromtimestamp(entry.timestamp).date()
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(entry)

        # Show graph
        print("Timeline Activity Graph")
        print("=" * 30)

        for date in sorted(date_groups.keys(), reverse=True):
            day_entries = date_groups[date]
            date_str = date.strftime("%m/%d")

            # Count by type
            type_counts = {}
            for entry in day_entries:
                type_counts[entry.change_type] = type_counts.get(entry.change_type, 0) + 1

            # Create visual representation
            line = f"{date_str}: "
            for change_type, count in type_counts.items():
                symbol = {'auto': 'o', 'manual': '*', 'restore': '#'}.get(change_type, 'x')
                line += f"{symbol}{count} "
            line += f"({len(day_entries)} total)"

            print(line)

