#!/usr/bin/env python3
"""
Deprecated/Old Code Detector for ISAAC Project
Agent 5: Dead Code Hunter

Finds deprecated, legacy, and backward compatibility code.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict


class DeprecatedCodeVisitor(ast.NodeVisitor):
    """AST visitor to find deprecated code patterns."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.findings = []

    def visit_FunctionDef(self, node):
        # Check for @deprecated decorator
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and 'deprecat' in decorator.id.lower():
                self.findings.append({
                    'type': '@deprecated function',
                    'name': node.name,
                    'line': node.lineno
                })
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                if 'deprecat' in decorator.func.id.lower():
                    self.findings.append({
                        'type': '@deprecated function',
                        'name': node.name,
                        'line': node.lineno
                    })

        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # Check for deprecated/legacy class markers
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and 'deprecat' in decorator.id.lower():
                self.findings.append({
                    'type': '@deprecated class',
                    'name': node.name,
                    'line': node.lineno
                })

        # Check class name for legacy indicators
        if 'legacy' in node.name.lower() or 'old' in node.name.lower():
            self.findings.append({
                'type': 'Legacy class (by name)',
                'name': node.name,
                'line': node.lineno
            })

        self.generic_visit(node)


def analyze_file(filepath: Path) -> List[Dict]:
    """Analyze a file for deprecated/old code."""
    findings = []

    try:
        # Check filename for legacy indicators
        filename = filepath.name.lower()
        if any(indicator in filename for indicator in ['old', 'legacy', 'deprecated', 'backup', '_v1', '_v2']):
            findings.append({
                'file': str(filepath),
                'type': 'Legacy/old filename',
                'name': filepath.name,
                'line': 0,
                'details': f'Filename contains legacy indicator: {filepath.name}',
                'replacement': 'Unknown',
                'still_used': 'To be checked',
                'recommendation': 'Review for removal or update'
            })

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Remove BOM if present
        if content.startswith('\ufeff'):
            content = content[1:]

        # Check for Python 2 compatibility code
        py2_patterns = [
            (r'from __future__ import', 'Python 2 compatibility import'),
            (r'import six\b', 'six library (Python 2/3 compatibility)'),
            (r'unicode\(', 'unicode() function (Python 2)'),
            (r'xrange\(', 'xrange() function (Python 2)'),
            (r'\.iteritems\(\)', '.iteritems() method (Python 2)'),
            (r'\.iterkeys\(\)', '.iterkeys() method (Python 2)'),
            (r'\.itervalues\(\)', '.itervalues() method (Python 2)'),
            (r'basestring', 'basestring type (Python 2)'),
        ]

        for pattern, description in py2_patterns:
            matches = list(re.finditer(pattern, content))
            if matches:
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    findings.append({
                        'file': str(filepath),
                        'type': 'Python 2 compatibility code',
                        'name': description,
                        'line': line_num,
                        'details': f'Found: {match.group()}',
                        'replacement': 'Python 3 native',
                        'still_used': 'Active',
                        'recommendation': 'Remove if Python 2 support not needed'
                    })

        # Check for explicit deprecation markers in comments/docstrings
        deprecation_patterns = [
            r'@deprecated',
            r'DEPRECATED',
            r'DO NOT USE',
            r'OBSOLETE',
            r'LEGACY',
        ]

        for pattern in deprecation_patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            if matches:
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    # Get context
                    line_start = content.rfind('\n', 0, match.start()) + 1
                    line_end = content.find('\n', match.end())
                    if line_end == -1:
                        line_end = len(content)
                    context = content[line_start:line_end].strip()

                    findings.append({
                        'file': str(filepath),
                        'type': 'Marked as deprecated',
                        'name': pattern,
                        'line': line_num,
                        'details': context[:100],
                        'replacement': 'See comments',
                        'still_used': 'To be checked',
                        'recommendation': 'Review removal timeline'
                    })

        # Parse with AST
        try:
            tree = ast.parse(content, filename=str(filepath))
            visitor = DeprecatedCodeVisitor(str(filepath))
            visitor.visit(tree)

            for finding in visitor.findings:
                findings.append({
                    'file': str(filepath),
                    'type': finding['type'],
                    'name': finding['name'],
                    'line': finding['line'],
                    'details': f'{finding["type"]}: {finding["name"]}',
                    'replacement': 'To be determined',
                    'still_used': 'To be checked',
                    'recommendation': 'Review and update or remove'
                })

        except SyntaxError:
            pass

        # Check for backward compatibility sections
        compat_patterns = [
            (r'# backward compatibility', 'Backward compatibility code'),
            (r'# legacy support', 'Legacy support code'),
            (r'# for compatibility', 'Compatibility layer'),
        ]

        for pattern, description in compat_patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            if matches:
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    findings.append({
                        'file': str(filepath),
                        'type': 'Backward compatibility code',
                        'name': description,
                        'line': line_num,
                        'details': 'Code section for backward compatibility',
                        'replacement': 'Modern implementation',
                        'still_used': 'Active',
                        'recommendation': 'Review if still needed'
                    })

        return findings

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return []


