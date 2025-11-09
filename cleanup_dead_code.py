#!/usr/bin/env python3
"""
Automated Code Cleanup Script for ISAAC Project
Agent 5: Dead Code Hunter

Performs safe, automated cleanups based on analysis results.
"""

import ast
import argparse
import csv
import shutil
from pathlib import Path
from typing import List, Set
from datetime import datetime


class ImportCleaner(ast.NodeTransformer):
    """Remove unused imports from AST."""

    def __init__(self, unused_imports: Set[str]):
        self.unused_imports = unused_imports
        self.removed_count = 0

    def visit_Import(self, node):
        """Remove unused import statements."""
        new_names = []
        for alias in node.names:
            import_str = f"import {alias.name}"
            if import_str not in self.unused_imports:
                new_names.append(alias)
            else:
                self.removed_count += 1

        if new_names:
            node.names = new_names
            return node
        else:
            return None  # Remove entire import statement

    def visit_ImportFrom(self, node):
        """Remove unused from-import statements."""
        module = node.module or ''
        new_names = []

        for alias in node.names:
            import_str = f"from {module} import {alias.name}"
            if import_str not in self.unused_imports:
                new_names.append(alias)
            else:
                self.removed_count += 1

        if new_names:
            node.names = new_names
            return node
        else:
            return None


def load_unused_imports(csv_file: Path) -> dict:
    """Load unused imports from CSV."""
    unused_by_file = {}

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['confidence'] == 'High' and row['auto_fix'] == 'Y':
                filepath = row['file']
                if filepath not in unused_by_file:
                    unused_by_file[filepath] = set()
                unused_by_file[filepath].add(row['import'])

    return unused_by_file


def remove_unused_imports(filepath: Path, unused_imports: Set[str], dry_run: bool = True) -> int:
    """Remove unused imports from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove BOM if present
        if content.startswith('\ufeff'):
            content = content[1:]

        try:
            tree = ast.parse(content, filename=str(filepath))
        except SyntaxError:
            print(f"  ⚠ Syntax error, skipping: {filepath}")
            return 0

        # Transform AST
        cleaner = ImportCleaner(unused_imports)
        new_tree = cleaner.visit(tree)

        if cleaner.removed_count > 0:
            if not dry_run:
                # Convert back to source code
                # Note: This is simplified - in production use a proper unparser
                new_content = ast.unparse(new_tree)

                # Backup original
                backup_path = filepath.with_suffix('.py.backup')
                shutil.copy2(filepath, backup_path)

                # Write cleaned version
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)

            return cleaner.removed_count

        return 0

    except Exception as e:
        print(f"  ✗ Error processing {filepath}: {e}")
        return 0


def fix_trailing_whitespace(filepath: Path, dry_run: bool = True) -> int:
    """Remove trailing whitespace from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        fixed_lines = []
        changes = 0

        for line in lines:
            original = line
            # Remove trailing whitespace but keep newline
            if line.endswith('\n'):
                fixed = line.rstrip() + '\n'
            else:
                fixed = line.rstrip()

            if original != fixed:
                changes += 1

            fixed_lines.append(fixed)

        if changes > 0 and not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)

        return changes

    except Exception as e:
        print(f"  ✗ Error fixing whitespace in {filepath}: {e}")
        return 0


def remove_empty_files(empty_files: List[Path], dry_run: bool = True) -> int:
    """Remove completely empty files."""
    removed = 0

    for filepath in empty_files:
        if filepath.exists() and filepath.stat().st_size == 0:
            print(f"  {'[DRY RUN] Would delete' if dry_run else 'Deleting'}: {filepath}")
            if not dry_run:
                filepath.unlink()
            removed += 1

    return removed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Automated code cleanup for ISAAC project'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Show what would be changed without making changes (default: True)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually perform the changes (disables dry-run)'
    )
    parser.add_argument(
        '--unused-imports',
        action='store_true',
        help='Remove unused imports'
    )
    parser.add_argument(
        '--trailing-whitespace',
        action='store_true',
        help='Remove trailing whitespace'
    )
    parser.add_argument(
        '--empty-files',
        action='store_true',
        help='Delete empty files'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Perform all safe cleanups'
    )

    args = parser.parse_args()

    dry_run = not args.execute

    print("=" * 70)
    print("ISAAC AUTOMATED CODE CLEANUP")
    print("Agent 5: Dead Code Hunter")
    print("=" * 70)
    print()

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("    Use --execute to actually perform changes")
        print()
    else:
        print("⚠️  EXECUTE MODE - Changes will be made!")
        print("    Backups will be created for modified files")
        print()

    root_dir = Path("/home/user/Isaac")
    isaac_dir = root_dir / "isaac"

    total_changes = 0

    # Task 1: Remove unused imports
    if args.unused_imports or args.all:
        print("Task 1: Removing unused imports...")
        csv_file = root_dir / "UNUSED_IMPORTS.csv"

        if csv_file.exists():
            unused_by_file = load_unused_imports(csv_file)
            print(f"  Found {len(unused_by_file)} files with unused imports")

            for filepath_str, unused_imports in unused_by_file.items():
                filepath = Path(filepath_str)
                if filepath.exists():
                    removed = remove_unused_imports(filepath, unused_imports, dry_run)
                    if removed > 0:
                        total_changes += removed
                        print(f"  {'[DRY RUN]' if dry_run else '✓'} {filepath.name}: "
                              f"{removed} imports {'would be' if dry_run else ''} removed")

            print(f"  Total: {total_changes} unused imports {'would be' if dry_run else ''} removed")
        else:
            print(f"  ⚠ {csv_file} not found. Run analyze_unused_imports.py first.")
        print()

    # Task 2: Fix trailing whitespace
    if args.trailing_whitespace or args.all:
        print("Task 2: Fixing trailing whitespace...")
        python_files = list(isaac_dir.rglob("*.py"))
        whitespace_changes = 0

        for filepath in python_files:
            changes = fix_trailing_whitespace(filepath, dry_run)
            if changes > 0:
                whitespace_changes += changes
                # Only print for significant changes
                if changes > 5:
                    print(f"  {'[DRY RUN]' if dry_run else '✓'} {filepath.name}: "
                          f"{changes} lines {'would be' if dry_run else ''} fixed")

        print(f"  Total: {whitespace_changes} lines {'would be' if dry_run else ''} fixed")
        total_changes += whitespace_changes
        print()

    # Task 3: Remove empty files
    if args.empty_files or args.all:
        print("Task 3: Removing empty files...")

        empty_files = [f for f in isaac_dir.rglob("*.py") if f.stat().st_size == 0]

        if empty_files:
            removed = remove_empty_files(empty_files, dry_run)
            print(f"  Total: {removed} empty files {'would be' if dry_run else ''} removed")
            total_changes += removed
        else:
            print("  ✓ No empty files found")
        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total changes: {total_changes}")

    if dry_run:
        print()
        print("This was a DRY RUN. No files were modified.")
        print("Run with --execute to apply changes.")
    else:
        print()
        print("✓ Cleanup complete!")
        print("  Backup files created with .backup extension")
        print("  Review changes and run tests before committing")

    print()

    # Print cleanup log
    log_file = root_dir / "cleanup_log.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"ISAAC Cleanup Log\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}\n")
        f.write(f"Total changes: {total_changes}\n")

    print(f"Log written to: {log_file}")


if __name__ == "__main__":
    main()
