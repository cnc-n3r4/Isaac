#!/usr/bin/env python3
"""
Unified Help Command - Combines /help, /man, /apropos, /whatis functionality
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml


class UnifiedHelpCommand:
    """Unified help system combining all help functionalities"""

    def __init__(self):
        self.commands_dir = Path(__file__).parent.parent
        self.command_cache: Optional[Dict[str, Dict[str, Any]]] = None

    def load_command_manifests(self) -> Dict[str, Dict[str, Any]]:
        """Load all command manifests"""
        if self.command_cache is not None:
            return self.command_cache

        commands = {}

        # Scan all command directories
        for item in self.commands_dir.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                manifest_path = item / 'command.yaml'
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = yaml.safe_load(f)

                        if manifest:
                            # Store by primary trigger
                            primary_trigger = manifest.get('triggers', [item.name])[0]
                            commands[primary_trigger] = manifest
                            commands[primary_trigger]['_dir'] = item.name

                            # Also index by aliases
                            for alias in manifest.get('aliases', []):
                                commands[alias] = manifest
                                commands[alias]['_alias_for'] = primary_trigger

                    except Exception as e:
                        print(f"Warning: Could not load {manifest_path}: {e}")

        self.command_cache = commands
        return commands

    def list_commands(self, show_all: bool = False) -> str:
        """List all available commands"""
        commands = self.load_command_manifests()

        # Group commands by category (inferred from directory structure)
        categories = {}
        for trigger, manifest in commands.items():
            if trigger.startswith('_'):  # Skip aliases
                continue

            category = self._infer_category(manifest)
            if category not in categories:
                categories[category] = []

            status = manifest.get('status', 'unknown')
            if not show_all and status == 'hidden':
                continue

            categories[category].append((trigger, manifest))

        # Format output
        output = ["ISAAC Commands Reference", "=" * 50, ""]

        for category in sorted(categories.keys()):
            if not categories[category]:
                continue

            output.append(f"{category.upper()}:")
            output.append("-" * (len(category) + 1))

            for trigger, manifest in sorted(categories[category]):
                summary = manifest.get('summary', 'No description')
                status = manifest.get('status', 'stable')
                status_indicator = " [HIDDEN]" if status == 'hidden' else ""
                output.append(f"  {trigger:<15} {summary}{status_indicator}")

            output.append("")

        output.append("For detailed help: /help <command>")
        output.append("For search: /help --search <keyword>")
        output.append("For one-line descriptions: /help --whatis <command>")

        return "\n".join(output)

    def _infer_category(self, manifest: Dict[str, Any]) -> str:
        """Infer command category from manifest"""
        # Try to infer from directory name or summary
        dir_name = manifest.get('_dir', '')

        # Common categories
        if any(word in dir_name.lower() for word in ['file', 'read', 'write', 'edit', 'search', 'grep']):
            return "File Operations"
        elif any(word in dir_name.lower() for word in ['config', 'status', 'backup', 'restore']):
            return "System Management"
        elif any(word in dir_name.lower() for word in ['ai', 'ask', 'analyze', 'claude', 'openai']):
            return "AI & Analysis"
        elif any(word in dir_name.lower() for word in ['workspace', 'tasks', 'queue']):
            return "Workspace"
        elif any(word in dir_name.lower() for word in ['images', 'upload', 'share']):
            return "Media & Sharing"
        elif any(word in dir_name.lower() for word in ['msg', 'mine', 'summarize']):
            return "Communication"
        else:
            return "General"

    def get_command_help(self, command: str) -> str:
        """Get detailed help for a specific command"""
        commands = self.load_command_manifests()

        manifest = commands.get(command)
        if not manifest:
            return f"Command '{command}' not found. Use /help to see available commands."

        output = []
        output.append(f"Command: {command}")
        output.append("=" * (9 + len(command)))
        output.append("")

        # Basic info
        if 'summary' in manifest:
            output.append(f"Summary: {manifest['summary']}")
        if 'description' in manifest:
            output.append("")
            output.append("Description:")
            output.append(manifest['description'].strip())
        if 'version' in manifest:
            output.append(f"Version: {manifest['version']}")
        if 'status' in manifest:
            output.append(f"Status: {manifest['status']}")

        # Triggers and aliases
        triggers = manifest.get('triggers', [])
        aliases = manifest.get('aliases', [])
        if triggers or aliases:
            output.append("")
            output.append("Usage:")
            all_triggers = triggers + aliases
            for trigger in all_triggers:
                output.append(f"  {trigger}")

        # Arguments
        args = manifest.get('args', [])
        if args:
            output.append("")
            output.append("Arguments:")
            for arg in args:
                required = "(required)" if arg.get('required', False) else "(optional)"
                output.append(f"  {arg['name']}: {arg.get('help', 'No description')} {required}")

        # Examples
        examples = manifest.get('examples', [])
        if examples:
            output.append("")
            output.append("Examples:")
            for example in examples:
                output.append(f"  {example}")

        # Dependencies
        deps = manifest.get('dependencies', {})
        packages = deps.get('packages', [])
        api_keys = deps.get('api_keys', [])
        if packages or api_keys:
            output.append("")
            output.append("Dependencies:")
            if packages:
                output.append(f"  Packages: {', '.join(packages)}")
            if api_keys:
                output.append(f"  API Keys: {', '.join(api_keys)}")

        return "\n".join(output)

    def search_commands(self, keyword: str) -> str:
        """Search commands by keyword (was /apropos)"""
        commands = self.load_command_manifests()
        keyword_lower = keyword.lower()

        matches = []
        for trigger, manifest in commands.items():
            if trigger.startswith('_'):  # Skip aliases
                continue

            # Search in various fields
            searchable = [
                trigger,
                manifest.get('summary', ''),
                manifest.get('description', ''),
                ' '.join(manifest.get('aliases', [])),
                manifest.get('_dir', '')
            ]

            searchable_text = ' '.join(searchable).lower()

            if keyword_lower in searchable_text:
                matches.append((trigger, manifest))

        if not matches:
            return f"No commands found matching '{keyword}'"

        output = [f"Commands matching '{keyword}':", ""]

        for trigger, manifest in sorted(matches):
            summary = manifest.get('summary', 'No description')
            output.append(f"  {trigger:<15} {summary}")

        return "\n".join(output)

    def whatis_command(self, command: str) -> str:
        """Show one-line description (was /whatis)"""
        commands = self.load_command_manifests()

        manifest = commands.get(command)
        if not manifest:
            return f"{command}: command not found"

        summary = manifest.get('summary', 'No description available')
        return f"{command}: {summary}"

    def show_manual(self, topic: str) -> str:
        """Show detailed manual page (was /man)"""
        # For now, just show command help - could be extended for special topics
        if topic in ['isaac', 'intro', 'tutorial']:
            return self._get_special_manual(topic)
        else:
            return self.get_command_help(topic)

    def _get_special_manual(self, topic: str) -> str:
        """Get special manual pages"""
        manuals = {
            'isaac': """
