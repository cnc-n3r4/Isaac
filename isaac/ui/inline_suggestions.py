"""
Inline Suggestions - Show predictive completions as gray text in prompt_toolkit
"""

from typing import Iterable, Optional, Tuple

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

from .predictive_completer import PredictionContext, PredictiveCompleter


class InlineSuggestionCompleter(Completer):
    """Prompt toolkit completer that shows inline suggestions."""

    def __init__(self, predictive_completer: PredictiveCompleter, context_provider=None):
        """Initialize with a predictive completer.

        Args:
            predictive_completer: The predictive completion engine
            context_provider: Function that returns PredictionContext
        """
        self.predictive = predictive_completer
        self.current_suggestion: Optional[str] = None
        self.current_confidence: float = 0.0
        self.last_shown_suggestion: Optional[str] = None
        self.context_provider = context_provider or self._default_context

    def _default_context(self) -> PredictionContext:
        """Default context provider when none is specified."""
        return PredictionContext(current_directory="", recent_commands=[], session_commands=[])

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """Get completions for the current document."""
        # Get the current text
        text = document.text

        if not text.strip():
            self.current_suggestion = None
            return

        # Create context using provider
        context = self.context_provider()

        # Get suggestion
        suggestion = self.predictive.get_suggestion(text, context)

        if suggestion and suggestion[1] > 0.4:  # Minimum confidence for inline display
            self.current_suggestion = suggestion[0]
            self.current_confidence = suggestion[1]
            self.last_shown_suggestion = suggestion[0]  # Track what was shown

            # Return completion that shows the rest of the suggestion
            remaining = suggestion[0][len(text) :]
            if remaining:
                yield Completion(
                    text=remaining,
                    start_position=0,
                    display=remaining,
                    display_meta=f"{suggestion[1]:.1%} confidence",
                )
        else:
            self.current_suggestion = None
            self.last_shown_suggestion = None

    def get_current_suggestion(self) -> Optional[Tuple[str, float]]:
        """Get the current inline suggestion."""
        if self.current_suggestion:
            return (self.current_suggestion, self.current_confidence)
        return None

    def accept_suggestion(self, current_text: str) -> str:
        """Accept the current suggestion and return the completed text."""
        if self.current_suggestion and self.current_suggestion.startswith(current_text):
            return self.current_suggestion
        return current_text

    def learn_from_correction(self, actual_command: str, context: PredictionContext) -> None:
        """Learn when a prediction was shown but user typed something different.

        Args:
            actual_command: What the user actually typed/executed
            context: Context information
        """
        if self.last_shown_suggestion and self.last_shown_suggestion != actual_command:
            # A correction was made - learn from it
            self.predictive.learn_from_correction(
                self.last_shown_suggestion, actual_command, context
            )

        # Reset the last shown suggestion
        self.last_shown_suggestion = None


class InlineSuggestionDisplay:
    """Handles displaying inline suggestions in the prompt."""

    def __init__(self, completer: InlineSuggestionCompleter):
        """Initialize with a completer.

        Args:
            completer: The inline suggestion completer
        """
        self.completer = completer

    def get_suggestion_display(self, current_text: str) -> str:
        """Get the gray text to display after the current input.

        Args:
            current_text: The current user input

        Returns:
            Gray text suggestion to append
        """
        suggestion = self.completer.get_current_suggestion()

        if suggestion and suggestion[0].startswith(current_text):
            remaining = suggestion[0][len(current_text) :]
            confidence = suggestion[1]

            # Show confidence indicator for high-confidence suggestions
            if confidence > 0.7:
                return f"\033[90m{remaining}\033[0m"  # Dark gray
            elif confidence > 0.5:
                return f"\033[37m{remaining}\033[0m"  # Light gray
            else:
                return f"\033[2m{remaining}\033[0m"  # Dim text

        return ""

    def accept_suggestion(self, current_text: str) -> str:
        """Accept the current suggestion.

        Args:
            current_text: Current input text

        Returns:
            Completed text with suggestion applied
        """
        return self.completer.accept_suggestion(current_text)
