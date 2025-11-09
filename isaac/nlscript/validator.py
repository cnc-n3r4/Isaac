"""
Script Validator

Validates bash scripts for safety and correctness.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import re
import subprocess
import tempfile


class ScriptValidator:
    """Validates bash scripts before execution."""

    def __init__(self, ai_router=None):
        """
        Initialize validator.

        Args:
            ai_router: AIRouter instance for AI-powered validation
        """
        self.ai_router = ai_router
        self.dangerous_patterns = self._init_dangerous_patterns()

    def validate(self, script: str, strict: bool = False) -> Dict[str, Any]:
        """
        Validate a bash script.

        Args:
            script: The bash script to validate
            strict: If True, apply stricter validation rules

        Returns:
            Dictionary with:
                - valid: Whether the script is valid
                - errors: List of errors
                - warnings: List of warnings
                - suggestions: List of improvement suggestions
                - safety_score: Safety score (0-100)
                - shellcheck_results: Results from shellcheck if available
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'safety_score': 100,
            'shellcheck_results': None
        }

        # Syntax validation
        syntax_errors = self._validate_syntax(script)
        if syntax_errors:
            result['errors'].extend(syntax_errors)
            result['valid'] = False

        # Safety checks
        safety_issues = self._check_safety(script)
        result['warnings'].extend(safety_issues)

        # Calculate safety score
        result['safety_score'] = max(0, 100 - len(safety_issues) * 10)

        # Best practices
        suggestions = self._check_best_practices(script)
        result['suggestions'].extend(suggestions)

        # Shellcheck if available
        shellcheck_results = self._run_shellcheck(script)
        if shellcheck_results:
            result['shellcheck_results'] = shellcheck_results
            # Add shellcheck errors to our errors list
            if shellcheck_results.get('errors'):
                result['errors'].extend(shellcheck_results['errors'])
                result['valid'] = False

        # Strict mode checks
        if strict:
            strict_issues = self._strict_validation(script)
            result['warnings'].extend(strict_issues)
            if strict_issues:
                result['valid'] = False

        return result

    def validate_file(self, file_path: Path, strict: bool = False) -> Dict[str, Any]:
        """
        Validate a bash script file.

        Args:
            file_path: Path to the script file
            strict: If True, apply stricter validation rules

        Returns:
            Validation result dictionary
        """
        with open(file_path, 'r') as f:
            script = f.read()

        result = self.validate(script, strict)
        result['file'] = str(file_path)
        return result

    def is_safe_to_run(self, script: str) -> bool:
        """
        Quick safety check.

        Args:
            script: The bash script to check

        Returns:
            True if the script appears safe to run
        """
        result = self.validate(script)
        return result['valid'] and result['safety_score'] >= 50

    def _validate_syntax(self, script: str) -> List[str]:
        """Validate bash syntax."""
        errors = []

        # Try to validate with bash -n
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script)
                temp_file = f.name

            result = subprocess.run(
                ['bash', '-n', temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                errors.append(f"Syntax error: {result.stderr.strip()}")

            Path(temp_file).unlink()

        except subprocess.TimeoutExpired:
            errors.append("Validation timed out")
        except Exception:
            # Bash might not be available in some environments
            pass

        # Basic pattern-based checks
        if not script.strip():
            errors.append("Script is empty")

        # Check for unmatched quotes
        single_quotes = script.count("'") - script.count("\\'")
        double_quotes = script.count('"') - script.count('\\"')

        if single_quotes % 2 != 0:
            errors.append("Unmatched single quote")
        if double_quotes % 2 != 0:
            errors.append("Unmatched double quote")

        # Check for unmatched braces
        open_braces = script.count('{')
        close_braces = script.count('}')
        if open_braces != close_braces:
            errors.append(f"Unmatched braces: {open_braces} open, {close_braces} close")

        return errors

    def _check_safety(self, script: str) -> List[str]:
        """Check for dangerous patterns."""
        warnings = []

        for pattern, description, severity in self.dangerous_patterns:
            if re.search(pattern, script, re.MULTILINE):
                prefix = "🚨" if severity == 'critical' else "⚠️ "
                warnings.append(f"{prefix} {description}")

        return warnings

    def _check_best_practices(self, script: str) -> List[str]:
        """Check for best practice violations."""
        suggestions = []

        lines = script.split('\n')

        # Check for shebang
        if lines and not lines[0].startswith('#!'):
            suggestions.append("💡 Add shebang line (#!/bin/bash)")

        # Check for error handling
        if 'set -e' not in script:
            suggestions.append("💡 Consider adding 'set -e' to exit on errors")

        if 'set -u' not in script:
            suggestions.append("💡 Consider adding 'set -u' to catch undefined variables")

        # Check for proper variable quoting
        unquoted_vars = re.findall(r'\$(\w+)(?![}"\'])', script)
        if unquoted_vars:
            suggestions.append(f"💡 Consider quoting variables: {', '.join(set(unquoted_vars[:3]))}")

        # Check for command substitution style
        if re.search(r'`[^`]+`', script):
            suggestions.append("💡 Use $() instead of backticks for command substitution")

        # Check for error checking after important commands
        critical_commands = ['curl', 'wget', 'git', 'docker', 'npm', 'pip']
        for cmd in critical_commands:
            if re.search(rf'\b{cmd}\b', script) and '||' not in script and 'set -e' not in script:
                suggestions.append(f"💡 Add error checking after '{cmd}' commands")
                break

        # Check for hardcoded paths
        if re.search(r'/home/\w+', script):
            suggestions.append("💡 Avoid hardcoding home directories, use $HOME or ~")

        return suggestions

    def _strict_validation(self, script: str) -> List[str]:
        """Strict validation rules."""
        issues = []

        # Must have shebang
        if not script.startswith('#!'):
            issues.append("Strict: Missing shebang")

        # Must have set -e
        if 'set -e' not in script:
            issues.append("Strict: Missing 'set -e'")

        # Must have set -u
        if 'set -u' not in script:
            issues.append("Strict: Missing 'set -u'")

        # No eval or exec
        if re.search(r'\b(eval|exec)\b', script):
            issues.append("Strict: 'eval' or 'exec' not allowed in strict mode")

        # All functions must have error handling
        functions = re.findall(r'^\s*(\w+)\s*\(\)', script, re.MULTILINE)
        for func in functions:
            # Very basic check - should be improved
            if func not in ['usage', 'help']:
                # In strict mode, we want explicit error handling
                pass

        return issues

    def _run_shellcheck(self, script: str) -> Optional[Dict[str, Any]]:
        """Run shellcheck if available."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script)
                temp_file = f.name

            result = subprocess.run(
                ['shellcheck', '-f', 'json', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )

            Path(temp_file).unlink()

            if result.stdout:
                import json
                issues = json.loads(result.stdout)

                return {
                    'errors': [
                        f"Line {issue['line']}: {issue['message']}"
                        for issue in issues
                        if issue['level'] == 'error'
                    ],
                    'warnings': [
                        f"Line {issue['line']}: {issue['message']}"
                        for issue in issues
                        if issue['level'] == 'warning'
                    ],
                    'info': [
                        f"Line {issue['line']}: {issue['message']}"
                        for issue in issues
                        if issue['level'] == 'info'
                    ]
                }

        except FileNotFoundError:
            # shellcheck not installed
            pass
        except Exception:
            pass

        return None

    def _init_dangerous_patterns(self) -> List[tuple]:
        """Initialize dangerous pattern list."""
        return [
            # Critical patterns
            (r'rm\s+-rf\s+/', 'Recursive deletion from root directory', 'critical'),
            (r'rm\s+-rf\s+\*', 'Recursive deletion of all files', 'critical'),
            (r':\(\)\{\s*:\|\:&\s*\}', 'Fork bomb detected', 'critical'),
            (r'dd\s+if=.*of=/dev/', 'Direct disk write operation', 'critical'),
            (r'mkfs\.\w+', 'Filesystem formatting operation', 'critical'),
            (r'>\s*/dev/sd[a-z]', 'Direct write to disk device', 'critical'),

            # High-risk patterns
            (r'rm\s+-rf\s+\$', 'Variable expansion in rm -rf (potential data loss)', 'high'),
            (r'chmod\s+777', 'Setting overly permissive file permissions', 'high'),
            (r'curl.*\|\s*bash', 'Piping downloaded content to bash', 'high'),
            (r'wget.*\|\s*sh', 'Piping downloaded content to shell', 'high'),
            (r'eval\s+\$', 'Using eval with variable expansion', 'high'),
            (r'sudo\s+rm', 'Using sudo with rm command', 'high'),

            # Medium-risk patterns
            (r'rm\s+-rf', 'Recursive file deletion', 'medium'),
            (r'\bexec\b', 'Using exec command', 'medium'),
            (r'source\s+http', 'Sourcing script from URL', 'medium'),
            (r'killall', 'Killing all processes by name', 'medium'),
            (r'>\s*/etc/', 'Writing to /etc directory', 'medium'),
            (r'docker.*--privileged', 'Running Docker with privileged mode', 'medium'),

            # Informational
            (r'/tmp/[a-zA-Z0-9]+', 'Using temporary files (check for race conditions)', 'low'),
            (r'password.*=', 'Possible hardcoded password', 'medium'),
            (r'api[_-]?key.*=', 'Possible hardcoded API key', 'medium'),
        ]
