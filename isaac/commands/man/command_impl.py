"""
Man Command - Standardized Implementation

Display manual pages for Isaac commands.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.core.man_pages import get_generator

ISAAC_MANUAL = """
ISAAC(1)                         User Commands                        ISAAC(1)

NAME
    isaac - Intelligent Shell Assistant with AI and Collections

SYNOPSIS
    isaac [OPTIONS] [QUERY]
    isaac --start
    /command [args...]

DESCRIPTION
    ISAAC is an intelligent command-line interface that combines traditional
    shell commands with AI-powered assistance. It provides:

    - Multi-provider AI routing (Grok, Claude, OpenAI)
    - Intelligent task complexity detection
    - Cost tracking and budget management
    - xAI Collections for personal knowledge
    - Message queue for notifications
    - Extensible plugin system

MODES
    Interactive Mode
        isaac --start
        Launches ISAAC shell with persistent session, message queue,
        and command history.

    Query Mode
        isaac "what is kubernetes?"
        Execute one-off AI queries or command translations.

COMMAND SYSTEM
    ISAAC uses a /slash command plugin architecture. All commands follow
    the pattern:
        /command [--flag value] [args...]

    Available Commands:
        Use 'man -k .' to list all commands
        Use 'apropos <keyword>' to search by keyword
        Use 'whatis <command>' for one-line summaries

CONFIGURATION
    Configuration files are stored in:
        ~/.isaac/

    Key files:
        ai_config.json         - AI provider settings
        ai_routing_config.json - Routing preferences
        cost_tracking.json     - Cost/budget data
        message_queue.db       - Notification queue
        session_config.json    - Session settings

AI ROUTING
    ISAAC automatically selects the best AI provider based on:
    - Task complexity (simple/medium/complex/expert)
    - Task type (code_write, code_debug, analysis, chat)
    - Cost budget and limits
    - User preferences

    Configure routing:
        /config --ai-routing
        /config --ai-routing-set <level> <provider>

COST TRACKING
    ISAAC tracks API costs and enforces budgets:
        Daily limit:   $10.00 (default)
        Monthly limit: $100.00 (default)

    View costs:
        /config --ai

    Set limits:
        /config --ai-routing-limits daily 10.0
        /config --ai-routing-limits monthly 100.0

MESSAGES
    Background operations and monitoring send notifications:
        ! - System messages
        ¢ - Code messages

    View messages:
        /msg
        /msg --read <id>

    Prompt indicator shows pending count:
        $>              (no messages)
        [!2¢1]>         (2 system, 1 code message)

EXAMPLES
    Start interactive session:
        $ isaac --start

    Query AI:
        $ isaac "explain docker compose"

    Use commands:
        $ isaac --start
        $> /msg
        $> /config --ai-routing
        $> /mine --search "kubernetes"

FILES
    ~/.isaac/ai_config.json
    ~/.isaac/ai_routing_config.json
    ~/.isaac/cost_tracking.json
    ~/.isaac/message_queue.db
    ~/.isaac/session_config.json

SEE ALSO
    /help, /config, /msg, /mine, /ask

    apropos(1), whatis(1)

    Online documentation:
        https://github.com/cnc-n3r4/Isaac

AUTHOR
    cnc-n3r4

VERSION
    ISAAC v2.0.0 with Phase 3 Enhanced AI Routing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              ISAAC v2.0.0
""".strip()


class ManCommand(BaseCommand):
    """Display manual pages for Isaac commands"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute man command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with manual page content
        """
        try:
            parser = FlagParser(args)
            command_arg = parser.get_positional(0, "isaac")

            # Special pages
            if command_arg in ["isaac", "intro", "introduction"]:
                return CommandResponse(
                    success=True,
                    data=ISAAC_MANUAL,
                    metadata={"page": command_arg}
                )

            # Get man page
            generator = get_generator()
            man_page = generator.get_man_page(command_arg)

            if man_page:
                return CommandResponse(
                    success=True,
                    data=man_page,
                    metadata={"page": command_arg}
                )
            else:
                error_msg = f"No manual entry for {command_arg}\n"
                error_msg += "Try: /man isaac\n"
                error_msg += "Or: /apropos <keyword>"
                return CommandResponse(
                    success=False,
                    error=error_msg,
                    metadata={"error_code": "PAGE_NOT_FOUND"}
                )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "MAN_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="man",
            description="Display manual pages for Isaac commands",
            usage="/man <command>",
            examples=[
                "/man isaac      # Show ISAAC system manual",
                "/man config     # Show manual for config command",
                "/man mine        # Show manual for mine command"
            ],
            tier=1,  # Safe - read-only information
            aliases=["manual", "help-man"],
            category="general"
        )
