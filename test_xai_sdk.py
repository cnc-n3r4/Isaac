#!/usr/bin/env python3
"""
Test script for the updated XaiCollectionsClient with SDK support.
This demonstrates the usage patterns from the x.ai documentation sample.
"""

import os
from isaac.ai.xai_collections_client import XaiCollectionsClient

def test_sdk_integration():
    """Test the SDK integration with sample code patterns."""
    
    # Initialize client (similar to x.ai sample)
    api_key = os.getenv("XAI_API_KEY")
    management_api_key = os.getenv("XAI_MANAGEMENT_API_KEY")
    
    if not api_key:
        print("❌ XAI_API_KEY environment variable not set")
        return
    
    try:
        # Initialize client
        client = XaiCollectionsClient(
            api_key=api_key,
            management_api_key=management_api_key
        )
        
        print("✓ XaiCollectionsClient initialized")
        print(f"  Using SDK: {client.use_sdk}")
        
        # Test connection
        if client.test_connection():
            print("✓ Connection test passed")
        else:
            print("❌ Connection test failed")
            return
        
        # Test search with a dummy collection ID (this will fail but test the method signature)
        try:
            # Use a dummy collection ID to test the method signature
            search_results = client.search_collection(
                collection_id="dummy-collection-id",
                query="test query",
                top_k=3
            )
            print(f"✓ Search method signature works: {len(search_results.get('results', []))} results")
        except Exception as e:
            error_str = str(e).lower()
            if "collection" in error_str and ("not found" in error_str or "invalid" in error_str):
                print("✓ Search method signature works (collection not found as expected)")
            else:
                print(f"❌ Search method failed unexpectedly: {str(e)}")
        
        # Test list collections (will fail without management key but test method)
        try:
            collections = client.list_collections()
            print(f"✓ Found {len(collections)} collections")
        except Exception as e:
            error_str = str(e).lower()
            if "management" in error_str and "key" in error_str:
                print("✓ List collections requires management key (as expected)")
            else:
                print(f"❌ List collections failed unexpectedly: {str(e)}")
        
    except Exception as e:
        print(f"❌ Client initialization failed: {str(e)}")

if __name__ == "__main__":
    print("Testing XaiCollectionsClient with SDK integration...")
    print()
    test_sdk_integration()