#!/usr/bin/env python3
"""
Commented Code Block Detector for ISAAC Project
Agent 5: Dead Code Hunter

Finds blocks of commented-out code that should be removed.
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple


def is_likely_code(line: str) -> bool:
    """Determine if a commented line looks like code rather than a comment."""
    line = line.strip()

    # Remove comment marker
    if line.startswith('#'):
        line = line[1:].strip()

    # Empty or very short - probably not code
    if len(line) < 3:
        return False

    # Common documentation patterns - not code
    doc_patterns = [
        r'^[A-Z][a-z]+:',  # "Note:", "Todo:", etc.
        r'^[-*+]',  # List items
        r'^\d+\.',  # Numbered lists
        r'^[A-Z\s]+$',  # All caps (headers)
        r'^\w+\s+\w+\s+\w+',  # Regular sentences
    ]

    for pattern in doc_patterns:
        if re.match(pattern, line):
            return False

    # Code patterns
    code_patterns = [
        r'^\s*(def|class|if|for|while|try|except|import|from|return|raise)',
        r'.*[=<>!]=',  # Comparisons
        r'.*\+=|-=|\*=|/=',  # Augmented assignments
        r'.*\(.*\)',  # Function calls
        r'.*\[.*\]',  # Indexing/lists
        r'.*\{.*\}',  # Dicts
        r'^[a-z_][a-z0-9_]*\s*=',  # Variable assignment
        r'^\s*\.',  # Method calls
        r'print\(',  # Print statements
    ]

    for pattern in code_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return True

    return False


def find_commented_code(filepath: Path) -> List[Dict]:
    """Find commented code blocks in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        findings = []
        in_comment_block = False
        block_start = 0
        block_lines = []
        comment_block_count = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for commented code
            if stripped.startswith('#') and not stripped.startswith('#!/'):
                if is_likely_code(stripped):
                    if not in_comment_block:
                        in_comment_block = True
                        block_start = i
                        block_lines = [line]
                        comment_block_count = 1
                    else:
                        block_lines.append(line)
                        comment_block_count += 1
                elif in_comment_block:
                    # Continue block even with non-code comments
                    block_lines.append(line)
            else:
                # End of comment block
                if in_comment_block and comment_block_count >= 3:
                    # Only report blocks with 3+ lines of commented code
                    snippet = ''.join(block_lines[:2] + (['...\n'] if len(block_lines) > 4 else []) + block_lines[-2:])

                    findings.append({
                        'file': str(filepath),
                        'line': block_start,
                        'num_lines': len(block_lines),
                        'code_lines': comment_block_count,
                        'snippet': snippet.rstrip(),
                        'type': 'Commented code block'
                    })

                in_comment_block = False
                block_lines = []
                comment_block_count = 0

        # Check for end of file block
        if in_comment_block and comment_block_count >= 3:
            snippet = ''.join(block_lines[:2] + (['...\n'] if len(block_lines) > 4 else []) + block_lines[-2:])
            findings.append({
                'file': str(filepath),
                'line': block_start,
                'num_lines': len(block_lines),
                'code_lines': comment_block_count,
                'snippet': snippet.rstrip(),
                'type': 'Commented code block'
            })

        # Check for "if False:" blocks
        content = ''.join(lines)
        if_false_pattern = r'if\s+False\s*:'
        for match in re.finditer(if_false_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            # Try to find the extent of the block
            start_pos = match.end()
            indent_match = re.search(r'\n(\s+)', content[start_pos:])
            if indent_match:
                base_indent = indent_match.group(1)
                # Find where block ends
                end_match = re.search(f'\n(?!{base_indent})', content[start_pos:])
                if end_match:
                    block = content[start_pos:start_pos + end_match.start()]
                    num_lines = block.count('\n')

                    snippet_lines = block.split('\n')[:4]
                    snippet = '\n'.join(snippet_lines)
                    if len(block.split('\n')) > 4:
                        snippet += '\n...'

                    findings.append({
                        'file': str(filepath),
                        'line': line_num,
                        'num_lines': num_lines,
                        'code_lines': num_lines,
                        'snippet': f"if False:\n{snippet}",
                        'type': 'if False: block'
                    })

        return findings

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return []


def main():
    """Main entry point."""
    root_dir = Path("/home/user/Isaac/isaac")

    print("=" * 70)
    print("ISAAC COMMENTED CODE DETECTOR")
    print("Agent 5: Dead Code Hunter")
    print("=" * 70)
    print()

    python_files = list(root_dir.rglob("*.py"))
    print(f"Scanning {len(python_files)} Python files...")
    print()

    all_findings = []

    for filepath in python_files:
        findings = find_commented_code(filepath)
        all_findings.extend(findings)

    # Sort by file and line
    all_findings.sort(key=lambda x: (x['file'], x['line']))

    # Write results
    output_file = "/home/user/Isaac/COMMENTED_CODE.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Commented Code Blocks Analysis\n\n")
        f.write("**Agent 5: Dead Code Hunter**\n\n")
        f.write(f"**Total files analyzed:** {len(python_files)}\n\n")
        f.write(f"**Commented code blocks found:** {len(all_findings)}\n\n")

        if not all_findings:
            f.write("✓ No significant commented code blocks detected!\n")
        else:
            # Summary statistics
            total_lines = sum(item['num_lines'] for item in all_findings)
            f.write(f"**Total lines of commented code:** {total_lines}\n\n")

            # Count by type
            types = {}
            for item in all_findings:
                t = item['type']
                types[t] = types.get(t, 0) + 1

            f.write("## Summary by Type\n\n")
            for t, count in sorted(types.items(), key=lambda x: -x[1]):
                f.write(f"- **{t}:** {count} blocks\n")

            f.write("\n---\n\n")
            f.write("## Detailed Findings\n\n")
            f.write("### Guidelines\n\n")
            f.write("- **Keep:** Commented examples, documentation, TODO with explanation\n")
            f.write("- **Delete:** Old implementations, debug print statements, experiments without explanation\n\n")
            f.write("---\n\n")

            current_file = None
            for i, item in enumerate(all_findings, 1):
                file_path = Path(item['file'])
                rel_path = file_path.relative_to("/home/user/Isaac")

                if str(rel_path) != current_file:
                    current_file = str(rel_path)
                    f.write(f"\n### File: `{rel_path}`\n\n")

                f.write(f"#### Block {i} - Line {item['line']}\n\n")
                f.write(f"- **Type:** {item['type']}\n")
                f.write(f"- **Lines:** {item['num_lines']}\n")
                f.write(f"- **Location:** `{rel_path}:{item['line']}`\n\n")
                f.write("```python\n")
                f.write(item['snippet'])
                f.write("\n```\n\n")
                f.write("**Recommendation:** Review and decide - Keep or Delete\n\n")
                f.write("---\n\n")

    print(f"✓ Analysis complete!")
    print(f"  Commented code blocks found: {len(all_findings)}")
    print(f"  Total lines: {sum(item['num_lines'] for item in all_findings)}")
    print(f"\n  Results written to: {output_file}")
    print()

    # Show top files with most commented code
    if all_findings:
        file_counts = {}
        for item in all_findings:
            file = item['file']
            file_counts[file] = file_counts.get(file, 0) + item['num_lines']

        print("Top 10 files with most commented code lines:")
        for file, lines in sorted(file_counts.items(), key=lambda x: -x[1])[:10]:
            rel_path = Path(file).relative_to("/home/user/Isaac")
            print(f"  {lines:3d} lines  {rel_path}")


if __name__ == "__main__":
    main()
