#!/usr/bin/env python3
"""
Code Hygiene Score Calculator for ISAAC Project
Agent 5: Dead Code Hunter

Synthesizes all analysis results into a comprehensive health score.
"""

import csv
from pathlib import Path
from typing import Dict


def count_csv_rows(filepath: Path) -> int:
    """Count rows in a CSV file (excluding header)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in csv.DictReader(f))
    except:
        return 0


def count_md_findings(filepath: Path, marker: str = "###") -> int:
    """Count findings in markdown file by counting header markers."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return content.count(marker)
    except:
        return 0


def extract_number_from_md(filepath: Path, search_text: str) -> int:
    """Extract a number following specific text in markdown."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            for line in lines:
                if search_text in line:
                    # Extract number
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        return int(numbers[0])
        return 0
    except:
        return 0


def calculate_scores() -> Dict:
    """Calculate individual category scores."""
    root_dir = Path("/home/user/Isaac")

    # Gather metrics
    metrics = {}

    # 1. Unused Imports (UNUSED_IMPORTS.csv)
    unused_imports = count_csv_rows(root_dir / "UNUSED_IMPORTS.csv")
    metrics['unused_imports'] = unused_imports

    # 2. Empty Files (EMPTY_FILES.md)
    empty_files = extract_number_from_md(
        root_dir / "EMPTY_FILES.md",
        "Empty/stub files found:"
    )
    metrics['empty_files'] = empty_files

    # 3. Commented Code (COMMENTED_CODE.md)
    commented_blocks = extract_number_from_md(
        root_dir / "COMMENTED_CODE.md",
        "Commented code blocks found:"
    )
    metrics['commented_blocks'] = commented_blocks

    # 4. Unreachable Code (UNREACHABLE_CODE.md)
    unreachable = extract_number_from_md(
        root_dir / "UNREACHABLE_CODE.md",
        "Unreachable blocks found:"
    )
    metrics['unreachable'] = unreachable

    # 5. Deprecated Code (DEPRECATED_CODE.md)
    deprecated = extract_number_from_md(
        root_dir / "DEPRECATED_CODE.md",
        "Deprecated/legacy items found:"
    )
    metrics['deprecated'] = deprecated

    # 6. Import Cycles (IMPORT_CYCLES.md)
    import_cycles = extract_number_from_md(
        root_dir / "IMPORT_CYCLES.md",
        "Import cycles found:"
    )
    critical_cycles = extract_number_from_md(
        root_dir / "IMPORT_CYCLES.md",
        "**Critical:**"
    )
    metrics['import_cycles'] = import_cycles
    metrics['critical_cycles'] = critical_cycles

    # 7. Complexity (CODE_COMPLEXITY.md)
    high_complexity = extract_number_from_md(
        root_dir / "CODE_COMPLEXITY.md",
        "High complexity functions"
    )
    long_functions = extract_number_from_md(
        root_dir / "CODE_COMPLEXITY.md",
        "Functions >50 lines:"
    )
    deeply_nested = extract_number_from_md(
        root_dir / "CODE_COMPLEXITY.md",
        "Deeply nested code"
    )
    metrics['high_complexity'] = high_complexity
    metrics['long_functions'] = long_functions
    metrics['deeply_nested'] = deeply_nested

    # 8. Duplication (STRING_DUPLICATION.md)
    dup_strings = extract_number_from_md(
        root_dir / "STRING_DUPLICATION.md",
        "Duplicate string literals:"
    )
    dup_numbers = extract_number_from_md(
        root_dir / "STRING_DUPLICATION.md",
        "Duplicate magic numbers:"
    )
    metrics['dup_strings'] = dup_strings
    metrics['dup_numbers'] = dup_numbers

    return metrics


def score_category(metric_value: int, excellent: int, good: int, fair: int, poor: int) -> Dict:
    """Score a metric based on thresholds."""
    if metric_value <= excellent:
        return {'score': 10, 'grade': 'A+', 'status': 'Excellent'}
    elif metric_value <= good:
        return {'score': 8, 'grade': 'A', 'status': 'Good'}
    elif metric_value <= fair:
        return {'score': 6, 'grade': 'B', 'status': 'Fair'}
    elif metric_value <= poor:
        return {'score': 4, 'grade': 'C', 'status': 'Needs Work'}
    else:
        return {'score': 2, 'grade': 'D', 'status': 'Critical'}


def main():
    """Main entry point."""
    print("=" * 70)
    print("ISAAC CODE HYGIENE SCORE")
    print("Agent 5: Dead Code Hunter")
    print("=" * 70)
    print()

    print("Collecting metrics from all analyses...")
    metrics = calculate_scores()

    print("Calculating scores...\n")

    # Calculate individual scores
    scores = {}

    # 1. Import Hygiene (unused imports)
    # Target: <50 excellent, <100 good, <200 fair, <400 poor
    scores['imports'] = score_category(
        metrics['unused_imports'],
        excellent=50, good=100, fair=200, poor=400
    )
    scores['imports']['metric'] = metrics['unused_imports']
    scores['imports']['name'] = 'Import Hygiene'

    # 2. Code Cleanliness (empty + commented + unreachable)
    code_issues = metrics['empty_files'] + metrics['commented_blocks'] + metrics['unreachable']
    scores['cleanliness'] = score_category(
        code_issues,
        excellent=10, good=25, fair=50, poor=100
    )
    scores['cleanliness']['metric'] = code_issues
    scores['cleanliness']['name'] = 'Code Cleanliness'

    # 3. Legacy Code (deprecated items)
    scores['legacy'] = score_category(
        metrics['deprecated'],
        excellent=5, good=10, fair=20, poor=40
    )
    scores['legacy']['metric'] = metrics['deprecated']
    scores['legacy']['name'] = 'Legacy Code'

    # 4. Architecture (import cycles, weight critical heavily)
    arch_score = metrics['import_cycles'] + (metrics['critical_cycles'] * 3)
    scores['architecture'] = score_category(
        arch_score,
        excellent=2, good=5, fair=10, poor=20
    )
    scores['architecture']['metric'] = f"{metrics['import_cycles']} cycles ({metrics['critical_cycles']} critical)"
    scores['architecture']['name'] = 'Architecture Health'

    # 5. Code Complexity (high complexity functions)
    scores['complexity'] = score_category(
        metrics['high_complexity'],
        excellent=50, good=100, fair=200, poor=300
    )
    scores['complexity']['metric'] = metrics['high_complexity']
    scores['complexity']['name'] = 'Code Complexity'

    # 6. Maintainability (long functions + deeply nested)
    maint_issues = metrics['long_functions'] + metrics['deeply_nested']
    scores['maintainability'] = score_category(
        maint_issues,
        excellent=100, good=200, fair=400, poor=600
    )
    scores['maintainability']['metric'] = maint_issues
    scores['maintainability']['name'] = 'Maintainability'

    # 7. Code Duplication
    dup_total = metrics['dup_strings'] + metrics['dup_numbers']
    scores['duplication'] = score_category(
        dup_total,
        excellent=20, good=40, fair=80, poor=150
    )
    scores['duplication']['metric'] = dup_total
    scores['duplication']['name'] = 'Code Duplication'

    # Calculate overall score (weighted average)
    weights = {
        'imports': 1.0,
        'cleanliness': 1.5,  # Higher weight - critical
        'legacy': 0.8,
        'architecture': 2.0,  # Highest weight - most important
        'complexity': 1.5,
        'maintainability': 1.2,
        'duplication': 1.0
    }

    weighted_sum = sum(scores[cat]['score'] * weights[cat] for cat in scores)
    total_weight = sum(weights.values())
    overall_score = weighted_sum / total_weight

    # Determine overall grade
    if overall_score >= 9:
        overall_grade = 'A+'
        overall_status = 'Excellent'
    elif overall_score >= 8:
        overall_grade = 'A'
        overall_status = 'Very Good'
    elif overall_score >= 7:
        overall_grade = 'B+'
        overall_status = 'Good'
    elif overall_score >= 6:
        overall_grade = 'B'
        overall_status = 'Fair'
    elif overall_score >= 5:
        overall_grade = 'C+'
        overall_status = 'Needs Improvement'
    else:
        overall_grade = 'C'
        overall_status = 'Needs Significant Work'

    # Write report
    output_file = Path("/home/user/Isaac/CODE_HYGIENE_SCORE.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# ISAAC Code Hygiene Score\n\n")
        f.write("**Agent 5: Dead Code Hunter - Final Report**\n\n")
        f.write("---\n\n")

        # Overall Score (big header)
        f.write(f"## Overall Health: {overall_score:.1f}/10 ({overall_grade})\n\n")
        f.write(f"**Status:** {overall_status}\n\n")
        f.write("---\n\n")

        # Category Breakdown
        f.write("## Category Scores\n\n")
        f.write("| Category | Score | Grade | Issues Found | Status |\n")
        f.write("|----------|-------|-------|--------------|--------|\n")

        for cat_key in ['architecture', 'complexity', 'cleanliness', 'maintainability',
                       'imports', 'duplication', 'legacy']:
            cat = scores[cat_key]
            f.write(f"| **{cat['name']}** | {cat['score']}/10 | {cat['grade']} | "
                   f"{cat['metric']} | {cat['status']} |\n")

        f.write("\n---\n\n")

        # Detailed Breakdown
        f.write("## Detailed Analysis\n\n")

        for cat_key in ['architecture', 'complexity', 'cleanliness', 'maintainability',
                       'imports', 'duplication', 'legacy']:
            cat = scores[cat_key]
            f.write(f"### {cat['name']}: {cat['score']}/10\n\n")
            f.write(f"- **Grade:** {cat['grade']}\n")
            f.write(f"- **Issues:** {cat['metric']}\n")
            f.write(f"- **Status:** {cat['status']}\n\n")

            # Recommendations based on score
            if cat['score'] >= 8:
                f.write(f"✓ **Excellent!** {cat['name']} is in great shape.\n\n")
            elif cat['score'] >= 6:
                f.write(f"⚠️ **Action needed:** Some improvements recommended for {cat['name']}.\n\n")
            else:
                f.write(f"🚨 **Critical:** {cat['name']} requires immediate attention.\n\n")

        # Key Findings
        f.write("---\n\n")
        f.write("## Key Findings\n\n")

        findings = []

        if metrics['critical_cycles'] > 0:
            findings.append(f"🚨 **{metrics['critical_cycles']} critical import cycles** - can cause import errors")

        if metrics['high_complexity'] > 100:
            findings.append(f"⚠️ **{metrics['high_complexity']} high complexity functions** - refactoring recommended")

        if metrics['unused_imports'] > 200:
            findings.append(f"⚠️ **{metrics['unused_imports']} unused imports** - cleanup recommended")

        if metrics['empty_files'] > 20:
            findings.append(f"⚠️ **{metrics['empty_files']} empty/stub files** - review for deletion")

        if not findings:
            f.write("✓ No critical issues found!\n\n")
        else:
            for finding in findings:
                f.write(f"- {finding}\n")
            f.write("\n")

        # Strengths
        f.write("---\n\n")
        f.write("## Strengths\n\n")

        strengths = []

        if metrics['commented_blocks'] < 5:
            strengths.append("✓ Very clean code with minimal commented-out code")

        if metrics['unreachable'] < 5:
            strengths.append("✓ Almost no unreachable code detected")

        if metrics['deprecated'] < 20:
            strengths.append("✓ Low amount of deprecated/legacy code")

        if scores['imports']['score'] >= 8:
            strengths.append("✓ Good import hygiene")

        if strengths:
            for strength in strengths:
                f.write(f"- {strength}\n")
        else:
            f.write("- Multiple areas need improvement\n")

        f.write("\n")

        # Action Items
        f.write("---\n\n")
        f.write("## Recommended Action Items\n\n")

        f.write("### Priority 1 (Critical)\n\n")
        if metrics['critical_cycles'] > 0:
            f.write(f"1. Fix {metrics['critical_cycles']} critical import cycles\n")
        if metrics['unreachable'] > 0:
            f.write(f"2. Remove {metrics['unreachable']} blocks of unreachable code\n")

        f.write("\n### Priority 2 (High)\n\n")
        if metrics['high_complexity'] > 50:
            f.write(f"1. Refactor top 20 most complex functions\n")
        if metrics['unused_imports'] > 100:
            f.write(f"2. Run automated cleanup for {metrics['unused_imports']} unused imports\n")
        if metrics['empty_files'] > 10:
            f.write(f"3. Review and delete {metrics['empty_files']} empty files\n")

        f.write("\n### Priority 3 (Medium)\n\n")
        if metrics['long_functions'] > 100:
            f.write(f"1. Break down {metrics['long_functions']} long functions\n")
        if metrics['dup_strings'] > 20:
            f.write(f"2. Extract {metrics['dup_strings']} duplicate string constants\n")
        if metrics['deprecated'] > 5:
            f.write(f"3. Remove or update {metrics['deprecated']} deprecated items\n")

        f.write("\n---\n\n")

        # Summary
        f.write("## Summary\n\n")
        f.write(f"The ISAAC codebase scores **{overall_score:.1f}/10** overall, "
               f"indicating **{overall_status.lower()}** code health.\n\n")

        if overall_score >= 8:
            f.write("The codebase is in excellent shape with only minor improvements needed. ")
            f.write("Continue maintaining current standards.\n\n")
        elif overall_score >= 6:
            f.write("The codebase is generally healthy but has some areas that need attention. ")
            f.write("Focus on the high-priority items to improve overall quality.\n\n")
        else:
            f.write("The codebase needs significant improvement. ")
            f.write("Prioritize critical issues and create a cleanup roadmap.\n\n")

    # Console output
    print("=" * 70)
    print(f"OVERALL SCORE: {overall_score:.1f}/10 ({overall_grade}) - {overall_status}")
    print("=" * 70)
    print()
    print("Category Breakdown:")
    for cat_key in ['architecture', 'complexity', 'cleanliness', 'maintainability',
                   'imports', 'duplication', 'legacy']:
        cat = scores[cat_key]
        print(f"  {cat['name']:.<30} {cat['score']}/10 ({cat['grade']})")
    print()
    print(f"✓ Report written to: {output_file}")


if __name__ == "__main__":
    main()
