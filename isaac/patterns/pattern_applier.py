"""
Pattern Application - Apply learned patterns to new code
Phase 3.4.2: Suggest and apply learned patterns intelligently
"""

import re
import ast
import difflib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import time
from .pattern_learner import CodePattern, PatternMatch


@dataclass
class PatternApplication:
    """Result of applying a pattern to code."""
    pattern: CodePattern
    original_code: str
    modified_code: str
    confidence: float
    changes_made: List[str]
    line_number: int
    explanation: str
    variables_used: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternSuggestion:
    """A suggestion to apply a pattern."""
    pattern: CodePattern
    target_code: str
    suggested_code: str
    confidence: float
    benefit: str  # Why this pattern should be applied
    risk: str  # Potential issues with applying this pattern
    line_number: int


class PatternApplier:
    """Applies learned patterns to code."""

    def __init__(self, pattern_learner):
        """Initialize pattern applier."""
        self.pattern_learner = pattern_learner
        self.suggestion_cache: Dict[str, List[PatternSuggestion]] = {}

    def analyze_and_suggest(self, file_path: str) -> List[PatternSuggestion]:
        """Analyze a file and suggest pattern applications."""
        cache_key = f"{file_path}:{Path(file_path).stat().st_mtime}"

        if cache_key in self.suggestion_cache:
            return self.suggestion_cache[cache_key]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            language = self._detect_language(file_path)
            if not language:
                return []

            # Parse the code
            tree = self._parse_code(content, language)
            if not tree:
                return []

            suggestions = []

            # Get available patterns for this language
            patterns = self.pattern_learner.get_patterns(language=language)

            # Analyze each node for pattern application opportunities
            for node in ast.walk(tree):
                node_suggestions = self._analyze_node_for_patterns(node, content, patterns, language)
                suggestions.extend(node_suggestions)

            # Additional suggestions based on code analysis
            analysis_suggestions = self._analyze_code_for_improvements(tree, content, language)
            suggestions.extend(analysis_suggestions)

            # Sort by confidence
            suggestions.sort(key=lambda s: s.confidence, reverse=True)

            self.suggestion_cache[cache_key] = suggestions
            return suggestions

        except Exception as e:
            print(f"Error analyzing file for suggestions {file_path}: {e}")
            return []

    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php'
        }
        return language_map.get(ext)

    def _parse_code(self, content: str, language: str) -> Optional[Any]:
        """Parse code into AST or similar structure."""
        try:
            if language == 'python':
                return ast.parse(content)
            return None
        except:
            return None

    def _analyze_node_for_patterns(self, node: ast.AST, content: str,
                                 patterns: List[CodePattern], language: str) -> List[PatternSuggestion]:
        """Analyze a node for pattern application opportunities."""
        suggestions = []

        if language != 'python':
            return suggestions

        # Get the source code for this node
        node_source = self._get_node_source(node, content)
        if not node_source or len(node_source.split('\n')) > 50:  # Skip very large nodes
            return suggestions

        for pattern in patterns:
            if pattern.is_anti_pattern or pattern.category not in ['function', 'class', 'loop']:
                continue

            # Check if this pattern could apply to this node
            match_result = self._pattern_matches_node(pattern, node, node_source, language)

            if match_result and match_result['confidence'] > 0.6:
                suggestion = PatternSuggestion(
                    pattern=pattern,
                    target_code=node_source,
                    suggested_code=match_result['suggested_code'],
                    confidence=match_result['confidence'],
                    benefit=match_result['benefit'],
                    risk=match_result['risk'],
                    line_number=getattr(node, 'lineno', 1)
                )
                suggestions.append(suggestion)

        return suggestions

    def _pattern_matches_node(self, pattern: CodePattern, node: ast.AST,
                            node_source: str, language: str) -> Optional[Dict[str, Any]]:
        """Check if a pattern matches a code node."""
        if language != 'python':
            return None

        # Simple pattern matching based on pattern type
        if pattern.category == 'function' and isinstance(node, ast.FunctionDef):
            return self._function_pattern_match(pattern, node, node_source)
        elif pattern.category == 'class' and isinstance(node, ast.ClassDef):
            return self._class_pattern_match(pattern, node, node_source)
        elif pattern.category == 'loop' and isinstance(node, (ast.For, ast.While)):
            return self._loop_pattern_match(pattern, node, node_source)

        return None

    def _function_pattern_match(self, pattern: CodePattern, node: ast.FunctionDef,
                              node_source: str) -> Optional[Dict[str, Any]]:
        """Check if a function pattern matches."""
        # Analyze function characteristics
        arg_count = len(node.args.args)
        has_docstring = self._has_docstring(node)
        has_type_hints = self._has_type_hints(node)
        complexity = self._calculate_complexity(node)

        # Check if pattern characteristics match
        pattern_vars = pattern.variables

        # Simple matching logic - in practice this would be more sophisticated
        confidence = 0.0
        reasons = []

        if 'function_name' in pattern_vars:
            confidence += 0.3
            reasons.append("Function structure matches pattern")

        if arg_count <= 3:  # Prefer patterns with reasonable arg counts
            confidence += 0.2
            reasons.append("Appropriate number of arguments")

        if not has_docstring and pattern.name.lower().find('documented') >= 0:
            # Suggest adding docstring
            suggested_code = self._add_docstring_to_function(node_source)
            return {
                'confidence': 0.8,
                'suggested_code': suggested_code,
                'benefit': 'Adds documentation following established patterns',
                'risk': 'May require updating docstring content'
            }

        if confidence > 0.5:
            return {
                'confidence': confidence,
                'suggested_code': node_source,  # No change needed
                'benefit': f"Follows established {pattern.name.lower()} pattern",
                'risk': 'Minimal - pattern already matches'
            }

        return None

    def _class_pattern_match(self, pattern: CodePattern, node: ast.ClassDef,
                           node_source: str) -> Optional[Dict[str, Any]]:
        """Check if a class pattern matches."""
        method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
        has_init = any(isinstance(n, ast.FunctionDef) and n.name == '__init__' for n in node.body)
        has_docstring = self._has_docstring(node)

        confidence = 0.0

        if not has_docstring:
            suggested_code = self._add_docstring_to_class(node_source)
            return {
                'confidence': 0.7,
                'suggested_code': suggested_code,
                'benefit': 'Adds class documentation following patterns',
                'risk': 'Requires writing appropriate docstring'
            }

        if method_count == 0 and len(node.body) > 0:
            # Suggest converting to dataclass
            suggested_code = self._convert_to_dataclass(node_source)
            return {
                'confidence': 0.6,
                'suggested_code': suggested_code,
                'benefit': 'Converts simple data class to dataclass for better pattern compliance',
                'risk': 'Requires dataclass import and may change behavior slightly'
            }

        return None

    def _loop_pattern_match(self, pattern: CodePattern, node: ast.AST,
                          node_source: str) -> Optional[Dict[str, Any]]:
        """Check if a loop pattern matches."""
        # Check for nested loops that could be simplified
        nesting_level = self._calculate_nesting_level(node)

        if nesting_level > 2:
            return {
                'confidence': 0.7,
                'suggested_code': self._simplify_nested_loops(node_source),
                'benefit': 'Reduces loop nesting complexity',
                'risk': 'May require extracting logic to separate functions'
            }

        # Check for loops that could be list comprehensions
        if isinstance(node, ast.For):
            comprehension_suggestion = self._suggest_list_comprehension(node, node_source)
            if comprehension_suggestion:
                return comprehension_suggestion

        return None

    def _analyze_code_for_improvements(self, tree: ast.AST, content: str,
                                     language: str) -> List[PatternSuggestion]:
        """Analyze code for general improvement opportunities."""
        suggestions = []

        if language != 'python':
            return suggestions

        # Check for imports that could be organized
        import_suggestions = self._analyze_imports(tree, content)
        suggestions.extend(import_suggestions)

        # Check for variable naming improvements
        naming_suggestions = self._analyze_naming(tree, content)
        suggestions.extend(naming_suggestions)

        # Check for code that could be simplified
        simplification_suggestions = self._analyze_simplifications(tree, content)
        suggestions.extend(simplification_suggestions)

        return suggestions

    def _analyze_imports(self, tree: ast.AST, content: str) -> List[PatternSuggestion]:
        """Analyze import statements for improvements."""
        suggestions = []

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)

        # Check for unused imports (simplified check)
        # In practice, this would need more sophisticated analysis
        if len(imports) > 10:
            suggestions.append(PatternSuggestion(
                pattern=CodePattern(
                    id="import_organization",
                    name="Import Organization",
                    description="Organize imports following PEP 8",
                    category="style",
                    language="python",
                    pattern_type="structural",
                    template="",
                    variables={}
                ),
                target_code="",  # Applies to whole file
                suggested_code="",  # Would be generated
                confidence=0.6,
                benefit="Improves code readability and follows conventions",
                risk="May require reorganizing import order",
                line_number=1
            ))

        return suggestions

    def _analyze_naming(self, tree: ast.AST, content: str) -> List[PatternSuggestion]:
        """Analyze variable naming for improvements."""
        suggestions = []

        # Collect all names
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.append(node.id)

        # Check for inconsistent naming
        snake_case = [n for n in names if re.match(r'^[a-z][a-z0-9_]*$', n)]
        camel_case = [n for n in names if re.match(r'^[a-z][a-zA-Z0-9]*$', n)]

        if snake_case and camel_case:
            suggestions.append(PatternSuggestion(
                pattern=CodePattern(
                    id="naming_consistency",
                    name="Naming Consistency",
                    description="Use consistent naming conventions",
                    category="naming",
                    language="python",
                    pattern_type="style",
                    template="",
                    variables={}
                ),
                target_code="",  # Applies to whole file
                suggested_code="",  # Would require manual fixes
                confidence=0.8,
                benefit="Improves code readability and maintainability",
                risk="Requires renaming variables/functions",
                line_number=1
            ))

        return suggestions

    def _analyze_simplifications(self, tree: ast.AST, content: str) -> List[PatternSuggestion]:
        """Analyze code for simplification opportunities."""
        suggestions = []

        # Look for complex boolean expressions that could be simplified
        for node in ast.walk(tree):
            if isinstance(node, ast.BoolOp) and len(node.values) > 2:
                suggestions.append(PatternSuggestion(
                    pattern=CodePattern(
                        id="boolean_simplification",
                        name="Boolean Expression Simplification",
                        description="Simplify complex boolean expressions",
                        category="logic",
                        language="python",
                        pattern_type="style",
                        template="",
                        variables={}
                    ),
                    target_code=self._get_node_source(node, content),
                    suggested_code="",  # Would need AST transformation
                    confidence=0.5,
                    benefit="Makes code more readable",
                    risk="May change logic if not careful",
                    line_number=getattr(node, 'lineno', 1)
                ))

        return suggestions

    def apply_pattern(self, suggestion: PatternSuggestion) -> PatternApplication:
        """Apply a pattern suggestion to code."""
        # In a real implementation, this would use AST transformations
        # For now, we'll just return the suggestion as an application

        return PatternApplication(
            pattern=suggestion.pattern,
            original_code=suggestion.target_code,
            modified_code=suggestion.suggested_code,
            confidence=suggestion.confidence,
            changes_made=["Applied pattern suggestion"],
            line_number=suggestion.line_number,
            explanation=suggestion.benefit,
            variables_used={}
        )

    def apply_patterns_to_file(self, file_path: str, min_confidence: float = 0.7) -> List[PatternApplication]:
        """Apply high-confidence patterns to a file."""
        suggestions = self.analyze_and_suggest(file_path)
        applications = []

        for suggestion in suggestions:
            if suggestion.confidence >= min_confidence:
                application = self.apply_pattern(suggestion)
                applications.append(application)

        return applications

    # Helper methods
    def _has_docstring(self, node: ast.AST) -> bool:
        """Check if a node has a docstring."""
        if hasattr(node, 'body') and node.body:
            first_stmt = node.body[0]
            return isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Str)
        return False

    def _has_type_hints(self, node: ast.FunctionDef) -> bool:
        """Check if a function has type hints."""
        has_arg_hints = any(arg.annotation for arg in node.args.args)
        has_return_hint = node.returns is not None
        return has_arg_hints or has_return_hint

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp) and len(child.values) > 1:
                complexity += len(child.values) - 1
        return complexity

    def _calculate_nesting_level(self, node: ast.AST, current_level: int = 0) -> int:
        """Calculate nesting level."""
        max_level = current_level
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While, ast.If, ast.Try, ast.With)):
                child_level = self._calculate_nesting_level(child, current_level + 1)
                max_level = max(max_level, child_level)
        return max_level

    def _get_node_source(self, node: ast.AST, content: str) -> str:
        """Extract source code for a node."""
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
            lines = content.split('\n')
            start_line = node.lineno - 1
            end_line = node.end_lineno
            return '\n'.join(lines[start_line:end_line])
        return ""

    # Code transformation methods
    def _add_docstring_to_function(self, code: str) -> str:
        """Add a docstring to a function."""
        lines = code.split('\n')
        if len(lines) > 1:
            # Insert docstring after function definition
            indent = '    '  # Assume 4-space indentation
            lines.insert(1, f'{indent}"""Function docstring."""')
            return '\n'.join(lines)
        return code

    def _add_docstring_to_class(self, code: str) -> str:
        """Add a docstring to a class."""
        lines = code.split('\n')
        if len(lines) > 1:
            indent = '    '  # Assume 4-space indentation
            lines.insert(1, f'{indent}"""Class docstring."""')
            return '\n'.join(lines)
        return code

    def _convert_to_dataclass(self, code: str) -> str:
        """Convert a simple class to a dataclass."""
        # This is a simplified transformation
        lines = code.split('\n')
        # Add dataclass decorator and import
        lines.insert(0, '@dataclass')
        lines.insert(0, 'from dataclasses import dataclass')
        lines.insert(1, '')  # Empty line
        return '\n'.join(lines)

    def _simplify_nested_loops(self, code: str) -> str:
        """Suggest simplification for nested loops."""
        # This would require more sophisticated analysis
        # For now, just add a comment
        return f"# TODO: Consider simplifying nested loops\n{code}"

    def _suggest_list_comprehension(self, node: ast.For, code: str) -> Optional[Dict[str, Any]]:
        """Suggest using list comprehension instead of loop."""
        # Simplified check - in practice this would be more complex
        loop_body = []
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                # Check if it's a list append
                if (isinstance(child.value.func, ast.Attribute) and
                    child.value.func.attr == 'append'):
                    loop_body.append(child)

        if len(loop_body) == 1:
            return {
                'confidence': 0.6,
                'suggested_code': f"# Consider: [item for item in iterable]",
                'benefit': 'List comprehensions are more concise and often faster',
                'risk': 'May not be suitable for complex loop logic'
            }

        return None