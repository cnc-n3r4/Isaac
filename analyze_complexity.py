#!/usr/bin/env python3
"""
Code Complexity Analyzer for ISAAC Project
Agent 5: Dead Code Hunter

Analyzes code complexity metrics across the codebase.
"""

import ast
from pathlib import Path
from typing import Dict, List, Tuple


class ComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity and other metrics."""

    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.functions = []
        self.classes = []
        self.deeply_nested = []

    def visit_FunctionDef(self, node):
        """Analyze function complexity."""
        # Calculate cyclomatic complexity
        complexity = self._calculate_complexity(node)

        # Count lines
        if hasattr(node, 'end_lineno'):
            lines = node.end_lineno - node.lineno + 1
        else:
            lines = 1

        # Count parameters
        num_params = len(node.args.args)
        if node.args.vararg:
            num_params += 1
        if node.args.kwarg:
            num_params += 1

        # Check nesting depth
        max_nesting = self._max_nesting_depth(node.body)

        self.functions.append({
            'name': node.name,
            'line': node.lineno,
            'lines': lines,
            'complexity': complexity,
            'params': num_params,
            'max_nesting': max_nesting
        })

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Handle async functions same as regular functions."""
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        """Analyze class size."""
        if hasattr(node, 'end_lineno'):
            lines = node.end_lineno - node.lineno + 1
        else:
            lines = 1

        # Count methods
        methods = sum(1 for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))

        self.classes.append({
            'name': node.name,
            'line': node.lineno,
            'lines': lines,
            'methods': methods
        })

        self.generic_visit(node)

    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Each decision point adds 1
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each 'and' or 'or' adds complexity
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                # Comprehensions add complexity
                complexity += 1

        return complexity

    def _max_nesting_depth(self, body, current_depth=0) -> int:
        """Calculate maximum nesting depth."""
        max_depth = current_depth

        for node in body:
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.Try)):
                # Get nested body
                nested_bodies = []
                if hasattr(node, 'body'):
                    nested_bodies.append(node.body)
                if hasattr(node, 'orelse'):
                    nested_bodies.append(node.orelse)
                if isinstance(node, ast.Try):
                    for handler in node.handlers:
                        nested_bodies.append(handler.body)
                    if node.finalbody:
                        nested_bodies.append(node.finalbody)

                for nested in nested_bodies:
                    depth = self._max_nesting_depth(nested, current_depth + 1)
                    max_depth = max(max_depth, depth)

        return max_depth


