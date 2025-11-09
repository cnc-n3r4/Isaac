"""
User Preference Learning - Phase 3.5 Self-Improving System
Learns and adapts to individual user coding styles, preferences, and patterns.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict, field
from pathlib import Path
import statistics
from collections import defaultdict, Counter

from isaac.core.session_manager import SessionManager


@dataclass
class CodingPattern:
    """Represents a learned coding pattern or preference."""
    pattern_type: str  # 'naming', 'structure', 'imports', 'comments', etc.
    pattern_key: str   # Specific pattern identifier
    preference_value: Any  # User's preferred value/approach
    confidence: float = 0.0  # 0-1 confidence in this preference
    occurrences: int = 0
    last_seen: float = 0.0
    examples: List[str] = field(default_factory=list)

    def update_confidence(self, new_preference: Any, weight: float = 1.0):
        """Update confidence based on new observation."""
        if self.preference_value is None:
            # First observation sets the preference
            self.preference_value = new_preference
            self.confidence = min(weight * 0.1, 1.0)
        elif self.preference_value == new_preference:
            # Reinforce existing preference
            self.confidence = min(self.confidence + (weight * 0.1), 1.0)
        else:
            # Challenge existing preference
            self.confidence = max(self.confidence - (weight * 0.05), 0.0)

        self.occurrences += 1
        self.last_seen = time.time()

        # Keep only recent examples
        if len(self.examples) >= 10:
            self.examples.pop(0)
        self.examples.append(str(new_preference))


@dataclass
class UserPreferences:
    """Comprehensive user preference profile."""
    user_id: str
    created_at: float
    last_updated: float

    # Coding style preferences
    naming_conventions: Dict[str, CodingPattern] = field(default_factory=dict)
    code_structure: Dict[str, CodingPattern] = field(default_factory=dict)
    import_style: Dict[str, CodingPattern] = field(default_factory=dict)
    documentation: Dict[str, CodingPattern] = field(default_factory=dict)

    # Interaction preferences
    communication_style: Dict[str, CodingPattern] = field(default_factory=dict)
    response_length: Dict[str, CodingPattern] = field(default_factory=dict)
    technical_level: Dict[str, CodingPattern] = field(default_factory=dict)

    # Tool and workflow preferences
    preferred_tools: Dict[str, CodingPattern] = field(default_factory=dict)
    workflow_patterns: Dict[str, CodingPattern] = field(default_factory=dict)

    # Command and shell preferences
    command_patterns: Dict[str, CodingPattern] = field(default_factory=dict)
    shell_habits: Dict[str, CodingPattern] = field(default_factory=dict)

    def get_preference(self, category: str, key: str) -> Optional[CodingPattern]:
        """Get a specific preference pattern."""
        category_dict = getattr(self, category, {})
        return category_dict.get(key)

    def set_preference(self, category: str, key: str, pattern: CodingPattern):
        """Set a preference pattern."""
        category_dict = getattr(self, category, {})
        category_dict[key] = pattern
        setattr(self, category, category_dict)
        self.last_updated = time.time()

    def get_top_preferences(self, category: str, limit: int = 5) -> List[Tuple[str, CodingPattern]]:
        """Get top preferences in a category by confidence."""
        category_dict = getattr(self, category, {})
        sorted_patterns = sorted(
            category_dict.items(),
            key=lambda x: x[1].confidence,
            reverse=True
        )
        return sorted_patterns[:limit]


class UserPreferenceLearner:
    """Learns and adapts to user preferences across all interactions."""

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

        # Data storage
        self.data_dir = Path.home() / '.isaac' / 'learning'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.preferences_file = self.data_dir / 'user_preferences.json'
        self.patterns_file = self.data_dir / 'learned_patterns.json'

        # Current user preferences
        self.user_preferences: Optional[UserPreferences] = None

        # Pattern learning data
        self.learned_patterns: Dict[str, Dict[str, CodingPattern]] = {}

        # Load existing data
        self._load_user_preferences()
        self._load_learned_patterns()

        # Initialize if needed
        if self.user_preferences is None:
            self._initialize_user_profile()

    def observe_coding_pattern(self, pattern_type: str, pattern_key: str,
                             observed_value: Any, context: Optional[Dict[str, Any]] = None):
        """Observe a coding pattern and update preferences."""
        if self.user_preferences is None:
            self._initialize_user_profile()

        # Get or create pattern
        pattern = self._get_or_create_pattern(pattern_type, pattern_key)

        # Update pattern with observation
        weight = self._calculate_observation_weight(context or {})
        pattern.update_confidence(observed_value, weight)

        # Update user preferences
        self.user_preferences.set_preference(pattern_type, pattern_key, pattern)

        # Save changes
        self._save_user_preferences()

    def observe_command_usage(self, command: str, args: List[str],
                            success: bool, context: Optional[Dict[str, Any]] = None):
        """Observe command usage patterns."""
        if not success:
            return  # Only learn from successful commands

        command_key = f"{command}_{'_'.join(args[:2])}"  # Include first 2 args in key

        self.observe_coding_pattern(
            'command_patterns',
            command_key,
            {'command': command, 'args': args, 'frequency': 1},
            context
        )

    def observe_file_operation(self, operation: str, file_path: str,
                             file_type: str, context: Optional[Dict[str, Any]] = None):
        """Observe file operation patterns."""
        file_extension = Path(file_path).suffix

        self.observe_coding_pattern(
            'workflow_patterns',
            f"{operation}_{file_type}",
            {'extension': file_extension, 'operation': operation},
            context
        )

    def observe_ai_interaction(self, interaction_type: str, user_input: str,
                             ai_response: str, user_feedback: Optional[str] = None,
                             context: Optional[Dict[str, Any]] = None):
        """Observe AI interaction patterns."""
        # Analyze communication style
        comm_style = self._analyze_communication_style(user_input)
        self.observe_coding_pattern('communication_style', 'input_style', comm_style, context)

        # Analyze response preferences
        if user_feedback:
            response_pref = self._analyze_response_preference(ai_response, user_feedback)
            self.observe_coding_pattern('response_length', 'preferred_length',
                                      len(ai_response.split()), context)

        # Analyze technical level preference
        tech_level = self._analyze_technical_level(user_input)
        self.observe_coding_pattern('technical_level', 'preferred_level', tech_level, context)

    def get_personalized_suggestion(self, suggestion_type: str, context: Dict[str, Any]) -> Optional[Any]:
        """Get a personalized suggestion based on learned preferences."""
        if self.user_preferences is None:
            return None

        # Get relevant preferences for this suggestion type
        preferences = self.user_preferences.get_top_preferences(suggestion_type, limit=3)

        if not preferences:
            return None

        # Find best match based on context
        best_match = None
        best_score = 0.0

        for key, pattern in preferences:
            score = self._calculate_context_match(pattern, context)
            if score > best_score and pattern.confidence > 0.5:  # Minimum confidence threshold
                best_score = score
                best_match = pattern

        return best_match.preference_value if best_match else None

    def get_coding_style_recommendations(self, code_context: Dict[str, Any]) -> List[str]:
        """Get coding style recommendations based on learned preferences."""
        recommendations = []

        if self.user_preferences is None:
            return recommendations

        # Naming conventions
        naming_prefs = self.user_preferences.get_top_preferences('naming_conventions', 2)
        for key, pattern in naming_prefs:
            if pattern.confidence > 0.7:
                recommendations.append(f"Consider using {pattern.pattern_key} naming: {pattern.preference_value}")

        # Code structure
        structure_prefs = self.user_preferences.get_top_preferences('code_structure', 2)
        for key, pattern in structure_prefs:
            if pattern.confidence > 0.7:
                recommendations.append(f"Preferred {pattern.pattern_key}: {pattern.preference_value}")

        # Import style
        import_prefs = self.user_preferences.get_top_preferences('import_style', 1)
        for key, pattern in import_prefs:
            if pattern.confidence > 0.7:
                recommendations.append(f"Import style preference: {pattern.preference_value}")

        return recommendations[:3]  # Limit to top 3

    def get_workflow_suggestions(self, current_context: Dict[str, Any]) -> List[str]:
        """Get workflow suggestions based on learned patterns."""
        suggestions = []

        if self.user_preferences is None:
            return suggestions

        # Command patterns
        command_prefs = self.user_preferences.get_top_preferences('command_patterns', 3)
        for key, pattern in command_prefs:
            if pattern.confidence > 0.6:
                cmd_data = pattern.preference_value
                if isinstance(cmd_data, dict) and 'command' in cmd_data:
                    suggestions.append(f"You often use: {cmd_data['command']} {' '.join(cmd_data.get('args', []))}")

        # Workflow patterns
        workflow_prefs = self.user_preferences.get_top_preferences('workflow_patterns', 2)
        for key, pattern in workflow_prefs:
            if pattern.confidence > 0.6:
                workflow_data = pattern.preference_value
                if isinstance(workflow_data, dict):
                    suggestions.append(f"Workflow pattern: {workflow_data.get('operation', key)} on {workflow_data.get('extension', 'files')}")

        return suggestions[:3]

    def _get_or_create_pattern(self, pattern_type: str, pattern_key: str) -> CodingPattern:
        """Get existing pattern or create new one."""
        if pattern_type not in self.learned_patterns:
            self.learned_patterns[pattern_type] = {}

        if pattern_key not in self.learned_patterns[pattern_type]:
            self.learned_patterns[pattern_type][pattern_key] = CodingPattern(
                pattern_type=pattern_type,
                pattern_key=pattern_key,
                preference_value=None
            )

        return self.learned_patterns[pattern_type][pattern_key]

    def _calculate_observation_weight(self, context: Dict[str, Any]) -> float:
        """Calculate weight for an observation based on context."""
        weight = 1.0

        # Recent observations are more important
        if 'timestamp' in context:
            age_hours = (time.time() - context['timestamp']) / 3600
            if age_hours < 24:
                weight *= 1.5  # Recent observations weighted higher

        # Successful operations are more important
        if context.get('success', True):
            weight *= 1.2
        else:
            weight *= 0.8  # Failed operations weighted lower

        # Explicit user feedback is highly weighted
        if 'user_feedback' in context:
            weight *= 2.0

        return weight

    def _analyze_communication_style(self, user_input: str) -> str:
        """Analyze user's communication style."""
        input_lower = user_input.lower()

        if any(word in input_lower for word in ['please', 'could you', 'would you']):
            return 'polite'
        elif any(word in input_lower for word in ['quickly', 'fast', 'hurry']):
            return 'direct'
        elif len(user_input.split()) > 15:  # Increased threshold for detailed
            return 'detailed'
        elif len(user_input.split()) < 5:
            return 'concise'
        else:
            return 'balanced'

    def _analyze_response_preference(self, ai_response: str, user_feedback: str) -> str:
        """Analyze preferred response characteristics from feedback."""
        feedback_lower = user_feedback.lower()
        response_words = len(ai_response.split())

        if any(word in feedback_lower for word in ['too long', 'shorter', 'brief']):
            return 'concise'
        elif any(word in feedback_lower for word in ['more detail', 'explain', 'expand']):
            return 'detailed'
        elif response_words < 20:  # Lower threshold for concise
            return 'concise'
        elif response_words > 100:  # Higher threshold for detailed
            return 'detailed'
        else:
            return 'balanced'

    def _analyze_technical_level(self, user_input: str) -> str:
        """Analyze preferred technical level."""
        input_lower = user_input.lower()

        technical_terms = ['api', 'framework', 'algorithm', 'implementation', 'architecture', 'design pattern']
        simple_terms = ['how to', 'explain', 'simple', 'basic', 'easy', 'beginner']

        technical_count = sum(1 for term in technical_terms if term in input_lower)
        simple_count = sum(1 for term in simple_terms if term in input_lower)

        if technical_count > simple_count:
            return 'technical'
        elif simple_count > technical_count:
            return 'simple'
        else:
            return 'intermediate'

    def _calculate_context_match(self, pattern: CodingPattern, context: Dict[str, Any]) -> float:
        """Calculate how well a pattern matches the current context."""
        score = pattern.confidence

        # Time-based decay (older patterns less relevant)
        age_days = (time.time() - pattern.last_seen) / 86400
        if age_days > 30:
            score *= 0.7  # 30% reduction for month-old patterns

        # Context relevance
        if 'file_type' in context and pattern.pattern_key.endswith(context['file_type']):
            score *= 1.2

        if 'operation' in context and context['operation'] in pattern.pattern_key:
            score *= 1.1

        return score

    def _initialize_user_profile(self):
        """Initialize a new user preference profile."""
        self.user_preferences = UserPreferences(
            user_id="default_user",  # Could be expanded to support multiple users
            created_at=time.time(),
            last_updated=time.time()
        )
        self._save_user_preferences()

    def _load_user_preferences(self):
        """Load user preferences from disk."""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r') as f:
                    data = json.load(f)
                    self.user_preferences = UserPreferences(**data)
            except Exception as e:
                print(f"Error loading user preferences: {e}")

    def _save_user_preferences(self):
        """Save user preferences to disk."""
        if self.user_preferences:
            try:
                with open(self.preferences_file, 'w') as f:
                    json.dump(asdict(self.user_preferences), f, indent=2)
            except Exception as e:
                print(f"Error saving user preferences: {e}")

    def _load_learned_patterns(self):
        """Load learned patterns from disk."""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
                    # Reconstruct CodingPattern objects
                    for category, patterns in data.items():
                        self.learned_patterns[category] = {}
                        for key, pattern_data in patterns.items():
                            self.learned_patterns[category][key] = CodingPattern(**pattern_data)
            except Exception as e:
                print(f"Error loading learned patterns: {e}")

    def _save_learned_patterns(self):
        """Save learned patterns to disk."""
        try:
            data = {}
            for category, patterns in self.learned_patterns.items():
                data[category] = {key: asdict(pattern) for key, pattern in patterns.items()}

            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving learned patterns: {e}")

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about learned preferences."""
        if self.user_preferences is None:
            return {"message": "No user preferences available"}

        total_patterns = sum(len(patterns) for patterns in self.learned_patterns.values())
        high_confidence_patterns = sum(
            1 for category in self.learned_patterns.values()
            for pattern in category.values()
            if pattern.confidence > 0.7
        )

        return {
            "total_patterns": total_patterns,
            "high_confidence_patterns": high_confidence_patterns,
            "learning_categories": list(self.learned_patterns.keys()),
            "profile_age_days": (time.time() - self.user_preferences.created_at) / 86400,
            "last_updated": datetime.fromtimestamp(self.user_preferences.last_updated).isoformat()
        }