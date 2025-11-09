#!/usr/bin/env python3
"""
Empty & Stub File Detector for ISAAC Project
Agent 5: Dead Code Hunter

Finds empty files, stub files, and incomplete implementations.
"""

import ast
import os
from pathlib import Path
from typing import List, Dict


def analyze_file(filepath: Path) -> Dict:
    """Analyze a file to determine if it's empty or a stub."""
    try:
        size = filepath.stat().st_size

        if size == 0:
            return {
                'file': str(filepath),
                'size': 0,
                'category': 'Empty (0 bytes)',
                'content_summary': 'Completely empty',
                'reason': 'Incomplete feature or forgotten file',
                'recommendation': 'Delete',
                'risk': 'Low'
            }

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Remove BOM if present
        if content.startswith('\ufeff'):
            content = content[1:]

        stripped = content.strip()

        # Check if empty after stripping
        if not stripped:
            return {
                'file': str(filepath),
                'size': size,
                'category': 'Whitespace only',
                'content_summary': 'Only whitespace/newlines',
                'reason': 'Incomplete implementation',
                'recommendation': 'Delete',
                'risk': 'Low'
            }

        # Parse with AST to understand structure
        try:
            tree = ast.parse(content, filename=str(filepath))
            body_nodes = tree.body

            if not body_nodes:
                return {
                    'file': str(filepath),
                    'size': size,
                    'category': 'No executable code',
                    'content_summary': 'Parses but has no statements',
                    'reason': 'Incomplete stub',
                    'recommendation': 'Delete',
                    'risk': 'Low'
                }

            # Filter out imports, docstrings, and type checking blocks
            non_import_nodes = []
            has_docstring = False
            has_imports = False
            has_pass = False
            has_todo = 'TODO' in content.upper() or 'FIXME' in content.upper()

            for node in body_nodes:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    has_imports = True
                elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                    if isinstance(node.value.value, str):
                        has_docstring = True
                        continue
                elif isinstance(node, ast.Pass):
                    has_pass = True
                else:
                    non_import_nodes.append(node)

            # Only imports
            if has_imports and not non_import_nodes and not has_docstring:
                return {
                    'file': str(filepath),
                    'size': size,
                    'category': 'Imports only',
                    'content_summary': f'{len([n for n in body_nodes if isinstance(n, (ast.Import, ast.ImportFrom))])} import statements',
                    'reason': 'Incomplete module or __init__.py for namespace',
                    'recommendation': 'Review - might be intentional __init__.py',
                    'risk': 'Medium'
                }

            # Only docstring
            if has_docstring and not non_import_nodes and not has_imports:
                return {
                    'file': str(filepath),
                    'size': size,
                    'category': 'Docstring only',
                    'content_summary': 'Module docstring with no code',
                    'reason': 'Placeholder or documentation stub',
                    'recommendation': 'Complete or delete',
                    'risk': 'Medium'
                }

            # Only imports and docstring
            if has_imports and has_docstring and not non_import_nodes:
                return {
                    'file': str(filepath),
                    'size': size,
                    'category': 'Imports + Docstring only',
                    'content_summary': 'Imports and docstring, no implementation',
                    'reason': 'Incomplete module',
                    'recommendation': 'Complete or delete',
                    'risk': 'Medium'
                }

            # Only pass statement(s)
            if has_pass and len(non_import_nodes) == 1:
                return {
                    'file': str(filepath),
                    'size': size,
                    'category': 'Pass statement only',
                    'content_summary': 'Contains only pass statement(s)',
                    'reason': 'Stub or placeholder',
                    'recommendation': 'Complete or delete',
                    'risk': 'Medium'
                }

            # Only TODO comments (no real implementation)
            if has_todo and len(non_import_nodes) <= 1:
                return {
                    'file': str(filepath),
                    'size': size,
                    'category': 'TODO placeholder',
                    'content_summary': 'Contains TODO/FIXME comments',
                    'reason': 'Planned but unimplemented feature',
                    'recommendation': 'Complete or remove',
                    'risk': 'Low'
                }

            # Check for minimal implementations (< 10 lines of actual code)
            lines_of_code = len([l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')])
            if lines_of_code < 10 and size < 300:
                return {
                    'file': str(filepath),
                    'size': size,
                    'category': 'Minimal implementation',
                    'content_summary': f'Only {lines_of_code} lines of code',
                    'reason': 'Very small module, possibly incomplete',
                    'recommendation': 'Review',
                    'risk': 'Medium'
                }

        except SyntaxError:
            # Files with syntax errors are handled separately
            return None

        return None

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return None


def main():
    """Main entry point."""
    root_dir = Path("/home/user/Isaac/isaac")

    print("=" * 70)
    print("ISAAC EMPTY & STUB FILE DETECTOR")
    print("Agent 5: Dead Code Hunter")
    print("=" * 70)
    print()

    python_files = list(root_dir.rglob("*.py"))
    print(f"Scanning {len(python_files)} Python files...")
    print()

    empty_files = []

    for filepath in python_files:
        result = analyze_file(filepath)
        if result:
            empty_files.append(result)

    # Sort by category and file path
    empty_files.sort(key=lambda x: (x['category'], x['file']))

    # Write results to markdown
    output_file = "/home/user/Isaac/EMPTY_FILES.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Empty & Stub Files Analysis\n\n")
        f.write("**Agent 5: Dead Code Hunter**\n\n")
        f.write(f"**Total files analyzed:** {len(python_files)}\n\n")
        f.write(f"**Empty/Stub files found:** {len(empty_files)}\n\n")

        if not empty_files:
            f.write("✓ No empty or stub files detected!\n")
        else:
            f.write("## Summary by Category\n\n")
            categories = {}
            for item in empty_files:
                cat = item['category']
                categories[cat] = categories.get(cat, 0) + 1

            for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
                f.write(f"- **{cat}:** {count} files\n")

            f.write("\n---\n\n")
            f.write("## Detailed Findings\n\n")

            current_category = None
            for i, item in enumerate(empty_files, 1):
                if item['category'] != current_category:
                    current_category = item['category']
                    f.write(f"\n### {current_category}\n\n")

                rel_path = Path(item['file']).relative_to("/home/user/Isaac")
                f.write(f"#### {i}. `{rel_path}`\n\n")
                f.write(f"- **Size:** {item['size']} bytes\n")
                f.write(f"- **Content:** {item['content_summary']}\n")
                f.write(f"- **Likely reason:** {item['reason']}\n")
                f.write(f"- **Recommendation:** {item['recommendation']}\n")
                f.write(f"- **Risk level:** {item['risk']}\n\n")

    print(f"✓ Analysis complete!")
    print(f"  Empty/stub files found: {len(empty_files)}")
    print(f"\n  Results written to: {output_file}")
    print()

    if empty_files:
        print("Summary by category:")
        categories = {}
        for item in empty_files:
            cat = item['category']
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"  {count:3d}  {cat}")


if __name__ == "__main__":
    main()