def analyze_file(filepath: Path) -> Dict:
    """Analyze complexity of a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Remove BOM
        if content.startswith('\ufeff'):
            content = content[1:]

        lines = content.split('\n')

        # Count lines of code (non-empty, non-comment)
        loc = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                loc += 1

        try:
            tree = ast.parse(content, filename=str(filepath))
        except SyntaxError:
            return None

        visitor = ComplexityVisitor(lines)
        visitor.visit(tree)

        return {
            'file': str(filepath),
            'total_lines': len(lines),
            'loc': loc,
            'functions': visitor.functions,
            'classes': visitor.classes
        }

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return None


def main():
    """Main entry point."""
    root_dir = Path("/home/user/Isaac/isaac")

    print("=" * 70)
    print("ISAAC CODE COMPLEXITY ANALYZER")
    print("Agent 5: Dead Code Hunter")
    print("=" * 70)
    print()

    python_files = list(root_dir.rglob("*.py"))
    print(f"Analyzing {len(python_files)} Python files...")
    print()

    all_results = []
    total_loc = 0
    all_functions = []
    all_classes = []

    for filepath in python_files:
        result = analyze_file(filepath)
        if result:
            all_results.append(result)
            total_loc += result['loc']

            # Collect all functions and classes with file info
            for func in result['functions']:
                all_functions.append({**func, 'file': result['file']})
            for cls in result['classes']:
                all_classes.append({**cls, 'file': result['file']})

    # Find problematic items
    long_functions = [f for f in all_functions if f['lines'] > 50]
    many_param_functions = [f for f in all_functions if f['params'] > 10]
    complex_functions = [f for f in all_functions if f['complexity'] > 10]
    deeply_nested = [f for f in all_functions if f['max_nesting'] > 4]
    large_classes = [c for c in all_classes if c['lines'] > 500]

    # Write report
    output_file = Path("/home/user/Isaac/CODE_COMPLEXITY.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Code Complexity Analysis\n\n")
        f.write("**Agent 5: Dead Code Hunter**\n\n")

        # Overall statistics
        f.write("## Overall Statistics\n\n")
        f.write(f"- **Total files:** {len(all_results)}\n")
        f.write(f"- **Total lines of code:** {total_loc:,}\n")
        f.write(f"- **Total functions:** {len(all_functions)}\n")
        f.write(f"- **Total classes:** {len(all_classes)}\n")
        f.write(f"- **Average LOC per file:** {total_loc // len(all_results) if all_results else 0}\n\n")

        # Problems summary
        f.write("## Complexity Issues Found\n\n")
        f.write(f"- **Functions >50 lines:** {len(long_functions)}\n")
        f.write(f"- **Functions >10 parameters:** {len(many_param_functions)}\n")
        f.write(f"- **High complexity functions (>10):** {len(complex_functions)}\n")
        f.write(f"- **Deeply nested code (>4 levels):** {len(deeply_nested)}\n")
        f.write(f"- **Large classes (>500 lines):** {len(large_classes)}\n\n")

        f.write("---\n\n")

        # Top 20 most complex functions
        f.write("## Top 20 Most Complex Functions\n\n")
        f.write("Sorted by cyclomatic complexity:\n\n")
        f.write("| Rank | Function | File | Lines | Complexity | Params | Recommendation |\n")
        f.write("|------|----------|------|-------|------------|--------|----------------|\n")

        sorted_complex = sorted(all_functions, key=lambda x: -x['complexity'])[:20]
        for i, func in enumerate(sorted_complex, 1):
            rel_path = Path(func['file']).relative_to("/home/user/Isaac")
            recommendation = "Refactor"
            if func['complexity'] > 20:
                recommendation = "URGENT: Refactor"
            elif func['complexity'] > 15:
                recommendation = "High priority refactor"

            f.write(f"| {i} | `{func['name']}` | `{rel_path}:{func['line']}` | "
                   f"{func['lines']} | {func['complexity']} | {func['params']} | {recommendation} |\n")

        # Long functions
        f.write("\n---\n\n")
        f.write("## Functions Exceeding 50 Lines\n\n")
        f.write(f"**Total:** {len(long_functions)}\n\n")

        if long_functions:
            f.write("Top 10 longest:\n\n")
            f.write("| Function | File | Lines | Complexity |\n")
            f.write("|----------|------|-------|------------|\n")

            sorted_long = sorted(long_functions, key=lambda x: -x['lines'])[:10]
            for func in sorted_long:
                rel_path = Path(func['file']).relative_to("/home/user/Isaac")
                f.write(f"| `{func['name']}` | `{rel_path}:{func['line']}` | "
                       f"{func['lines']} | {func['complexity']} |\n")

        # Functions with many parameters
        f.write("\n---\n\n")
        f.write("## Functions with >10 Parameters\n\n")
        f.write(f"**Total:** {len(many_param_functions)}\n\n")

        if many_param_functions:
            sorted_params = sorted(many_param_functions, key=lambda x: -x['params'])
            for func in sorted_params:
                rel_path = Path(func['file']).relative_to("/home/user/Isaac")
                f.write(f"- `{func['name']}` in `{rel_path}:{func['line']}` - "
                       f"**{func['params']} parameters** (consider using a config object)\n")

        # Deeply nested code
        f.write("\n---\n\n")
        f.write("## Deeply Nested Code (>4 levels)\n\n")
        f.write(f"**Total:** {len(deeply_nested)}\n\n")

        if deeply_nested:
            f.write("| Function | File | Max Nesting | Complexity | Recommendation |\n")
            f.write("|----------|------|-------------|------------|----------------|\n")

            sorted_nested = sorted(deeply_nested, key=lambda x: -x['max_nesting'])[:15]
            for func in sorted_nested:
                rel_path = Path(func['file']).relative_to("/home/user/Isaac")
                f.write(f"| `{func['name']}` | `{rel_path}:{func['line']}` | "
                       f"{func['max_nesting']} | {func['complexity']} | Extract nested logic |\n")

        # Large classes
        f.write("\n---\n\n")
        f.write("## Large Classes (>500 lines)\n\n")
        f.write(f"**Total:** {len(large_classes)}\n\n")

        if large_classes:
            sorted_classes = sorted(large_classes, key=lambda x: -x['lines'])
            for cls in sorted_classes:
                rel_path = Path(cls['file']).relative_to("/home/user/Isaac")
                f.write(f"- `{cls['name']}` in `{rel_path}:{cls['line']}` - "
                       f"**{cls['lines']} lines**, {cls['methods']} methods "
                       f"(consider splitting responsibilities)\n")

        # Recommendations
        f.write("\n---\n\n")
        f.write("## Refactoring Recommendations\n\n")
        f.write("### Priority Levels\n\n")

        p0 = [f for f in all_functions if f['complexity'] > 20]
        p1 = [f for f in all_functions if 15 < f['complexity'] <= 20]
        p2 = [f for f in all_functions if 10 < f['complexity'] <= 15]

        f.write(f"- **P0 (Critical):** {len(p0)} functions with complexity >20\n")
        f.write(f"- **P1 (High):** {len(p1)} functions with complexity 15-20\n")
        f.write(f"- **P2 (Medium):** {len(p2)} functions with complexity 10-15\n\n")

        f.write("### General Guidelines\n\n")
        f.write("1. **Target complexity:** Keep cyclomatic complexity < 10\n")
        f.write("2. **Function length:** Aim for < 50 lines per function\n")
        f.write("3. **Parameters:** Use config objects for > 5 parameters\n")
        f.write("4. **Nesting:** Keep nesting depth < 4 levels\n")
        f.write("5. **Class size:** Split classes > 300 lines into smaller components\n\n")

    print(f"✓ Analysis complete!")
    print(f"  Total LOC: {total_loc:,}")
    print(f"  Total functions: {len(all_functions)}")
    print(f"  High complexity functions: {len(complex_functions)}")
    print(f"  Long functions (>50 lines): {len(long_functions)}")
    print(f"  Functions with many params (>10): {len(many_param_functions)}")
    print(f"  Deeply nested functions (>4): {len(deeply_nested)}")
    print(f"  Large classes (>500 lines): {len(large_classes)}")
    print(f"\n  Results written to: {output_file}")


if __name__ == "__main__":
    main()
