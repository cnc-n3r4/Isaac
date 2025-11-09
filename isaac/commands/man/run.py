#!/usr/bin/env python3
"""
Man Command - Display Manual Pages
"""

import sys
import json
from pathlib import Path

# Add Isaac to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

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


def main():
    """Main entry point"""
    # Read payload
    try:
        payload = json.loads(sys.stdin.read())
        args_dict = payload.get("args", {})
        command_arg = args_dict.get("command", "isaac")
    except (json.JSONDecodeError, KeyError):
        # Fallback to command line args
        command_arg = sys.argv[1] if len(sys.argv) > 1 else "isaac"

    # Special pages
    if command_arg in ["isaac", "intro", "introduction"]:
        print(ISAAC_MANUAL)
        return

    # Get man page
    generator = get_generator()
    man_page = generator.get_man_page(command_arg)

    if man_page:
        print(man_page)
    else:
        print(f"No manual entry for {command_arg}", file=sys.stderr)
        print(f"Try: /man isaac", file=sys.stderr)
        print(f"Or: /apropos <keyword>", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
