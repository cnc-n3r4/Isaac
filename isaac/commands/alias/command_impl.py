"""
Alias Command - Standardized Implementation

Unix-to-PowerShell command alias management system.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.core.unix_aliases import UnixAliasTranslator


class AliasCommand(BaseCommand):
    """Unix-to-PowerShell alias management"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute alias command.

        Args:
            args: Command arguments
            context: Optional execution context with session data

        Returns:
            CommandResponse with alias operation results
        """
        try:
            parser = FlagParser(args)
            translator = UnixAliasTranslator()

            # Get session from context if available
            session = {}
            if context and "session" in context:
                session = context["session"]

            # Determine action from flags
            if parser.has_flag("list"):
                result = self._handle_list(translator)
            elif parser.has_flag("show"):
                command = parser.get_flag("show")
                if not command:
                    command = parser.get_positional(0)
                if not command:
                    result = "Usage: /alias --show <command>"
                else:
                    result = self._handle_show(translator, command)
            elif parser.has_flag("enable"):
                result = self._handle_enable(session)
            elif parser.has_flag("disable"):
                result = self._handle_disable(session)
            elif parser.has_flag("add"):
                positional = parser.get_all_positional()
                if len(positional) >= 2:
                    unix_cmd, powershell_cmd = positional[0], positional[1]
                    result = self._handle_add(session, unix_cmd, powershell_cmd)
                else:
                    result = "Usage: /alias --add <unix_cmd> <powershell_cmd>"
            elif parser.has_flag("remove"):
                unix_cmd = parser.get_flag("remove")
                if not unix_cmd:
                    unix_cmd = parser.get_positional(0)
                if not unix_cmd:
                    result = "Usage: /alias --remove <unix_cmd>"
                else:
                    result = self._handle_remove(session, unix_cmd)
            elif parser.has_flag("help", aliases=["h"]):
                result = self.get_help()
            elif not parser.get_all_flags():
                # Default to list if no flags
                result = self._handle_list(translator)
            else:
                result = f"Unknown flags: {list(parser.get_all_flags().keys())}\n\n{self.get_help()}"

            return CommandResponse(
                success=True,
                data=result,
                metadata={"operation": "alias"}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "ALIAS_ERROR"}
            )

    def _handle_list(self, translator: UnixAliasTranslator) -> str:
        """Show all available aliases"""
        aliases = translator.list_aliases()

        if not aliases:
            return "No aliases available"

        result = "Available Unix aliases:\n\n"
        for cmd, desc in sorted(aliases.items()):
            result += f"  {cmd:<10} → {desc}\n"

        result += "\nUse '/alias show <command>' for details and examples"
        return result

    def _handle_show(self, translator: UnixAliasTranslator, command: str) -> str:
        """Show translation for specific command"""
        description = translator.get_description(command)
        if not description:
            return f"No alias found for: {command}"

        examples = translator.get_examples(command)

        result = f"{command}: {description}\n\n"

        if examples:
            result += "Examples:\n"
            for example in examples:
                unix = example.get("unix", "")
                powershell = example.get("powershell", "")
                result += f"  Unix:       {unix}\n"
                result += f"  PowerShell: {powershell}\n\n"

        return result.strip()

    def _handle_enable(self, session) -> str:
        """Enable Unix alias translation"""
        session["enable_unix_aliases"] = True
        session["show_translated_command"] = True
        return "Unix alias translation enabled. Commands like 'ls' will be translated to PowerShell equivalents."

    def _handle_disable(self, session) -> str:
        """Disable Unix alias translation"""
        session["enable_unix_aliases"] = False
        return "Unix alias translation disabled. Unix commands will fail normally."

    def _handle_add(self, session, unix_cmd: str, powershell_cmd: str) -> str:
        """Add custom alias"""
        overrides = session.get("alias_overrides", {})
        overrides[unix_cmd] = powershell_cmd
        session["alias_overrides"] = overrides
        return f"Added alias: {unix_cmd} → {powershell_cmd}"

    def _handle_remove(self, session, unix_cmd: str) -> str:
        """Remove custom alias"""
        overrides = session.get("alias_overrides", {})
        if unix_cmd in overrides:
            del overrides[unix_cmd]
            session["alias_overrides"] = overrides
            return f"Removed alias: {unix_cmd}"
        else:
            return f"No custom alias found for: {unix_cmd}"

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="alias",
            description="Unix-to-PowerShell command alias management",
            usage="/alias [--list|--show <cmd>|--enable|--disable|--add <unix> <ps>|--remove <unix>]",
            examples=[
                "/alias                   # List all Unix-to-PowerShell aliases",
                "/alias --show ls        # Show PowerShell equivalent for 'ls'",
                "/alias --enable         # Enable automatic Unix→PowerShell translation",
                "/alias --add ll 'ls -la' # Add custom alias for detailed listing",
                "/alias --remove ll      # Remove custom alias"
            ],
            tier=1,  # Safe - configuration only
            aliases=["aliases"],
            category="system"
        )
