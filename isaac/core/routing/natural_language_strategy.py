"""
Natural language strategy - handles "isaac ..." queries.
"""

from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy


class NaturalLanguageStrategy(CommandStrategy):
    """Strategy for handling natural language queries."""

    def can_handle(self, input_text: str) -> bool:
        """Check if input is natural language starting with 'isaac'."""
        if not self._is_natural_language(input_text):
            return False

        # Must start with "isaac " (lowercase check done in _is_natural_language)
        return input_text.lower().startswith("isaac ")

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Translate natural language to command and execute."""
        # Remove "isaac " prefix
        query = input_text[6:].strip()

        # Check if query should route to chat mode (geographic/general info)
        query_classifier = context.get("query_classifier")
        if query_classifier and query_classifier.is_chat_mode_query(query):
            # Route to chat mode (like /ask command)
            return self._handle_chat_query(query, context)

        # AI translation to command
        from isaac.ai.translator import translate_query

        result = translate_query(query, self.shell.name, self.session)

        if result["success"]:
            # Log AI query separately (privacy)
            if hasattr(self.session, "log_ai_query"):
                self.session.log_ai_query(
                    query=query,
                    translated_command=result["command"],
                    explanation=result.get("explanation", ""),
                    executed=True,
                    shell_name=self.shell.name,
                )

            # Execute translated command through tier system (CRITICAL)
            print(f"Isaac > Executing: {result['command']}")
            # Need to route back through router for tier processing
            router = context.get("router")
            if router:
                return router.route_command(result["command"])
            else:
                return self.shell.execute(result["command"])
        else:
            # Translation failed
            return CommandResult(success=False, output=f"Isaac > {result['error']}", exit_code=-1)

    def get_help(self) -> str:
        """Get help text for natural language."""
        return "Natural language: isaac <your request> - Translate natural language to commands"

    def get_priority(self) -> int:
        """Medium priority."""
        return 55

    def _is_natural_language(self, input_text: str) -> bool:
        """Check if input contains natural language (spaces, common words)."""
        # Simple heuristic: has spaces and not obviously a command
        if " " not in input_text.strip():
            return False

        # Check for obvious command patterns
        first_word = input_text.strip().split()[0].lower()
        obvious_commands = ["ls", "cd", "pwd", "grep", "find", "cat", "echo", "rm", "cp", "mv"]

        return first_word not in obvious_commands

    def _handle_chat_query(self, query: str, context: Dict[str, Any]) -> CommandResult:
        """Handle chat-style query (no execution, just AI response)."""
        try:
            from isaac.ai import AIRouter

            # Initialize AI router with session config
            router = AIRouter(session_mgr=self.session)

            # Build chat preprompt
            preprompt = self._build_chat_preprompt()

            # Prepare messages for router
            messages = [
                {"role": "system", "content": preprompt},
                {"role": "user", "content": query},
            ]

            # Query AI through router
            response = router.chat(messages=messages)

            if response.success:
                # Log query to AI history
                self.session.log_ai_query(
                    query=query,
                    translated_command="[chat_mode_auto]",
                    explanation=response.content[:100],
                    executed=False,
                    shell_name="chat",
                )

                return CommandResult(
                    success=True, output=f"Isaac > {response.content}", exit_code=0
                )
            else:
                return CommandResult(
                    success=False, output=f"Isaac > AI Error: {response.error}", exit_code=-1
                )

        except Exception as e:
            return CommandResult(
                success=False, output=f"Isaac > Error querying AI: {e}", exit_code=-1
            )

    def _build_chat_preprompt(self) -> str:
        """Build context-aware preprompt for chat mode."""
        from pathlib import Path

        shell_name = self.shell.name if hasattr(self.shell, "name") else "PowerShell"
        current_dir = Path.cwd()

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

Current user query follows below:
"""

        return preprompt
