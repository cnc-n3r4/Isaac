#!/usr/bin/env python3
"""
Test script for xAI Collections Integration
"""

import sys
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent))

from isaac.commands.ask.run import _classify_query_intent

def test_query_classification():
    """Test query classification logic"""
    print("Testing Query Classification:")
    print("=" * 50)

    test_queries = [
        ('where did I move my backup files?', 'file_history', 'tc_logs'),
        ('show me all times I copied to the NAS', 'file_history', 'tc_logs'),
        ('what is docker?', 'chat', None),
        ('explain kubernetes networking', 'chat', None),
        ('when did I delete those temp files?', 'file_history', 'tc_logs'),
        ('find my project snapshots', 'file_history', 'cpf_logs'),
        ('where is alaska?', 'chat', None),
        ('show me my files', 'file_history', 'tc_logs'),
    ]

    passed = 0
    total = len(test_queries)

    for query, expected_intent, expected_collection in test_queries:
        intent, collection = _classify_query_intent(query)
        if intent == expected_intent and collection == expected_collection:
            status = "✓"
            passed += 1
        else:
            status = "✗"
        print(f"{status} {query[:35]:35} -> {intent:12} {collection or 'N/A':8}")

    print(f"\nQuery classification: {passed}/{total} tests passed")
    return passed == total

def test_collections_client():
    """Test Collections client initialization"""
    print("\nTesting Collections Client:")
    print("=" * 30)

    try:
        from isaac.ai.xai_collections_client import XaiCollectionsClient
        client = XaiCollectionsClient(api_key='test-key')
        print("✓ XaiCollectionsClient initialized successfully")
        print(f"  Base URL: {client.base_url}")
        print(f"  Timeout: {client.timeout}")
        return True
    except Exception as e:
        print(f"✗ Collections client error: {e}")
        return False

def test_config_command():
    """Test config command collections display"""
    print("\nTesting Config Command:")
    print("=" * 25)

    try:
        from isaac.commands.config.run import show_collections_config
        # Mock session data
        session = {
            'collections_enabled': True,
            'tc_log_collection_id': 'collection_ea35fd69-106d-4ded-9359-e31248430774',
            'cpf_log_collection_id': 'collection_ec1409e2-1071-4731-a3bc-af35fe59fbc6'
        }
        output = show_collections_config(session)
        print("✓ Collections config display:")
        for line in output.split('\n'):
            print(f"  {line}")
        return True
    except Exception as e:
        print(f"✗ Config command error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("xAI Collections Integration Test Suite")
    print("=" * 45)

    results = []
    results.append(test_query_classification())
    results.append(test_collections_client())
    results.append(test_config_command())

    passed = sum(results)
    total = len(results)

    print(f"\n{'='*45}")
    print(f"Integration Tests: {passed}/{total} suites passed")

    if passed == total:
        print("🎉 All integration tests passed!")
        print("\nNext steps:")
        print("1. Upload TC logs to xAI Collections portal")
        print("2. Get collection UUID and add to ~/.isaac/config.json")
        print("3. Test with real queries: /ask where did I move my files?")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()