"""
Script Explainer

Explains what bash scripts do in natural language.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import re


class ScriptExplainer:
    """Explains bash scripts in clear, natural language."""

    def __init__(self, ai_router=None):
        """
        Initialize explainer.

        Args:
            ai_router: AIRouter instance for AI-powered explanations
        """
        self.ai_router = ai_router

    def explain(self, script: str, detail_level: str = 'medium') -> Dict[str, Any]:
        """
        Explain what a bash script does.

        Args:
            script: The bash script to explain
            detail_level: 'brief', 'medium', or 'detailed'

        Returns:
            Dictionary with:
                - summary: Brief summary of what the script does
                - line_by_line: Line-by-line explanation
                - functions: Explanation of functions
                - potential_issues: Potential problems or warnings
                - complexity: Complexity assessment
        """
        # Build the explanation prompt
        prompt = self._build_explanation_prompt(script, detail_level)

        # Use AI router if available
        if self.ai_router:
            response = self.ai_router.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=3000
            )
            result = self._parse_explanation_response(response.content)
        else:
            # Fallback to basic analysis
            result = self._basic_explanation(script)

        # Add complexity score
        result['complexity'] = self._assess_complexity(script)

        return result

    def explain_file(self, file_path: Path, detail_level: str = 'medium') -> Dict[str, Any]:
        """
        Explain a bash script file.

        Args:
            file_path: Path to the script file
            detail_level: 'brief', 'medium', or 'detailed'

        Returns:
            Explanation dictionary
        """
        with open(file_path, 'r') as f:
            script = f.read()

        result = self.explain(script, detail_level)
        result['file'] = str(file_path)
        return result

    def explain_command(self, command: str) -> str:
        """
        Explain a single bash command.

        Args:
            command: Single bash command

        Returns:
            Natural language explanation
        """
        result = self.explain(command, detail_level='brief')
        return result.get('summary', 'Unable to explain command')

    def _build_explanation_prompt(self, script: str, detail_level: str) -> str:
        """Build the AI prompt for explanation."""
        detail_instructions = {
            'brief': 'Provide a concise 1-2 sentence summary.',
            'medium': 'Provide a summary and explain key parts of the script.',
            'detailed': 'Provide a comprehensive explanation including line-by-line breakdown.'
        }

        instruction = detail_instructions.get(detail_level, detail_instructions['medium'])

        prompt = f"""You are a bash scripting expert. Explain the following bash script in clear, natural language.

Script:
```bash
{script}
```

Detail level: {detail_level}
{instruction}

Provide your explanation in the following format:

SUMMARY:
Brief summary of what the script does

LINE_BY_LINE:
Explanation of important lines (skip trivial comments)

FUNCTIONS:
Description of any functions defined

POTENTIAL_ISSUES:
Security concerns, bugs, or improvements

