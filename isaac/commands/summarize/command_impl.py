"""
Summarize Command - Standardized Implementation

AI-powered content summarization.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse

try:
    from isaac.ai.xai_client import XaiClient
    HAS_XAI_CLIENT = True
except ImportError:
    HAS_XAI_CLIENT = False


class SummarizeCommand(BaseCommand):
    """AI-powered content summarization"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute summarize command.

        Args:
            args: Command arguments (summary length: short|medium|long)
            context: Optional execution context with piped input

        Returns:
            CommandResponse with summarization results
        """
        try:
            parser = FlagParser(args)

            # Get summary length from arguments (default: medium)
            summary_length = parser.get_positional(0, "medium")

            # Get piped content from context
            if context and "piped_input" in context:
                content = context["piped_input"]
                kind = context.get("piped_kind", "text")
            else:
                return CommandResponse(
                    success=False,
                    error="Usage: <content> | /summarize [short|medium|long]",
                    metadata={"error_code": "NO_INPUT"}
                )

            # Summarize content
            result = self._summarize_content(content, kind, summary_length)

            return CommandResponse(
                success=True,
                data=result,
                metadata={
                    "kind": "text",
                    "summary_length": summary_length
                }
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "SUMMARIZE_ERROR"}
            )

    def _summarize_content(self, content: str, kind: str, length: str) -> str:
        """Summarize content using AI."""
        if not HAS_XAI_CLIENT:
            return "Error: xAI client not available. Check xai_sdk installation and API key configuration."

        try:
            # Get session for configuration
            from isaac.core.session_manager import SessionManager

            session = SessionManager()
            config = session.get_config()

            # Get API configuration
            xai_config = config.get("xai", {})
            chat_config = xai_config.get("chat", {})
            api_key = chat_config.get("api_key")

            # Fallback to old flat structure
            if not api_key:
                api_key = config.get("xai_api_key") or config.get("api_key")

            if not api_key:
                return "Error: xAI Chat API key not configured. Set it in ~/.isaac/config.json under xai.chat.api_key"

            # Initialize xAI client
            client = XaiClient(
                api_key=api_key,
                api_url=config.get("xai_api_url", "https://api.x.ai/v1/chat/completions"),
                model=config.get("xai_model", "grok-3"),
            )

            # Build summarization prompt based on length
            if length == "short":
                prompt = f"Summarize this {kind} content in 1-2 sentences:\n\n{content[:2000]}"
            elif length == "long":
                prompt = f"Provide a detailed summary of this {kind} content with key points and main themes:\n\n{content[:4000]}"
            else:  # medium
                prompt = f"Summarize this {kind} content in 3-4 sentences, capturing the main points:\n\n{content[:3000]}"

            # Get AI summary
            response = client.chat(
                prompt=prompt,
                system_prompt="You are an AI assistant specialized in creating clear, concise summaries. Focus on the most important information and maintain the original meaning.",
            )

            # Log query to AI history
            session.log_ai_query(
                query=f"[summary:{length}] {content[:100]}...",
                translated_command=f"/summarize {length}",
                explanation=response[:100],
                executed=True,
                shell_name="summary",
            )

            return response

        except Exception as e:
            return f"Error summarizing content: {e}"

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="summarize",
            description="AI-powered content summarization of piped data",
            usage="<content> | /summarize [short|medium|long]",
            examples=[
                "/read file.txt | /summarize         # Summarize file content (medium)",
                "/read doc.md | /summarize short     # Brief summary",
                "/read report.txt | /summarize long  # Detailed summary",
                "/grep 'error' logs/ | /summarize    # Summarize errors"
            ],
            tier=2,  # Needs validation - uses AI API
            aliases=["summary"],
            category="ai"
        )
