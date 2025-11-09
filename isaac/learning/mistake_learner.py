"""
Mistake Learning Framework - Phase 3.5 Self-Improving System
Learn from user corrections, failures, and feedback to continuously improve.
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import time

from isaac.core.session_manager import SessionManager


@dataclass
class MistakeRecord:
    """A record of a mistake and its correction."""
    id: str
    timestamp: float
    mistake_type: str  # 'command_error', 'ai_response', 'pattern_failure', etc.
    original_input: str
    mistake_description: str
    user_correction: str
    context: Dict[str, Any]  # Additional context about the mistake
    severity: str  # 'low', 'medium', 'high', 'critical'
    learned: bool = False  # Whether we've learned from this mistake
    recurrence_count: int = 1


@dataclass
class LearningPattern:
    """A pattern learned from mistakes."""
    id: str
    mistake_type: str
    pattern_description: str
    trigger_conditions: Dict[str, Any]
    correction_action: str
    confidence: float
    created_at: float
    success_count: int = 0
    failure_count: int = 0
    last_used: float = 0.0


class MistakeLearner:
    """Core mistake learning system that tracks and learns from errors."""

    def __init__(self, session_manager: SessionManager, start_background_learning: bool = True):
        self.session_manager = session_manager
        self.data_dir = Path.home() / '.isaac' / 'learning'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Database for mistake storage
        self.db_path = self.data_dir / 'mistakes.db'
        self._init_database()

        # Learning patterns
        self.patterns_file = self.data_dir / 'learning_patterns.json'
        self.learning_patterns: Dict[str, LearningPattern] = {}
        self._load_patterns()

        # Background learning thread
        self._stop_learning = False
        if start_background_learning:
            self.learning_thread = threading.Thread(target=self._background_learning, daemon=True)
            self.learning_thread.start()
        else:
            self.learning_thread = None

    def _init_database(self):
        """Initialize SQLite database for mistake storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS mistakes (
                    id TEXT PRIMARY KEY,
                    timestamp REAL,
                    mistake_type TEXT,
                    original_input TEXT,
                    mistake_description TEXT,
                    user_correction TEXT,
                    context TEXT,
                    severity TEXT,
                    learned BOOLEAN DEFAULT 0,
                    recurrence_count INTEGER DEFAULT 1
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_type ON mistakes(mistake_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON mistakes(timestamp)')

    def _load_patterns(self):
        """Load learning patterns from disk."""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
                    for pattern_id, pattern_data in data.items():
                        self.learning_patterns[pattern_id] = LearningPattern(**pattern_data)
            except Exception as e:
                print(f"Error loading learning patterns: {e}")

    def _save_patterns(self):
        """Save learning patterns to disk."""
        try:
            data = {pid: asdict(pattern) for pid, pattern in self.learning_patterns.items()}
            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving learning patterns: {e}")

    def record_mistake(self, mistake: MistakeRecord):
        """Record a new mistake for learning."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO mistakes
                (id, timestamp, mistake_type, original_input, mistake_description,
                 user_correction, context, severity, learned, recurrence_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                mistake.id,
                mistake.timestamp,
                mistake.mistake_type,
                mistake.original_input,
                mistake.mistake_description,
                mistake.user_correction,
                json.dumps(mistake.context),
                mistake.severity,
                mistake.learned,
                mistake.recurrence_count
            ))

    def get_similar_mistakes(self, mistake_type: str, context: Dict[str, Any],
                           limit: int = 10) -> List[MistakeRecord]:
        """Find similar mistakes for pattern learning."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT * FROM mistakes
                WHERE mistake_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (mistake_type, limit))

            mistakes = []
            for row in cursor:
                context_data = json.loads(row[6]) if row[6] else {}
                mistakes.append(MistakeRecord(
                    id=row[0],
                    timestamp=row[1],
                    mistake_type=row[2],
                    original_input=row[3],
                    mistake_description=row[4],
                    user_correction=row[5],
                    context=context_data,
                    severity=row[7],
                    learned=bool(row[8]),
                    recurrence_count=row[9]
                ))
            return mistakes

    def learn_from_mistakes(self, mistake_type: str) -> Optional[LearningPattern]:
        """Analyze mistakes and create learning patterns."""
        mistakes = self.get_similar_mistakes(mistake_type, {}, limit=50)

        if len(mistakes) < 3:  # Need minimum samples
            return None

        # Analyze common patterns in mistakes
        corrections = {}
        contexts = []

        for mistake in mistakes:
            correction_key = mistake.user_correction.lower().strip()
            corrections[correction_key] = corrections.get(correction_key, 0) + 1
            contexts.append(mistake.context)

        # Find most common correction
        most_common_correction = max(corrections.items(), key=lambda x: x[1])

        if most_common_correction[1] < 2:  # Need at least 2 instances
            return None

        # Create learning pattern
        pattern_id = f"pattern_{mistake_type}_{int(time.time())}"
        pattern = LearningPattern(
            id=pattern_id,
            mistake_type=mistake_type,
            pattern_description=f"Common {mistake_type} correction pattern",
            trigger_conditions=self._extract_trigger_conditions(contexts),
            correction_action=most_common_correction[0],
            confidence=min(0.9, most_common_correction[1] / len(mistakes)),
            created_at=time.time()
        )

        self.learning_patterns[pattern_id] = pattern
        self._save_patterns()

        # Mark mistakes as learned
        self._mark_mistakes_learned([m.id for m in mistakes])

        return pattern

    def _extract_trigger_conditions(self, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract common trigger conditions from mistake contexts."""
        if not contexts:
            return {}

        # Find common keys and values
        common_conditions = {}
        all_keys = set()

        for context in contexts:
            all_keys.update(context.keys())

        for key in all_keys:
            values = [ctx.get(key) for ctx in contexts if key in ctx]
            if len(values) > len(contexts) * 0.6:  # 60% have this key
                # Find most common value
                value_counts = {}
                for v in values:
                    if isinstance(v, (str, int, float, bool)):
                        value_counts[str(v)] = value_counts.get(str(v), 0) + 1

                if value_counts:
                    most_common = max(value_counts.items(), key=lambda x: x[1])
                    if most_common[1] > len(values) * 0.5:  # 50% agreement
                        common_conditions[key] = most_common[0]

        return common_conditions

    def _mark_mistakes_learned(self, mistake_ids: List[str]):
        """Mark mistakes as having been learned from."""
        with sqlite3.connect(self.db_path) as conn:
            for mistake_id in mistake_ids:
                conn.execute(
                    'UPDATE mistakes SET learned = 1 WHERE id = ?',
                    (mistake_id,)
                )

    def apply_learning(self, mistake_type: str, context: Dict[str, Any]) -> Optional[str]:
        """Apply learned patterns to suggest corrections."""
        applicable_patterns = []

        for pattern in self.learning_patterns.values():
            if pattern.mistake_type == mistake_type:
                # Check if trigger conditions match
                if self._conditions_match(pattern.trigger_conditions, context):
                    applicable_patterns.append(pattern)

        if not applicable_patterns:
            return None

        # Return highest confidence pattern
        best_pattern = max(applicable_patterns, key=lambda p: p.confidence)
        best_pattern.last_used = time.time()
        self._save_patterns()

        return best_pattern.correction_action

    def _conditions_match(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if trigger conditions match current context."""
        for key, expected_value in conditions.items():
            actual_value = context.get(key)
            if actual_value is None or str(actual_value) != str(expected_value):
                return False
        return True

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about the learning system."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM mistakes')
            total_mistakes = cursor.fetchone()[0]

            cursor = conn.execute('SELECT COUNT(*) FROM mistakes WHERE learned = 1')
            learned_mistakes = cursor.fetchone()[0]

            cursor = conn.execute('SELECT mistake_type, COUNT(*) FROM mistakes GROUP BY mistake_type')
            type_counts = {row[0]: row[1] for row in cursor}

        return {
            'total_mistakes': total_mistakes,
            'learned_mistakes': learned_mistakes,
            'learning_patterns': len(self.learning_patterns),
            'mistake_types': type_counts,
            'learning_rate': learned_mistakes / max(total_mistakes, 1)
        }

    def stop_learning(self):
        """Stop the background learning thread."""
        self._stop_learning = True
        if self.learning_thread.is_alive():
            self.learning_thread.join(timeout=1.0)

    def _background_learning(self):
        """Background thread for continuous learning."""
        while not self._stop_learning:
            try:
                # Check for new patterns every 5 minutes
                time.sleep(300)

                # Learn from different mistake types
                mistake_types = ['command_error', 'ai_response', 'pattern_failure']

                for mistake_type in mistake_types:
                    if self._stop_learning:
                        break
                    pattern = self.learn_from_mistakes(mistake_type)
                    if pattern:
                        print(f"Learned new pattern: {pattern.id}")

            except Exception as e:
                print(f"Background learning error: {e}")
                time.sleep(60)  # Wait a minute before retrying