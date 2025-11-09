#!/usr/bin/env python3
"""
Unused Imports Scanner for ISAAC Project
Agent 5: Dead Code Hunter

Scans all Python files for unused imports using AST analysis.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import csv


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to collect imports and name usages."""

    def __init__(self):
        self.imports: Dict[str, Tuple[int, str, str]] = {}  # name -> (line, full_import, type)
        self.names_used: Set[str] = set()
        self.from_imports: Dict[str, Tuple[int, str, str]] = {}

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            # Handle cases like 'import os.path'
            base_name = name.split('.')[0]
            self.imports[base_name] = (node.lineno, f"import {alias.name}", "module")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ''
        for alias in node.names:
            if alias.name == '*':
                # Star imports - can't reliably detect unused
                continue
            name = alias.asname if alias.asname else alias.name
            import_str = f"from {module} import {alias.name}"
            if alias.asname:
                import_str += f" as {alias.asname}"
            self.from_imports[name] = (node.lineno, import_str, "function/class")
        self.generic_visit(node)

    def visit_Name(self, node):
        self.names_used.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Handle cases like 'os.path.join'
        if isinstance(node.value, ast.Name):
            self.names_used.add(node.value.id)
        self.generic_visit(node)


def analyze_file(filepath: Path) -> List[Dict]:
    """Analyze a single Python file for unused imports."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip empty files
        if not content.strip():
            return []

        tree = ast.parse(content, filename=str(filepath))
        visitor = ImportVisitor()
        visitor.visit(tree)

        unused = []
        all_imports = {**visitor.imports, **visitor.from_imports}

        for name, (lineno, import_str, import_type) in all_imports.items():
            # Check if the name is used in the code
            if name not in visitor.names_used:
                # Additional checks for common false positives

                # Check if it's used in __all__
                if '__all__' in content and f"'{name}'" in content:
                    continue
                if '__all__' in content and f'"{name}"' in content:
                    continue

                # Check if it's used in string type hints
                if f"'{name}'" in content or f'"{name}"' in content:
                    # Might be used in forward references
                    continue

                # Determine confidence
                confidence = "High"
                auto_fix = "Y"

                # Lower confidence for certain patterns
                if name.startswith('_'):
                    confidence = "Medium"
                if 'TYPE_CHECKING' in content:
                    confidence = "Medium"

                unused.append({
                    'file': str(filepath),
                    'line': lineno,
                    'import': import_str,
                    'type': import_type,
                    'confidence': confidence,
                    'auto_fix': auto_fix
                })

        return unused

    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}", file=sys.stderr)
        return []


def scan_directory(root_dir: Path) -> List[Dict]:
    """Recursively scan directory for unused imports."""
    all_unused = []

    python_files = list(root_dir.rglob("*.py"))
    total = len(python_files)

    print(f"Scanning {total} Python files...")

    for i, filepath in enumerate(python_files, 1):
        if i % 50 == 0:
            print(f"Progress: {i}/{total} files...")

        unused = analyze_file(filepath)
        all_unused.extend(unused)

    return all_unused


def main():
    """Main entry point."""
    root_dir = Path("/home/user/Isaac/isaac")

    print("=" * 70)
    print("ISAAC UNUSED IMPORTS SCANNER")
    print("Agent 5: Dead Code Hunter")
    print("=" * 70)
    print()

    unused_imports = scan_directory(root_dir)

    # Sort by file path for organized output
    unused_imports.sort(key=lambda x: (x['file'], x['line']))

    # Write to CSV
    output_file = "/home/user/Isaac/UNUSED_IMPORTS.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'file', 'line', 'import', 'type', 'confidence', 'auto_fix'
        ])
        writer.writeheader()
        writer.writerows(unused_imports)

    print(f"\n✓ Analysis complete!")
    print(f"  Total Python files scanned: {len(list(root_dir.rglob('*.py')))}")
    print(f"  Unused imports found: {len(unused_imports)}")
    print(f"  High confidence: {sum(1 for u in unused_imports if u['confidence'] == 'High')}")
    print(f"  Medium confidence: {sum(1 for u in unused_imports if u['confidence'] == 'Medium')}")
    print(f"  Auto-fix safe: {sum(1 for u in unused_imports if u['auto_fix'] == 'Y')}")
    print(f"\n  Results written to: {output_file}")
    print()

    # Show top 10 files with most unused imports
    file_counts = {}
    for item in unused_imports:
        file = item['file']
        file_counts[file] = file_counts.get(file, 0) + 1

    if file_counts:
        print("\nTop 10 files with most unused imports:")
        for file, count in sorted(file_counts.items(), key=lambda x: -x[1])[:10]:
            rel_path = Path(file).relative_to("/home/user/Isaac")
            print(f"  {count:3d}  {rel_path}")


if __name__ == "__main__":
    main()
