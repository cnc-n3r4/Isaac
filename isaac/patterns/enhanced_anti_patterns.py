"""
Enhanced Anti-Pattern Detection - Advanced code quality analysis
Phase 3.4.5: Sophisticated anti-pattern detection with detailed suggestions
"""

import ast
import re
import json
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
import time
from collections import defaultdict, Counter
import inspect


@dataclass
class AntiPatternRule:
    """A rule for detecting anti-patterns."""
    id: str
    name: str
    description: str
    category: str  # function, class, module, performance, security, etc.
    severity: str  # critical, high, medium, low, info
    language: str = "python"

    # Detection criteria
    condition_checker: Callable = None  # Function to check if rule applies
    pattern_matcher: Optional[str] = None  # Regex pattern to match

    # Suggestions and fixes
    suggestions: List[str] = field(default_factory=list)
    auto_fix_available: bool = False
    fix_function: Optional[Callable] = None

    # Metadata
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)  # Links to documentation


@dataclass
class AntiPatternDetection:
    """Result of anti-pattern detection."""
    rule_id: str
    rule_name: str
    description: str
    severity: str
    category: str

    # Location info
    file_path: str
    line_number: int
    matched_code: str
    column_offset: int = 0
    end_line_number: Optional[int] = None

    # Code context
    context_lines: List[str] = field(default_factory=list)

    # Suggestions and fixes
    suggestions: List[str] = field(default_factory=list)
    can_auto_fix: bool = False
    auto_fix_code: Optional[str] = None

    # Additional metadata
    confidence: float = 1.0
    tags: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


@dataclass
class CodeQualityReport:
    """Comprehensive code quality report."""
    file_path: str
    analyzed_at: float = field(default_factory=time.time)

    # Summary stats
    total_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_modules: int = 0

    # Anti-patterns found
    anti_patterns: List[AntiPatternDetection] = field(default_factory=list)

    # Quality metrics
    quality_score: float = 0.0
    maintainability_index: float = 0.0
    complexity_score: float = 0.0

    # Category breakdown
    issues_by_category: Dict[str, int] = field(default_factory=dict)
    issues_by_severity: Dict[str, int] = field(default_factory=dict)

    # Auto-fixable issues
    auto_fixable_count: int = 0


