"""
XaiCollectionsClient - Wrapper for xAI Collections API using official SDK
Enables semantic search over uploaded collections (file logs, documents, etc.)

Updated to use the official xai-sdk instead of direct HTTP requests.
"""

import os
import requests
from typing import Dict, List, Optional

try:
    from xai_sdk import Client
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    Client = None


class XaiCollectionsClient:
    """Client for xAI Collections API integration using official SDK."""

    def __init__(self, api_key: str, management_api_key: Optional[str] = None, 
                 base_url: str = "https://api.x.ai/v1", 
                 api_host: str = "api.x.ai", management_api_host: str = "management-api.x.ai"):
        """
        Initialize xAI Collections API client.

        Args:
            api_key: x.ai API key
            management_api_key: x.ai management API key (optional, required for collection management)
            base_url: API base URL (used for fallback HTTP client only)
            api_host: Host for regular API operations (default: api.x.ai)
            management_api_host: Host for management API operations (default: management-api.x.ai)
        """
        self.api_key = api_key
        self.management_api_key = management_api_key or os.getenv("XAI_MANAGEMENT_API_KEY")
        self.base_url = base_url  # Store base_url for both SDK and HTTP modes
        self.api_host = api_host
        self.management_api_host = management_api_host
        self.timeout = 15  # Default timeout for HTTP fallback
        
        if SDK_AVAILABLE and Client is not None:
            # Use official SDK with configurable hosts
            self.client = Client(
                api_key=api_key,
                management_api_key=self.management_api_key,
                api_host=self.api_host,
                management_api_host=self.management_api_host,
                timeout=3600  # Extended timeout for reasoning models
            )
            self.use_sdk = True
        else:
            # Fallback to HTTP client
            self.base_url = base_url.rstrip('/')
            self.timeout = 15
            self.use_sdk = False

    def test_connection(self) -> bool:
        """
        Test if the Collections API is accessible.
        
        Returns:
            True if API responds (even with auth error), False if 404/not found
        """
        if self.use_sdk:
            try:
                # Try to list collections to test connection
                self.client.collections.list()
                return True
            except Exception as e:
                # Check if it's an auth error (API exists) vs 404 (API doesn't exist)
                error_str = str(e).lower()
                if '404' in error_str or 'not found' in error_str:
                    return False
                return True  # Other errors likely mean API exists but auth/other issues
        else:
            # Fallback HTTP implementation
            try:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                response = requests.get(
                    f"{self.base_url}/collections",
                    headers=headers,
                    timeout=10
                )
                
                return response.status_code != 404
                
            except requests.exceptions.Timeout:
                return False
            except requests.exceptions.ConnectionError:
                return False
            except Exception:
                return False

    def list_collections(self) -> List[Dict]:
        """
        Get all available collections for the user.

        Returns:
            List of collection dicts with metadata
        """
        if self.use_sdk:
            try:
                # Use official SDK
                collections = self.client.collections.list()
                # Convert SDK response to expected format
                if hasattr(collections, 'data'):
                    return [{"id": c.id, "name": c.name, "created_at": getattr(c, 'created_at', None)} 
                           for c in collections.data]
                else:
                    return []
            except Exception as e:
                raise Exception(f"Collections list error (SDK): {str(e)}")
        else:
            # Fallback HTTP implementation
            try:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }

                response = requests.get(
                    f"{self.base_url}/api/v1/list",
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get('collections', [])
                else:
                    raise Exception(f"API error {response.status_code}: {response.text}\nAttempted URL: {response.url}")

            except requests.exceptions.Timeout:
                raise Exception(f"Collections API timeout ({self.timeout} seconds)")
            except requests.exceptions.ConnectionError:
                raise Exception("Network connection failed")
            except Exception as e:
                raise Exception(f"Collections list error: {str(e)}")

    def search_collection(self, collection_id: str, query: str,
                         top_k: int = 5) -> Dict:
        """
        Semantic search within a collection.

        Args:
            collection_id: Collection UUID
            query: Natural language search query
            top_k: Number of results to return

        Returns:
            {
                "results": [
                    {
                        "content": "file content snippet",
                        "metadata": {"filename": "...", "timestamp": "..."},
                        "score": 0.95
                    }
                ],
                "query": "original query"
            }
        """
        if self.use_sdk:
            try:
                # Use official SDK
                search_results = self.client.collections.search(
                    collection_ids=[collection_id],  # SDK expects plural collection_ids
                    query=query,
                    limit=top_k
                )
                
                # Convert SDK response to expected format
                results = []
                try:
                    # Try different possible response structures
                    if hasattr(search_results, 'data') and getattr(search_results, 'data', None):  # type: ignore
                        results_data = search_results.data  # type: ignore
                    elif hasattr(search_results, 'results') and getattr(search_results, 'results', None):  # type: ignore
                        results_data = search_results.results  # type: ignore
                    elif isinstance(search_results, list):
                        results_data = search_results
                    else:
                        # If we can't determine the structure, return empty results
                        results_data = []
                    
                    for result in results_data:
                        if hasattr(result, 'content') or hasattr(result, 'metadata') or hasattr(result, 'score'):
                            results.append({
                                "content": getattr(result, 'content', ''),
                                "metadata": getattr(result, 'metadata', {}),
                                "score": getattr(result, 'score', 0.0)
                            })
                        else:
                            # If result doesn't have expected attributes, try to convert it directly
                            results.append({
                                "content": str(result),
                                "metadata": {},
                                "score": 0.0
                            })
                except Exception:
                    # If all else fails, return empty results
                    results = []
                
                return {
                    "results": results,
                    "query": query
                }
                
            except Exception as e:
                raise Exception(f"Collections search error (SDK): {str(e)}")
        else:
            # Fallback HTTP implementation
            try:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }

                payload = {
                    "collection_id": collection_id,
                    "query": query,
                    "top_k": top_k
                }

                response = requests.post(
                    f"{self.base_url}/collections/{collection_id}/search",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()

                    # Validate response format
                    if not isinstance(data, dict):
                        raise Exception("Invalid response format: expected dict")

                    # Ensure results array exists
                    if 'results' not in data:
                        data['results'] = []

                    # Add original query for context
                    data['query'] = query

                    return data

                else:
                    raise Exception(f"Search API error {response.status_code}: {response.text}\nAttempted URL: {response.url}")

            except requests.exceptions.Timeout:
                raise Exception(f"Collections search timeout ({self.timeout} seconds)")
            except requests.exceptions.ConnectionError:
                raise Exception("Network connection failed")
            except Exception as e:
                raise Exception(f"Collections search error: {str(e)}")

    def get_collection_info(self, collection_id: str) -> Dict:
        """
        Get collection metadata (name, file count, created date).

        Args:
            collection_id: Collection UUID

        Returns:
            Collection metadata dict
        """
        if self.use_sdk:
            try:
                # Use official SDK
                collection = self.client.collections.get(collection_id)
                return {
                    "id": collection.id,
                    "name": collection.name,
                    "created_at": getattr(collection, 'created_at', None),
                    "file_count": getattr(collection, 'file_count', 0),
                    "status": getattr(collection, 'status', 'unknown')
                }
            except Exception as e:
                raise Exception(f"Collections info error (SDK): {str(e)}")
        else:
            # Fallback HTTP implementation
            try:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }

                response = requests.get(
                    f"{self.base_url}/api/v1/{collection_id}/info",
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"API error {response.status_code}: {response.text}\nAttempted URL: {response.url}")

            except requests.exceptions.Timeout:
                raise Exception(f"Collections info timeout ({self.timeout} seconds)")
            except requests.exceptions.ConnectionError:
                raise Exception("Network connection failed")
            except Exception as e:
                raise Exception(f"Collections info error: {str(e)}")

    def create_collection(self, name: str, model_name: Optional[str] = None, 
                         chunk_configuration: Optional[Dict] = None) -> Dict:
        """
        Create a new collection.

        Args:
            name: Collection name
            model_name: Optional model name for embeddings
            chunk_configuration: Optional chunking configuration

        Returns:
            Collection creation response
        """
        if self.use_sdk:
            try:
                # Use official SDK
                kwargs = {"name": name}
                if model_name:
                    kwargs["model_name"] = model_name
                if chunk_configuration:
                    kwargs["chunk_configuration"] = chunk_configuration
                    
                collection = self.client.collections.create(**kwargs)
                return {
                    "id": collection.id,
                    "name": collection.name,
                    "status": getattr(collection, 'status', 'created'),
                    "created_at": getattr(collection, 'created_at', None)
                }
            except Exception as e:
                raise Exception(f"Collections create error (SDK): {str(e)}")
        else:
            # Fallback HTTP implementation
            try:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }

                payload = {"name": name}
                if model_name:
                    payload["model_name"] = model_name
                if chunk_configuration:
                    payload["chunk_configuration"] = chunk_configuration

                response = requests.post(
                    f"{self.base_url}/collections",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    raise Exception(f"API error {response.status_code}: {response.text}\nAttempted URL: {response.url}")

            except requests.exceptions.Timeout:
                raise Exception(f"Collections create timeout ({self.timeout} seconds)")
            except requests.exceptions.ConnectionError:
                raise Exception("Network connection failed")
            except Exception as e:
                raise Exception(f"Collections create error: {str(e)}")