"""
Analyze Command - Standardized Implementation

AI-powered analysis of piped data.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse

try:
    from isaac.ai.xai_client import XaiClient
    from isaac.core.session_manager import SessionManager
    HAS_XAI_CLIENT = True
except ImportError:
    HAS_XAI_CLIENT = False


class AnalyzeCommand(BaseCommand):
    """AI-powered analysis of piped data"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute analyze command.

        Args:
            args: Command arguments (analysis type)
            context: Optional execution context (should include piped_input)

        Returns:
            CommandResponse with analysis or error
        """
        if not HAS_XAI_CLIENT:
            return CommandResponse(
                success=False,
                error="xAI client not available. Check xai_sdk installation and API key configuration.",
                metadata={"error_code": "DEPENDENCY_ERROR"}
            )

        parser = FlagParser(args)

        # Get analysis type from first positional arg (default: general)
        analysis_type = parser.get_positional(0, default="general")

        # Check for piped input
        if not context or "piped_input" not in context:
            return CommandResponse(
                success=False,
                error="Usage: <content> | /analyze [type]\n\nAnalysis types: sentiment, summary, keywords, code, data, general",
                metadata={"error_code": "MISSING_INPUT"}
            )

        content = context.get("piped_input", "")
        kind = context.get("piped_kind", "text")

        if not content:
            return CommandResponse(
                success=False,
                error="No content to analyze",
                metadata={"error_code": "EMPTY_INPUT"}
            )

        # Perform analysis
        try:
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
                return CommandResponse(
                    success=False,
                    error="xAI Chat API key not configured. Set it in ~/.isaac/config.json under xai.chat.api_key",
                    metadata={"error_code": "CONFIG_ERROR"}
                )

            # Initialize xAI client
            client = XaiClient(
                api_key=api_key,
                api_url=config.get("xai_api_url", "https://api.x.ai/v1/chat/completions"),
                model=config.get("xai_model", "grok-3"),
            )

            # Build analysis prompt based on type and content kind
            prompt = self._build_analysis_prompt(content, kind, analysis_type)

            # Get AI analysis
            response = client.chat(
                prompt=prompt,
                system_prompt="You are an AI assistant specialized in content analysis. Provide clear, concise, and accurate analysis.",
            )

            # Log query to AI history
            session.log_ai_query(
                query=f"[analysis:{analysis_type}] {content[:100]}...",
                translated_command=f"/analyze {analysis_type}",
                explanation=response[:100],
                executed=True,
                shell_name="analysis",
            )

            return CommandResponse(
                success=True,
                data=response,
                metadata={
                    "analysis_type": analysis_type,
                    "content_kind": kind
                }
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error analyzing content: {e}",
                metadata={"error_code": "EXECUTION_ERROR"}
            )

    def _build_analysis_prompt(self, content: str, kind: str, analysis_type: str) -> str:
        """Build the analysis prompt based on type and content"""
        # Limit content to avoid token limits (first 2000 chars)
        content_snippet = content[:2000]

        prompts = {
            "sentiment": f"Analyze the sentiment of this {kind} content. Provide a sentiment score (-1 to 1) and brief explanation:\n\n{content_snippet}",
            "summary": f"Summarize this {kind} content in 2-3 sentences:\n\n{content_snippet}",
            "keywords": f"Extract the main keywords and key phrases from this {kind} content:\n\n{content_snippet}",
            "code": f"Analyze this code for potential issues, improvements, and best practices:\n\n{content_snippet}",
            "data": f"Analyze this data structure and provide insights about its content and structure:\n\n{content_snippet}",
            "general": f"Provide a general analysis of this {kind} content, including main themes, key points, and insights:\n\n{content_snippet}"
        }

        return prompts.get(analysis_type, prompts["general"])

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="analyze",
            description="AI-powered analysis of piped data",
            usage="<content> | /analyze [type]",
            examples=[
                "/read log.txt | /analyze",
                "/grep ERROR *.log | /analyze sentiment",
                "/read code.py | /analyze code",
                "echo 'some data' | /analyze summary"
            ],
            tier=1,  # Safe - read-only analysis
            aliases=[],
            category="ai"
        )
