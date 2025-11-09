"""
Pattern Library - Isaac's Code Pattern Learning and Application System
Phase 3.4: Learn from user's code patterns and apply them intelligently
"""

import os
import json
import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import time


@dataclass
class CodePattern:
    """Represents a learned code pattern."""
    id: str
    name: str
    description: str
    category: str  # function, class, loop, error_handling, etc.
    language: str  # python, javascript, etc.
    pattern_type: str  # structural, naming, style, etc.

    # Pattern content
    template: str  # The actual pattern template
    variables: Dict[str, Any]  # Variable placeholders in template
    examples: List[str] = field(default_factory=list)  # Example usages

    # Metadata
    confidence: float = 1.0  # How confident we are in this pattern
    usage_count: int = 0
    success_rate: float = 1.0
    created_at: float = field(default_factory=time.time)
    last_used: float = 0.0
    source_files: List[str] = field(default_factory=list)  # Files this pattern was learned from

    # Evolution tracking
    version: int = 1
    parent_pattern: Optional[str] = None  # ID of pattern this evolved from
    evolution_score: float = 0.0  # How much this pattern has evolved

    # Anti-pattern detection
    is_anti_pattern: bool = False
    anti_pattern_reason: Optional[str] = None
    alternative_suggestions: List[str] = field(default_factory=list)


@dataclass
class PatternMatch:
    """Result of matching a pattern against code."""
    pattern: CodePattern
    confidence: float
    matched_code: str
    suggested_replacement: str
    line_number: int
    explanation: str
    variables_extracted: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternAnalysis:
    """Analysis of code for patterns."""
    file_path: str
    patterns_found: List[PatternMatch]
    anti_patterns_found: List[PatternMatch]
    suggestions: List[str]
    overall_score: float  # Code quality score based on patterns
    analyzed_at: float = field(default_factory=time.time)


