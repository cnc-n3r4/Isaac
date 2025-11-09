#!/usr/bin/env python3
"""
String & Constant Duplication Detector for ISAAC Project
Agent 5: Dead Code Hunter

Finds duplicate string literals, magic numbers, and repeated patterns.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


class DuplicationVisitor(ast.NodeVisitor):
    """Extract strings and constants from code."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.strings = defaultdict(list)  # string -> [(line, context)]
        self.numbers = defaultdict(list)  # number -> [(line, context)]

    def visit_Constant(self, node):
        """Visit constant nodes (Python 3.8+)."""
        if isinstance(node.value, str):
            # String literal
            s = node.value.strip()
            if len(s) >= 20:  # Only track longer strings
                # Skip docstrings (we check context)
                if not self._is_docstring(node):
                    self.strings[s].append(node.lineno)
        elif isinstance(node.value, (int, float)):
            # Number literal
            num = node.value
            # Skip common numbers
            if num not in (0, 1, -1, 2, 10, 100, 1000):
                self.numbers[num].append(node.lineno)

        self.generic_visit(node)

    def visit_Str(self, node):
        """Visit string nodes (Python < 3.8)."""
        s = node.s.strip()
        if len(s) >= 20:
            if not self._is_docstring(node):
                self.strings[s].append(node.lineno)
        self.generic_visit(node)

    def visit_Num(self, node):
        """Visit number nodes (Python < 3.8)."""
        num = node.n
        if num not in (0, 1, -1, 2, 10, 100, 1000):
            self.numbers[num].append(node.lineno)
        self.generic_visit(node)

    def _is_docstring(self, node) -> bool:
        """Check if a string constant is likely a docstring."""
        # This is a simple heuristic
        parent = getattr(node, '_parent', None)
        if parent and isinstance(parent, ast.Expr):
            return True
        return False


def find_regex_patterns(content: str, filepath: str) -> Dict[str, List[int]]:
    """Find duplicate regex patterns in the code."""
    patterns = defaultdict(list)

    # Find all re.compile() calls
    regex_calls = re.finditer(r're\.compile\s*\(\s*[\'"](.+?)[\'"]\s*[,)]', content)
    for match in regex_calls:
        pattern = match.group(1)
        if len(pattern) > 10:  # Only track longer patterns
            line_num = content[:match.start()].count('\n') + 1
            patterns[pattern].append(line_num)

    # Find all re.search/match/findall calls with inline patterns
    inline_patterns = re.finditer(r're\.(search|match|findall)\s*\(\s*[\'"](.+?)[\'"]\s*,', content)
    for match in inline_patterns:
        pattern = match.group(2)
        if len(pattern) > 10:
            line_num = content[:match.start()].count('\n') + 1
            patterns[pattern].append(line_num)

    return {k: v for k, v in patterns.items() if len(v) > 1}


