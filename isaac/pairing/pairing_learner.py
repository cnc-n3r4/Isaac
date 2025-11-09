"""
Pairing Learning System - Phase 4.2
Learn from pair programming sessions to improve future assistance.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict
import uuid
import threading
import time

from isaac.core.session_manager import SessionManager


@dataclass
class PairingPattern:
    """A learned pattern from pairing sessions."""
    id: str
    pattern_type: str  # 'code_style', 'workflow', 'preference', 'reaction'
    description: str
    trigger_context: Dict[str, Any]
    learned_behavior: str
    confidence: float
    occurrence_count: int
    created_at: float
    last_seen: float
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StylePreference:
    """User's coding style preference."""
    category: str  # 'naming', 'formatting', 'structure', 'documentation'
    preference: str
    examples: List[str]
    confidence: float
    learned_at: float


class PairingLearner:
    """Learn from pair programming sessions."""

    def __init__(self, session_manager: SessionManager, start_background_learning: bool = True):
        """Initialize pairing learner.

        Args:
            session_manager: Session manager instance
            start_background_learning: Start background learning thread
        """
        self.session_manager = session_manager
        self.data_dir = Path.home() / '.isaac' / 'pairing'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Database for learned patterns
        self.db_path = self.data_dir / 'learned_patterns.db'
        self._init_database()

        # In-memory cache of patterns
        self.patterns: Dict[str, PairingPattern] = {}
        self.style_preferences: Dict[str, StylePreference] = {}
        self._load_patterns()

        # Background learning
        self._stop_learning = False
        if start_background_learning:
            self.learning_thread = threading.Thread(target=self._background_learning, daemon=True)
            self.learning_thread.start()
        else:
            self.learning_thread = None

    def _init_database(self):
        """Initialize SQLite database for pattern storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pairing_patterns (
                    id TEXT PRIMARY KEY,
                    pattern_type TEXT,
                    description TEXT,
                    trigger_context TEXT,
                    learned_behavior TEXT,
                    confidence REAL,
                    occurrence_count INTEGER,
                    created_at REAL,
                    last_seen REAL,
                    metadata TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_type ON pairing_patterns(pattern_type)')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS style_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    preference TEXT,
                    examples TEXT,
                    confidence REAL,
                    learned_at REAL
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON style_preferences(category)')

            # Interaction history for learning
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pairing_interactions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    timestamp REAL,
                    interaction_type TEXT,
                    context TEXT,
                    user_action TEXT,
                    isaac_suggestion TEXT,
                    user_response TEXT,
                    metadata TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_session ON pairing_interactions(session_id)')

    def _load_patterns(self):
        """Load patterns from database."""
        with sqlite3.connect(self.db_path) as conn:
            # Load pairing patterns
            cursor = conn.execute('''
                SELECT id, pattern_type, description, trigger_context, learned_behavior,
                       confidence, occurrence_count, created_at, last_seen, metadata
                FROM pairing_patterns
            ''')

            for row in cursor:
                pattern = PairingPattern(
                    id=row[0],
                    pattern_type=row[1],
                    description=row[2],
                    trigger_context=json.loads(row[3]) if row[3] else {},
                    learned_behavior=row[4],
                    confidence=row[5],
                    occurrence_count=row[6],
                    created_at=row[7],
                    last_seen=row[8],
                    metadata=json.loads(row[9]) if row[9] else {}
                )
                self.patterns[pattern.id] = pattern

            # Load style preferences
            cursor = conn.execute('''
                SELECT category, preference, examples, confidence, learned_at
                FROM style_preferences
            ''')

            for row in cursor:
                pref = StylePreference(
                    category=row[0],
                    preference=row[1],
                    examples=json.loads(row[2]) if row[2] else [],
                    confidence=row[3],
                    learned_at=row[4]
                )
                self.style_preferences[row[0]] = pref

    def record_interaction(
        self,
        session_id: str,
        interaction_type: str,
        context: Dict[str, Any],
        user_action: str,
        isaac_suggestion: Optional[str] = None,
        user_response: Optional[str] = None
    ):
        """Record a pairing interaction for learning.

        Args:
            session_id: Session ID
            interaction_type: Type of interaction
            context: Interaction context
            user_action: What the user did
            isaac_suggestion: What Isaac suggested (if any)
            user_response: User's response to suggestion
        """
        interaction_id = str(uuid.uuid4())

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO pairing_interactions
                (id, session_id, timestamp, interaction_type, context,
                 user_action, isaac_suggestion, user_response, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                interaction_id,
                session_id,
                datetime.now().timestamp(),
                interaction_type,
                json.dumps(context),
                user_action,
                isaac_suggestion,
                user_response,
                json.dumps({})
            ))

    def learn_from_code_edit(
        self,
        file_path: str,
        old_code: str,
        new_code: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Learn from a code edit.

        Args:
            file_path: File path
            old_code: Original code
            new_code: Modified code
            context: Additional context
        """
        # Analyze the edit to learn preferences
        file_ext = Path(file_path).suffix

        # Learn naming conventions
        self._learn_naming_conventions(new_code, file_ext)

        # Learn formatting preferences
        self._learn_formatting_preferences(new_code, file_ext)

        # Learn code structure preferences
        self._learn_structure_preferences(old_code, new_code, file_ext)

    def _learn_naming_conventions(self, code: str, file_ext: str):
        """Learn naming conventions from code.

        Args:
            code: Code to analyze
            file_ext: File extension
        """
        if file_ext != '.py':
            return

        # Simple pattern matching for Python naming
        import re

        # Find variable names
        var_pattern = r'\b([a-z_][a-z0-9_]*)\s*='
        variables = re.findall(var_pattern, code)

        if variables:
            # Check if snake_case is used
            snake_case_count = sum(1 for v in variables if '_' in v)
            if snake_case_count / len(variables) > 0.7:
                self._update_style_preference(
                    'naming',
                    'Prefers snake_case for variable names',
                    variables[:5],
                    0.8
                )

        # Find class names
        class_pattern = r'class\s+([A-Z][a-zA-Z0-9]*)'
        classes = re.findall(class_pattern, code)

        if classes:
            # All start with uppercase - PascalCase
            self._update_style_preference(
                'naming',
                'Uses PascalCase for class names',
                classes[:5],
                0.9
            )

    def _learn_formatting_preferences(self, code: str, file_ext: str):
        """Learn formatting preferences.

        Args:
            code: Code to analyze
            file_ext: File extension
        """
        lines = code.split('\n')

        # Check indentation
        indent_counts = defaultdict(int)
        for line in lines:
            if line.strip() and line[0] == ' ':
                leading_spaces = len(line) - len(line.lstrip(' '))
                if leading_spaces > 0:
                    indent_counts[leading_spaces] += 1

        if indent_counts:
            most_common_indent = max(indent_counts.items(), key=lambda x: x[1])[0]
            if most_common_indent == 4:
                self._update_style_preference(
                    'formatting',
                    'Uses 4-space indentation',
                    ['4 spaces'],
                    0.9
                )
            elif most_common_indent == 2:
                self._update_style_preference(
                    'formatting',
                    'Uses 2-space indentation',
                    ['2 spaces'],
                    0.9
                )

        # Check line length preference
        long_lines = sum(1 for line in lines if len(line) > 80)
        if long_lines / max(len(lines), 1) < 0.1:
            self._update_style_preference(
                'formatting',
                'Keeps lines under 80 characters',
                ['Short lines'],
                0.7
            )

    def _learn_structure_preferences(self, old_code: str, new_code: str, file_ext: str):
        """Learn code structure preferences from changes.

        Args:
            old_code: Original code
            new_code: Modified code
            file_ext: File extension
        """
        # Analyze what structural changes were made
        # This is a simplified version - real implementation would be more sophisticated

        if 'def ' in new_code and 'def ' not in old_code:
            self._update_style_preference(
                'structure',
                'Extracts functionality into separate functions',
                ['Function extraction'],
                0.6
            )

        if 'class ' in new_code and 'class ' not in old_code:
            self._update_style_preference(
                'structure',
                'Organizes code into classes',
                ['Class usage'],
                0.6
            )

    def _update_style_preference(
        self,
        category: str,
        preference: str,
        examples: List[str],
        confidence: float
    ):
        """Update a style preference.

        Args:
            category: Preference category
            preference: Preference description
            examples: Example instances
            confidence: Confidence level
        """
        if category in self.style_preferences:
            # Update existing preference
            pref = self.style_preferences[category]
            if pref.preference == preference:
                # Same preference, increase confidence
                pref.confidence = min(1.0, pref.confidence + 0.1)
                pref.examples.extend(examples)
                pref.examples = pref.examples[-10:]  # Keep last 10 examples
            else:
                # Different preference, reduce confidence of old one
                pref.confidence = max(0.0, pref.confidence - 0.1)
                if pref.confidence < 0.3:
                    # Replace with new preference
                    self.style_preferences[category] = StylePreference(
                        category=category,
                        preference=preference,
                        examples=examples,
                        confidence=confidence,
                        learned_at=datetime.now().timestamp()
                    )
        else:
            # New preference
            self.style_preferences[category] = StylePreference(
                category=category,
                preference=preference,
                examples=examples,
                confidence=confidence,
                learned_at=datetime.now().timestamp()
            )

        # Save to database
        self._save_style_preference(self.style_preferences[category])

    def get_style_preferences(self) -> Dict[str, StylePreference]:
        """Get learned style preferences.

        Returns:
            Dictionary of style preferences by category
        """
        return self.style_preferences.copy()

    def get_pattern_suggestions(
        self,
        context: Dict[str, Any]
    ) -> List[PairingPattern]:
        """Get pattern-based suggestions for current context.

        Args:
            context: Current context

        Returns:
            List of relevant patterns
        """
        relevant_patterns = []

        for pattern in self.patterns.values():
            if self._context_matches(pattern.trigger_context, context):
                if pattern.confidence > 0.5:
                    relevant_patterns.append(pattern)

        # Sort by confidence
        relevant_patterns.sort(key=lambda p: p.confidence, reverse=True)

        return relevant_patterns

    def _context_matches(
        self,
        trigger_context: Dict[str, Any],
        current_context: Dict[str, Any]
    ) -> bool:
        """Check if current context matches trigger context.

        Args:
            trigger_context: Required context
            current_context: Current context

        Returns:
            True if contexts match
        """
        for key, value in trigger_context.items():
            if key not in current_context:
                return False
            if current_context[key] != value:
                return False

        return True

    def _background_learning(self):
        """Background thread for pattern learning."""
        while not self._stop_learning:
            try:
                # Analyze recent interactions and discover new patterns
                self._analyze_recent_interactions()

                # Sleep for a while
                time.sleep(60)  # Run every minute

            except Exception:
                # Silently handle errors in background learning
                pass

    def _analyze_recent_interactions(self):
        """Analyze recent interactions to discover patterns."""
        cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)  # Last 24 hours

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT session_id, interaction_type, context, user_action,
                       isaac_suggestion, user_response
                FROM pairing_interactions
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (cutoff_time,))

            interactions = cursor.fetchall()

        # Group by interaction type
        by_type = defaultdict(list)
        for interaction in interactions:
            by_type[interaction[1]].append(interaction)

        # Look for patterns in each type
        for interaction_type, group in by_type.items():
            if len(group) >= 3:
                # Found a recurring interaction type
                # Create or update pattern
                pass  # Simplified - real implementation would do pattern extraction

    def _save_style_preference(self, preference: StylePreference):
        """Save style preference to database.

        Args:
            preference: Preference to save
        """
        with sqlite3.connect(self.db_path) as conn:
            # Delete existing preference in this category
            conn.execute('DELETE FROM style_preferences WHERE category = ?', (preference.category,))

            # Insert new preference
            conn.execute('''
                INSERT INTO style_preferences
                (category, preference, examples, confidence, learned_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                preference.category,
                preference.preference,
                json.dumps(preference.examples),
                preference.confidence,
                preference.learned_at
            ))

    def cleanup(self):
        """Cleanup resources."""
        self._stop_learning = True
        if self.learning_thread:
            self.learning_thread.join(timeout=1.0)