class PatternLearner:
    """Learns patterns from user code."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize pattern learner."""
        self.config = config or {}
        self.patterns: Dict[str, CodePattern] = {}
        self.patterns_file = Path.home() / '.isaac' / 'patterns' / 'learned_patterns.json'
        self.analysis_cache: Dict[str, PatternAnalysis] = {}

        # Learning parameters
        self.min_pattern_frequency = self.config.get('min_pattern_frequency', 3)
        self.min_confidence_threshold = self.config.get('min_confidence_threshold', 0.7)
        self.max_patterns_per_file = self.config.get('max_patterns_per_file', 50)

        # Pattern categories to learn
        self.categories = {
            'function': self._learn_function_patterns,
            'class': self._learn_class_patterns,
            'loop': self._learn_loop_patterns,
            'error_handling': self._learn_error_handling_patterns,
            'async': self._learn_async_patterns,
            'data_structure': self._learn_data_structure_patterns,
            'naming': self._learn_naming_patterns,
            'style': self._learn_style_patterns
        }

        self._load_patterns()

    def _load_patterns(self):
        """Load learned patterns from disk."""
        try:
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                    for pattern_data in patterns_data:
                        pattern = CodePattern(**pattern_data)
                        self.patterns[pattern.id] = pattern
        except Exception as e:
            print(f"Error loading patterns: {e}")

    def _save_patterns(self):
        """Save learned patterns to disk."""
        try:
            self.patterns_file.parent.mkdir(parents=True, exist_ok=True)
            patterns_data = [asdict(p) for p in self.patterns.values()]
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving patterns: {e}")

    def analyze_file(self, file_path: str) -> PatternAnalysis:
        """Analyze a file for patterns."""
        if file_path in self.analysis_cache:
            # Return cached analysis if file hasn't changed
            cached = self.analysis_cache[file_path]
            if self._file_modified_time(file_path) <= cached.analyzed_at:
                return cached

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            language = self._detect_language(file_path)
            if not language:
                return PatternAnalysis(file_path, [], [], [], 0.5)

            # Parse the code
            tree = self._parse_code(content, language)
            if not tree:
                return PatternAnalysis(file_path, [], [], [], 0.5)

            # Analyze for patterns
            patterns_found = []
            anti_patterns_found = []
            suggestions = []

            for category, analyzer in self.categories.items():
                try:
                    category_patterns, category_anti_patterns, category_suggestions = analyzer(tree, content, language)
                    patterns_found.extend(category_patterns)
                    anti_patterns_found.extend(category_anti_patterns)
                    suggestions.extend(category_suggestions)
                except Exception as e:
                    print(f"Error analyzing {category} patterns in {file_path}: {e}")

            # Calculate overall score
            overall_score = self._calculate_code_score(patterns_found, anti_patterns_found)

            analysis = PatternAnalysis(
                file_path=file_path,
                patterns_found=patterns_found,
                anti_patterns_found=anti_patterns_found,
                suggestions=suggestions,
                overall_score=overall_score
            )

            self.analysis_cache[file_path] = analysis
            return analysis

        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            return PatternAnalysis(file_path, [], [], [], 0.5)

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
            # For other languages, we'd need their respective parsers
            # For now, return None for unsupported languages
            return None
        except:
            return None

    def _learn_function_patterns(self, tree: ast.AST, content: str, language: str) -> Tuple[List[PatternMatch], List[PatternMatch], List[str]]:
        """Learn function definition patterns."""
        patterns = []
        anti_patterns = []
        suggestions = []

        if language != 'python':
            return patterns, anti_patterns, suggestions

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Analyze function structure
                pattern_info = self._analyze_function_pattern(node, content)

                if pattern_info:
                    # Check for anti-patterns
                    anti_pattern_check = self._check_function_anti_patterns(node, content)
                    if anti_pattern_check:
                        anti_patterns.append(anti_pattern_check)
                        suggestions.append(anti_pattern_check.explanation)

                    # Learn positive patterns
                    if pattern_info['confidence'] > self.min_confidence_threshold:
                        pattern = self._create_function_pattern(pattern_info, node, content)
                        if pattern:
                            patterns.append(PatternMatch(
                                pattern=pattern,
                                confidence=pattern_info['confidence'],
                                matched_code=self._get_node_source(node, content),
                                suggested_replacement="",  # Would be generated by pattern application
                                line_number=node.lineno,
                                explanation=f"Learned function pattern: {pattern.name}"
                            ))

        return patterns, anti_patterns, suggestions

    def _analyze_function_pattern(self, node: ast.FunctionDef, content: str) -> Optional[Dict[str, Any]]:
        """Analyze a function definition for patterns."""
        # Count various elements
        arg_count = len(node.args.args)
        has_docstring = self._has_docstring(node)
        has_type_hints = self._has_type_hints(node)
        line_count = len(self._get_node_source(node, content).split('\n'))
        complexity = self._calculate_complexity(node)

        # Determine pattern type based on characteristics
        if arg_count == 0 and line_count < 5:
            pattern_type = "simple_getter"
        elif arg_count > 4:
            pattern_type = "complex_function"
        elif has_docstring and has_type_hints:
            pattern_type = "well_documented_function"
        elif complexity > 10:
            pattern_type = "complex_logic"
        else:
            pattern_type = "standard_function"

        return {
            'pattern_type': pattern_type,
            'arg_count': arg_count,
            'has_docstring': has_docstring,
            'has_type_hints': has_type_hints,
            'line_count': line_count,
            'complexity': complexity,
            'confidence': min(1.0, (arg_count + (1 if has_docstring else 0) + (1 if has_type_hints else 0)) / 5.0)
        }

    def _check_function_anti_patterns(self, node: ast.FunctionDef, content: str) -> Optional[PatternMatch]:
        """Check for function anti-patterns."""
        issues = []

        # Too many arguments
        if len(node.args.args) > 7:
            issues.append("Function has too many parameters (>7)")

        # Too long function
        source_lines = self._get_node_source(node, content).split('\n')
        if len(source_lines) > 50:
            issues.append("Function is too long (>50 lines)")

        # No docstring
        if not self._has_docstring(node):
            issues.append("Function missing docstring")

        # Complex function without type hints
        complexity = self._calculate_complexity(node)
        if complexity > 15 and not self._has_type_hints(node):
            issues.append("Complex function should have type hints")

        if issues:
            return PatternMatch(
                pattern=CodePattern(
                    id=f"anti_pattern_{hash(str(issues))}",
                    name="Function Anti-Patterns",
                    description="Detected problematic function patterns",
                    category="function",
                    language="python",
                    pattern_type="anti_pattern",
                    template="",
                    variables={},
                    is_anti_pattern=True,
                    anti_pattern_reason="; ".join(issues),
                    alternative_suggestions=[
                        "Break down large functions into smaller ones",
                        "Add docstrings and type hints",
                        "Reduce parameter count using data classes or config objects"
                    ]
                ),
                confidence=0.8,
                matched_code=self._get_node_source(node, content),
                suggested_replacement="",
                line_number=node.lineno,
                explanation="; ".join(issues)
            )

        return None

    def _create_function_pattern(self, pattern_info: Dict[str, Any], node: ast.FunctionDef, content: str) -> Optional[CodePattern]:
        """Create a pattern from function analysis."""
        pattern_id = f"func_{pattern_info['pattern_type']}_{hash(self._get_node_source(node, content))}"

        # Skip if we already have this pattern
        if pattern_id in self.patterns:
            return None

        # Create template (simplified for now)
        template = self._create_function_template(node, content)

        pattern = CodePattern(
            id=pattern_id,
            name=f"{pattern_info['pattern_type'].replace('_', ' ').title()} Function",
            description=f"A {pattern_info['pattern_type']} function pattern",
            category="function",
            language="python",
            pattern_type="structural",
            template=template,
            variables=self._extract_function_variables(node),
            examples=[self._get_node_source(node, content)]
        )

        self.patterns[pattern_id] = pattern
        return pattern

    def _learn_class_patterns(self, tree: ast.AST, content: str, language: str) -> Tuple[List[PatternMatch], List[PatternMatch], List[str]]:
        """Learn class definition patterns."""
        patterns = []
        anti_patterns = []
        suggestions = []

        if language != 'python':
            return patterns, anti_patterns, suggestions

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Analyze class structure
                pattern_info = self._analyze_class_pattern(node, content)

                if pattern_info:
                    # Check for anti-patterns
                    anti_pattern_check = self._check_class_anti_patterns(node, content)
                    if anti_pattern_check:
                        anti_patterns.append(anti_pattern_check)
                        suggestions.append(anti_pattern_check.explanation)

                    # Learn positive patterns
                    if pattern_info['confidence'] > self.min_confidence_threshold:
                        pattern = self._create_class_pattern(pattern_info, node, content)
                        if pattern:
                            patterns.append(PatternMatch(
                                pattern=pattern,
                                confidence=pattern_info['confidence'],
                                matched_code=self._get_node_source(node, content),
                                suggested_replacement="",
                                line_number=node.lineno,
                                explanation=f"Learned class pattern: {pattern.name}"
                            ))

        return patterns, anti_patterns, suggestions

    def _analyze_class_pattern(self, node: ast.ClassDef, content: str) -> Optional[Dict[str, Any]]:
        """Analyze a class definition for patterns."""
        method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
        has_init = any(isinstance(n, ast.FunctionDef) and n.name == '__init__' for n in node.body)
        has_docstring = self._has_docstring(node)
        inheritance_count = len(node.bases)
        line_count = len(self._get_node_source(node, content).split('\n'))

        # Determine pattern type
        if method_count == 0:
            pattern_type = "data_class"
        elif has_init and method_count < 5:
            pattern_type = "simple_class"
        elif inheritance_count > 0:
            pattern_type = "inheritance_class"
        elif method_count > 10:
            pattern_type = "complex_class"
        else:
            pattern_type = "standard_class"

        return {
            'pattern_type': pattern_type,
            'method_count': method_count,
            'has_init': has_init,
            'has_docstring': has_docstring,
            'inheritance_count': inheritance_count,
            'line_count': line_count,
            'confidence': min(1.0, (method_count + (1 if has_init else 0) + (1 if has_docstring else 0)) / 5.0)
        }

    def _check_class_anti_patterns(self, node: ast.ClassDef, content: str) -> Optional[PatternMatch]:
        """Check for class anti-patterns."""
        issues = []

        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        method_count = len(methods)

        # God class (too many methods)
        if method_count > 20:
            issues.append("Class has too many methods (>20) - consider splitting")

        # Class without docstring
        if not self._has_docstring(node):
            issues.append("Class missing docstring")

        # Data class with methods
        if method_count == 0 and len(node.body) > 0:
            non_method_nodes = [n for n in node.body if not isinstance(n, ast.FunctionDef)]
            if len(non_method_nodes) > 5:
                issues.append("Data class has too many attributes - consider using dataclass")

        if issues:
            return PatternMatch(
                pattern=CodePattern(
                    id=f"anti_pattern_class_{hash(str(issues))}",
                    name="Class Anti-Patterns",
                    description="Detected problematic class patterns",
                    category="class",
                    language="python",
                    pattern_type="anti_pattern",
                    template="",
                    variables={},
                    is_anti_pattern=True,
                    anti_pattern_reason="; ".join(issues),
                    alternative_suggestions=[
                        "Split large classes into smaller ones",
                        "Add docstrings to classes",
                        "Use dataclasses for simple data containers"
                    ]
                ),
                confidence=0.8,
                matched_code=self._get_node_source(node, content),
                suggested_replacement="",
                line_number=node.lineno,
                explanation="; ".join(issues)
            )

        return None

    def _learn_loop_patterns(self, tree: ast.AST, content: str, language: str) -> Tuple[List[PatternMatch], List[PatternMatch], List[str]]:
        """Learn loop patterns."""
        patterns = []
        anti_patterns = []
        suggestions = []

        if language != 'python':
            return patterns, anti_patterns, suggestions

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Check for anti-patterns
                anti_pattern_check = self._check_loop_anti_patterns(node, content)
                if anti_pattern_check:
                    anti_patterns.append(anti_pattern_check)
                    suggestions.append(anti_pattern_check.explanation)

        return patterns, anti_patterns, suggestions

    def _check_loop_anti_patterns(self, node: ast.For, content: str) -> Optional[PatternMatch]:
        """Check for loop anti-patterns."""
        issues = []

        # Nested loops (deep nesting)
        nesting_level = self._calculate_nesting_level(node)
        if nesting_level > 3:
            issues.append(f"Deeply nested loops (level {nesting_level})")

        # Loop body too long
        loop_body = self._get_node_source(node, content)
        line_count = len(loop_body.split('\n'))
        if line_count > 20:
            issues.append("Loop body too long (>20 lines)")

        if issues:
            return PatternMatch(
                pattern=CodePattern(
                    id=f"anti_pattern_loop_{hash(str(issues))}",
                    name="Loop Anti-Patterns",
                    description="Detected problematic loop patterns",
                    category="loop",
                    language="python",
                    pattern_type="anti_pattern",
                    template="",
                    variables={},
                    is_anti_pattern=True,
                    anti_pattern_reason="; ".join(issues),
                    alternative_suggestions=[
                        "Extract nested loops into separate functions",
                        "Use list comprehensions for simple transformations",
                        "Consider using itertools for complex iterations"
                    ]
                ),
                confidence=0.8,
                matched_code=self._get_node_source(node, content),
                suggested_replacement="",
                line_number=node.lineno,
                explanation="; ".join(issues)
            )

        return None

    def _learn_error_handling_patterns(self, tree: ast.AST, content: str, language: str) -> Tuple[List[PatternMatch], List[PatternMatch], List[str]]:
        """Learn error handling patterns."""
        patterns = []
        anti_patterns = []
        suggestions = []

        if language != 'python':
            return patterns, anti_patterns, suggestions

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # Check for anti-patterns
                anti_pattern_check = self._check_error_handling_anti_patterns(node, content)
                if anti_pattern_check:
                    anti_patterns.append(anti_pattern_check)
                    suggestions.append(anti_pattern_check.explanation)

        return patterns, anti_patterns, suggestions

    def _check_error_handling_anti_patterns(self, node: ast.Try, content: str) -> Optional[PatternMatch]:
        """Check for error handling anti-patterns."""
        issues = []

        # Bare except
        for handler in node.handlers:
            if isinstance(handler, ast.ExceptHandler) and handler.type is None:
                issues.append("Bare 'except:' clause catches all exceptions")

        # Too broad exception handling
        for handler in node.handlers:
            if isinstance(handler, ast.ExceptHandler) and handler.type:
                if isinstance(handler.type, ast.Name) and handler.type.id == 'Exception':
                    issues.append("Catching base 'Exception' class")

        # No finally block for resource cleanup
        has_finally = node.finalbody is not None
        has_with_statements = any(isinstance(n, ast.With) for n in ast.walk(node))
        if not has_finally and not has_with_statements:
            # Check if there are file operations or other resources
            has_resource_operations = any(
                isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and
                n.func.id in ['open', 'connect', 'socket']
                for n in ast.walk(node)
            )
            if has_resource_operations:
                issues.append("Resource operations without proper cleanup (finally or context manager)")

        if issues:
            return PatternMatch(
                pattern=CodePattern(
                    id=f"anti_pattern_error_{hash(str(issues))}",
                    name="Error Handling Anti-Patterns",
                    description="Detected problematic error handling patterns",
                    category="error_handling",
                    language="python",
                    pattern_type="anti_pattern",
                    template="",
                    variables={},
                    is_anti_pattern=True,
                    anti_pattern_reason="; ".join(issues),
                    alternative_suggestions=[
                        "Catch specific exceptions instead of bare 'except'",
                        "Use context managers (with statements) for resource cleanup",
                        "Avoid catching base Exception class"
                    ]
                ),
                confidence=0.8,
                matched_code=self._get_node_source(node, content),
                suggested_replacement="",
                line_number=node.lineno,
                explanation="; ".join(issues)
            )

        return None

    def _learn_naming_patterns(self, tree: ast.AST, content: str, language: str) -> Tuple[List[PatternMatch], List[PatternMatch], List[str]]:
        """Learn naming convention patterns."""
        patterns = []
        anti_patterns = []
        suggestions = []

        if language != 'python':
            return patterns, anti_patterns, suggestions

        # Analyze variable and function names
        names = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Name, ast.FunctionDef, ast.ClassDef)):
                if hasattr(node, 'name'):
                    names.append(node.name)
                elif hasattr(node, 'id'):
                    names.append(node.id)

        # Check naming conventions
        anti_pattern_check = self._check_naming_anti_patterns(names)
        if anti_pattern_check:
            anti_patterns.append(anti_pattern_check)
            suggestions.append(anti_pattern_check.explanation)

        return patterns, anti_patterns, suggestions

    def _check_naming_anti_patterns(self, names: List[str]) -> Optional[PatternMatch]:
        """Check for naming convention anti-patterns."""
        issues = []

        # Check for inconsistent naming
        snake_case = [n for n in names if re.match(r'^[a-z][a-z0-9_]*_[a-z0-9_]*$', n)]  # Must have underscore
        camel_case = [n for n in names if re.match(r'^[a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*$', n)]  # Must have uppercase
        pascal_case = [n for n in names if re.match(r'^[A-Z][a-zA-Z0-9]*$', n)]
        screaming_snake = [n for n in names if re.match(r'^[A-Z][A-Z0-9_]*_[A-Z0-9_]*$', n)]  # Must have underscore

        # If we have mixed conventions, it might be an issue
        conventions_used = sum([
            1 if snake_case else 0,
            1 if camel_case else 0,
            1 if pascal_case else 0,
            1 if screaming_snake else 0
        ])

        if conventions_used > 2:
            issues.append("Mixed naming conventions detected")

        # Check for single-letter variable names (except common ones)
        single_letter_vars = [n for n in names if len(n) == 1 and n not in ['i', 'j', 'k', 'x', 'y', 'z', '_']]
        if single_letter_vars:
            issues.append(f"Single-letter variable names: {', '.join(single_letter_vars[:3])}")

        if issues:
            return PatternMatch(
                pattern=CodePattern(
                    id=f"anti_pattern_naming_{hash(str(issues))}",
                    name="Naming Convention Anti-Patterns",
                    description="Detected problematic naming patterns",
                    category="naming",
                    language="python",
                    pattern_type="anti_pattern",
                    template="",
                    variables={},
                    is_anti_pattern=True,
                    anti_pattern_reason="; ".join(issues),
                    alternative_suggestions=[
                        "Use consistent naming conventions (snake_case for variables/functions)",
                        "Avoid single-letter variable names except for common loop indices",
                        "Follow PEP 8 naming conventions"
                    ]
                ),
                confidence=0.7,
                matched_code="",  # This applies to the whole file
                suggested_replacement="",
                line_number=1,
                explanation="; ".join(issues)
            )

        return None

    def _learn_style_patterns(self, tree: ast.AST, content: str, language: str) -> Tuple[List[PatternMatch], List[PatternMatch], List[str]]:
        """Learn code style patterns."""
        patterns = []
        anti_patterns = []
        suggestions = []

        if language != 'python':
            return patterns, anti_patterns, suggestions

        # Check line length
        lines = content.split('\n')
        long_lines = [i for i, line in enumerate(lines, 1) if len(line) > 88]  # PEP 8 recommends 79, but 88 is common

        if long_lines:
            anti_patterns.append(PatternMatch(
                pattern=CodePattern(
                    id="anti_pattern_long_lines",
                    name="Long Lines",
                    description="Lines exceed recommended length",
                    category="style",
                    language="python",
                    pattern_type="anti_pattern",
                    template="",
                    variables={},
                    is_anti_pattern=True,
                    anti_pattern_reason=f"{len(long_lines)} lines exceed 88 characters",
                    alternative_suggestions=[
                        "Break long lines using parentheses or backslashes",
                        "Extract complex expressions into variables",
                        "Use shorter variable names where appropriate"
                    ]
                ),
                confidence=0.9,
                matched_code="",  # Applies to multiple lines
                suggested_replacement="",
                line_number=long_lines[0],
                explanation=f"Found {len(long_lines)} lines longer than 88 characters"
            ))

        return patterns, anti_patterns, suggestions

    # Placeholder methods for other pattern types
    def _learn_async_patterns(self, tree: ast.AST, content: str, language: str) -> Tuple[List[PatternMatch], List[PatternMatch], List[str]]:
        return [], [], []

    def _learn_data_structure_patterns(self, tree: ast.AST, content: str, language: str) -> Tuple[List[PatternMatch], List[PatternMatch], List[str]]:
        return [], [], []

    # Helper methods
    def _has_docstring(self, node: ast.AST) -> bool:
        """Check if a node has a docstring."""
        if hasattr(node, 'body') and node.body:
            first_stmt = node.body[0]
            if isinstance(first_stmt, ast.Expr):
                # Handle both old (ast.Str) and new (ast.Constant) AST formats
                ast_str = getattr(ast, 'Str', None)
                if ast_str and isinstance(first_stmt.value, ast_str):
                    return True
                # Try new format (Python >= 3.8)
                if isinstance(first_stmt.value, ast.Constant) and isinstance(first_stmt.value.value, str):
                    return True
        return False

    def _has_type_hints(self, node: ast.FunctionDef) -> bool:
        """Check if a function has type hints."""
        has_arg_hints = any(arg.annotation for arg in node.args.args)
        has_return_hint = node.returns is not None
        return has_arg_hints or has_return_hint

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a node."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp) and len(child.values) > 1:
                complexity += len(child.values) - 1

        return complexity

    def _calculate_nesting_level(self, node: ast.AST, current_level: int = 0) -> int:
        """Calculate nesting level of a node."""
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

    def _file_modified_time(self, file_path: str) -> float:
        """Get file modification time."""
        try:
            return os.path.getmtime(file_path)
        except:
            return 0.0

    def _calculate_code_score(self, patterns: List[PatternMatch], anti_patterns: List[PatternMatch]) -> float:
        """Calculate overall code quality score."""
        pattern_score = len(patterns) * 0.1  # Positive patterns add points
        anti_pattern_penalty = len(anti_patterns) * 0.2  # Anti-patterns subtract points

        # Base score of 50, adjusted by patterns (scale to 0-100)
        score = 50.0 + (pattern_score * 100) - (anti_pattern_penalty * 100)

        # Clamp between 0 and 100
        return max(0.0, min(100.0, score))

    def _create_function_template(self, node: ast.FunctionDef, content: str) -> str:
        """Create a template from function definition."""
        # This is a simplified template creation
        # In a real implementation, this would be more sophisticated
        source = self._get_node_source(node, content)
        # Replace specific names with placeholders
        template = re.sub(r'\b' + re.escape(node.name) + r'\b', '{{function_name}}', source)

        # Replace argument names
        for arg in node.args.args:
            template = re.sub(r'\b' + re.escape(arg.arg) + r'\b', '{{' + arg.arg + '}}', template)

        return template

    def _extract_function_variables(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Extract variable information from function."""
        variables = {}

        # Function name
        variables['function_name'] = node.name

        # Arguments
        for arg in node.args.args:
            variables[arg.arg] = {
                'type': 'argument',
                'annotation': str(arg.annotation) if arg.annotation else None
            }

        return variables

    def _create_class_pattern(self, pattern_info: Dict[str, Any], node: ast.ClassDef, content: str) -> Optional[CodePattern]:
        """Create a pattern from class analysis."""
        pattern_id = f"class_{pattern_info['pattern_type']}_{hash(self._get_node_source(node, content))}"

        if pattern_id in self.patterns:
            return None

        template = self._create_class_template(node, content)

        pattern = CodePattern(
            id=pattern_id,
            name=f"{pattern_info['pattern_type'].replace('_', ' ').title()} Class",
            description=f"A {pattern_info['pattern_type']} class pattern",
            category="class",
            language="python",
            pattern_type="structural",
            template=template,
            variables=self._extract_class_variables(node),
            examples=[self._get_node_source(node, content)]
        )

        self.patterns[pattern_id] = pattern
        return pattern

    def _create_class_template(self, node: ast.ClassDef, content: str) -> str:
        """Create a template from class definition."""
        source = self._get_node_source(node, content)
        template = re.sub(r'\b' + re.escape(node.name) + r'\b', '{{class_name}}', source)
        return template

    def _extract_class_variables(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Extract variable information from class."""
        variables = {'class_name': node.name}

        # Methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                variables[item.name] = {
                    'type': 'method',
                    'args': [arg.arg for arg in item.args.args]
                }

        return variables

    def learn_from_files(self, file_paths: List[str]) -> Dict[str, PatternAnalysis]:
        """Learn patterns from multiple files."""
        results = {}

        for file_path in file_paths:
            try:
                analysis = self.analyze_file(file_path)
                results[file_path] = analysis

                # Update pattern usage
                for pattern_match in analysis.patterns_found:
                    pattern = pattern_match.pattern
                    pattern.usage_count += 1
                    pattern.last_used = time.time()
                    pattern.source_files.append(file_path)

            except Exception as e:
                print(f"Error learning from {file_path}: {e}")

        # Save updated patterns
        self._save_patterns()

        return results

    def get_patterns(self, category: Optional[str] = None, language: Optional[str] = None) -> List[CodePattern]:
        """Get learned patterns, optionally filtered."""
        patterns = list(self.patterns.values())

        if category:
            patterns = [p for p in patterns if p.category == category]

        if language:
            patterns = [p for p in patterns if p.language == language]

        # Sort by usage and confidence
        patterns.sort(key=lambda p: (p.usage_count, p.confidence), reverse=True)

        return patterns

    def get_anti_patterns(self) -> List[CodePattern]:
        """Get anti-patterns."""
        return [p for p in self.patterns.values() if p.is_anti_pattern]

    def export_patterns(self, file_path: str):
        """Export patterns to a file."""
        patterns_data = [asdict(p) for p in self.patterns.values()]
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(patterns_data, f, indent=2, ensure_ascii=False)

    def import_patterns(self, file_path: str):
        """Import patterns from a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            patterns_data = json.load(f)

        for pattern_data in patterns_data:
            pattern = CodePattern(**pattern_data)
            self.patterns[pattern.id] = pattern

        self._save_patterns()