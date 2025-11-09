"""
AI Translation Layer for Isaac Command Execution Framework

This module provides natural language to command translation capabilities.
Phase 2 implementation uses heuristic-based translation as a placeholder
for full AI integration in Phase 3.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TranslationResult:
    """Result of natural language translation."""

    original: str
    translated: str
    resolved_paths: List[str]
    confidence: float
    needs_confirmation: bool
    metadata: Dict[str, Any]


class AITranslator:
    """Heuristic-based AI translator for natural language commands."""

    def __init__(self):
        """Initialize translator with common patterns."""
        self.backup_patterns = [
            r"backup\s+(?:my\s+)?(.+)",
            r"save\s+(?:my\s+)?(.+)",
            r"copy\s+(?:my\s+)?(.+)",
            r"back\s+up\s+(?:my\s+)?(.+)",
        ]

        self.restore_patterns = [
            r"restore\s+(?:my\s+)?(.+)",
            r"recover\s+(?:my\s+)?(.+)",
            r"get\s+back\s+(?:my\s+)?(.+)",
        ]

        self.list_patterns = [
            r"(?:show\s+|list\s+|display\s+)(?:my\s+)?(.+)",
            r"what\s+(?:do\s+i\s+have|are\s+my\s+.+|is\s+in\s+my\s+.+)".replace("'", '"'),
        ]

        self.help_patterns = [
            r"^(?:help|what\s+can\s+you\s+do|how\s+do\s+i\s+.+|show\s+commands?|command\s+list)$",
        ]

        # Casual conversation patterns
        self.casual_patterns = [
            r"(?:hi|hello|hey|greetings?)(?:\s+there)?",
            r"good\s+(?:morning|afternoon|evening|day)",
            r"how\s+are\s+you",
            r"what'?s\s+up",
            r"yo(?:\s+isaac)?",
            r"howdy",
        ]

        # Question patterns (general queries)
        self.question_patterns = [
            r"what\s+(?:is|are|was|were)\s+(.+)",
            r"when\s+(?:is|are|was|were)\s+(.+)",
            r"where\s+(?:is|are|was|were)\s+(.+)",
            r"why\s+(?:is|are|was|were|do|does)\s+(.+)",
            r"how\s+(?:do|does|can|could|would)\s+(.+)",
            r"can\s+you\s+(.+)",
            r"could\s+you\s+(.+)",
            r"would\s+you\s+(.+)",
        ]

        # Time and weather patterns
        self.time_weather_patterns = [
            r"what\s+time\s+(?:is\s+it)?",
            r"what'?s\s+the\s+(?:time|date)",
            r"what\s+(?:is\s+)?(?:the\s+)?date",
            r"(?:what'?s\s+)?the\s+weather",
            r"is\s+it\s+(?:raining|snowing|sunny|cloudy)",
            r"how'?s\s+the\s+weather",
        ]

        # Common path mappings
        self.path_mappings = {
            "documents": ["~/Documents", "~/My Documents"],
            "desktop": ["~/Desktop"],
            "downloads": ["~/Downloads"],
            "pictures": ["~/Pictures", "~/My Pictures"],
            "music": ["~/Music", "~/My Music"],
            "videos": ["~/Videos", "~/My Videos"],
            "home": ["~"],
            "config": ["~/.config", "~/.isaac"],
        }

    def translate(self, text: str) -> Optional[TranslationResult]:
        """
        Translate natural language to Isaac command.

        Args:
            text: Natural language input

        Returns:
            TranslationResult if translatable, None otherwise
        """
        text_lower = text.lower().strip()

        # Try backup patterns
        for pattern in self.backup_patterns:
            match = re.search(pattern, text_lower)
            if match:
                source = match.group(1).strip()
                resolved = self._resolve_paths(source)
                # Always return translation, let handler deal with path resolution
                return TranslationResult(
                    original=text,
                    translated=f"backup {source}",
                    resolved_paths=resolved,
                    confidence=0.8,
                    needs_confirmation=True,
                    metadata={"operation": "backup", "source": source},
                )

        # Try restore patterns
        for pattern in self.restore_patterns:
            match = re.search(pattern, text_lower)
            if match:
                target = match.group(1).strip()
                resolved = self._resolve_paths(target)
                # Always return translation, let handler deal with path resolution
                return TranslationResult(
                    original=text,
                    translated=f"restore {target}",
                    resolved_paths=resolved,
                    confidence=0.7,
                    needs_confirmation=True,
                    metadata={"operation": "restore", "target": target},
                )

        # Try list patterns
        for pattern in self.list_patterns:
            match = re.search(pattern, text_lower)
            if match:
                subject = match.group(1).strip()
                if "backup" in subject or "save" in subject:
                    return TranslationResult(
                        original=text,
                        translated="list backups",
                        resolved_paths=[],
                        confidence=0.9,
                        needs_confirmation=False,
                        metadata={"operation": "list", "subject": "backups"},
                    )
                elif "history" in subject or "command" in subject:
                    return TranslationResult(
                        original=text,
                        translated="list history",
                        resolved_paths=[],
                        confidence=0.9,
                        needs_confirmation=False,
                        metadata={"operation": "list", "subject": "history"},
                    )

        # Try help patterns
        for pattern in self.help_patterns:
            if re.search(pattern, text_lower):
                # Additional check: make sure this is actually a help request, not just contains "help"
                # For example, "can you help me" should not match help pattern
                if "help" in text_lower and not any(
                    word in text_lower for word in ["can", "could", "would", "how", "what"]
                ):
                    return TranslationResult(
                        original=text,
                        translated="help",
                        resolved_paths=[],
                        confidence=0.95,
                        needs_confirmation=False,
                        metadata={"operation": "help"},
                    )
                # For other help patterns, allow them
                elif not "help" in text_lower:
                    return TranslationResult(
                        original=text,
                        translated="help",
                        resolved_paths=[],
                        confidence=0.95,
                        needs_confirmation=False,
                        metadata={"operation": "help"},
                    )

        # Try question patterns
        for pattern in self.question_patterns:
            match = re.search(pattern, text_lower)
            if match:
                # Extract the subject of the question from original text to preserve case
                original_match = re.search(pattern, text)
                subject = ""
                if original_match and original_match.lastindex and original_match.lastindex >= 1:
                    subject = original_match.group(1).strip()
                return TranslationResult(
                    original=text,
                    translated=f"query {subject}" if subject else "query",
                    resolved_paths=[],
                    confidence=0.8,
                    needs_confirmation=False,
                    metadata={
                        "operation": "query",
                        "type": "question",
                        "subject": subject,
                        "intent": "information_request",
                    },
                )

        # Try casual conversation patterns
        for pattern in self.casual_patterns:
            if re.search(pattern, text_lower):
                return TranslationResult(
                    original=text,
                    translated="chat",
                    resolved_paths=[],
                    confidence=0.9,
                    needs_confirmation=False,
                    metadata={
                        "operation": "chat",
                        "type": "greeting",
                        "intent": "casual_conversation",
                    },
                )

        # Try time/weather patterns
        for pattern in self.time_weather_patterns:
            if re.search(pattern, text_lower):
                # Determine if it's time or weather related
                pattern_type = "time" if "time" in pattern or "date" in pattern else "weather"
                return TranslationResult(
                    original=text,
                    translated="info",
                    resolved_paths=[],
                    confidence=0.85,
                    needs_confirmation=False,
                    metadata={
                        "operation": "info",
                        "info_type": pattern_type,
                        "intent": "system_query",
                    },
                )

        return None

    def suggest_paths(self, partial: str) -> List[str]:
        """
        Suggest paths based on partial input.

        Args:
            partial: Partial path or name

        Returns:
            List of suggested path strings
        """
        partial_lower = partial.lower()
        suggestions = []

        # Check path mappings
        for key, paths in self.path_mappings.items():
            if key.startswith(partial_lower):
                suggestions.extend(paths)

        # Check common directories
        home = Path.home()
        for item in home.iterdir():
            if item.is_dir() and partial_lower in item.name.lower():
                suggestions.append(str(item))

        return list(set(suggestions))[:5]  # Limit to 5 suggestions

    def _resolve_paths(self, path_spec: str) -> List[str]:
        """
        Resolve natural language path specifications to actual paths.

        Args:
            path_spec: Natural language path description

        Returns:
            List of resolved path strings
        """
        path_spec_lower = path_spec.lower()
        resolved = []

        # Check exact path mappings
        if path_spec_lower in self.path_mappings:
            for path_template in self.path_mappings[path_spec_lower]:
                expanded = os.path.expanduser(path_template)
                if os.path.exists(expanded):
                    resolved.append(expanded)

        # Check partial matches
        for key, paths in self.path_mappings.items():
            if key in path_spec_lower:
                for path_template in paths:
                    expanded = os.path.expanduser(path_template)
                    if os.path.exists(expanded):
                        resolved.append(expanded)

        # If no mappings found, treat as direct path or folder name
        if not resolved:
            # Try current directory + path_spec
            current_dir = Path.cwd()
            potential_path = current_dir / path_spec
            if potential_path.exists():
                resolved.append(str(potential_path))
            # Try as absolute path
            elif os.path.isabs(path_spec) and os.path.exists(path_spec):
                resolved.append(path_spec)
            # Try as relative path from home
            else:
                home_path = Path.home() / path_spec
                if home_path.exists():
                    resolved.append(str(home_path))
                # Try to find a directory with similar name in current directory
                else:
                    for item in current_dir.iterdir():
                        if (
                            item.is_dir()
                            and path_spec.lower().replace(" ", "").replace("folder", "")
                            in item.name.lower()
                        ):
                            resolved.append(str(item))
                            break

        return list(set(resolved))  # Remove duplicates

    def learn_from_feedback(self, translation: TranslationResult, was_correct: bool):
        """
        Learn from user confirmations/rejections.

        Args:
            translation: The translation result
            was_correct: Whether the user confirmed it was correct
        """
        # Placeholder for learning system
        # In Phase 3, this would update AI model weights

    def set_context(self, session_history: List[str], current_directory: str):
        """
        Provide context for better translations.

        Args:
            session_history: Recent command history
            current_directory: Current working directory
        """
        # Placeholder for context management
        # In Phase 3, this would improve translation accuracy


def create_translator() -> AITranslator:
    """Factory function to create AI translator instance."""
    return AITranslator()
