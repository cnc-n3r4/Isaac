#!/usr/bin/env python3
"""
Test File Auditor for ISAAC Project
Agent 5: Dead Code Hunter

Audits all test_*.py files in the root directory.
"""

import ast
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def find_tested_feature(filepath: Path, content: str) -> str:
    """Try to determine what feature this test file tests."""
    filename = filepath.stem  # e.g., test_ai_router
    feature_name = filename.replace('test_', '')

    # Common patterns to search for
    patterns = [
        f'from isaac.*.{feature_name}',
        f'import isaac.*.{feature_name}',
        f'from isaac.ai.{feature_name}',
        f'from isaac.commands.{feature_name}',
        f'from isaac.core.{feature_name}',
    ]

    for pattern in patterns:
        if re.search(pattern.replace('.', r'\.').replace('*', '.*'), content):
            return feature_name

    # Try to find imports
    imports = re.findall(r'from\s+(isaac\.\S+)\s+import', content)
    if imports:
        return f"Multiple: {', '.join(set(imports[:3]))}"

    return feature_name


def feature_exists_in_codebase(feature_name: str) -> bool:
    """Check if the feature exists in the isaac/ directory."""
    if not feature_name or feature_name.startswith('Multiple'):
        return True  # Unknown, assume exists

    # Search for the feature in the codebase
    isaac_dir = Path("/home/user/Isaac/isaac")

    # Check for module file
    searches = [
        isaac_dir / f"{feature_name}.py",
        isaac_dir / "ai" / f"{feature_name}.py",
        isaac_dir / "core" / f"{feature_name}.py",
        isaac_dir / "commands" / feature_name / "run.py",
    ]

    for search_path in searches:
        if search_path.exists():
            return True

    # Also search by pattern
    matches = list(isaac_dir.rglob(f"*{feature_name}*.py"))
    return len(matches) > 0


def get_file_modified_date(filepath: Path) -> str:
    """Get the last modified date of a file."""
    try:
        stat = filepath.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        return mod_time.strftime("%Y-%m-%d")
    except:
        return "Unknown"


def count_test_functions(content: str) -> int:
    """Count the number of test functions in the file."""
    try:
        tree = ast.parse(content)
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    count += 1
        return count
    except:
        return 0


def analyze_test_file(filepath: Path) -> Dict:
    """Analyze a single test file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        feature = find_tested_feature(filepath, content)
        exists = feature_exists_in_codebase(feature)
        modified = get_file_modified_date(filepath)
        num_tests = count_test_functions(content)

        # Try to detect if tests would pass (basic check)
        # Look for incomplete test markers
        incomplete_markers = ['pass', 'TODO', 'FIXME', 'NotImplemented']
        has_incomplete = any(marker in content for marker in incomplete_markers)

        # Determine recommendation
        if not exists:
            recommendation = "Delete - feature doesn't exist"
        elif num_tests == 0:
            recommendation = "Delete - no test functions"
        elif has_incomplete:
            recommendation = "Review - contains incomplete tests"
        else:
            recommendation = "Keep - appears functional"

        return {
            'file': filepath.name,
            'feature': feature,
            'exists': 'Yes' if exists else 'No',
            'num_tests': num_tests,
            'modified': modified,
            'size': filepath.stat().st_size,
            'passes': 'Unknown',
            'recommendation': recommendation
        }

    except Exception as e:
        return {
            'file': filepath.name,
            'feature': 'Error analyzing',
            'exists': 'Unknown',
            'num_tests': 0,
            'modified': 'Unknown',
            'size': 0,
            'passes': 'Unknown',
            'recommendation': f'Error: {e}'
        }


def main():
    """Main entry point."""
    root_dir = Path("/home/user/Isaac")

    print("=" * 70)
    print("ISAAC TEST FILE AUDITOR")
    print("Agent 5: Dead Code Hunter")
    print("=" * 70)
    print()

    # Find all test_*.py files in root directory
    test_files = sorted(root_dir.glob("test_*.py"))

    print(f"Found {len(test_files)} test files in root directory")
    print()

    results = []
    for filepath in test_files:
        print(f"Analyzing {filepath.name}...")
        result = analyze_test_file(filepath)
        results.append(result)

    # Write markdown report
    output_file = root_dir / "TEST_FILE_AUDIT.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Test File Audit\n\n")
        f.write("**Agent 5: Dead Code Hunter**\n\n")
        f.write(f"**Test files analyzed:** {len(results)}\n\n")

        # Summary statistics
        total_tests = sum(r['num_tests'] for r in results)
        exists_count = sum(1 for r in results if r['exists'] == 'Yes')
        missing_count = sum(1 for r in results if r['exists'] == 'No')

        f.write("## Summary\n\n")
        f.write(f"- **Total test files:** {len(results)}\n")
        f.write(f"- **Total test functions:** {total_tests}\n")
        f.write(f"- **Features exist:** {exists_count}\n")
        f.write(f"- **Features missing:** {missing_count}\n\n")

        # Recommendations summary
        rec_counts = {}
        for r in results:
            rec = r['recommendation'].split(' - ')[0]  # Get first part
            rec_counts[rec] = rec_counts.get(rec, 0) + 1

        f.write("## Recommendations Summary\n\n")
        for rec, count in sorted(rec_counts.items(), key=lambda x: -x[1]):
            f.write(f"- **{rec}:** {count} files\n")

        f.write("\n---\n\n")
        f.write("## Detailed Analysis\n\n")

        # Table header
        f.write("| File | Feature | Exists? | Tests | Modified | Size | Recommendation |\n")
        f.write("|------|---------|---------|-------|----------|------|----------------|\n")

        for r in results:
            feature_short = r['feature'][:30] + '...' if len(r['feature']) > 30 else r['feature']
            size_kb = r['size'] // 1024
            f.write(f"| `{r['file']}` | {feature_short} | {r['exists']} | {r['num_tests']} | {r['modified']} | {size_kb}KB | {r['recommendation']} |\n")

        f.write("\n---\n\n")
        f.write("## Individual File Details\n\n")

        for i, r in enumerate(results, 1):
            f.write(f"### {i}. `{r['file']}`\n\n")
            f.write(f"- **Tests feature:** {r['feature']}\n")
            f.write(f"- **Feature exists in codebase:** {r['exists']}\n")
            f.write(f"- **Number of test functions:** {r['num_tests']}\n")
            f.write(f"- **Last modified:** {r['modified']}\n")
            f.write(f"- **File size:** {r['size']} bytes\n")
            f.write(f"- **Tests pass:** {r['passes']}\n")
            f.write(f"- **Recommendation:** {r['recommendation']}\n\n")

            # Additional details based on recommendation
            if r['exists'] == 'No':
                f.write(f"⚠️ **WARNING:** The feature `{r['feature']}` does not appear to exist in the codebase. This test file may be orphaned.\n\n")
            elif r['num_tests'] == 0:
                f.write(f"⚠️ **WARNING:** No test functions found in this file.\n\n")

            f.write("---\n\n")

    print(f"\n✓ Analysis complete!")
    print(f"  Test files analyzed: {len(results)}")
    print(f"  Total test functions: {total_tests}")
    print(f"  Features exist: {exists_count}")
    print(f"  Features missing: {missing_count}")
    print(f"\n  Results written to: {output_file}")
    print()

    # Show recommendations
    print("Recommendations:")
    for rec, count in sorted(rec_counts.items(), key=lambda x: -x[1]):
        print(f"  {count:3d}  {rec}")


if __name__ == "__main__":
    main()
