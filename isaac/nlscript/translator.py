"""
English to Bash Translator

Converts natural language descriptions to bash commands and scripts.
"""

from typing import Dict, Any, Optional
import re


class EnglishToBashTranslator:
    """Translates natural language to bash commands using AI."""

    def __init__(self, ai_router=None):
        """
        Initialize translator.

        Args:
            ai_router: AIRouter instance for AI-powered translation
        """
        self.ai_router = ai_router
        self.translation_cache: Dict[str, str] = {}

    def translate(self, natural_language: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Translate natural language to bash.

        Args:
            natural_language: The natural language description
            context: Optional context (current directory, environment, etc.)

        Returns:
            Dictionary with:
                - bash_code: The generated bash script
                - explanation: What the script does
                - warnings: Any safety warnings
                - confidence: Confidence score (0-1)
        """
        # Check cache first
        cache_key = self._get_cache_key(natural_language, context)
        if cache_key in self.translation_cache:
            return self._parse_cached_result(self.translation_cache[cache_key])

        # Build the AI prompt
        prompt = self._build_translation_prompt(natural_language, context)

        # Use AI router if available
        if self.ai_router:
            response = self.ai_router.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for more deterministic output
                max_tokens=2000
            )
            result = self._parse_ai_response(response.content)
        else:
            # Fallback to simple pattern matching
            result = self._simple_translation(natural_language, context)

        # Cache the result
        self.translation_cache[cache_key] = result['bash_code']

        return result

    def translate_simple(self, natural_language: str) -> str:
        """
        Simple translation that returns just the bash code.

        Args:
            natural_language: The natural language description

        Returns:
            Bash code string
        """
        result = self.translate(natural_language)
        return result['bash_code']

    def _build_translation_prompt(self, nl: str, context: Optional[Dict[str, Any]]) -> str:
        """Build the AI prompt for translation."""
        context_str = ""
        if context:
            context_str = f"\n\nContext:\n"
            if 'cwd' in context:
                context_str += f"- Current directory: {context['cwd']}\n"
            if 'env' in context:
                context_str += f"- Environment: {context['env']}\n"
            if 'files' in context:
                context_str += f"- Available files: {', '.join(context['files'])}\n"

        prompt = f"""You are a bash scripting expert. Convert the following natural language description into a bash script.

Natural language request: {nl}{context_str}

Provide a response in the following format:

BASH_CODE:
```bash
# Your bash script here
```

EXPLANATION:
Brief explanation of what the script does

WARNINGS:
Any safety warnings or things to be aware of (or "None" if no warnings)

CONFIDENCE:
A confidence score from 0.0 to 1.0

Important guidelines:
1. Generate safe, production-ready bash code
2. Include error handling where appropriate
3. Add comments for clarity
4. Use best practices (set -e, set -u for scripts, etc.)
5. Warn about destructive operations
6. Consider edge cases
7. Make scripts portable when possible
"""
        return prompt

    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """Parse the AI response into structured data."""
        result = {
            'bash_code': '',
            'explanation': '',
            'warnings': [],
            'confidence': 0.8
        }

        # Extract bash code
        bash_match = re.search(r'BASH_CODE:\s*```bash\s*(.*?)\s*```', content, re.DOTALL)
        if bash_match:
            result['bash_code'] = bash_match.group(1).strip()

        # Extract explanation
        expl_match = re.search(r'EXPLANATION:\s*(.*?)(?=WARNINGS:|CONFIDENCE:|$)', content, re.DOTALL)
        if expl_match:
            result['explanation'] = expl_match.group(1).strip()

        # Extract warnings
        warn_match = re.search(r'WARNINGS:\s*(.*?)(?=CONFIDENCE:|$)', content, re.DOTALL)
        if warn_match:
            warnings_text = warn_match.group(1).strip()
            if warnings_text.lower() != 'none':
                result['warnings'] = [w.strip() for w in warnings_text.split('\n') if w.strip()]

        # Extract confidence
        conf_match = re.search(r'CONFIDENCE:\s*([0-9.]+)', content)
        if conf_match:
            try:
                result['confidence'] = float(conf_match.group(1))
            except ValueError:
                pass

        return result

    def _simple_translation(self, nl: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple pattern-based translation for common commands (fallback)."""
        nl_lower = nl.lower().strip()

        # Common patterns
        patterns = [
            # File operations
            (r'list (?:all )?files', 'ls -la', 'List all files in current directory'),
            (r'find (?:all )?(.+?) files', r'find . -name "*\1*"', 'Find files matching pattern'),
            (r'delete (?:all )?(.+?) files', r'rm -f *\1*', 'Delete files (DESTRUCTIVE)'),
            (r'copy (.+?) to (.+?)', r'cp "\1" "\2"', 'Copy file'),
            (r'move (.+?) to (.+?)', r'mv "\1" "\2"', 'Move file'),

            # Directory operations
            (r'create (?:a )?directory (?:named )?(.+)', r'mkdir -p "\1"', 'Create directory'),
            (r'change to (.+?) directory', r'cd "\1"', 'Change directory'),
            (r'show current directory', 'pwd', 'Print working directory'),

            # Process operations
            (r'show (?:all )?(?:running )?processes', 'ps aux', 'Show all processes'),
            (r'kill process (?:with pid )?(\d+)', r'kill \1', 'Kill process'),
            (r'find processes? (?:named )?(.+)', r'ps aux | grep "\1"', 'Find processes by name'),

            # System info
            (r'show disk usage', 'df -h', 'Show disk usage'),
            (r'show memory usage', 'free -h', 'Show memory usage'),
            (r'show system info', 'uname -a', 'Show system information'),

            # Git operations
            (r'git status', 'git status', 'Show git status'),
            (r'commit (?:with message )?(.+)', r'git commit -m "\1"', 'Git commit'),
            (r'push to (.+)', r'git push origin \1', 'Git push to branch'),
        ]

        for pattern, replacement, explanation in patterns:
            match = re.search(pattern, nl_lower)
            if match:
                bash_code = replacement
                # Replace capture groups
                for i, group in enumerate(match.groups(), 1):
                    bash_code = bash_code.replace(f'\\{i}', group)

                warnings = []
                if 'delete' in nl_lower or 'rm ' in bash_code:
                    warnings.append('⚠️  This is a destructive operation. Files will be permanently deleted.')
                if 'kill' in nl_lower:
                    warnings.append('⚠️  Killing processes can cause data loss or system instability.')

                return {
                    'bash_code': bash_code,
                    'explanation': explanation,
                    'warnings': warnings,
                    'confidence': 0.7
                }

        # No pattern matched
        return {
            'bash_code': '# Could not translate to bash\n# Manual implementation required',
            'explanation': 'No matching pattern found. AI router needed for complex translations.',
            'warnings': ['⚠️  Translation failed. Please provide more specific instructions or use AI mode.'],
            'confidence': 0.0
        }

    def _get_cache_key(self, nl: str, context: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for translation."""
        context_key = ""
        if context:
            context_key = str(sorted(context.items()))
        return f"{nl}::{context_key}"

    def _parse_cached_result(self, bash_code: str) -> Dict[str, Any]:
        """Parse cached bash code into result format."""
        return {
            'bash_code': bash_code,
            'explanation': 'Cached result',
            'warnings': [],
            'confidence': 1.0
        }

    def clear_cache(self):
        """Clear the translation cache."""
        self.translation_cache.clear()