Important:
1. Use simple, clear language
2. Explain the purpose, not just what each line does
3. Highlight any dangerous operations
4. Note any best practices or anti-patterns
5. Explain complex constructs (regex, parameter expansion, etc.)
"""
        return prompt

    def _parse_explanation_response(self, content: str) -> Dict[str, Any]:
        """Parse the AI response into structured data."""
        result = {
            'summary': '',
            'line_by_line': [],
            'functions': {},
            'potential_issues': []
        }

        # Extract summary
        summary_match = re.search(r'SUMMARY:\s*(.*?)(?=LINE_BY_LINE:|FUNCTIONS:|POTENTIAL_ISSUES:|$)', content, re.DOTALL)
        if summary_match:
            result['summary'] = summary_match.group(1).strip()

        # Extract line-by-line
        lbl_match = re.search(r'LINE_BY_LINE:\s*(.*?)(?=FUNCTIONS:|POTENTIAL_ISSUES:|$)', content, re.DOTALL)
        if lbl_match:
            lines = lbl_match.group(1).strip().split('\n')
            result['line_by_line'] = [line.strip() for line in lines if line.strip()]

        # Extract functions
        func_match = re.search(r'FUNCTIONS:\s*(.*?)(?=POTENTIAL_ISSUES:|$)', content, re.DOTALL)
        if func_match:
            func_text = func_match.group(1).strip()
            result['functions'] = self._parse_functions(func_text)

        # Extract potential issues
        issues_match = re.search(r'POTENTIAL_ISSUES:\s*(.*?)$', content, re.DOTALL)
        if issues_match:
            issues_text = issues_match.group(1).strip()
            if issues_text.lower() not in ['none', 'none found', 'no issues']:
                result['potential_issues'] = [
                    issue.strip() for issue in issues_text.split('\n') if issue.strip()
                ]

        return result

    def _parse_functions(self, func_text: str) -> Dict[str, str]:
        """Parse function descriptions."""
        functions = {}
        current_func = None

        for line in func_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Check if it's a function name (e.g., "function_name:")
            if ':' in line and not line.startswith('-'):
                parts = line.split(':', 1)
                current_func = parts[0].strip()
                desc = parts[1].strip() if len(parts) > 1 else ''
                functions[current_func] = desc
            elif current_func:
                # Continuation of previous function description
                functions[current_func] += ' ' + line

        return functions

    def _basic_explanation(self, script: str) -> Dict[str, Any]:
        """Basic script analysis (fallback)."""
        lines = script.split('\n')

        # Count key elements
        has_shebang = lines[0].startswith('#!') if lines else False
        has_set_e = 'set -e' in script
        has_set_u = 'set -u' in script

        # Find functions
        func_pattern = re.compile(r'^\s*(?:function\s+)?(\w+)\s*\(\)', re.MULTILINE)
        functions = func_pattern.findall(script)

        # Identify potential issues
        issues = []
        if not has_shebang:
            issues.append('⚠️  Missing shebang line (#!/bin/bash)')
        if not has_set_e:
            issues.append('💡 Consider adding "set -e" to exit on errors')
        if 'rm -rf' in script:
            issues.append('⚠️  Contains potentially destructive command (rm -rf)')
        if 'eval' in script:
            issues.append('⚠️  Uses eval which can be dangerous')
        if re.search(r'\$\{[^}]+\}', script) is None and '$' in script:
            issues.append('💡 Consider using ${var} instead of $var for clarity')

        summary = f"Bash script with {len(lines)} lines"
        if functions:
            summary += f", {len(functions)} function(s): {', '.join(functions)}"
        if has_set_e or has_set_u:
            summary += ", includes error handling"

        return {
            'summary': summary,
            'line_by_line': [f'Script has {len(lines)} lines of code'],
            'functions': {func: 'Function definition found' for func in functions},
            'potential_issues': issues
        }

    def _assess_complexity(self, script: str) -> Dict[str, Any]:
        """Assess script complexity."""
        lines = [line.strip() for line in script.split('\n') if line.strip() and not line.strip().startswith('#')]

        # Count various elements
        num_lines = len(lines)
        num_functions = len(re.findall(r'^\s*(?:function\s+)?(\w+)\s*\(\)', script, re.MULTILINE))
        num_loops = len(re.findall(r'\b(for|while|until)\b', script))
        num_conditions = len(re.findall(r'\b(if|case)\b', script))
        num_pipes = script.count('|')
        num_redirects = script.count('>') + script.count('<')

        # Calculate complexity score (0-100)
        score = min(100, (
            num_lines * 0.5 +
            num_functions * 10 +
            num_loops * 5 +
            num_conditions * 3 +
            num_pipes * 2 +
            num_redirects * 1
        ))

        # Determine level
        if score < 20:
            level = 'Simple'
        elif score < 50:
            level = 'Moderate'
        elif score < 80:
            level = 'Complex'
        else:
            level = 'Very Complex'

        return {
            'score': round(score, 1),
            'level': level,
            'metrics': {
                'lines': num_lines,
                'functions': num_functions,
                'loops': num_loops,
                'conditions': num_conditions,
                'pipes': num_pipes,
                'redirects': num_redirects
            }
        }
