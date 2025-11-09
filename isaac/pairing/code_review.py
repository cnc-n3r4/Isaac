"""
Real-time Code Review Mode - Phase 4.2
Isaac provides real-time code review as you write code.
"""

import json
import sqlite3
import re
import ast
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import uuid

from isaac.core.session_manager import SessionManager


class ReviewSeverity(Enum):
    """Review suggestion severity."""
    INFO = "info"
    SUGGESTION = "suggestion"
    WARNING = "warning"
    ERROR = "error"


class ReviewCategory(Enum):
    """Review suggestion category."""
    STYLE = "style"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    CORRECTNESS = "correctness"
    BEST_PRACTICE = "best_practice"


@dataclass
class ReviewSuggestion:
    """A code review suggestion."""
    id: str
    file_path: str
    line_number: int
    severity: str
    category: str
    message: str
    suggestion: str
    code_snippet: str
    created_at: float
    resolved: bool = False
    resolution: Optional[str] = None


class CodeReviewer:
    """Real-time code review system."""

    def __init__(self, session_manager: SessionManager):
        """Initialize code reviewer.

        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
        self.data_dir = Path.home() / '.isaac' / 'pairing'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Database for review history
        self.db_path = self.data_dir / 'reviews.db'
        self._init_database()

        # Known anti-patterns and their fixes
        self._load_review_rules()

    def _init_database(self):
        """Initialize SQLite database for review storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS review_suggestions (
                    id TEXT PRIMARY KEY,
                    file_path TEXT,
                    line_number INTEGER,
                    severity TEXT,
                    category TEXT,
                    message TEXT,
                    suggestion TEXT,
                    code_snippet TEXT,
                    created_at REAL,
                    resolved BOOLEAN,
                    resolution TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_file ON review_suggestions(file_path)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_resolved ON review_suggestions(resolved)')

    def _load_review_rules(self):
        """Load code review rules."""
        # Basic Python code review rules
        # In a real implementation, this would be more sophisticated
        self.python_rules = [
            {
                'pattern': r'except\s*:',
                'category': ReviewCategory.BEST_PRACTICE,
                'severity': ReviewSeverity.WARNING,
                'message': 'Bare except clause catches all exceptions',
                'suggestion': 'Specify the exception type: except Exception:'
            },
            {
                'pattern': r'eval\s*\(',
                'category': ReviewCategory.SECURITY,
                'severity': ReviewSeverity.ERROR,
                'message': 'Using eval() is a security risk',
                'suggestion': 'Avoid eval(); use safer alternatives like ast.literal_eval() for data'
            },
            {
                'pattern': r'exec\s*\(',
                'category': ReviewCategory.SECURITY,
                'severity': ReviewSeverity.ERROR,
                'message': 'Using exec() is a security risk',
                'suggestion': 'Avoid exec(); refactor to use safer alternatives'
            },
            {
                'pattern': r'TODO:',
                'category': ReviewCategory.MAINTAINABILITY,
                'severity': ReviewSeverity.INFO,
                'message': 'TODO comment found',
                'suggestion': 'Consider creating a task or issue to track this TODO'
            },
            {
                'pattern': r'FIXME:',
                'category': ReviewCategory.MAINTAINABILITY,
                'severity': ReviewSeverity.WARNING,
                'message': 'FIXME comment found',
                'suggestion': 'This code needs to be fixed'
            },
            {
                'pattern': r'import\s+\*',
                'category': ReviewCategory.BEST_PRACTICE,
                'severity': ReviewSeverity.SUGGESTION,
                'message': 'Wildcard imports make code harder to read',
                'suggestion': 'Import specific names instead of using import *'
            },
        ]

    def review_code(
        self,
        file_path: str,
        content: Optional[str] = None,
        language: str = 'python'
    ) -> List[ReviewSuggestion]:
        """Review code and generate suggestions.

        Args:
            file_path: Path to the file
            content: File content (reads from disk if None)
            language: Programming language

        Returns:
            List of review suggestions
        """
        if content is None:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
            except Exception:
                return []

        suggestions = []

        if language == 'python':
            suggestions.extend(self._review_python_code(file_path, content))

        # Save suggestions
        for suggestion in suggestions:
            self._save_suggestion(suggestion)

        return suggestions

    def _review_python_code(self, file_path: str, content: str) -> List[ReviewSuggestion]:
        """Review Python code.

        Args:
            file_path: File path
            content: File content

        Returns:
            List of suggestions
        """
        suggestions = []
        lines = content.split('\n')

        # Pattern-based reviews
        for i, line in enumerate(lines, 1):
            for rule in self.python_rules:
                if re.search(rule['pattern'], line):
                    suggestion = ReviewSuggestion(
                        id=str(uuid.uuid4()),
                        file_path=file_path,
                        line_number=i,
                        severity=rule['severity'].value,
                        category=rule['category'].value,
                        message=rule['message'],
                        suggestion=rule['suggestion'],
                        code_snippet=line.strip(),
                        created_at=datetime.now().timestamp()
                    )
                    suggestions.append(suggestion)

        # AST-based reviews
        try:
            tree = ast.parse(content)
            suggestions.extend(self._review_python_ast(file_path, tree, lines))
        except SyntaxError:
            # File has syntax errors, can't do AST analysis
            pass

        return suggestions

    def _review_python_ast(
        self,
        file_path: str,
        tree: ast.AST,
        lines: List[str]
    ) -> List[ReviewSuggestion]:
        """Review Python code using AST analysis.

        Args:
            file_path: File path
            tree: AST tree
            lines: File lines

        Returns:
            List of suggestions
        """
        suggestions = []

        for node in ast.walk(tree):
            # Check for long functions
            if isinstance(node, ast.FunctionDef):
                func_length = self._get_function_length(node)
                if func_length > 50:
                    suggestion = ReviewSuggestion(
                        id=str(uuid.uuid4()),
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=ReviewSeverity.SUGGESTION.value,
                        category=ReviewCategory.MAINTAINABILITY.value,
                        message=f'Function "{node.name}" is {func_length} lines long',
                        suggestion='Consider breaking this function into smaller, more focused functions',
                        code_snippet=f'def {node.name}(...):',
                        created_at=datetime.now().timestamp()
                    )
                    suggestions.append(suggestion)

            # Check for complex conditions
            if isinstance(node, ast.If):
                complexity = self._get_condition_complexity(node.test)
                if complexity > 3:
                    suggestion = ReviewSuggestion(
                        id=str(uuid.uuid4()),
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=ReviewSeverity.SUGGESTION.value,
                        category=ReviewCategory.MAINTAINABILITY.value,
                        message='Complex conditional statement',
                        suggestion='Consider extracting condition into a well-named variable or function',
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else '',
                        created_at=datetime.now().timestamp()
                    )
                    suggestions.append(suggestion)

            # Check for mutable default arguments
            if isinstance(node, ast.FunctionDef):
                for arg_idx, default in enumerate(node.args.defaults):
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        suggestion = ReviewSuggestion(
                            id=str(uuid.uuid4()),
                            file_path=file_path,
                            line_number=node.lineno,
                            severity=ReviewSeverity.WARNING.value,
                            category=ReviewCategory.CORRECTNESS.value,
                            message=f'Function "{node.name}" has mutable default argument',
                            suggestion='Use None as default and create the mutable object inside the function',
                            code_snippet=f'def {node.name}(...):',
                            created_at=datetime.now().timestamp()
                        )
                        suggestions.append(suggestion)

        return suggestions

    def _get_function_length(self, node: ast.FunctionDef) -> int:
        """Get the length of a function in lines.

        Args:
            node: Function node

        Returns:
            Number of lines
        """
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno - node.lineno + 1
        return 0

    def _get_condition_complexity(self, node: ast.AST) -> int:
        """Get the complexity of a conditional expression.

        Args:
            node: AST node

        Returns:
            Complexity score
        """
        if isinstance(node, ast.BoolOp):
            return 1 + sum(self._get_condition_complexity(val) for val in node.values)
        elif isinstance(node, ast.UnaryOp):
            return 1 + self._get_condition_complexity(node.operand)
        elif isinstance(node, ast.Compare):
            return 1
        else:
            return 0

    def review_diff(
        self,
        file_path: str,
        old_content: str,
        new_content: str
    ) -> List[ReviewSuggestion]:
        """Review only the changed lines in a diff.

        Args:
            file_path: File path
            old_content: Original content
            new_content: New content

        Returns:
            List of suggestions for changed lines
        """
        # Simple line-by-line diff
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')

        suggestions = []

        # Review only new/modified lines
        for i, new_line in enumerate(new_lines, 1):
            if i > len(old_lines) or old_lines[i - 1] != new_line:
                # This line was added or modified
                for rule in self.python_rules:
                    if re.search(rule['pattern'], new_line):
                        suggestion = ReviewSuggestion(
                            id=str(uuid.uuid4()),
                            file_path=file_path,
                            line_number=i,
                            severity=rule['severity'].value,
                            category=rule['category'].value,
                            message=rule['message'],
                            suggestion=rule['suggestion'],
                            code_snippet=new_line.strip(),
                            created_at=datetime.now().timestamp()
                        )
                        suggestions.append(suggestion)

        return suggestions

    def get_unresolved_suggestions(
        self,
        file_path: Optional[str] = None
    ) -> List[ReviewSuggestion]:
        """Get unresolved review suggestions.

        Args:
            file_path: Filter by file path (None for all files)

        Returns:
            List of unresolved suggestions
        """
        suggestions = []
        with sqlite3.connect(self.db_path) as conn:
            if file_path:
                cursor = conn.execute('''
                    SELECT id, file_path, line_number, severity, category, message,
                           suggestion, code_snippet, created_at, resolved, resolution
                    FROM review_suggestions
                    WHERE resolved = 0 AND file_path = ?
                    ORDER BY severity DESC, line_number ASC
                ''', (file_path,))
            else:
                cursor = conn.execute('''
                    SELECT id, file_path, line_number, severity, category, message,
                           suggestion, code_snippet, created_at, resolved, resolution
                    FROM review_suggestions
                    WHERE resolved = 0
                    ORDER BY severity DESC, created_at DESC
                ''')

            for row in cursor:
                suggestion = ReviewSuggestion(
                    id=row[0],
                    file_path=row[1],
                    line_number=row[2],
                    severity=row[3],
                    category=row[4],
                    message=row[5],
                    suggestion=row[6],
                    code_snippet=row[7],
                    created_at=row[8],
                    resolved=bool(row[9]),
                    resolution=row[10]
                )
                suggestions.append(suggestion)

        return suggestions

    def resolve_suggestion(
        self,
        suggestion_id: str,
        resolution: str = "fixed"
    ) -> bool:
        """Mark a suggestion as resolved.

        Args:
            suggestion_id: Suggestion ID
            resolution: How it was resolved

        Returns:
            True if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE review_suggestions
                SET resolved = 1, resolution = ?
                WHERE id = ?
            ''', (resolution, suggestion_id))

        return True

    def _save_suggestion(self, suggestion: ReviewSuggestion):
        """Save suggestion to database.

        Args:
            suggestion: Suggestion to save
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO review_suggestions
                (id, file_path, line_number, severity, category, message,
                 suggestion, code_snippet, created_at, resolved, resolution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                suggestion.id,
                suggestion.file_path,
                suggestion.line_number,
                suggestion.severity,
                suggestion.category,
                suggestion.message,
                suggestion.suggestion,
                suggestion.code_snippet,
                suggestion.created_at,
                suggestion.resolved,
                suggestion.resolution
            ))

    def get_review_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get review statistics.

        Args:
            days: Number of days to look back

        Returns:
            Statistics dictionary
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        with sqlite3.connect(self.db_path) as conn:
            # Total suggestions
            cursor = conn.execute('''
                SELECT COUNT(*) FROM review_suggestions
                WHERE created_at >= ?
            ''', (cutoff_time,))
            total_suggestions = cursor.fetchone()[0]

            # Resolved suggestions
            cursor = conn.execute('''
                SELECT COUNT(*) FROM review_suggestions
                WHERE created_at >= ? AND resolved = 1
            ''', (cutoff_time,))
            resolved_suggestions = cursor.fetchone()[0]

            # By severity
            cursor = conn.execute('''
                SELECT severity, COUNT(*) FROM review_suggestions
                WHERE created_at >= ?
                GROUP BY severity
            ''', (cutoff_time,))
            by_severity = dict(cursor.fetchall())

            # By category
            cursor = conn.execute('''
                SELECT category, COUNT(*) FROM review_suggestions
                WHERE created_at >= ?
                GROUP BY category
            ''', (cutoff_time,))
            by_category = dict(cursor.fetchall())

        return {
            'total_suggestions': total_suggestions,
            'resolved_suggestions': resolved_suggestions,
            'unresolved_suggestions': total_suggestions - resolved_suggestions,
            'resolution_rate': resolved_suggestions / total_suggestions if total_suggestions > 0 else 0,
            'by_severity': by_severity,
            'by_category': by_category,
            'period_days': days
        }
