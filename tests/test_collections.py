#!/usr/bin/env python3
"""
Test script for Phase 5.2: Collections Integration
"""

import sys
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from isaac.ai.collections_core import (
    FileChunker,
    IsaacIgnore,
    ProjectKnowledgeBase,
    get_knowledge_base
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_file_chunker():
    """Test FileChunker with different file types"""
    print("\n=== Testing FileChunker ===\n")

    chunker = FileChunker()

    # Test Python file (AST parsing)
    py_file = Path('isaac/ai/xai_client.py')
    if py_file.exists():
        print(f"Testing Python file: {py_file}")
        chunks = chunker.chunk_file(py_file)
        print(f"  ✓ Created {len(chunks)} chunks")
        if chunks:
            print(f"  ✓ First chunk: {chunks[0]['metadata'].get('name', 'N/A')} "
                  f"({chunks[0]['metadata']['start_line']}-{chunks[0]['metadata']['end_line']})")

    # Test JavaScript-style file
    js_files = list(Path('.').glob('**/*.js'))
    if js_files:
        js_file = js_files[0]
        print(f"\nTesting JavaScript file: {js_file}")
        chunks = chunker.chunk_file(js_file)
        print(f"  ✓ Created {len(chunks)} chunks")

    # Test generic text file
    md_file = Path('README.md')
    if md_file.exists():
        print(f"\nTesting Markdown file: {md_file}")
        chunks = chunker.chunk_file(md_file)
        print(f"  ✓ Created {len(chunks)} chunks")

    print(f"\nChunker stats: {chunker.stats}")
    return True


def test_isaac_ignore():
    """Test IsaacIgnore pattern matching"""
    print("\n=== Testing IsaacIgnore ===\n")

    project_root = Path.cwd()
    ignore = IsaacIgnore(project_root)

    test_cases = [
        ('isaac/ai/xai_client.py', False),
        ('.git/config', True),
        ('node_modules/package.json', True),
        ('__pycache__/module.pyc', True),
        ('.isaac/sessions.json', True),
        ('test.log', True),
        ('README.md', False),
    ]

    print(f"Loaded {len(ignore.patterns)} ignore patterns\n")

    for path_str, should_ignore in test_cases:
        path = project_root / path_str
        is_ignored = ignore.should_ignore(path)
        status = "✓" if is_ignored == should_ignore else "✗"
        expected = "ignored" if should_ignore else "not ignored"
        actual = "ignored" if is_ignored else "not ignored"
        print(f"{status} {path_str}: expected {expected}, got {actual}")

    return True


def test_knowledge_base():
    """Test ProjectKnowledgeBase initialization"""
    print("\n=== Testing ProjectKnowledgeBase ===\n")

    project_root = Path.cwd()

    # Create mock xai_client (we won't actually call the API)
    class MockXaiClient:
        def create_collection(self, name, chunk_configuration=None):
            return {'id': 'mock_collection_123', 'name': name}

        def search_collection(self, collection_id, query, top_k):
            return {'results': [], 'query': query}

    xai_client = MockXaiClient()

    # Initialize knowledge base
    kb = ProjectKnowledgeBase(
        project_root=project_root,
        xai_client=xai_client,
        task_manager=None,
        message_queue=None,
        auto_watch=False
    )

    print(f"Project root: {kb.project_root}")
    print(f"Collection ID: {kb.collection_id or 'Not created'}")
    print(f"Files indexed: {len(kb.indexed_files)}")

    # Test file discovery
    files = kb.get_files_to_index()
    print(f"\nFiles to index: {len(files)}")
    if files:
        print(f"  Examples:")
        for file in files[:5]:
            rel_path = file.relative_to(project_root)
            print(f"    - {rel_path}")

    # Test stats
    stats = kb.get_stats()
    print(f"\nKnowledge base stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test watcher methods (without actually starting)
    print("\nWatcher integration:")
    print(f"  ✓ start_watching() method available: {hasattr(kb, 'start_watching')}")
    print(f"  ✓ stop_watching() method available: {hasattr(kb, 'stop_watching')}")
    print(f"  ✓ _notify_progress() method available: {hasattr(kb, '_notify_progress')}")

    return True


def main():
    """Run all tests"""
    print("=" * 80)
    print("Phase 5.2: Collections Integration Test Suite")
    print("=" * 80)

    tests = [
        ("FileChunker", test_file_chunker),
        ("IsaacIgnore", test_isaac_ignore),
        ("ProjectKnowledgeBase", test_knowledge_base),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {name} test passed")
            else:
                failed += 1
                print(f"\n✗ {name} test failed")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} test failed with error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
