"""
XaiCollectionsClient - HTTP wrapper for xAI Collections API
Enables semantic search over uploaded collections (file logs, documents, etc.)
"""

import requests
import json
from typing import Dict, List, Optional


class XaiCollectionsClient:
    """HTTP client for xAI Collections API integration."""

    def __init__(self, api_key: str, base_url: str = "https://api.x.ai/v1"):
        """
        Initialize xAI Collections API client.

        Args:
            api_key: x.ai API key
            base_url: API base URL (default: x.ai official)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = 15  # Collections searches can be slower

    def list_collections(self) -> List[Dict]:
        """
        Get all available collections for the user.

        Returns:
            List of collection dicts with metadata
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                f"{self.base_url}/collections",
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('collections', [])
            else:
                raise Exception(f"API error {response.status_code}: {response.text}")

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
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
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
                raise Exception(f"Search API error {response.status_code}: {response.text}")

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
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                f"{self.base_url}/collections/{collection_id}",
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API error {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            raise Exception(f"Collections info timeout ({self.timeout} seconds)")
        except requests.exceptions.ConnectionError:
            raise Exception("Network connection failed")
        except Exception as e:
            raise Exception(f"Collections info error: {str(e)}")