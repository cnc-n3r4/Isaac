"""
Ask Command - Standardized Implementation

Direct AI chat interface without command execution.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.ai.xai_client import XaiClient
from isaac.core.session_manager import SessionManager


class AskCommand(BaseCommand):
    """Direct AI chat interface - ask questions without executing commands"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute ask command.

        Args:
            args: Command arguments (the question to ask)
            context: Optional execution context (may include piped_input)

        Returns:
            CommandResponse with AI response or error
        """
        parser = FlagParser(args)

        # Get query from positional args or piped input
        query = " ".join(parser.get_all_positional())

        # Check for piped input
        is_piped_input = False
        if context and "piped_input" in context:
            piped_content = context.get("piped_input", "")
            is_piped_input = True

            # Build query: combine piped data with user's question
            if query:
                # User asked a specific question about the data
                query = f"{query}\n\nContext data:\n{piped_content}"
            else:
                # No question, just analyze the data
                query = f"Analyze this data:\n\n{piped_content}"

        # Validate
        if not query:
            return CommandResponse(
                success=False,
                error="No query provided. Usage: /ask <question>",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        # Get session and config
        try:
            session = SessionManager()
            config = session.get_config()

            # Get API configuration - use nested structure for chat
            xai_config = config.get("xai", {})
            chat_config = xai_config.get("chat", {})
            api_key = chat_config.get("api_key")

            # Fallback to old flat structure for backward compatibility
            if not api_key:
                api_key = config.get("xai_api_key") or config.get("api_key")

            if not api_key:
                return CommandResponse(
                    success=False,
                    error="xAI Chat API key not configured. Set it in ~/.isaac/config.json under xai.chat.api_key",
                    metadata={"error_code": "CONFIG_ERROR"}
                )

            # Smart truncation for large piped content
            if is_piped_input and len(query) > 10000:  # ~3000 tokens estimated
                # Extract user question and context data
                if "\n\nContext data:\n" in query:
                    parts = query.split("\n\nContext data:\n", 1)
                    user_question = parts[0]
                    content = parts[1]

                    # Truncate context intelligently
                    max_context_chars = 8000  # ~2500 tokens - safe for most models
                    if len(content) > max_context_chars:
                        content = (
                            content[:max_context_chars]
                            + "\n\n... [Context truncated - original content was too large for API limits]"
                        )

                    query = f"{user_question}\n\nContext data:\n{content}"

            # Initialize xAI client
            client = XaiClient(
                api_key=api_key,
                api_url=config.get("xai_api_url", "https://api.x.ai/v1/chat/completions"),
                model=config.get("xai_model", "grok-3"),
            )

            # Build chat preprompt (context-aware with history)
            preprompt = self._build_chat_preprompt(session, query, is_piped_input)

            # Query AI
            response = client.chat(prompt=query, system_prompt=preprompt)

            # Log query to AI history
            session.log_ai_query(
                query=query,
                translated_command="[chat_mode]",
                explanation=response[:100],
                executed=False,
                shell_name="chat",
            )

            return CommandResponse(
                success=True,
                data=response,
                metadata={
                    "mode": "chat",
                    "is_piped": is_piped_input
                }
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "EXECUTION_ERROR"}
            )

    def _build_chat_preprompt(
        self, session: SessionManager, current_query: str, is_piped_input: bool = False
    ) -> str:
        """
        Build context-aware preprompt for chat mode with conversation history.

        Includes:
        - System context (OS, shell, current directory)
        - User preferences
        - Recent chat history (for memory)
        - Special mode for piped data analysis
        """
        # Get system context
        shell_name = "PowerShell"  # Default for Windows
        if hasattr(session, "shell_adapter") and session.shell_adapter:
            shell_name = session.shell_adapter.__class__.__name__.replace("Adapter", "")

        current_dir = Path.cwd()

        # Special preprompt for piped input - focus on data analysis
        if is_piped_input:
            preprompt = f"""You are Isaac, an AI assistant analyzing data piped from a previous command.

CRITICAL INSTRUCTIONS:
- The user has piped data from another command and is asking a question about that specific data
- Focus ONLY on analyzing the provided data to answer their question
- DO NOT suggest shell commands or PowerShell syntax
- DO NOT give generic advice about using commands
- Answer their specific question using ONLY the data provided

The data is in the query below, followed by the user's question.
Analyze the data and answer the question directly.
"""
        else:
            # Regular chat mode preprompt
            preprompt = f"""You are Isaac, an AI assistant integrated into the user's shell.

CONTEXT:
- Operating System: Windows
- Current Shell: {shell_name}
- Current Directory: {current_dir}

IMPORTANT DISTINCTIONS:
1. Geographic/General Questions: Answer directly
   - "where is alaska?" → Geographic information
   - "what is docker?" → Technical explanation

2. File/Command Questions: Mention the command but don't execute
   - "where is alaska.exe?" → "You can search with: where.exe alaska.exe"
   - "show me my files" → "You can list files with: ls or dir"

3. Shell-Specific Awareness:
   - User is on {shell_name}, so reference appropriate commands
   - PowerShell: Get-*, Set-*, cmdlets
   - Bash: ls, grep, awk, sed

RESPONSE STYLE:
- Conversational and helpful
- Brief but complete answers
- Reference shell commands when relevant
- No command execution (this is chat mode)
"""

        # Add conversation history if available
        try:
            if hasattr(session, "ai_query_history") and session.ai_query_history:
                recent_queries = session.ai_query_history.get_recent(count=5)

                # Filter to only chat mode queries (not translation mode)
                chat_queries = [
                    q
                    for q in recent_queries
                    if q.get("shell") == "chat" or q.get("command") == "[chat_mode]"
                ]

                if chat_queries:
                    preprompt += "\n\nRECENT CONVERSATION HISTORY:\n"
                    preprompt += "(Use this to maintain context and answer questions about previous exchanges)\n\n"

                    for i, q in enumerate(reversed(chat_queries), 1):  # Chronological order
                        query_text = q.get("query", "")
                        response_preview = q.get("explanation", "")[:100]  # First 100 chars of response

                        preprompt += f'{i}. User asked: "{query_text}"\n'
                        if response_preview:
                            preprompt += f'   You responded: "{response_preview}..."\n'
                        preprompt += "\n"

                    preprompt += "You can reference these previous exchanges when relevant.\n"
        except Exception:
            # Don't fail if history unavailable, just skip it
            pass

        preprompt += "\nCurrent user query follows below:\n"

        return preprompt

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="ask",
            description="Direct AI chat interface without command execution",
            usage="/ask <question>",
            examples=[
                "/ask where is alaska?",
                "/ask what is docker?",
                "/ask explain kubernetes networking",
                "/a quick question"
            ],
            tier=1,  # Safe - no command execution
            aliases=["a"],
            category="ai"
        )
