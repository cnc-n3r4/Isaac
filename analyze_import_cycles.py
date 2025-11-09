#!/usr/bin/env python3
"""
Import Cycle Detector for ISAAC Project
Agent 5: Dead Code Hunter

Detects circular import dependencies.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class ImportExtractor(ast.NodeVisitor):
    """Extract all imports from a file."""

    def __init__(self, current_module: str):
        self.current_module = current_module
        self.imports = set()

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.startswith('isaac'):
                self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.startswith('isaac'):
            self.imports.add(node.module)
        self.generic_visit(node)


def extract_imports(filepath: Path, root_dir: Path) -> Tuple[str, Set[str]]:
    """Extract imports from a Python file."""
    try:
        # Convert file path to module name
        rel_path = filepath.relative_to(root_dir)
        module_parts = list(rel_path.parts[:-1])  # Remove filename
        if filepath.stem != '__init__':
            module_parts.append(filepath.stem)

        module_name = '.'.join(module_parts)
        if not module_name.startswith('isaac'):
            module_name = 'isaac.' + module_name if module_name else 'isaac'

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Remove BOM
        if content.startswith('\ufeff'):
            content = content[1:]

        try:
            tree = ast.parse(content, filename=str(filepath))
        except SyntaxError:
            return module_name, set()

        extractor = ImportExtractor(module_name)
        extractor.visit(tree)

        return module_name, extractor.imports

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return '', set()


def find_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Find all cycles in the import graph using DFS."""
    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node: str) -> bool:
        """DFS to detect cycles."""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        if node in graph:
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True

        path.pop()
        rec_stack.remove(node)
        return False

    # Run DFS from each unvisited node
    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def assess_severity(cycle: List[str]) -> Tuple[str, str]:
    """Assess the severity of an import cycle."""
    length = len(cycle) - 1  # -1 because last element repeats first

    if length == 2:
        severity = "Critical"
        description = "Direct circular import (A imports B, B imports A)"
    elif length == 3:
        severity = "High"
        description = "Three-way circular import"
    elif length <= 5:
        severity = "Medium"
        description = f"{length}-way circular import"
    else:
        severity = "Low"
        description = f"Long cycle ({length} modules) - possibly indirect"

    return severity, description


def suggest_breaking_strategy(cycle: List[str]) -> str:
    """Suggest how to break the import cycle."""
    if len(cycle) <= 2:
        return "No cycle (single module)"

    strategies = []

    # Strategy 1: Look for common patterns
    if any('__init__' in m for m in cycle):
        strategies.append("Move imports out of __init__.py files")

    # Strategy 2: Suggest lazy imports
    strategies.append("Use lazy imports (import inside functions)")

    # Strategy 3: Suggest dependency inversion
    strategies.append("Extract shared dependencies to a separate module")

    # Strategy 4: Check for type hints
    strategies.append("Use TYPE_CHECKING for type hint imports")

    return " OR ".join(strategies)


def main():
    """Main entry point."""
    root_dir = Path("/home/user/Isaac")
    isaac_dir = root_dir / "isaac"

    print("=" * 70)
    print("ISAAC IMPORT CYCLE DETECTOR")
    print("Agent 5: Dead Code Hunter")
    print("=" * 70)
    print()

    # Build import graph
    print("Building import graph...")
    python_files = list(isaac_dir.rglob("*.py"))
    import_graph = defaultdict(set)

    for filepath in python_files:
        module_name, imports = extract_imports(filepath, root_dir)
        if module_name:
            import_graph[module_name] = imports

    print(f"Analyzed {len(python_files)} files")
    print(f"Found {len(import_graph)} modules with imports")
    print()

    # Find cycles
    print("Detecting cycles...")
    cycles = find_cycles(dict(import_graph))

    # Deduplicate cycles (same cycle in different orders)
    unique_cycles = []
    seen_cycles = set()

    for cycle in cycles:
        # Normalize cycle to start with smallest element
        if len(cycle) > 1:
            min_idx = cycle[:-1].index(min(cycle[:-1]))
            normalized = tuple(cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]])

            if normalized not in seen_cycles:
                seen_cycles.add(normalized)
                unique_cycles.append(cycle)

    print(f"Found {len(unique_cycles)} unique import cycles")
    print()

    # Write report
    output_file = root_dir / "IMPORT_CYCLES.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Import Cycle Analysis\n\n")
        f.write("**Agent 5: Dead Code Hunter**\n\n")
        f.write(f"**Modules analyzed:** {len(import_graph)}\n\n")
        f.write(f"**Import cycles found:** {len(unique_cycles)}\n\n")

        if not unique_cycles:
            f.write("✓ No circular import dependencies detected!\n\n")
            f.write("The ISAAC codebase has a clean import structure with no circular dependencies.\n")
        else:
            # Severity summary
            severities = {}
            for cycle in unique_cycles:
                severity, _ = assess_severity(cycle)
                severities[severity] = severities.get(severity, 0) + 1

            f.write("## Summary by Severity\n\n")
            for sev in ['Critical', 'High', 'Medium', 'Low']:
                if sev in severities:
                    f.write(f"- **{sev}:** {severities[sev]} cycles\n")

            f.write("\n---\n\n")
            f.write("## Detailed Findings\n\n")

            for i, cycle in enumerate(sorted(unique_cycles, key=lambda c: len(c)), 1):
                severity, description = assess_severity(cycle)
                strategy = suggest_breaking_strategy(cycle)

                f.write(f"### Cycle {i}: {severity} Severity\n\n")
                f.write(f"**Description:** {description}\n\n")
                f.write(f"**Cycle length:** {len(cycle) - 1} modules\n\n")

                f.write("**Import chain:**\n\n")
                f.write("```\n")
                for j in range(len(cycle) - 1):
                    f.write(f"{cycle[j]}\n")
                    f.write(f"  ↓ imports\n")
                f.write(f"{cycle[-1]}\n")
                f.write("```\n\n")

                f.write(f"**Modules involved:**\n\n")
                unique_modules = sorted(set(cycle[:-1]))
                for module in unique_modules:
                    f.write(f"- `{module}`\n")

                f.write(f"\n**Breaking strategy:** {strategy}\n\n")
                f.write(f"**Estimated effort:** ")
                if severity == "Critical":
                    f.write("2-4 hours (high priority)\n\n")
                elif severity == "High":
                    f.write("1-3 hours\n\n")
                elif severity == "Medium":
                    f.write("30 mins - 2 hours\n\n")
                else:
                    f.write("< 1 hour (low priority)\n\n")

                f.write("---\n\n")

            f.write("\n## Recommendations\n\n")
            f.write("1. **Address Critical and High severity cycles first** - these can cause import errors\n")
            f.write("2. **Use lazy imports** - import inside functions when possible\n")
            f.write("3. **Extract shared code** - move common dependencies to separate modules\n")
            f.write("4. **Use TYPE_CHECKING** - for type hint imports only\n")
            f.write("5. **Refactor module structure** - consider if modules have too many responsibilities\n\n")

    print(f"✓ Analysis complete!")
    print(f"  Import cycles found: {len(unique_cycles)}")
    print(f"\n  Results written to: {output_file}")
    print()

    if unique_cycles:
        print("Cycles by severity:")
        severities = {}
        for cycle in unique_cycles:
            severity, _ = assess_severity(cycle)
            severities[severity] = severities.get(severity, 0) + 1

        for sev in ['Critical', 'High', 'Medium', 'Low']:
            if sev in severities:
                print(f"  {severities[sev]:3d}  {sev}")


if __name__ == "__main__":
    main()
