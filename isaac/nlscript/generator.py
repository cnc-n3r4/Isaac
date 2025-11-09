"""
Script Generator

Generates complex bash scripts from natural language descriptions.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from datetime import datetime


class ScriptGenerator:
    """Generates complex bash scripts with proper structure and error handling."""

    def __init__(self, ai_router=None):
        """
        Initialize generator.

        Args:
            ai_router: AIRouter instance for AI-powered generation
        """
        self.ai_router = ai_router
        self.generated_scripts: List[Dict[str, Any]] = []
        self.storage_path = Path.home() / '.isaac' / 'nlscripts'
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        description: str,
        requirements: Optional[List[str]] = None,
        output_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Generate a complex bash script.

        Args:
            description: Natural language description of the script
            requirements: List of specific requirements
            output_file: Optional path to save the script

        Returns:
            Dictionary with:
                - script: The generated bash script
                - metadata: Script metadata (functions, dependencies, etc.)
                - tests: Suggested test cases
                - documentation: Usage documentation
        """
        # Build the generation prompt
        prompt = self._build_generation_prompt(description, requirements)

        # Generate using AI
        if self.ai_router:
            response = self.ai_router.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=4000
            )
            result = self._parse_generation_response(response.content)
        else:
            result = self._generate_basic_script(description, requirements)

        # Add metadata
        result['generated_at'] = datetime.now().isoformat()
        result['description'] = description

        # Save if output file specified
        if output_file:
            self._save_script(result, output_file)

        # Store in history
        self.generated_scripts.append(result)
        self._save_history()

        return result

    def _build_generation_prompt(self, description: str, requirements: Optional[List[str]]) -> str:
        """Build the AI prompt for script generation."""
        req_str = ""
        if requirements:
            req_str = "\n\nSpecific requirements:\n" + "\n".join(f"- {req}" for req in requirements)

        prompt = f"""You are an expert bash script developer. Generate a production-ready bash script based on the following description.

Description: {description}{req_str}

Generate a complete, robust bash script with the following structure:

SCRIPT:
```bash
#!/bin/bash
# Your script here
```

METADATA:
- Functions: List all functions defined
- Dependencies: Required commands/tools
- Input parameters: Script arguments
- Output: What the script produces
- Error handling: How errors are handled

TESTS:
Suggested test cases to validate the script

DOCUMENTATION:
Usage instructions and examples

Guidelines:
1. Include proper shebang (#!/bin/bash)
2. Add comprehensive error handling
3. Use functions for modularity
4. Include input validation
5. Add usage/help function
6. Use shellcheck-compliant code
7. Add logging/debugging options
8. Handle edge cases
9. Make it idempotent where possible
10. Include cleanup on exit if needed
"""
        return prompt

    def _parse_generation_response(self, content: str) -> Dict[str, Any]:
        """Parse the AI response into structured data."""
        import re

        result = {
            'script': '',
            'metadata': {},
            'tests': [],
            'documentation': ''
        }

        # Extract script
        script_match = re.search(r'SCRIPT:\s*```bash\s*(.*?)\s*```', content, re.DOTALL)
        if script_match:
            result['script'] = script_match.group(1).strip()

        # Extract metadata
        metadata_match = re.search(r'METADATA:\s*(.*?)(?=TESTS:|DOCUMENTATION:|$)', content, re.DOTALL)
        if metadata_match:
            metadata_text = metadata_match.group(1).strip()
            result['metadata'] = self._parse_metadata(metadata_text)

        # Extract tests
        tests_match = re.search(r'TESTS:\s*(.*?)(?=DOCUMENTATION:|$)', content, re.DOTALL)
        if tests_match:
            tests_text = tests_match.group(1).strip()
            result['tests'] = [t.strip() for t in tests_text.split('\n') if t.strip()]

        # Extract documentation
        doc_match = re.search(r'DOCUMENTATION:\s*(.*?)$', content, re.DOTALL)
        if doc_match:
            result['documentation'] = doc_match.group(1).strip()

        return result

    def _parse_metadata(self, metadata_text: str) -> Dict[str, Any]:
        """Parse metadata section."""
        import re
        metadata = {}

        patterns = {
            'functions': r'Functions:\s*(.*?)(?=\n-|\n\n|$)',
            'dependencies': r'Dependencies:\s*(.*?)(?=\n-|\n\n|$)',
            'input_parameters': r'Input parameters:\s*(.*?)(?=\n-|\n\n|$)',
            'output': r'Output:\s*(.*?)(?=\n-|\n\n|$)',
            'error_handling': r'Error handling:\s*(.*?)(?=\n-|\n\n|$)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, metadata_text, re.IGNORECASE | re.DOTALL)
            if match:
                metadata[key] = match.group(1).strip()

        return metadata

    def _generate_basic_script(self, description: str, requirements: Optional[List[str]]) -> Dict[str, Any]:
        """Generate a basic script template (fallback)."""
        script = f"""#!/bin/bash
# Generated script: {description}
# Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e  # Exit on error
set -u  # Error on undefined variable

# Usage function
usage() {{
    echo "Usage: $0 [options]"
    echo "Description: {description}"
    exit 1
}}

# Main function
main() {{
    # TODO: Implement script logic
    echo "Script not yet implemented"
    echo "Description: {description}"

    # Requirements:
"""
        if requirements:
            for req in requirements:
                script += f"    # - {req}\n"

        script += """
    return 0
}

# Run main function
main "$@"
"""

        return {
            'script': script,
            'metadata': {
                'functions': 'usage, main',
                'dependencies': 'bash',
                'input_parameters': 'None yet',
                'output': 'Exit code',
                'error_handling': 'set -e for early exit'
            },
            'tests': ['Run script with no arguments', 'Check exit code'],
            'documentation': f'Basic template for: {description}'
        }

    def _save_script(self, result: Dict[str, Any], output_file: Path):
        """Save the generated script to a file."""
        with open(output_file, 'w') as f:
            f.write(result['script'])
        output_file.chmod(0o755)  # Make executable

        # Save metadata alongside
        metadata_file = output_file.with_suffix('.json')
        metadata = {
            'description': result.get('description', ''),
            'metadata': result.get('metadata', {}),
            'tests': result.get('tests', []),
            'documentation': result.get('documentation', ''),
            'generated_at': result.get('generated_at', '')
        }
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _save_history(self):
        """Save generation history."""
        history_file = self.storage_path / 'generation_history.json'
        # Keep only last 100 entries
        history = self.generated_scripts[-100:]
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def list_generated_scripts(self) -> List[Dict[str, Any]]:
        """List all generated scripts."""
        return self.generated_scripts.copy()

    def get_script_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get a generated script by index."""
        if 0 <= index < len(self.generated_scripts):
            return self.generated_scripts[index]
        return None
