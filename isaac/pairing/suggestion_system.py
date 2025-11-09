"""
Inline Suggestion System - Phase 4.2
Provide inline improvement suggestions as code is written.
"""

import json
import sqlite3
import re
import ast
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import uuid

from isaac.core.session_manager import SessionManager


class SuggestionType(Enum):
    """Type of suggestion."""
    AUTOCOMPLETE = "autocomplete"
    REFACTOR = "refactor"
    OPTIMIZATION = "optimization"
    BUG_FIX = "bug_fix"
    STYLE = "style"
    DOCUMENTATION = "documentation"


@dataclass
class InlineSuggestion:
    """An inline code suggestion."""
    id: str
    file_path: str
    line_number: int
    column: int
    suggestion_type: str
    original_code: str
    suggested_code: str
    explanation: str
    confidence: float  # 0.0 to 1.0
    context: Dict[str, Any]
    created_at: float
    accepted: Optional[bool] = None
    feedback: Optional[str] = None


class SuggestionSystem:
    """Intelligent inline suggestion system."""

    def __init__(self, session_manager: SessionManager):
        """Initialize suggestion system.

        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
        self.data_dir = Path.home() / '.isaac' / 'pairing'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Database for suggestion history
        self.db_path = self.data_dir / 'suggestions.db'
        self._init_database()

        # Common patterns for suggestions
        self._load_suggestion_patterns()

    def _init_database(self):
        """Initialize SQLite database for suggestion storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS inline_suggestions (
                    id TEXT PRIMARY KEY,
                    file_path TEXT,
                    line_number INTEGER,
                    column_number INTEGER,
                    suggestion_type TEXT,
                    original_code TEXT,
                    suggested_code TEXT,
                    explanation TEXT,
                    confidence REAL,
                    context TEXT,
                    created_at REAL,
                    accepted BOOLEAN,
                    feedback TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_file ON inline_suggestions(file_path)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_accepted ON inline_suggestions(accepted)')

    def _load_suggestion_patterns(self):
        """Load suggestion patterns."""
        # Common refactoring patterns
        self.refactor_patterns = [
            {
                'pattern': r'if\s+(\w+)\s*==\s*True:',
                'replacement': r'if \1:',
                'explanation': 'Simplify boolean comparison',
                'type': SuggestionType.STYLE
            },
            {
                'pattern': r'if\s+(\w+)\s*==\s*False:',
                'replacement': r'if not \1:',
                'explanation': 'Simplify boolean comparison',
                'type': SuggestionType.STYLE
            },
            {
                'pattern': r'if\s+len\((\w+)\)\s*>\s*0:',
                'replacement': r'if \1:',
                'explanation': 'Pythonic emptiness check',
                'type': SuggestionType.STYLE
            },
            {
                'pattern': r'(\w+)\s*=\s*(\w+)\s*\+\s*\[([^\]]+)\]',
                'replacement': r'\1 = \2.copy()\n\1.append(\3)',
                'explanation': 'More efficient list append',
                'type': SuggestionType.OPTIMIZATION
            },
        ]

        # Autocomplete patterns based on common Python idioms
        self.autocomplete_patterns = {
            'with open(': 'with open(file_path, "r") as f:\n    content = f.read()',
            'for i in range(': 'for i in range(len(items)):\n    ',
            'try:': 'try:\n    pass\nexcept Exception as e:\n    pass',
            'class ': 'class ClassName:\n    def __init__(self):\n        pass',
        }

    def suggest_for_line(
        self,
        file_path: str,
        line_number: int,
        line_content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[InlineSuggestion]:
        """Generate suggestions for a line of code.

        Args:
            file_path: Path to the file
            line_number: Line number
            line_content: Content of the line
            context: Additional context

        Returns:
            List of suggestions
        """
        suggestions = []

        # Pattern-based refactoring suggestions
        for pattern_info in self.refactor_patterns:
            match = re.search(pattern_info['pattern'], line_content)
            if match:
                suggested_code = re.sub(
                    pattern_info['pattern'],
                    pattern_info['replacement'],
                    line_content
                )

                suggestion = InlineSuggestion(
                    id=str(uuid.uuid4()),
                    file_path=file_path,
                    line_number=line_number,
                    column=match.start(),
                    suggestion_type=pattern_info['type'].value,
                    original_code=line_content,
                    suggested_code=suggested_code,
                    explanation=pattern_info['explanation'],
                    confidence=0.9,
                    context=context or {},
                    created_at=datetime.now().timestamp()
                )
                suggestions.append(suggestion)

        # Save suggestions
        for suggestion in suggestions:
            self._save_suggestion(suggestion)

        return suggestions

    def suggest_autocomplete(
        self,
        file_path: str,
        line_number: int,
        partial_line: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[InlineSuggestion]:
        """Generate autocomplete suggestions.

        Args:
            file_path: Path to the file
            line_number: Line number
            partial_line: Partial line content
            context: Additional context

        Returns:
            List of autocomplete suggestions
        """
        suggestions = []

        for trigger, completion in self.autocomplete_patterns.items():
            if trigger in partial_line and not partial_line.strip().endswith(':'):
                # Don't suggest if the pattern is already complete
                continue

            if partial_line.strip().startswith(trigger.split('(')[0]):
                suggestion = InlineSuggestion(
                    id=str(uuid.uuid4()),
                    file_path=file_path,
                    line_number=line_number,
                    column=len(partial_line),
                    suggestion_type=SuggestionType.AUTOCOMPLETE.value,
                    original_code=partial_line,
                    suggested_code=completion,
                    explanation=f'Complete common pattern: {trigger}',
                    confidence=0.8,
                    context=context or {},
                    created_at=datetime.now().timestamp()
                )
                suggestions.append(suggestion)

        return suggestions

    def suggest_optimization(
        self,
        file_path: str,
        code_block: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[InlineSuggestion]:
        """Suggest optimizations for a code block.

        Args:
            file_path: Path to the file
            code_block: Block of code to optimize
            context: Additional context

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        try:
            tree = ast.parse(code_block)
            suggestions.extend(self._analyze_for_optimizations(file_path, tree, code_block, context))
        except SyntaxError:
            pass

        return suggestions

    def _analyze_for_optimizations(
        self,
        file_path: str,
        tree: ast.AST,
        code: str,
        context: Optional[Dict[str, Any]]
    ) -> List[InlineSuggestion]:
        """Analyze AST for optimization opportunities.

        Args:
            file_path: File path
            tree: AST tree
            code: Original code
            context: Context

        Returns:
            List of suggestions
        """
        suggestions = []

        for node in ast.walk(tree):
            # Suggest list comprehension instead of loop
            if isinstance(node, ast.For):
                if self._is_simple_append_loop(node):
                    suggestion = InlineSuggestion(
                        id=str(uuid.uuid4()),
                        file_path=file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        suggestion_type=SuggestionType.OPTIMIZATION.value,
                        original_code=ast.unparse(node) if hasattr(ast, 'unparse') else code,
                        suggested_code='# Use list comprehension instead',
                        explanation='List comprehension is more efficient and Pythonic',
                        confidence=0.85,
                        context=context or {},
                        created_at=datetime.now().timestamp()
                    )
                    suggestions.append(suggestion)

            # Suggest using 'any' or 'all' instead of loops
            if isinstance(node, ast.For):
                if self._is_boolean_search_loop(node):
                    suggestion = InlineSuggestion(
                        id=str(uuid.uuid4()),
                        file_path=file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        suggestion_type=SuggestionType.OPTIMIZATION.value,
                        original_code=ast.unparse(node) if hasattr(ast, 'unparse') else code,
                        suggested_code='# Use any() or all() built-in',
                        explanation='Built-in any/all is more efficient for boolean searches',
                        confidence=0.8,
                        context=context or {},
                        created_at=datetime.now().timestamp()
                    )
                    suggestions.append(suggestion)

        return suggestions

    def _is_simple_append_loop(self, node: ast.For) -> bool:
        """Check if a loop is a simple append pattern.

        Args:
            node: For loop node

        Returns:
            True if it's a simple append loop
        """
        if not node.body or len(node.body) != 1:
            return False

        stmt = node.body[0]
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Attribute) and call.func.attr == 'append':
                return True

        return False

    def _is_boolean_search_loop(self, node: ast.For) -> bool:
        """Check if a loop is searching for a boolean condition.

        Args:
            node: For loop node

        Returns:
            True if it's a boolean search loop
        """
        # Look for pattern: for x in items: if condition: return True
        if not node.body:
            return False

        for stmt in node.body:
            if isinstance(stmt, ast.If):
                if any(isinstance(s, ast.Return) for s in stmt.body):
                    return True

        return False

    def accept_suggestion(self, suggestion_id: str, feedback: Optional[str] = None) -> bool:
        """Mark a suggestion as accepted.

        Args:
            suggestion_id: Suggestion ID
            feedback: Optional feedback

        Returns:
            True if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE inline_suggestions
                SET accepted = 1, feedback = ?
                WHERE id = ?
            ''', (feedback, suggestion_id))

        return True

    def reject_suggestion(self, suggestion_id: str, feedback: Optional[str] = None) -> bool:
        """Mark a suggestion as rejected.

        Args:
            suggestion_id: Suggestion ID
            feedback: Optional feedback

        Returns:
            True if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE inline_suggestions
                SET accepted = 0, feedback = ?
                WHERE id = ?
            ''', (feedback, suggestion_id))

        return True

    def get_suggestion_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get suggestion statistics.

        Args:
            days: Number of days to look back

        Returns:
            Statistics dictionary
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        with sqlite3.connect(self.db_path) as conn:
            # Total suggestions
            cursor = conn.execute('''
                SELECT COUNT(*) FROM inline_suggestions
                WHERE created_at >= ?
            ''', (cutoff_time,))
            total_suggestions = cursor.fetchone()[0]

            # Accepted suggestions
            cursor = conn.execute('''
                SELECT COUNT(*) FROM inline_suggestions
                WHERE created_at >= ? AND accepted = 1
            ''', (cutoff_time,))
            accepted_suggestions = cursor.fetchone()[0]

            # Rejected suggestions
            cursor = conn.execute('''
                SELECT COUNT(*) FROM inline_suggestions
                WHERE created_at >= ? AND accepted = 0
            ''', (cutoff_time,))
            rejected_suggestions = cursor.fetchone()[0]

            # By type
            cursor = conn.execute('''
                SELECT suggestion_type, COUNT(*) FROM inline_suggestions
                WHERE created_at >= ?
                GROUP BY suggestion_type
            ''', (cutoff_time,))
            by_type = dict(cursor.fetchall())

            # Average confidence
            cursor = conn.execute('''
                SELECT AVG(confidence) FROM inline_suggestions
                WHERE created_at >= ?
            ''', (cutoff_time,))
            avg_confidence = cursor.fetchone()[0] or 0

        acceptance_rate = accepted_suggestions / total_suggestions if total_suggestions > 0 else 0

        return {
            'total_suggestions': total_suggestions,
            'accepted_suggestions': accepted_suggestions,
            'rejected_suggestions': rejected_suggestions,
            'pending_suggestions': total_suggestions - accepted_suggestions - rejected_suggestions,
            'acceptance_rate': acceptance_rate,
            'by_type': by_type,
            'average_confidence': avg_confidence,
            'period_days': days
        }

    def _save_suggestion(self, suggestion: InlineSuggestion):
        """Save suggestion to database.

        Args:
            suggestion: Suggestion to save
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO inline_suggestions
                (id, file_path, line_number, column_number, suggestion_type,
                 original_code, suggested_code, explanation, confidence, context,
                 created_at, accepted, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                suggestion.id,
                suggestion.file_path,
                suggestion.line_number,
                suggestion.column,
                suggestion.suggestion_type,
                suggestion.original_code,
                suggestion.suggested_code,
                suggestion.explanation,
                suggestion.confidence,
                json.dumps(suggestion.context),
                suggestion.created_at,
                suggestion.accepted,
                suggestion.feedback
            ))
