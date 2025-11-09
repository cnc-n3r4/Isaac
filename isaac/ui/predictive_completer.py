"""
Predictive Command Completion - Isaac's intelligent command prediction system
Learns from user behavior and provides context-aware command suggestions
"""

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class PredictionContext:
    """Context information for making predictions."""

    current_directory: str = ""
    recent_commands: List[str] = field(default_factory=list)
    project_type: str = ""
    time_of_day: str = ""
    day_of_week: str = ""
    session_commands: List[str] = field(default_factory=list)


@dataclass
class PredictionPattern:
    """A learned prediction pattern."""

    trigger: str
    predictions: List[str]
    confidence: float
    context_matches: int = 0
    last_used: Optional[datetime] = None
    created: datetime = field(default_factory=datetime.now)


class PredictiveCompleter:
    """Intelligent command completion system that learns from user behavior."""

    def __init__(self, history_file: Optional[Path] = None):
        """Initialize the predictive completer.

        Args:
            history_file: Path to store learned patterns
        """
        self.history_file = history_file or Path.home() / ".isaac" / "prediction_patterns.json"
        self.history_file.parent.mkdir(exist_ok=True)

        # Pattern storage
        self.patterns: Dict[str, PredictionPattern] = {}
        self.command_sequences: Dict[str, Counter] = defaultdict(Counter)
        self.context_patterns: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Learning data
        self.command_history: List[Tuple[str, PredictionContext]] = []
        self.max_history = 10000

        # Load existing patterns
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load learned patterns from disk."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)

                # Load patterns
                for trigger, pattern_data in data.get("patterns", {}).items():
                    self.patterns[trigger] = PredictionPattern(
                        trigger=trigger,
                        predictions=pattern_data["predictions"],
                        confidence=pattern_data["confidence"],
                        context_matches=pattern_data.get("context_matches", 0),
                        last_used=pattern_data.get("last_used"),
                        created=datetime.fromisoformat(pattern_data["created"]),
                    )

                # Load command sequences
                for seq, counts in data.get("sequences", {}).items():
                    self.command_sequences[seq] = Counter(counts)

                # Load context patterns
                self.context_patterns = data.get("contexts", {})

            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load prediction patterns: {e}")

    def _save_patterns(self) -> None:
        """Save learned patterns to disk."""
        data = {"patterns": {}, "sequences": {}, "contexts": dict(self.context_patterns)}

        # Convert patterns to serializable format
        for trigger, pattern in self.patterns.items():
            data["patterns"][trigger] = {
                "predictions": pattern.predictions,
                "confidence": pattern.confidence,
                "context_matches": pattern.context_matches,
                "last_used": pattern.last_used.isoformat() if pattern.last_used else None,
                "created": pattern.created.isoformat(),
            }

        # Convert sequences
        for seq, counter in self.command_sequences.items():
            data["sequences"][seq] = dict(counter)

        try:
            with open(self.history_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save prediction patterns: {e}")

    def learn_from_command(self, command: str, context: PredictionContext) -> None:
        """Learn patterns from a executed command.

        Args:
            command: The command that was executed
            context: Context information when command was executed
        """
        # Add to history
        self.command_history.append((command, context))
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)

        # Learn command sequences
        if len(context.session_commands) >= 2:
            prev_command = context.session_commands[-2]
            self.command_sequences[prev_command][command] += 1

        # Learn context patterns
        context_key = self._get_context_key(context)
        if context_key not in self.context_patterns:
            self.context_patterns[context_key] = {}
        self.context_patterns[context_key][command] = (
            self.context_patterns[context_key].get(command, 0) + 1
        )

        # Learn command prefixes for partial completion
        self._learn_command_prefixes(command)

        # Update existing patterns
        self._update_patterns(command, context)

        # Save periodically (every 10 commands)
        if len(self.command_history) % 10 == 0:
            self._save_patterns()

    def _learn_command_prefixes(self, command: str) -> None:
        """Learn command prefixes for partial completion."""
        # For each possible prefix of this command, learn that it can complete to this command
        words = command.split()
        if not words:
            return

        base_cmd = words[0]

        # Ensure the base command pattern exists and includes this command
        if base_cmd not in self.patterns:
            self.patterns[base_cmd] = PredictionPattern(
                trigger=base_cmd, predictions=[], confidence=0.0
            )

        base_pattern = self.patterns[base_cmd]
        if command not in base_pattern.predictions:
            base_pattern.predictions.append(command)

        # Update confidence - base commands get high confidence
        base_usage_count = len([c for c, _ in self.command_history if c[0].startswith(base_cmd)])
        total_commands = len(self.command_history)
        base_pattern.confidence = min(
            base_usage_count / max(total_commands, 1) * 2, 1.0
        )  # Boost confidence for base commands

        # Also learn partial prefixes for longer commands
        for i in range(1, min(len(command), 10)):  # Up to 10 chars
            prefix = command[:i]
            if prefix not in self.patterns:
                self.patterns[prefix] = PredictionPattern(
                    trigger=prefix, predictions=[], confidence=0.0
                )

            prefix_pattern = self.patterns[prefix]
            if command not in prefix_pattern.predictions:
                prefix_pattern.predictions.append(command)

            # Higher confidence for longer, more specific prefixes
            prefix_pattern.confidence = min(i / len(command), 1.0) * 0.8  # Max 80% confidence

        # Also learn partial prefixes for longer commands
        for i in range(1, min(len(command), 10)):  # Up to 10 chars
            prefix = command[:i]
            if prefix not in self.patterns:
                self.patterns[prefix] = PredictionPattern(
                    trigger=prefix, predictions=[], confidence=0.0
                )

            prefix_pattern = self.patterns[prefix]
            if command not in prefix_pattern.predictions:
                prefix_pattern.predictions.append(command)

            # Higher confidence for longer, more specific prefixes
            prefix_pattern.confidence = min(i / len(command), 1.0) * 0.8  # Max 80% confidence

    def _update_patterns(self, command: str, context: PredictionContext) -> None:
        """Update prediction patterns based on new command."""
        # Find similar commands that could be triggers
        similar_commands = self._find_similar_commands(command)

        for similar in similar_commands:
            if similar not in self.patterns:
                self.patterns[similar] = PredictionPattern(
                    trigger=similar, predictions=[], confidence=0.0
                )

            pattern = self.patterns[similar]
            if command not in pattern.predictions:
                pattern.predictions.append(command)
                pattern.context_matches += 1

            # Update confidence based on frequency
            total_matches = sum(self.command_sequences[similar].values())
            if total_matches > 0:
                pattern.confidence = self.command_sequences[similar][command] / total_matches

            pattern.last_used = datetime.now()

    def _find_similar_commands(self, command: str) -> List[str]:
        """Find commands that are similar to the given command."""
        similar = []

        # Split command into parts
        parts = command.split()
        if not parts:
            return similar

        base_cmd = parts[0]

        # Find commands that start with same base
        for hist_cmd, _ in self.command_history[-100:]:  # Last 100 commands
            hist_parts = hist_cmd.split()
            if hist_parts and hist_parts[0] == base_cmd and hist_cmd != command:
                similar.append(hist_cmd)

        # Find commands with similar structure
        for hist_cmd, _ in self.command_history[-50:]:
            if self._commands_similar(command, hist_cmd):
                similar.append(hist_cmd)

        return list(set(similar))[:5]  # Limit to 5 similar commands

    def _commands_similar(self, cmd1: str, cmd2: str) -> bool:
        """Check if two commands are structurally similar."""
        parts1 = cmd1.split()
        parts2 = cmd2.split()

        if len(parts1) != len(parts2) or not parts1 or not parts2:
            return False

        # Same base command
        if parts1[0] != parts2[0]:
            return False

        # Similar argument patterns (same flags, different values)
        flags1 = {p for p in parts1 if p.startswith("-")}
        flags2 = {p for p in parts2 if p.startswith("-")}

        return flags1 == flags2 and len(flags1) > 0

    def _get_context_key(self, context: PredictionContext) -> str:
        """Generate a context key for pattern matching."""
        return f"{context.project_type}:{context.time_of_day}:{context.day_of_week}"

    def get_predictions(
        self, partial_command: str, context: PredictionContext
    ) -> List[Tuple[str, float]]:
        """Get prediction suggestions for a partial command.

        Args:
            partial_command: The command being typed
            context: Current context information

        Returns:
            List of (prediction, confidence) tuples
        """
        predictions = []

        # Direct sequence predictions
        if context.session_commands:
            last_cmd = context.session_commands[-1]
            if last_cmd in self.command_sequences:
                seq_predictions = self.command_sequences[last_cmd]
                total = sum(seq_predictions.values())

                for cmd, count in seq_predictions.most_common(3):
                    confidence = count / total
                    predictions.append((cmd, confidence))

        # Pattern-based predictions (from learned prefixes)
        if partial_command in self.patterns:
            pattern = self.patterns[partial_command]
            for prediction in pattern.predictions:
                # Boost confidence if context matches
                context_boost = 1.0
                context_key = self._get_context_key(context)
                if context_key in self.context_patterns:
                    context_freq = self.context_patterns[context_key].get(prediction, 0)
                    if context_freq > 0:
                        context_boost = 1.2

                adjusted_confidence = min(pattern.confidence * context_boost, 1.0)
                predictions.append((prediction, adjusted_confidence))

        # Context-based predictions
        context_key = self._get_context_key(context)
        if context_key in self.context_patterns:
            context_commands = self.context_patterns[context_key]
            total_context = sum(context_commands.values())

            for cmd, count in context_commands.items():
                if cmd.startswith(partial_command):
                    confidence = count / total_context
                    predictions.append((cmd, confidence))

        # Remove duplicates and sort by confidence
        seen = set()
        unique_predictions = []
        for pred, conf in sorted(predictions, key=lambda x: x[1], reverse=True):
            if pred not in seen:
                unique_predictions.append((pred, conf))
                seen.add(pred)

        return unique_predictions[:5]  # Return top 5 predictions

    def get_suggestion(
        self, partial_command: str, context: PredictionContext
    ) -> Optional[Tuple[str, float]]:
        """Get the best suggestion for inline display.

        Args:
            partial_command: The command being typed
            context: Current context

        Returns:
            Tuple of (suggestion, confidence) or None
        """
        predictions = self.get_predictions(partial_command, context)

        if predictions and predictions[0][1] > 0.2:  # Minimum confidence threshold
            return predictions[0]

        return None

    def get_command_sequence(
        self, start_command: str, context: PredictionContext, max_length: int = 3
    ) -> List[str]:
        """Get a predicted sequence of commands starting from the given command.

        Args:
            start_command: The command to start the sequence from
            context: Current context
            max_length: Maximum length of sequence

        Returns:
            List of predicted commands in sequence
        """
        sequence = [start_command]
        current_cmd = start_command

        for _ in range(max_length - 1):
            if current_cmd in self.command_sequences:
                next_cmd = self.command_sequences[current_cmd].most_common(1)
                if next_cmd and next_cmd[0][1] > 1:  # At least 2 occurrences
                    current_cmd = next_cmd[0][0]
                    sequence.append(current_cmd)
                else:
                    break
            else:
                break

        return sequence[1:]  # Return the predicted sequence without the start command

    def learn_from_correction(
        self, original_prediction: str, actual_command: str, context: PredictionContext
    ) -> None:
        """Learn from when a prediction was incorrect.

        Args:
            original_prediction: What was predicted
            actual_command: What was actually executed
            context: Context information
        """
        # Reduce confidence of incorrect prediction
        for trigger, pattern in self.patterns.items():
            if original_prediction in pattern.predictions:
                pattern.confidence *= 0.8  # Reduce confidence by 20%

        # Learn the correct pattern
        self.learn_from_command(actual_command, context)
