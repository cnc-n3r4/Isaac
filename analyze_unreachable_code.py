#!/usr/bin/env python3
"""
Unreachable Code Detector for ISAAC Project
Agent 5: Dead Code Hunter

Finds code that can never be executed.
"""

import ast
from pathlib import Path
from typing import List, Dict, Set


class UnreachableCodeVisitor(ast.NodeVisitor):
    """AST visitor to find unreachable code."""

    def __init__(self, filepath: str, source_lines: List[str]):
        self.filepath = filepath
        self.source_lines = source_lines
        self.findings = []
        self.defined_functions = set()
        self.called_functions = set()

    def visit_FunctionDef(self, node):
        """Track function definitions."""
        self.defined_functions.add(node.name)
        self._check_unreachable_in_block(node.body, node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Track async function definitions."""
        self.defined_functions.add(node.name)
        self._check_unreachable_in_block(node.body, node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        """Track function calls."""
        if isinstance(node.func, ast.Name):
            self.called_functions.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                # Track module.function calls
                self.called_functions.add(f"{node.func.value.id}.{node.func.attr}")
                if node.func.attr == 'exit':
                    # This could make code after it unreachable
                    pass
        self.generic_visit(node)

    def _check_unreachable_in_block(self, body: List[ast.stmt], context: str):
        """Check for unreachable code in a block of statements."""
        for i, stmt in enumerate(body):
            # Check if this statement terminates the block
            terminates = self._is_terminating_statement(stmt)

            if terminates and i < len(body) - 1:
                # There are statements after a terminating statement
                next_stmt = body[i + 1]

                # Get code snippet
                start_line = next_stmt.lineno
                end_line = body[-1].end_lineno if hasattr(body[-1], 'end_lineno') else body[-1].lineno
                num_lines = end_line - start_line + 1

                snippet_lines = self.source_lines[start_line - 1:min(start_line + 3, end_line)]
                snippet = '\n'.join(snippet_lines)
                if num_lines > 4:
                    snippet += '\n...'

                reason = "after return" if isinstance(stmt, ast.Return) else \
                         "after raise" if isinstance(stmt, ast.Raise) else \
                         "after sys.exit()" if self._is_sys_exit(stmt) else \
                         "after break/continue"

                self.findings.append({
                    'file': self.filepath,
                    'line': start_line,
                    'num_lines': num_lines,
                    'snippet': snippet,
                    'reason': reason,
                    'context': context
                })

                # Don't continue checking this block
                break

            # Recursively check nested blocks
            if isinstance(stmt, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                self._check_nested_blocks(stmt, context)

    def _check_nested_blocks(self, stmt, context):
        """Check unreachable code in nested blocks."""
        if isinstance(stmt, ast.If):
            self._check_unreachable_in_block(stmt.body, f"{context} > if")
            self._check_unreachable_in_block(stmt.orelse, f"{context} > else")
        elif isinstance(stmt, (ast.While, ast.For)):
            self._check_unreachable_in_block(stmt.body, f"{context} > loop")
            self._check_unreachable_in_block(stmt.orelse, f"{context} > loop-else")
        elif isinstance(stmt, ast.With):
            self._check_unreachable_in_block(stmt.body, f"{context} > with")
        elif isinstance(stmt, ast.Try):
            self._check_unreachable_in_block(stmt.body, f"{context} > try")
            for handler in stmt.handlers:
                self._check_unreachable_in_block(handler.body, f"{context} > except")
            self._check_unreachable_in_block(stmt.orelse, f"{context} > try-else")
            self._check_unreachable_in_block(stmt.finalbody, f"{context} > finally")

    def _is_terminating_statement(self, stmt) -> bool:
        """Check if a statement terminates execution."""
        if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
            return True

        # Check for sys.exit() or similar
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            if self._is_sys_exit(stmt):
                return True

        return False

    def _is_sys_exit(self, stmt) -> bool:
        """Check if statement is sys.exit() or similar."""
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Attribute):
                if isinstance(call.func.value, ast.Name):
                    if call.func.value.id in ('sys', 'os') and call.func.attr == 'exit':
                        return True
                    if call.func.value.id == 'sys' and call.func.attr == '_exit':
                        return True
        return False


def analyze_file(filepath: Path) -> Dict:
    """Analyze a file for unreachable code."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Remove BOM if present
        if content.startswith('\ufeff'):
            content = content[1:]

        source_lines = content.split('\n')

        try:
            tree = ast.parse(content, filename=str(filepath))
        except SyntaxError:
            return None

        visitor = UnreachableCodeVisitor(str(filepath), source_lines)
        visitor.visit(tree)

        # Find uncalled functions (only private functions that look unused)
        uncalled = []
        for func in visitor.defined_functions:
            if func.startswith('_') and not func.startswith('__'):
                # Private function
                if func not in visitor.called_functions:
                    # Not called anywhere in this file
                    uncalled.append(func)

        return {
            'unreachable': visitor.findings,
            'uncalled_private': uncalled
        }

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return None


def main():
    """Main entry point."""
    root_dir = Path("/home/user/Isaac/isaac")

    print("=" * 70)
    print("ISAAC UNREACHABLE CODE DETECTOR")
    print("Agent 5: Dead Code Hunter")
    print("=" * 70)
    print()

    python_files = list(root_dir.rglob("*.py"))
    print(f"Scanning {len(python_files)} Python files...")
    print()

    all_unreachable = []
    all_uncalled = {}

    for filepath in python_files:
        result = analyze_file(filepath)
        if result:
            if result['unreachable']:
                all_unreachable.extend(result['unreachable'])
            if result['uncalled_private']:
                all_uncalled[str(filepath)] = result['uncalled_private']

    # Write results
    output_file = "/home/user/Isaac/UNREACHABLE_CODE.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Unreachable Code Analysis\n\n")
        f.write("**Agent 5: Dead Code Hunter**\n\n")
        f.write(f"**Total files analyzed:** {len(python_files)}\n\n")

        # Section 1: Unreachable code after return/raise
        f.write("## 1. Code After Terminating Statements\n\n")
        f.write(f"**Unreachable blocks found:** {len(all_unreachable)}\n\n")

        if not all_unreachable:
            f.write("✓ No unreachable code detected!\n\n")
        else:
            for i, item in enumerate(all_unreachable, 1):
                rel_path = Path(item['file']).relative_to("/home/user/Isaac")
                f.write(f"### {i}. `{rel_path}:{item['line']}`\n\n")
                f.write(f"- **Location:** Line {item['line']} in `{item['context']}`\n")
                f.write(f"- **Reason:** Code {item['reason']}\n")
                f.write(f"- **Lines affected:** {item['num_lines']}\n\n")
                f.write("```python\n")
                f.write(item['snippet'])
                f.write("\n```\n\n")
                f.write("**Recommendation:** Delete or fix control flow\n\n")
                f.write("---\n\n")

        # Section 2: Uncalled private functions
        f.write("\n## 2. Potentially Unused Private Functions\n\n")
        f.write(f"**Files with uncalled private functions:** {len(all_uncalled)}\n\n")

        if not all_uncalled:
            f.write("✓ No obviously uncalled private functions detected!\n\n")
        else:
            f.write("**Note:** These are private functions (starting with `_`) that don't appear to be called ")
            f.write("within their own module. They may still be called from other modules or used as callbacks.\n\n")

            for filepath, functions in sorted(all_uncalled.items()):
                rel_path = Path(filepath).relative_to("/home/user/Isaac")
                f.write(f"### `{rel_path}`\n\n")
                for func in sorted(functions):
                    f.write(f"- `{func}()`\n")
                f.write("\n")

    print(f"✓ Analysis complete!")
    print(f"  Unreachable code blocks: {len(all_unreachable)}")
    print(f"  Files with uncalled private functions: {len(all_uncalled)}")
    print(f"\n  Results written to: {output_file}")


if __name__ == "__main__":
    main()