def main():
    """Main entry point."""
    root_dir = Path("/home/user/Isaac/isaac")

    print("=" * 70)
    print("ISAAC DEPRECATED/OLD CODE DETECTOR")
    print("Agent 5: Dead Code Hunter")
    print("=" * 70)
    print()

    python_files = list(root_dir.rglob("*.py"))
    print(f"Scanning {len(python_files)} Python files...")
    print()

    all_findings = []

    for filepath in python_files:
        findings = analyze_file(filepath)
        all_findings.extend(findings)

    # Sort by type and file
    all_findings.sort(key=lambda x: (x['type'], x['file'], x['line']))

    # Write results
    output_file = "/home/user/Isaac/DEPRECATED_CODE.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Deprecated & Legacy Code Analysis\n\n")
        f.write("**Agent 5: Dead Code Hunter**\n\n")
        f.write(f"**Total files analyzed:** {len(python_files)}\n\n")
        f.write(f"**Deprecated/legacy items found:** {len(all_findings)}\n\n")

        if not all_findings:
            f.write("✓ No deprecated or legacy code detected!\n")
        else:
            # Summary by type
            types = {}
            for item in all_findings:
                t = item['type']
                types[t] = types.get(t, 0) + 1

            f.write("## Summary by Type\n\n")
            for t, count in sorted(types.items(), key=lambda x: -x[1]):
                f.write(f"- **{t}:** {count}\n")

            f.write("\n---\n\n")
            f.write("## Detailed Findings\n\n")

            current_type = None
            for i, item in enumerate(all_findings, 1):
                if item['type'] != current_type:
                    current_type = item['type']
                    f.write(f"\n### {current_type}\n\n")

                rel_path = Path(item['file']).relative_to("/home/user/Isaac")
                f.write(f"#### {i}. `{rel_path}:{item['line']}`\n\n")
                f.write(f"- **Location:** `{rel_path}:{item['line']}`\n")
                f.write(f"- **Item:** {item['name']}\n")
                f.write(f"- **Details:** {item['details']}\n")
                f.write(f"- **Replacement:** {item['replacement']}\n")
                f.write(f"- **Still used:** {item['still_used']}\n")
                f.write(f"- **Recommendation:** {item['recommendation']}\n\n")
                f.write("---\n\n")

    print(f"✓ Analysis complete!")
    print(f"  Deprecated/legacy items found: {len(all_findings)}")
    print(f"\n  Results written to: {output_file}")
    print()

    # Summary by type
    if all_findings:
        types = {}
        for item in all_findings:
            t = item['type']
            types[t] = types.get(t, 0) + 1

        print("Summary by type:")
        for t, count in sorted(types.items(), key=lambda x: -x[1]):
            print(f"  {count:3d}  {t}")


if __name__ == "__main__":
    main()
