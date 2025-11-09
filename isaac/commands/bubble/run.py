#!/usr/bin/env python3
"""
Bubble Command - Workspace state management
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add the isaac package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.bubbles import BubbleManager, WorkspaceState


class BubbleCommand:
    """Workspace bubble management command"""

    def __init__(self):
        self.manager = BubbleManager()

    def execute(self, args: Dict[str, Any]) -> str:
        """Execute the bubble command"""

        # Normalize argument names (convert dashes to underscores)
        normalized_args = {}
        for key, value in args.items():
            normalized_key = key.replace('-', '_')
            normalized_args[normalized_key] = value

        action = normalized_args.get('action')

        if action == 'create':
            return self._create_bubble(normalized_args)
        elif action == 'list':
            return self._list_bubbles()
        elif action == 'show':
            return self._show_bubble(normalized_args)
        elif action == 'restore':
            return self._restore_bubble(normalized_args)
        elif action == 'delete':
            return self._delete_bubble(normalized_args)
        elif action == 'export':
            return self._export_bubble(normalized_args)
        elif action == 'import':
            return self._import_bubble(normalized_args)
        elif action == 'suspend':
            return self._suspend_bubble(normalized_args)
        elif action == 'resume':
            return self._resume_bubble(normalized_args)
        elif action == 'version':
            return self._create_bubble_version(normalized_args)
        elif action == 'versions':
            return self._list_bubble_versions(normalized_args)
        else:
            return "❌ Invalid action. Use: create, list, show, restore, delete, export, import, suspend, resume, version, versions"

    def _create_bubble(self, args: Dict[str, Any]) -> str:
        """Create a new workspace bubble"""
        name = args.get('name', '')
        description = args.get('description', '')
        tags_str = args.get('tags', '')

        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(',')] if tags_str else []

        try:
            bubble = self.manager.create_bubble(name=name, description=description, tags=tags)

            result = f"✅ Created workspace bubble '{bubble.name}'\n"
            result += f"   ID: {bubble.bubble_id}\n"
            result += f"   Directory: {bubble.cwd}\n"
            result += f"   Git Branch: {bubble.git_branch or 'N/A'}\n"
            result += f"   Processes: {len(bubble.running_processes)}\n"
            if tags:
                result += f"   Tags: {', '.join(tags)}\n"

            return result

        except Exception as e:
            return f"❌ Failed to create bubble: {e}"

    def _list_bubbles(self) -> str:
        """List all workspace bubbles"""
        bubbles = self.manager.list_bubbles()

        if not bubbles:
            return "📭 No workspace bubbles found. Create one with: /bubble create"

        result = f"🫧 Workspace Bubbles ({len(bubbles)}):\n\n"

        for bubble in bubbles:
            result += f"• {bubble.name} ({bubble.bubble_id})\n"
            result += f"  Created: {self._format_timestamp(bubble.timestamp)}\n"
            result += f"  Directory: {bubble.cwd}\n"
            if bubble.git_branch:
                result += f"  Branch: {bubble.git_branch}\n"
            if bubble.description:
                result += f"  Description: {bubble.description}\n"
            if bubble.tags:
                result += f"  Tags: {', '.join(bubble.tags)}\n"
            result += "\n"

        return result

    def _show_bubble(self, args: Dict[str, Any]) -> str:
        """Show detailed information about a bubble"""
        bubble_id = args.get('bubble_id')
        if not bubble_id:
            return "❌ Bubble ID required. Use: /bubble show --bubble-id <id>"

        bubble = self.manager.get_bubble(bubble_id)
        if not bubble:
            return f"❌ Bubble '{bubble_id}' not found"

        result = f"🫧 Bubble: {bubble.name} ({bubble.bubble_id})\n"
        result += f"Created: {self._format_timestamp(bubble.timestamp)}\n"
        result += f"Description: {bubble.description or 'N/A'}\n"
        result += f"Directory: {bubble.cwd}\n"
        result += f"Git Branch: {bubble.git_branch or 'N/A'}\n\n"

        # Git status
        git_status = bubble.git_status
        if git_status.get('is_git_repo'):
            result += "Git Status:\n"
            if git_status.get('modified_files'):
                result += f"  Modified: {len(git_status['modified_files'])} files\n"
            if git_status.get('staged_files'):
                result += f"  Staged: {len(git_status['staged_files'])} files\n"
            if git_status.get('untracked_files'):
                result += f"  Untracked: {len(git_status['untracked_files'])} files\n"
        else:
            result += "Git Status: Not a git repository\n"

        # Environment
        env = bubble.environment
        if env:
            result += f"\nEnvironment Variables: {len(env)} captured\n"
            for key in sorted(env.keys()):
                result += f"  {key}={env[key]}\n"

        # Processes
        processes = bubble.running_processes
        if processes:
            result += f"\nRunning Processes: {len(processes)}\n"
            for proc in processes[:5]:  # Show first 5
                cmd = ' '.join(proc.get('cmdline', []))[:50]
                result += f"  {proc['name']} (PID: {proc['pid']}) - {cmd}...\n"
            if len(processes) > 5:
                result += f"  ... and {len(processes) - 5} more\n"

        # Tags
        if bubble.tags:
            result += f"\nTags: {', '.join(bubble.tags)}\n"

        # Recent commands
        if bubble.recent_commands:
            result += f"\nRecent Commands ({len(bubble.recent_commands)}):\n"
            for i, cmd in enumerate(bubble.recent_commands[-5:], 1):  # Show last 5
                result += f"  {i}. {cmd[:60]}{'...' if len(cmd) > 60 else ''}\n"

        # System info
        if bubble.system_info:
            result += f"\nSystem Info:\n"
            cpu = bubble.system_info.get('cpu_percent')
            mem = bubble.system_info.get('memory_percent')
            disk = bubble.system_info.get('disk_percent')
            if cpu is not None:
                result += f"  CPU: {cpu}%\n"
            if mem is not None:
                result += f"  Memory: {mem}%\n"
            if disk is not None:
                result += f"  Disk: {disk}%\n"

        return result

    def _restore_bubble(self, args: Dict[str, Any]) -> str:
        """Restore workspace to bubble state"""
        bubble_id = args.get('bubble_id')
        if not bubble_id:
            return "❌ Bubble ID required. Use: /bubble restore --bubble-id <id>"

        success = self.manager.restore_bubble(bubble_id)
        if success:
            return f"✅ Restored workspace to bubble '{bubble_id}'"
        else:
            return f"❌ Failed to restore bubble '{bubble_id}'"

    def _delete_bubble(self, args: Dict[str, Any]) -> str:
        """Delete a workspace bubble"""
        bubble_id = args.get('bubble_id')
        if not bubble_id:
            return "❌ Bubble ID required. Use: /bubble delete --bubble-id <id>"

        success = self.manager.delete_bubble(bubble_id)
        if success:
            return f"✅ Deleted bubble '{bubble_id}'"
        else:
            return f"❌ Bubble '{bubble_id}' not found"

    def _export_bubble(self, args: Dict[str, Any]) -> str:
        """Export bubble to file"""
        bubble_id = args.get('bubble_id')
        file_path = args.get('file')

        if not bubble_id or not file_path:
            return "❌ Both bubble-id and file required. Use: /bubble export --bubble-id <id> --file <path>"

        bubble = self.manager.get_bubble(bubble_id)
        if not bubble:
            return f"❌ Bubble '{bubble_id}' not found"

        try:
            import json
            with open(file_path, 'w') as f:
                json.dump({
                    'bubble': bubble.__dict__,
                    'exported_at': time.time(),
                    'version': '1.0'
                }, f, indent=2, default=str)
            return f"✅ Exported bubble '{bubble_id}' to {file_path}"
        except Exception as e:
            return f"❌ Failed to export bubble: {e}"

    def _import_bubble(self, args: Dict[str, Any]) -> str:
        """Import bubble from file"""
        file_path = args.get('file')
        if not file_path:
            return "❌ File path required. Use: /bubble import --file <path>"

        try:
            import json
            with open(file_path, 'r') as f:
                data = json.load(f)

            bubble_data = data.get('bubble', {})
            # Create new bubble with imported data
            bubble = WorkspaceState(**bubble_data)

            # Save it with the manager
            self.manager._save_bubble(bubble)

            return f"✅ Imported bubble '{bubble.name}' ({bubble.bubble_id})"
        except Exception as e:
            return f"❌ Failed to import bubble: {e}"

    def _suspend_bubble(self, args: Dict[str, Any]) -> str:
        """Suspend a workspace bubble"""
        bubble_id = args.get('bubble_id')
        suspend_processes = args.get('suspend_processes', False)

        if not bubble_id:
            return "❌ Bubble ID required. Use: /bubble suspend --bubble-id <id> [--suspend-processes]"

        success = self.manager.suspend_bubble(bubble_id, suspend_processes)
        if success:
            process_msg = " (with process suspension)" if suspend_processes else ""
            return f"✅ Suspended bubble '{bubble_id}'{process_msg}"
        else:
            return f"❌ Failed to suspend bubble '{bubble_id}'"

    def _resume_bubble(self, args: Dict[str, Any]) -> str:
        """Resume a suspended workspace bubble"""
        bubble_id = args.get('bubble_id')
        if not bubble_id:
            return "❌ Bubble ID required. Use: /bubble resume --bubble-id <id>"

        success = self.manager.resume_bubble(bubble_id)
        if success:
            return f"✅ Resumed bubble '{bubble_id}'"
        else:
            return f"❌ Failed to resume bubble '{bubble_id}' (not suspended or not found)"

    def _create_bubble_version(self, args: Dict[str, Any]) -> str:
        """Create a new version of a bubble"""
        bubble_id = args.get('bubble_id')
        name = args.get('name')
        description = args.get('description')

        if not bubble_id:
            return "❌ Bubble ID required. Use: /bubble version --bubble-id <id> [--name <name>] [--description <desc>]"

        new_bubble = self.manager.create_bubble_version(bubble_id, name=name, description=description)
        if new_bubble:
            return f"✅ Created version {new_bubble.version} of bubble '{new_bubble.name}' ({new_bubble.bubble_id})"
        else:
            return f"❌ Failed to create version of bubble '{bubble_id}'"

    def _list_bubble_versions(self, args: Dict[str, Any]) -> str:
        """List all versions of a bubble"""
        bubble_id = args.get('bubble_id')
        if not bubble_id:
            return "❌ Bubble ID required. Use: /bubble versions --bubble-id <id>"

        versions = self.manager.get_bubble_versions(bubble_id)
        if not versions:
            return f"❌ No versions found for bubble '{bubble_id}'"

        result = f"🫧 Bubble Versions for {bubble_id}:\n\n"

        for bubble in versions:
            result += f"• v{bubble.version}: {bubble.name} ({bubble.bubble_id})\n"
            result += f"  Created: {self._format_timestamp(bubble.timestamp)}\n"
            if bubble.description:
                result += f"  Description: {bubble.description}\n"
            result += "\n"

        return result

    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp for display"""
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Main entry point"""
    import sys
    import json

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python run.py <action> [options]")
        print("Actions: create, list, show, restore, delete, export, import, suspend, resume, version, versions")
        print("Options:")
        print("  --name <name>           Name for new bubble")
        print("  --description <desc>    Description for new bubble")
        print("  --bubble-id <id>        Bubble ID for operations")
        print("  --tags <tags>           Comma-separated tags")
        print("  --file <path>           File path for export/import")
        return

    action = sys.argv[1]
    args = {'action': action}

    # Parse additional arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith('--'):
            key = arg[2:]  # Remove --
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                value = sys.argv[i + 1]
                args[key] = value
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1

    command = BubbleCommand()
    result = command.execute(args)
    print(result)


if __name__ == "__main__":
    main()