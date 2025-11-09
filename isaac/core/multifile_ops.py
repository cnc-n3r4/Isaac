#!/usr/bin/env python3
"""
Multi-file Operations - Batch file operations with AI assistance

Enables cross-file refactoring, batch operations, and project-wide analysis.
"""

import logging
from typing import List, Dict, Any
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class MultiFileOperationManager:
    """
    Manages batch operations across multiple files

    Features:
    - Batch file operations (read, search, modify)
    - Cross-file refactoring support
    - Project-wide analysis
    - AI-assisted batch operations
    """

    def __init__(self, project_root: Path, rag_engine=None):
        """
        Initialize multi-file operation manager

        Args:
            project_root: Project root directory
            rag_engine: Optional RAG engine for AI assistance
        """
        self.project_root = project_root
        self.rag_engine = rag_engine

    def batch_search(self, pattern: str, file_patterns: List[str] = None) -> Dict[str, List[Dict]]:
        """
        Search for pattern across multiple files

        Args:
            pattern: Regex pattern to search
            file_patterns: Optional list of file glob patterns

        Returns:
            Dict mapping file paths to matches
        """
        results = {}

        if file_patterns is None:
            file_patterns = ['**/*.py', '**/*.js', '**/*.ts']

        for glob_pattern in file_patterns:
            for file_path in self.project_root.glob(glob_pattern):
                if not file_path.is_file():
                    continue

                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    matches = list(re.finditer(pattern, content, re.MULTILINE))

                    if matches:
                        file_matches = []
                        for match in matches:
                            # Get line number
                            line_num = content[:match.start()].count('\n') + 1

                            file_matches.append({
                                'line': line_num,
                                'match': match.group(),
                                'context': match.string[max(0, match.start()-50):match.end()+50]
                            })

                        results[str(file_path.relative_to(self.project_root))] = file_matches

                except Exception as e:
                    logger.error(f"Error searching {file_path}: {e}")

        logger.info(f"Batch search found {len(results)} files with matches")
        return results

    def batch_replace(self, pattern: str, replacement: str,
                     file_patterns: List[str] = None,
                     dry_run: bool = True) -> Dict[str, Any]:
        """
        Replace pattern across multiple files

        Args:
            pattern: Regex pattern to replace
            replacement: Replacement string
            file_patterns: Optional list of file glob patterns
            dry_run: If True, only show what would be changed

        Returns:
            Operation results with changes per file
        """
        changes = {}
        total_replacements = 0

        if file_patterns is None:
            file_patterns = ['**/*.py', '**/*.js', '**/*.ts']

        for glob_pattern in file_patterns:
            for file_path in self.project_root.glob(glob_pattern):
                if not file_path.is_file():
                    continue

                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    new_content, count = re.subn(pattern, replacement, content)

                    if count > 0:
                        rel_path = str(file_path.relative_to(self.project_root))
                        changes[rel_path] = {
                            'replacements': count,
                            'original_size': len(content),
                            'new_size': len(new_content)
                        }

                        if not dry_run:
                            file_path.write_text(new_content, encoding='utf-8')

                        total_replacements += count

                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")

        mode = "dry-run" if dry_run else "applied"
        logger.info(f"Batch replace ({mode}): {total_replacements} replacements in {len(changes)} files")

        return {
            'files_changed': len(changes),
            'total_replacements': total_replacements,
            'changes': changes,
            'dry_run': dry_run
        }

    def analyze_dependencies(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze file dependencies (imports, requires)

        Args:
            file_path: File to analyze

        Returns:
            Dependency analysis results
        """
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            file_type = file_path.suffix

            dependencies = {
                'imports': [],
                'from_imports': [],
                'requires': []
            }

            if file_type == '.py':
                # Python imports
                import_pattern = r'^import\s+([^\s#]+)'
                from_pattern = r'^from\s+([^\s]+)\s+import'

                dependencies['imports'] = re.findall(import_pattern, content, re.MULTILINE)
                dependencies['from_imports'] = re.findall(from_pattern, content, re.MULTILINE)

            elif file_type in ['.js', '.ts', '.jsx', '.tsx']:
                # JavaScript/TypeScript imports
                import_pattern = r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]'
                require_pattern = r'require\([\'"]([^\'"]+)[\'"]\)'

                dependencies['imports'] = re.findall(import_pattern, content)
                dependencies['requires'] = re.findall(require_pattern, content)

            return {
                'file': str(file_path.relative_to(self.project_root)),
                'dependencies': dependencies,
                'dependency_count': sum(len(v) for v in dependencies.values())
            }

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {'file': str(file_path), 'error': str(e)}

    def find_definition(self, symbol: str, file_patterns: List[str] = None) -> List[Dict]:
        """
        Find definition of a symbol across project

        Args:
            symbol: Symbol name to find (function, class, variable)
            file_patterns: Optional file patterns to search

        Returns:
            List of potential definitions with file and line
        """
        definitions = []

        if file_patterns is None:
            file_patterns = ['**/*.py', '**/*.js', '**/*.ts']

        # Patterns for different definition types
        patterns = [
            rf'^def\s+{symbol}\s*\(',           # Python function
            rf'^class\s+{symbol}\s*[\(:]',      # Python class
            rf'^async\s+def\s+{symbol}\s*\(',   # Python async function
            rf'function\s+{symbol}\s*\(',       # JS function
            rf'const\s+{symbol}\s*=',           # JS const
            rf'class\s+{symbol}\s*\{{',         # JS class
        ]

        for glob_pattern in file_patterns:
            for file_path in self.project_root.glob(glob_pattern):
                if not file_path.is_file():
                    continue

                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')

                    for pattern in patterns:
                        matches = re.finditer(pattern, content, re.MULTILINE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1

                            definitions.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': line_num,
                                'type': pattern.split('\\')[0],  # Approximate type
                                'context': match.string[match.start():match.end()+50]
                            })

                except Exception as e:
                    logger.error(f"Error searching {file_path}: {e}")

        logger.info(f"Found {len(definitions)} potential definitions for '{symbol}'")
        return definitions

    def ai_assisted_refactor(self, description: str, files: List[Path]) -> Dict[str, Any]:
        """
        Use AI to suggest refactoring across files

        Args:
            description: Description of refactoring goal
            files: Files to refactor

        Returns:
            AI suggestions for refactoring
        """
        if not self.rag_engine:
            return {
                'success': False,
                'error': 'RAG engine not available'
            }

        # Build context from files
        context = []
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                rel_path = str(file_path.relative_to(self.project_root))
                context.append(f"# {rel_path}\n{content}")
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")

        file_context = "\n\n---\n\n".join(context)

        # Query AI
        prompt = f"""Analyze the following files and suggest refactoring to: {description}

Files:
{file_context}

Provide specific suggestions for each file including:
1. What to change
2. Why the change improves the code
3. Any potential issues or considerations"""

        try:
            result = self.rag_engine.query(prompt, use_codebase=True)

            return {
                'success': result['success'],
                'suggestions': result.get('response', ''),
                'files_analyzed': len(files)
            }

        except Exception as e:
            logger.error(f"AI refactor failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


if __name__ == '__main__':
    # Test multi-file operations
    logging.basicConfig(level=logging.INFO)

    project_root = Path.cwd()
    mgr = MultiFileOperationManager(project_root)

    print("=== Multi-file Operations Test ===\n")

    # Test batch search
    print("Test 1: Batch search for 'class.*:'")
    results = mgr.batch_search(r'class\s+\w+.*:', ['**/*.py'])
    print(f"  Found in {len(results)} files")
    if results:
        for file, matches in list(results.items())[:3]:
            print(f"    {file}: {len(matches)} matches")

    # Test dependency analysis
    print("\nTest 2: Dependency analysis")
    py_files = list(project_root.glob('isaac/**/*.py'))[:3]
    for file in py_files:
        deps = mgr.analyze_dependencies(file)
        if 'error' not in deps:
            print(f"  {deps['file']}: {deps['dependency_count']} dependencies")

    # Test find definition
    print("\nTest 3: Find definition of 'XaiClient'")
    defs = mgr.find_definition('XaiClient', ['**/*.py'])
    for d in defs[:3]:
        print(f"  {d['file']}:{d['line']}")

    print("\n✓ Multi-file operations working")