ISAAC - AI-Enhanced Multi-Platform Shell Assistant

ISAAC is an intelligent shell assistant that combines AI capabilities with
traditional command-line tools. It provides context-aware assistance,
persistent memory, and seamless integration with development workflows.

KEY FEATURES:
- AI-powered command assistance and code generation
- Persistent conversation memory across sessions
- Intelligent file operations and analysis
- Multi-platform shell compatibility
- Extensible plugin architecture

GETTING STARTED:
- Type commands normally for shell execution
- Use 'isaac <query>' for AI assistance
- Use '/command' for built-in ISAAC commands
- Use '/help' for command reference

For more information, see /help tutorial
""",
            'intro': """
ISAAC Introduction

ISAAC enhances your shell experience with AI assistance while maintaining
full compatibility with existing workflows.

BASIC USAGE:
1. Normal commands work as expected
2. 'isaac <question>' for AI help
3. '/help' shows available commands
4. '/config' manages settings

AI FEATURES:
- Context-aware responses
- Code generation and analysis
- Intelligent file operations
- Persistent memory

For detailed command help, use /help <command>
""",
            'tutorial': """
ISAAC Tutorial - Getting Started

1. BASIC COMMANDS:
   ls                           # Normal shell command
   isaac how do I use git?     # AI assistance
   /help                       # Show all commands
   /help config                # Help for specific command

2. AI FEATURES:
   isaac analyze this file     # AI file analysis
   isaac generate a script     # Code generation
   isaac explain this error    # Error explanation

3. FILE OPERATIONS:
   /read file.txt              # Read file contents
   /write file.txt "content"   # Write to file
   /search "pattern"           # Search files

4. WORKSPACE MANAGEMENT:
   /workspace create myproject # Create workspace
   /workspace switch myproject # Switch workspace
   /status                     # Show current status

5. ADVANCED FEATURES:
   /images --history           # Image management
   /backup                     # Backup current state
   /config --edit              # Edit configuration

For more help, use /help or /help --search <topic>
"""
        }

        return manuals.get(topic, f"Manual page '{topic}' not found")

    def run(self, args: List[str]) -> str:
        """Main command execution"""
        if not args:
            # Default: list all commands
            return self.list_commands()

        # Parse flags and arguments
        flags = {}
        positional_args = []

        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('--'):
                # Long flag
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    flags[key[2:]] = value
                else:
                    flags[arg[2:]] = True
                    # Check for flag with value
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        flags[arg[2:]] = args[i + 1]
                        i += 1
            elif arg.startswith('-') and len(arg) > 1:
                # Short flag
                flag_name = arg[1:]
                if flag_name in ['s', 'w', 'm', 'a', 'v']:
                    # Known short flags
                    flag_map = {'s': 'search', 'w': 'whatis', 'm': 'man', 'a': 'all', 'v': 'verbose'}
                    flags[flag_map[flag_name]] = True
                    if flag_name in ['s', 'w', 'm'] and i + 1 < len(args):
                        flags[flag_map[flag_name]] = args[i + 1]
                        i += 1
                else:
                    flags[flag_name] = True
            else:
                positional_args.append(arg)
            i += 1

        # Handle different modes
        if 'search' in flags or 's' in flags:
            keyword = flags.get('search') or flags.get('s')
            if isinstance(keyword, bool):
                keyword = positional_args[0] if positional_args else ""
            return self.search_commands(str(keyword) if keyword else "")

        elif 'whatis' in flags or 'w' in flags:
            command = flags.get('whatis') or flags.get('w')
            if isinstance(command, bool):
                command = positional_args[0] if positional_args else ""
            return self.whatis_command(str(command) if command else "")

        elif 'man' in flags or 'm' in flags:
            topic = flags.get('man') or flags.get('m')
            if isinstance(topic, bool):
                topic = positional_args[0] if positional_args else "isaac"
            return self.show_manual(str(topic) if topic else "isaac")

        elif positional_args:
            # Specific command help
            return self.get_command_help(positional_args[0])

        else:
            # Default: list commands
            show_all = flags.get('all', False) or flags.get('a', False)
            return self.list_commands(show_all)


def main():
    """Command entry point"""
    import sys
    command = UnifiedHelpCommand()
    result = command.run(sys.argv[1:])
    print(result)


if __name__ == "__main__":
    main()