class EnhancedAntiPatternDetector:
    """Enhanced anti-pattern detection with comprehensive analysis."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the enhanced anti-pattern detector."""
        self.config = config or {}
        self.rules: Dict[str, AntiPatternRule] = {}

        # Load built-in rules
        self._load_builtin_rules()

        # Custom rules from config
        self._load_custom_rules()

        # Analysis settings
        self.max_function_length = self.config.get('max_function_length', 50)
        self.max_class_length = self.config.get('max_class_length', 300)
        self.max_parameters = self.config.get('max_parameters', 7)
        self.max_complexity = self.config.get('max_complexity', 15)
        self.min_docstring_length = self.config.get('min_docstring_length', 10)

    def analyze_file(self, file_path: str, content: Optional[str] = None) -> CodeQualityReport:
        """Analyze a file for anti-patterns."""
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                return CodeQualityReport(file_path=file_path, anti_patterns=[
                    AntiPatternDetection(
                        rule_id="file_read_error",
                        rule_name="File Read Error",
                        description=f"Could not read file: {e}",
                        severity="critical",
                        category="file",
                        file_path=file_path,
                        line_number=1,
                        matched_code="",
                        suggestions=["Check file permissions and encoding"]
                    )
                ])

        # Parse AST
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            return CodeQualityReport(file_path=file_path, anti_patterns=[
                AntiPatternDetection(
                    rule_id="syntax_error",
                    rule_name="Syntax Error",
                    description=f"Syntax error in file: {e.msg}",
                    severity="critical",
                    category="syntax",
                    file_path=file_path,
                    line_number=e.lineno or 1,
                    matched_code=e.text or "",
                    suggestions=["Fix the syntax error before analysis"]
                )
            ])

        # Initialize report
        report = CodeQualityReport(file_path=file_path)
        lines = content.split('\n')
        report.total_lines = len(lines)

        # Analyze different AST node types
        anti_patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                report.total_functions += 1
                anti_patterns.extend(self._analyze_function(node, content, lines))
            elif isinstance(node, ast.ClassDef):
                report.total_classes += 1
                anti_patterns.extend(self._analyze_class(node, content, lines))
            elif isinstance(node, ast.Module):
                report.total_modules += 1
                anti_patterns.extend(self._analyze_module(node, content, lines))

        # Apply general rules
        anti_patterns.extend(self._apply_general_rules(tree, content, lines))

        # Filter and deduplicate
        report.anti_patterns = self._deduplicate_anti_patterns(anti_patterns)

        # Calculate quality metrics
        report.quality_score = self._calculate_quality_score(report)
        report.maintainability_index = self._calculate_maintainability_index(report)
        report.complexity_score = self._calculate_complexity_score(tree)

        # Categorize issues
        for ap in report.anti_patterns:
            report.issues_by_category[ap.category] = report.issues_by_category.get(ap.category, 0) + 1
            report.issues_by_severity[ap.severity] = report.issues_by_severity.get(ap.severity, 0) + 1
            if ap.can_auto_fix:
                report.auto_fixable_count += 1

        return report

    def analyze_code_snippet(self, code: str, language: str = "python") -> List[AntiPatternDetection]:
        """Analyze a code snippet for anti-patterns."""
        if language != "python":
            return []  # For now, only support Python

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        lines = code.split('\n')
        anti_patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                anti_patterns.extend(self._analyze_function(node, code, lines))
            elif isinstance(node, ast.ClassDef):
                anti_patterns.extend(self._analyze_class(node, code, lines))

        return self._deduplicate_anti_patterns(anti_patterns)

    def get_rule(self, rule_id: str) -> Optional[AntiPatternRule]:
        """Get a specific rule by ID."""
        return self.rules.get(rule_id)

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False

    def add_custom_rule(self, rule: AntiPatternRule):
        """Add a custom rule."""
        self.rules[rule.id] = rule

    def get_available_rules(self) -> List[AntiPatternRule]:
        """Get all available rules."""
        return list(self.rules.values())

    def generate_fix_script(self, report: CodeQualityReport) -> str:
        """Generate a script to auto-fix issues."""
        fixable_issues = [ap for ap in report.anti_patterns if ap.can_auto_fix]

        if not fixable_issues:
            return "# No auto-fixable issues found"

        script_lines = [
            "#!/usr/bin/env python3",
            '"""Auto-fix script generated by Isaac Anti-Pattern Detector"""',
            "import re",
            "import sys",
            "from pathlib import Path",
            "",
            f'FILE_PATH = "{report.file_path}"',
            "",
            "def apply_fixes():",
            '    with open(FILE_PATH, "r", encoding="utf-8") as f:',
            "        content = f.read()",
            "",
            "    original_content = content",
            ""
        ]

        for i, issue in enumerate(fixable_issues):
            if issue.auto_fix_code:
                script_lines.extend([
                    f"    # Fix {i+1}: {issue.rule_name}",
                    f"    {issue.auto_fix_code}",
                    ""
                ])

        script_lines.extend([
            '    if content != original_content:',
            '        with open(FILE_PATH, "w", encoding="utf-8") as f:',
            '            f.write(content)',
            '        print(f"Applied {len(fixable_issues)} fixes to {FILE_PATH}")',
            '    else:',
            '        print("No changes needed")',
            "",
            "if __name__ == '__main__':",
            "    apply_fixes()"
        ])

        return "\n".join(script_lines)

    def _analyze_function(self, node: ast.FunctionDef, content: str, lines: List[str]) -> List[AntiPatternDetection]:
        """Analyze a function for anti-patterns."""
        anti_patterns = []

        # Check various function-related rules
        for rule_id, rule in self.rules.items():
            if not rule.enabled or rule.category not in ['function', 'general']:
                continue

            if rule.condition_checker:
                try:
                    result = rule.condition_checker(node, content, lines)
                    if result:
                        detection = self._create_detection_from_result(rule, result, node, content, lines)
                        if detection:
                            anti_patterns.append(detection)
                except Exception as e:
                    print(f"Error checking rule {rule_id}: {e}")

        return anti_patterns

    def _analyze_class(self, node: ast.ClassDef, content: str, lines: List[str]) -> List[AntiPatternDetection]:
        """Analyze a class for anti-patterns."""
        anti_patterns = []

        # Check various class-related rules
        for rule_id, rule in self.rules.items():
            if not rule.enabled or rule.category not in ['class', 'general']:
                continue

            if rule.condition_checker:
                try:
                    result = rule.condition_checker(node, content, lines)
                    if result:
                        detection = self._create_detection_from_result(rule, result, node, content, lines)
                        if detection:
                            anti_patterns.append(detection)
                except Exception as e:
                    print(f"Error checking rule {rule_id}: {e}")

        return anti_patterns

    def _analyze_module(self, node: ast.Module, content: str, lines: List[str]) -> List[AntiPatternDetection]:
        """Analyze a module for anti-patterns."""
        anti_patterns = []

        # Check module-level rules
        for rule_id, rule in self.rules.items():
            if not rule.enabled or rule.category != 'module':
                continue

            if rule.condition_checker:
                try:
                    result = rule.condition_checker(node, content, lines)
                    if result:
                        detection = AntiPatternDetection(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            description=rule.description,
                            severity=rule.severity,
                            category=rule.category,
                            file_path="",  # Will be set by caller
                            line_number=result.get('line_number', 1),
                            matched_code=result.get('matched_code', ''),
                            suggestions=rule.suggestions.copy(),
                            can_auto_fix=rule.auto_fix_available,
                            confidence=result.get('confidence', 1.0)
                        )
                        anti_patterns.append(detection)
                except Exception as e:
                    print(f"Error checking rule {rule_id}: {e}")

        return anti_patterns

    def _apply_general_rules(self, tree: ast.AST, content: str, lines: List[str]) -> List[AntiPatternDetection]:
        """Apply general rules that don't fit specific node types."""
        anti_patterns = []

        # Check for imports at wrong locations
        for rule_id, rule in self.rules.items():
            if rule_id == 'imports_not_at_top' and rule.enabled:
                result = self._check_imports_not_at_top(tree, content, lines)
                if result:
                    detection = AntiPatternDetection(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        description=rule.description,
                        severity=rule.severity,
                        category=rule.category,
                        file_path="",
                        line_number=result['line_number'],
                        matched_code=result['matched_code'],
                        suggestions=rule.suggestions.copy(),
                        can_auto_fix=rule.auto_fix_available
                    )
                    anti_patterns.append(detection)

        return anti_patterns

    def _create_detection_from_result(self, rule: AntiPatternRule, result: Dict[str, Any],
                                    node: ast.AST, content: str, lines: List[str]) -> Optional[AntiPatternDetection]:
        """Create an AntiPatternDetection from a rule check result."""
        if not result.get('triggered', False):
            return None

        # Get code context
        start_line = getattr(node, 'lineno', 1)
        end_line = getattr(node, 'end_lineno', start_line)

        matched_code = '\n'.join(lines[start_line-1:end_line]) if start_line <= len(lines) else ""

        # Get context lines
        context_start = max(1, start_line - 2)
        context_end = min(len(lines), end_line + 2)
        context_lines = lines[context_start-1:context_end]

        return AntiPatternDetection(
            rule_id=rule.id,
            rule_name=rule.name,
            description=result.get('description', rule.description),
            severity=rule.severity,
            category=rule.category,
            file_path="",
            line_number=start_line,
            end_line_number=end_line,
            matched_code=matched_code,
            context_lines=context_lines,
            suggestions=result.get('suggestions', rule.suggestions),
            can_auto_fix=rule.auto_fix_available,
            confidence=result.get('confidence', 1.0),
            tags=rule.tags.copy(),
            references=rule.references.copy()
        )

    def _deduplicate_anti_patterns(self, anti_patterns: List[AntiPatternDetection]) -> List[AntiPatternDetection]:
        """Remove duplicate anti-pattern detections."""
        seen = set()
        deduplicated = []

        for ap in anti_patterns:
            key = (ap.rule_id, ap.line_number, ap.matched_code[:50])  # Use first 50 chars as fingerprint
            if key not in seen:
                seen.add(key)
                deduplicated.append(ap)

        return deduplicated

    def _calculate_quality_score(self, report: CodeQualityReport) -> float:
        """Calculate overall quality score (0-100)."""
        if not report.anti_patterns:
            return 100.0

        # Base score starts at 100
        score = 100.0

        # Deduct points based on severity
        severity_penalties = {
            'critical': 20,
            'high': 10,
            'medium': 5,
            'low': 2,
            'info': 0.5
        }

        for ap in report.anti_patterns:
            penalty = severity_penalties.get(ap.severity, 1)
            score -= penalty

        # Factor in code size (larger codebases can have more issues)
        size_factor = min(1.0, report.total_lines / 1000.0)
        score *= (1.0 - size_factor * 0.1)  # Up to 10% penalty for large files

        return max(0.0, score)

    def _calculate_maintainability_index(self, report: CodeQualityReport) -> float:
        """Calculate maintainability index (0-100)."""
        # Simplified maintainability calculation
        base_score = 100.0

        # Factors that reduce maintainability
        factors = {
            'function_length': len([ap for ap in report.anti_patterns if 'long' in ap.rule_name.lower()]),
            'complexity': len([ap for ap in report.anti_patterns if 'complex' in ap.rule_name.lower()]),
            'documentation': len([ap for ap in report.anti_patterns if 'docstring' in ap.rule_name.lower()]),
            'structure': len([ap for ap in report.anti_patterns if 'structure' in ap.rule_name.lower()])
        }

        for factor, count in factors.items():
            base_score -= count * 5  # 5 points per issue

        return max(0.0, base_score)

    def _calculate_complexity_score(self, tree: ast.AST) -> float:
        """Calculate code complexity score."""
        complexity = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def _load_builtin_rules(self):
        """Load built-in anti-pattern detection rules."""
        self.rules.update({
            'too_many_parameters': AntiPatternRule(
                id='too_many_parameters',
                name='Too Many Parameters',
                description='Function has too many parameters',
                category='function',
                severity='medium',
                condition_checker=self._check_too_many_parameters,
                suggestions=[
                    'Consider using a configuration object or data class',
                    'Break function into smaller functions with fewer parameters',
                    'Use *args or **kwargs if appropriate'
                ],
                tags=['parameters', 'maintainability']
            ),

            'function_too_long': AntiPatternRule(
                id='function_too_long',
                name='Function Too Long',
                description='Function exceeds maximum recommended length',
                category='function',
                severity='medium',
                condition_checker=self._check_function_too_long,
                suggestions=[
                    'Break function into smaller, focused functions',
                    'Extract repeated code into helper functions',
                    'Consider using early returns to reduce nesting'
                ],
                tags=['length', 'maintainability']
            ),

            'missing_docstring': AntiPatternRule(
                id='missing_docstring',
                name='Missing Docstring',
                description='Function or class missing documentation',
                category='function',
                severity='low',
                condition_checker=self._check_missing_docstring,
                suggestions=[
                    'Add a docstring describing the function purpose',
                    'Include parameter descriptions and return value',
                    'Follow docstring conventions (Google, NumPy, etc.)'
                ],
                auto_fix_available=True,
                fix_function=self._add_docstring_fix,
                tags=['documentation', 'readability']
            ),

            'high_complexity': AntiPatternRule(
                id='high_complexity',
                name='High Cyclomatic Complexity',
                description='Function has high cyclomatic complexity',
                category='function',
                severity='high',
                condition_checker=self._check_high_complexity,
                suggestions=[
                    'Break complex function into smaller functions',
                    'Use early returns to reduce nesting',
                    'Replace complex conditionals with polymorphism',
                    'Extract decision logic into separate functions'
                ],
                tags=['complexity', 'maintainability']
            ),

            'missing_type_hints': AntiPatternRule(
                id='missing_type_hints',
                name='Missing Type Hints',
                description='Function parameters and return lack type hints',
                category='function',
                severity='low',
                condition_checker=self._check_missing_type_hints,
                suggestions=[
                    'Add type hints to parameters and return type',
                    'Use Union types for multiple possible types',
                    'Consider Optional for nullable parameters'
                ],
                tags=['typing', 'maintainability']
            ),

            'god_class': AntiPatternRule(
                id='god_class',
                name='God Class',
                description='Class has too many responsibilities',
                category='class',
                severity='high',
                condition_checker=self._check_god_class,
                suggestions=[
                    'Split class into smaller, focused classes',
                    'Extract related methods into separate classes',
                    'Use composition over inheritance',
                    'Apply Single Responsibility Principle'
                ],
                tags=['structure', 'maintainability']
            ),

            'imports_not_at_top': AntiPatternRule(
                id='imports_not_at_top',
                name='Imports Not At Top',
                description='Import statements found outside top of file',
                category='module',
                severity='low',
                suggestions=[
                    'Move all imports to the top of the file',
                    'Group imports: standard library, third-party, local',
                    'Use blank lines to separate import groups'
                ],
                tags=['imports', 'style']
            ),

            'unused_import': AntiPatternRule(
                id='unused_import',
                name='Unused Import',
                description='Imported module is never used',
                category='module',
                severity='low',
                condition_checker=self._check_unused_imports,
                suggestions=[
                    'Remove unused import statements',
                    'Check if import is needed for side effects only'
                ],
                auto_fix_available=True,
                tags=['imports', 'cleanup']
            ),

            'mutable_default_args': AntiPatternRule(
                id='mutable_default_args',
                name='Mutable Default Arguments',
                description='Function uses mutable objects as default arguments',
                category='function',
                severity='high',
                condition_checker=self._check_mutable_defaults,
                suggestions=[
                    'Use None as default and create mutable object inside function',
                    'Use immutable defaults when possible',
                    'Document the behavior clearly if intentional'
                ],
                auto_fix_available=True,
                fix_function=self._fix_mutable_defaults,
                tags=['bugs', 'gotchas']
            ),

            'bare_except': AntiPatternRule(
                id='bare_except',
                name='Bare Except Clause',
                description='Except clause catches all exceptions',
                category='function',
                severity='medium',
                condition_checker=self._check_bare_except,
                suggestions=[
                    'Catch specific exceptions instead of bare except',
                    'Use multiple except blocks for different exception types',
                    'At minimum, catch Exception instead of bare except'
                ],
                tags=['error_handling', 'robustness']
            )
        })

    def _load_custom_rules(self):
        """Load custom rules from configuration."""
        custom_rules = self.config.get('custom_rules', [])
        for rule_config in custom_rules:
            rule = AntiPatternRule(**rule_config)
            self.rules[rule.id] = rule

    # Rule checker functions
    def _check_too_many_parameters(self, node: ast.FunctionDef, content: str, lines: List[str]) -> Dict[str, Any]:
        """Check if function has too many parameters."""
        param_count = len(node.args.args)
        if param_count > self.max_parameters:
            return {
                'triggered': True,
                'description': f'Function has {param_count} parameters (max recommended: {self.max_parameters})',
                'confidence': min(1.0, param_count / (self.max_parameters * 2)),
                'suggestions': [
                    f'Consider reducing parameters (current: {param_count})',
                    'Use a configuration object or data class',
                    'Break function into smaller functions'
                ]
            }
        return {'triggered': False}

    def _check_function_too_long(self, node: ast.FunctionDef, content: str, lines: List[str]) -> Dict[str, Any]:
        """Check if function is too long."""
        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', start_line)
        length = end_line - start_line + 1

        if length > self.max_function_length:
            return {
                'triggered': True,
                'description': f'Function is {length} lines long (max recommended: {self.max_function_length})',
                'confidence': min(1.0, length / (self.max_function_length * 2)),
                'suggestions': [
                    f'Break into smaller functions (current: {length} lines)',
                    'Extract repeated code into helpers',
                    'Use early returns to reduce nesting'
                ]
            }
        return {'triggered': False}

    def _check_missing_docstring(self, node: ast.AST, content: str, lines: List[str]) -> Dict[str, Any]:
        """Check if function/class is missing docstring."""
        if not hasattr(node, 'body') or not node.body:
            return {'triggered': False}

        first_stmt = node.body[0]
        has_docstring = isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Str)

        if not has_docstring:
            node_type = 'function' if isinstance(node, ast.FunctionDef) else 'class'
            return {
                'triggered': True,
                'description': f'{node_type.capitalize()} missing docstring',
                'confidence': 0.9,
                'suggestions': [
                    f'Add a docstring to describe the {node_type} purpose',
                    'Include parameter descriptions and return values',
                    'Follow consistent docstring format'
                ]
            }
        return {'triggered': False}

    def _check_high_complexity(self, node: ast.FunctionDef, content: str, lines: List[str]) -> Dict[str, Any]:
        """Check if function has high cyclomatic complexity."""
        complexity = self._calculate_node_complexity(node)

        if complexity > self.max_complexity:
            return {
                'triggered': True,
                'description': f'Function has cyclomatic complexity of {complexity} (max recommended: {self.max_complexity})',
                'confidence': min(1.0, complexity / (self.max_complexity * 2)),
                'suggestions': [
                    f'Reduce complexity (current: {complexity})',
                    'Break into smaller functions',
                    'Use early returns',
                    'Replace complex conditionals with polymorphism'
                ]
            }
        return {'triggered': False}

    def _check_missing_type_hints(self, node: ast.FunctionDef, content: str, lines: List[str]) -> Dict[str, Any]:
        """Check if function is missing type hints."""
        has_type_hints = False

        # Check return annotation
        if node.returns:
            has_type_hints = True

        # Check parameter annotations
        for arg in node.args.args:
            if arg.annotation:
                has_type_hints = True
                break

        if not has_type_hints:
            return {
                'triggered': True,
                'description': 'Function missing type hints for parameters and/or return type',
                'confidence': 0.8,
                'suggestions': [
                    'Add type hints to all parameters',
                    'Add return type annotation',
                    'Use Union for multiple types, Optional for nullable'
                ]
            }
        return {'triggered': False}

    def _check_god_class(self, node: ast.ClassDef, content: str, lines: List[str]) -> Dict[str, Any]:
        """Check if class is a "God Class" with too many responsibilities."""
        method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
        total_lines = getattr(node, 'end_lineno', node.lineno) - node.lineno + 1

        # Simple heuristics for god class detection
        if method_count > 20 or total_lines > self.max_class_length:
            issues = []
            if method_count > 20:
                issues.append(f'{method_count} methods')
            if total_lines > self.max_class_length:
                issues.append(f'{total_lines} lines')

            return {
                'triggered': True,
                'description': f'Class appears to be a "God Class" ({", ".join(issues)})',
                'confidence': 0.7,
                'suggestions': [
                    'Split class into smaller, focused classes',
                    'Extract related methods into separate classes',
                    'Apply Single Responsibility Principle'
                ]
            }
        return {'triggered': False}

    def _check_unused_imports(self, node: ast.Module, content: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Check for unused imports."""
        # This is a simplified check - a full implementation would need symbol analysis
        # For now, return empty list as this requires more complex analysis
        return []

    def _check_mutable_defaults(self, node: ast.FunctionDef, content: str, lines: List[str]) -> Dict[str, Any]:
        """Check for mutable default arguments."""
        for arg in node.args.defaults:
            if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                return {
                    'triggered': True,
                    'description': 'Function uses mutable object as default argument',
                    'confidence': 0.95,
                    'suggestions': [
                        'Use None as default and create mutable object inside function',
                        'Use immutable defaults when possible'
                    ]
                }
        return {'triggered': False}

    def _check_bare_except(self, node: ast.FunctionDef, content: str, lines: List[str]) -> Dict[str, Any]:
        """Check for bare except clauses."""
        for child in ast.walk(node):
            if isinstance(child, ast.ExceptHandler) and child.type is None:
                return {
                    'triggered': True,
                    'description': 'Bare except clause catches all exceptions',
                    'confidence': 0.9,
                    'suggestions': [
                        'Catch specific exceptions instead',
                        'Use multiple except blocks for different types',
                        'At minimum, catch Exception instead of bare except'
                    ]
                }
        return {'triggered': False}

    def _check_imports_not_at_top(self, tree: ast.AST, content: str, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Check for imports not at the top of the file."""
        imports_found = False
        non_import_found = False

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if non_import_found:
                    return {
                        'line_number': node.lineno,
                        'matched_code': lines[node.lineno - 1].strip(),
                        'description': 'Import statement found after non-import code'
                    }
                imports_found = True
            elif not isinstance(node, (ast.Expr, ast.Constant)) and not (hasattr(ast, 'Str') and isinstance(node, ast.Str)):  # Skip docstrings and strings
                non_import_found = True

        return None

    def _calculate_node_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a node."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.And):
                complexity += 1
            elif isinstance(child, ast.Or):
                complexity += 1

        return complexity

    def _add_docstring_fix(self, detection: AntiPatternDetection) -> str:
        """Generate auto-fix code for missing docstring."""
        # This would generate code to add a docstring
        # For now, return a placeholder
        return f'# TODO: Add docstring at line {detection.line_number}'

    def _fix_mutable_defaults(self, detection: AntiPatternDetection) -> str:
        """Generate auto-fix code for mutable defaults."""
        # This would generate code to fix mutable defaults
        # For now, return a placeholder
        return f'# TODO: Fix mutable defaults at line {detection.line_number}'