def analyze_file(filepath: Path) -> Tuple[Dict, Dict, Dict]:
    """Analyze a file for duplicate strings and constants."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Remove BOM
        if content.startswith('\ufeff'):
            content = content[1:]

        # Extract regex patterns first (from raw text)
        regex_patterns = find_regex_patterns(content, str(filepath))

        try:
            tree = ast.parse(content, filename=str(filepath))
        except SyntaxError:
            return {}, {}, regex_patterns

        visitor = DuplicationVisitor(str(filepath))
        visitor.visit(tree)

        # Filter to only duplicates
        dup_strings = {k: v for k, v in visitor.strings.items() if len(v) > 1}
        dup_numbers = {k: v for k, v in visitor.numbers.items() if len(v) > 1}

        return dup_strings, dup_numbers, regex_patterns

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return {}, {}, {}


def main():
    """Main entry point."""
    root_dir = Path("/home/user/Isaac/isaac")

    print("=" * 70)
    print("ISAAC STRING & CONSTANT DUPLICATION DETECTOR")
    print("Agent 5: Dead Code Hunter")
    print("=" * 70)
    print()

    python_files = list(root_dir.rglob("*.py"))
    print(f"Scanning {len(python_files)} Python files...")
    print()

    # Global tracking
    global_strings = defaultdict(list)  # string -> [(file, lines)]
    global_numbers = defaultdict(list)  # number -> [(file, lines)]
    global_regexes = defaultdict(list)  # regex -> [(file, lines)]

    for filepath in python_files:
        dup_strings, dup_numbers, dup_regexes = analyze_file(filepath)

        # Aggregate strings
        for string, lines in dup_strings.items():
            global_strings[string].append((str(filepath), lines))

        # Aggregate numbers
        for number, lines in dup_numbers.items():
            global_numbers[number].append((str(filepath), lines))

        # Aggregate regexes
        for regex, lines in dup_regexes.items():
            global_regexes[regex].append((str(filepath), lines))

    # Find truly duplicated items (across multiple locations)
    cross_file_strings = {}
    for string, locations in global_strings.items():
        total_occurrences = sum(len(lines) for _, lines in locations)
        if total_occurrences > 2:  # More than 2 occurrences
            cross_file_strings[string] = locations

    cross_file_numbers = {}
    for number, locations in global_numbers.items():
        total_occurrences = sum(len(lines) for _, lines in locations)
        if total_occurrences > 3:  # More than 3 occurrences (numbers are more common)
            cross_file_numbers[number] = locations

    # Sort by frequency
    sorted_strings = sorted(cross_file_strings.items(),
                           key=lambda x: sum(len(lines) for _, lines in x[1]),
                           reverse=True)

    sorted_numbers = sorted(cross_file_numbers.items(),
                           key=lambda x: sum(len(lines) for _, lines in x[1]),
                           reverse=True)

    sorted_regexes = sorted(global_regexes.items(),
                           key=lambda x: sum(len(lines) for _, lines in x[1]),
                           reverse=True)

    # Write report
    output_file = Path("/home/user/Isaac/STRING_DUPLICATION.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# String & Constant Duplication Analysis\n\n")
        f.write("**Agent 5: Dead Code Hunter**\n\n")

        f.write("## Summary\n\n")
        f.write(f"- **Duplicate string literals:** {len(sorted_strings)}\n")
        f.write(f"- **Duplicate magic numbers:** {len(sorted_numbers)}\n")
        f.write(f"- **Duplicate regex patterns:** {len(sorted_regexes)}\n\n")

        # Duplicate strings
        f.write("---\n\n")
        f.write("## Duplicate String Literals\n\n")
        f.write(f"**Total found:** {len(sorted_strings)}\n\n")

        if sorted_strings:
            f.write("Top 20 most duplicated strings:\n\n")

            for i, (string, locations) in enumerate(sorted_strings[:20], 1):
                total = sum(len(lines) for _, lines in locations)
                num_files = len(locations)

                # Truncate long strings for display
                display_string = string[:100] + '...' if len(string) > 100 else string

                f.write(f"### {i}. String (occurs {total} times in {num_files} files)\n\n")
                f.write(f"```\n{display_string}\n```\n\n")
                f.write("**Locations:**\n\n")

                for filepath, lines in locations[:5]:  # Show first 5 files
                    rel_path = Path(filepath).relative_to("/home/user/Isaac")
                    lines_str = ', '.join(map(str, lines[:3]))
                    if len(lines) > 3:
                        lines_str += f' ... ({len(lines)} total)'
                    f.write(f"- `{rel_path}`: lines {lines_str}\n")

                if len(locations) > 5:
                    f.write(f"- ... and {len(locations) - 5} more files\n")

                f.write(f"\n**Recommendation:** Extract to constant `CONST_STRING_{i}`\n\n")
                f.write("---\n\n")

        # Duplicate numbers
        f.write("\n## Magic Numbers (Duplicate Numeric Literals)\n\n")
        f.write(f"**Total found:** {len(sorted_numbers)}\n\n")

        if sorted_numbers:
            f.write("Top 15 most used magic numbers:\n\n")

            for i, (number, locations) in enumerate(sorted_numbers[:15], 1):
                total = sum(len(lines) for _, lines in locations)
                num_files = len(locations)

                f.write(f"### {i}. Number: `{number}` (occurs {total} times in {num_files} files)\n\n")
                f.write("**Locations:**\n\n")

                for filepath, lines in locations[:5]:
                    rel_path = Path(filepath).relative_to("/home/user/Isaac")
                    lines_str = ', '.join(map(str, lines[:3]))
                    if len(lines) > 3:
                        lines_str += f' ... ({len(lines)} total)'
                    f.write(f"- `{rel_path}`: lines {lines_str}\n")

                if len(locations) > 5:
                    f.write(f"- ... and {len(locations) - 5} more files\n")

                f.write(f"\n**Recommendation:** Extract to constant (e.g., `MAX_RETRIES`, `TIMEOUT_SECONDS`)\n\n")
                f.write("---\n\n")

        # Duplicate regex patterns
        f.write("\n## Duplicate Regex Patterns\n\n")
        f.write(f"**Total found:** {len(sorted_regexes)}\n\n")

        if sorted_regexes:
            for i, (pattern, locations) in enumerate(sorted_regexes[:10], 1):
                total = sum(len(lines) for _, lines in locations)

                f.write(f"### {i}. Pattern (occurs {total} times)\n\n")
                f.write(f"```python\n{pattern}\n```\n\n")
                f.write("**Locations:**\n\n")

                for filepath, lines in locations:
                    rel_path = Path(filepath).relative_to("/home/user/Isaac")
                    f.write(f"- `{rel_path}`: lines {', '.join(map(str, lines))}\n")

                f.write(f"\n**Recommendation:** Extract to module-level compiled regex\n\n")
                f.write("---\n\n")

        # General recommendations
        f.write("\n## Recommendations\n\n")
        f.write("1. **Extract string constants** to a constants module or config file\n")
        f.write("2. **Replace magic numbers** with named constants that explain their meaning\n")
        f.write("3. **Compile regex patterns** once at module level for better performance\n")
        f.write("4. **Use configuration** for values that might change\n")
        f.write("5. **Document constants** with comments explaining their purpose\n\n")

    print(f"✓ Analysis complete!")
    print(f"  Duplicate strings: {len(sorted_strings)}")
    print(f"  Duplicate numbers: {len(sorted_numbers)}")
    print(f"  Duplicate regex patterns: {len(sorted_regexes)}")
    print(f"\n  Results written to: {output_file}")


if __name__ == "__main__":
    main()
