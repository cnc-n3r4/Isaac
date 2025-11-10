"""
Help Command - Standardized Implementation

Command help and reference documentation.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse


class HelpCommand(BaseCommand):
    """Display help information for commands"""

    def __init__(self):
        super().__init__()
        self.command_manifests = self._load_command_manifests()
        self.help_map = self._build_help_map()

    def _load_command_manifests(self) -> Dict[str, Dict]:
        """Load all command manifests from the commands directory"""
        import yaml
        
        manifests = {}
        commands_dir = Path(__file__).parent.parent
        
        # Find all command.yaml files
        for yaml_file in commands_dir.rglob("command.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    manifest = yaml.safe_load(f)
                    if manifest:
                        # Register by all triggers and aliases
                        for trigger in manifest.get("triggers", []):
                            manifests[trigger] = manifest
                        for alias in manifest.get("aliases", []):
                            manifests[alias] = manifest
            except Exception as e:
                # Skip malformed manifests
                continue
                
        return manifests

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute help command.

        Args:
            args: Command arguments (optional command name for detailed help)
            context: Optional execution context

        Returns:
            CommandResponse with help text
        """
        parser = FlagParser(args)

        # Get command name from first positional arg
        command_name = parser.get_positional(0)

        try:
            if command_name:
                # Show detailed help for specific command
                output = self._get_detailed_help(command_name)
            else:
                # Show overview of all commands
                output = self._get_overview_help()

            return CommandResponse(
                success=True,
                data=output,
                metadata={"command": command_name} if command_name else {}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "EXECUTION_ERROR"}
            )

    def _get_overview_help(self) -> str:
        """Show overview of available commands"""
        # Group commands by category
        categories = {}
        for trigger, manifest in self.command_manifests.items():
            if trigger.startswith('/'):  # Only show slash commands
                category = manifest.get("category", "general")
                if category not in categories:
                    categories[category] = []
                if trigger not in categories[category]:  # Avoid duplicates
                    categories[category].append(trigger)
        
        # Build help text
        help_text = "ISAAC COMMAND REFERENCE\n"
        help_text += "=" * 50 + "\n\n"
        
        # Sort categories
        category_order = ["system", "file", "ai", "communication", "workspace", "general"]
        for cat in category_order:
            if cat in categories:
                help_text += f"{cat.upper()}:\n"
                for cmd in sorted(categories[cat]):
                    manifest = self.command_manifests[cmd]
                    summary = manifest.get("summary", manifest.get("description", ""))
                    if len(summary) > 60:
                        summary = summary[:57] + "..."
                    help_text += f"  {cmd:<20} {summary}\n"
                help_text += "\n"
        
        # Add any remaining categories
        for cat, commands in categories.items():
            if cat not in category_order:
                help_text += f"{cat.upper()}:\n"
                for cmd in sorted(commands):
                    manifest = self.command_manifests[cmd]
                    summary = manifest.get("summary", manifest.get("description", ""))
                    if len(summary) > 60:
                        summary = summary[:57] + "..."
                    help_text += f"  {cmd:<20} {summary}\n"
                help_text += "\n"
        
        help_text += "For detailed help: /help <command>\n"
        help_text += "Example: /help /msg\n"
        
        return help_text

    def _get_detailed_help(self, command_name: str) -> str:
        """Show detailed help for a specific command"""
        # First check if we have custom help
        if command_name in self.help_map:
            return self.help_map[command_name]
        
        # Otherwise generate help from manifest
        manifest = self.command_manifests.get(command_name)
        if manifest:
            return self._generate_help_from_manifest(manifest)
        
        return f"No help available for: {command_name}\n\nUse /help to see available commands."

    def _generate_help_from_manifest(self, manifest: Dict) -> str:
        """Generate help text from a command manifest"""
        name = manifest.get("name", "Unknown")
        description = manifest.get("description", "")
        usage = manifest.get("usage", "")
        examples = manifest.get("examples", [])
        tier = manifest.get("tier", "?")
        aliases = manifest.get("aliases", [])
        args = manifest.get("args", [])
        
        help_text = f"{name.upper()} COMMAND - DETAILED HELP\n\n"
        
        if description:
            help_text += f"DESCRIPTION:\n  {description}\n\n"
            
        if usage:
            help_text += f"USAGE:\n  {usage}\n\n"
            
        if examples:
            help_text += "EXAMPLES:\n"
            for example in examples:
                help_text += f"  {example}\n"
            help_text += "\n"
            
        if args:
            help_text += "ARGUMENTS:\n"
            for arg in args:
                arg_name = arg.get("name", "")
                arg_type = arg.get("type", "")
                required = arg.get("required", False)
                arg_help = arg.get("help", "")
                enum_values = arg.get("enum", [])
                
                req_str = "required" if required else "optional"
                help_text += f"  --{arg_name} ({arg_type}, {req_str})"
                if enum_values:
                    help_text += f" [{', '.join(enum_values)}]"
                help_text += f"\n    {arg_help}\n"
            help_text += "\n"
            
        help_text += f"SAFETY TIER: {tier}\n"
        
        if aliases:
            help_text += f"ALIASES: {', '.join(aliases)}\n"
            
        return help_text.strip()

    def _build_help_map(self) -> Dict[str, str]:
        """Build comprehensive help map for all commands"""
        return {
            "/config": """Config Command - Detailed Help

USAGE:
  /config                    - Show configuration overview
  /config --status           - Detailed system status
  /config --ai               - AI provider configuration
  /config --ai-routing       - AI routing configuration
  /config --cloud            - Cloud sync status
  /config --plugins          - List available plugins
  /config --collections      - xAI Collections status
  /config --set <key> <value> - Change configuration setting
  /config --apikey <service> <key> - Set API key for AI service

AI ROUTING CONFIGURATION:
  /config --ai-routing                         - View current routing settings
  /config --ai-routing-set <level> <provider>  - Set provider for complexity
  /config --ai-routing-model <prov> <model>    - Set model for provider
  /config --ai-routing-limits <period> <amt>   - Set cost limits
  /config --ai-routing-reset                   - Reset to defaults

EXAMPLES:
  /config                    - Show version, session, history
  /config --status          - Show cloud, AI, network status
  /config --ai              - Show AI provider and connection
  /config --ai-routing      - View routing configuration
  /config --set default_tier 3 - Change safety tier
  /config --apikey xai-chat YOUR_API_KEY - Set xAI chat API key
  /config --apikey claude YOUR_API_KEY - Set Claude API key""".strip(),

            "/ask": """Ask Command - Direct AI Chat

USAGE:
  /ask <question>    - Query AI without command execution
  /a <question>      - Short alias for /ask

DESCRIPTION:
  Chat with AI directly without command execution.
  Unlike 'isaac <query>', this sends queries to AI
  and returns text responses without executing commands.

EXAMPLES:
  /ask where is alaska? - Geographic question
  /ask what is docker? - Technical explanation
  /ask explain kubernetes networking - Detailed information
  /a quick question - Short alias

DIFFERENCE FROM ISAAC:
  /ask - Conversational, returns text only
  isaac <query> - Translates to shell commands for execution""".strip(),

            "/status": """Status Command - Detailed Help

USAGE:
  /status       - One-line system summary
  /status -v    - Detailed status

EXAMPLES:
  /status       - Shows: Session ID, Workspace, AI status
  /status -v    - Full system diagnostics

DISPLAY:
  Session: Machine identifier
  Workspace: ✓ Active / ○ None
  AI: ✓ Available / ✗ Not configured
  Tasks: Background task stats
  Machines: Orchestration status""".strip(),

            "/help": """Help Command - Detailed Help

USAGE:
  /help              - Show command overview
  /help <command>    - Detailed help for specific command

EXAMPLES:
  /help              - List all available commands
  /help /config      - Show config command details
  /help /status      - Show status command details

ALIASES:
  /h, /?             - Same as /help""".strip(),

            "/analyze": """Analyze Command - AI Analysis

USAGE:
  <content> | /analyze [type]

ANALYSIS TYPES:
  general   - General analysis (default)
  sentiment - Sentiment analysis with score
  summary   - 2-3 sentence summary
  keywords  - Extract key phrases
  code      - Code quality analysis
  data      - Data structure insights

EXAMPLES:
  /read log.txt | /analyze
  /grep ERROR *.log | /analyze sentiment
  /read code.py | /analyze code
  echo 'data' | /analyze summary

DESCRIPTION:
  Analyzes piped data using AI to provide insights,
  summaries, or specialized analysis based on type.""".strip(),

            "/read": """Read Command - Display File Contents

USAGE:
  /read <file>              - Read entire file
  /read <file> --offset 10  - Start from line 10
  /read <file> --limit 50   - Read first 50 lines

DESCRIPTION:
  Display the contents of text files with line numbers
  and optional offset/limit for large files.

EXAMPLES:
  /read config.json         - Show entire config file
  /read script.py --offset 10 --limit 20 - Show lines 10-30
  /read log.txt --limit 50   - Show first 50 lines

OPTIONS:
  --offset N    - Start reading from line N
  --limit N     - Read at most N lines""".strip(),

            "/write": """Write Command - Create or Overwrite Files

USAGE:
  /write <file>             - Create file from stdin
  echo "text" | /write <file> - Write text to file

DESCRIPTION:
  Create new files or overwrite existing ones with text content.

EXAMPLES:
  echo "Hello" | /write test.txt
  /write config.json < input.json

OPTIONS:
  Content is read from stdin (piped input)""".strip(),

            "/edit": """Edit Command - Modify Existing Files

USAGE:
  /edit <file> <old> <new>           - Replace first occurrence
  /edit <file> <old> <new> --replace-all - Replace all occurrences

DESCRIPTION:
  Modify existing files using exact string replacement.

EXAMPLES:
  /edit script.py "old_var" "new_var"
  /edit config.json "localhost" "0.0.0.0" --replace-all

OPTIONS:
  --replace-all    - Replace all occurrences (not just first)""".strip(),

            "/grep": """Grep Command - Search Files

USAGE:
  /grep <pattern>                - Search all files
  /grep <pattern> --path <dir>   - Search specific directory
  /grep <pattern> -i              - Case insensitive
  /grep <pattern> --output content - Show matching lines

DESCRIPTION:
  Search file contents using regular expressions.

EXAMPLES:
  /grep "TODO" --path src/
  /grep "class.*Manager" --output content
  /grep "error" -i

OPTIONS:
  -i, --ignore-case    - Case insensitive search
  -C, --context N      - Show N lines of context
  --output content     - Show matching lines
  --output count       - Show match counts
  --path DIR           - Search in directory""".strip(),

            "/glob": """Glob Command - Find Files

USAGE:
  /glob <pattern>          - Find files matching pattern
  /glob <pattern> --path <dir> - Search specific directory
  /glob <pattern> --type f     - Files only

DESCRIPTION:
  Search for files using glob patterns.

EXAMPLES:
  /glob "*.py"
  /glob "**/*.js" --path src/
  /glob "test_*" --type f

PATTERN SYNTAX:
  *     - Match any characters
  ?     - Match single character
  [abc] - Match character in set
  **    - Recursive directory match""".strip(),
        }

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="help",
            description="Display help information for commands",
            usage="/help [command_name]",
            examples=[
                "/help",
                "/help /config",
                "/help /status",
                "/help /ask"
            ],
            tier=1,  # Safe - documentation only
            aliases=["h", "?"],
            category="system"
        )
