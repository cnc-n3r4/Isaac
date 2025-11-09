"""Team collections for shared knowledge base."""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from .models import SharedResource, ResourceType


class TeamCollections:
    """Shared knowledge base for teams."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize team collections.

        Args:
            base_dir: Base directory for team collections (default: ~/.isaac/team_collections/)
        """
        self.base_dir = Path(base_dir or os.path.expanduser("~/.isaac/team_collections"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def share_collection(self, team_id: str, collection_id: str,
                        shared_by: str, name: str = "", description: str = "",
                        content: Optional[Dict] = None) -> SharedResource:
        """Share a collection with a team.

        Args:
            team_id: Team ID
            collection_id: Collection ID (or generate new one)
            shared_by: User ID sharing the collection
            name: Collection name
            description: Collection description
            content: Collection content data

        Returns:
            SharedResource object
        """
        # Create shared resource
        resource = SharedResource(
            resource_id=collection_id,
            resource_type=ResourceType.COLLECTION,
            team_id=team_id,
            shared_by=shared_by,
            name=name or f"Collection {datetime.now().strftime('%Y-%m-%d')}",
            description=description,
            metadata={
                'item_count': len(content.get('items', [])) if content else 0,
                'tags': content.get('tags', []) if content else [],
            }
        )

        # Save collection data
        if content:
            collection_file = self.base_dir / team_id / f"{collection_id}.json"
            collection_file.parent.mkdir(parents=True, exist_ok=True)
            with open(collection_file, 'w') as f:
                json.dump(content, f, indent=2)

        return resource

    def get_collection(self, team_id: str, collection_id: str) -> Optional[Dict]:
        """Get collection data.

        Args:
            team_id: Team ID
            collection_id: Collection ID

        Returns:
            Collection data dictionary or None if not found
        """
        collection_file = self.base_dir / team_id / f"{collection_id}.json"
        if not collection_file.exists():
            return None

        with open(collection_file) as f:
            return json.load(f)

    def update_collection(self, team_id: str, collection_id: str,
                         content: Dict, updated_by: str) -> bool:
        """Update a shared collection.

        Args:
            team_id: Team ID
            collection_id: Collection ID
            content: Updated collection content
            updated_by: User ID updating the collection

        Returns:
            True if updated, False on error
        """
        collection_file = self.base_dir / team_id / f"{collection_id}.json"
        collection_file.parent.mkdir(parents=True, exist_ok=True)

        # Add update metadata
        content['last_updated_by'] = updated_by
        content['last_updated_at'] = datetime.now().isoformat()

        try:
            with open(collection_file, 'w') as f:
                json.dump(content, f, indent=2)
            return True
        except Exception:
            return False

    def add_item(self, team_id: str, collection_id: str, item: Dict,
                added_by: str) -> bool:
        """Add an item to a shared collection.

        Args:
            team_id: Team ID
            collection_id: Collection ID
            item: Item data to add
            added_by: User ID adding the item

        Returns:
            True if added, False on error
        """
        content = self.get_collection(team_id, collection_id)
        if content is None:
            content = {'items': [], 'tags': []}

        # Add metadata to item
        item['added_by'] = added_by
        item['added_at'] = datetime.now().isoformat()

        # Add item
        content['items'].append(item)

        return self.update_collection(team_id, collection_id, content, added_by)

    def search_collections(self, team_id: str, query: str) -> List[Dict]:
        """Search collections for a team.

        Args:
            team_id: Team ID
            query: Search query

        Returns:
            List of matching items across all collections
        """
        results = []
        team_dir = self.base_dir / team_id

        if not team_dir.exists():
            return results

        query_lower = query.lower()

        for collection_file in team_dir.glob("*.json"):
            try:
                with open(collection_file) as f:
                    content = json.load(f)

                collection_id = collection_file.stem

                # Search in items
                for item in content.get('items', []):
                    # Search in item text fields
                    item_text = json.dumps(item).lower()
                    if query_lower in item_text:
                        results.append({
                            'collection_id': collection_id,
                            'item': item,
                            'match_type': 'content',
                        })

            except Exception:
                continue

        return results

    def delete_collection(self, team_id: str, collection_id: str) -> bool:
        """Delete a shared collection.

        Args:
            team_id: Team ID
            collection_id: Collection ID

        Returns:
            True if deleted, False if not found
        """
        collection_file = self.base_dir / team_id / f"{collection_id}.json"
        if collection_file.exists():
            collection_file.unlink()
            return True
        return False

    def list_collections(self, team_id: str) -> List[Dict]:
        """List all collections for a team.

        Args:
            team_id: Team ID

        Returns:
            List of collection metadata
        """
        collections = []
        team_dir = self.base_dir / team_id

        if not team_dir.exists():
            return collections

        for collection_file in team_dir.glob("*.json"):
            try:
                with open(collection_file) as f:
                    content = json.load(f)

                collections.append({
                    'collection_id': collection_file.stem,
                    'name': content.get('name', collection_file.stem),
                    'description': content.get('description', ''),
                    'item_count': len(content.get('items', [])),
                    'tags': content.get('tags', []),
                    'last_updated_at': content.get('last_updated_at'),
                    'last_updated_by': content.get('last_updated_by'),
                })
            except Exception:
                continue

        return collections

    def export_collection(self, team_id: str, collection_id: str, export_path: str) -> bool:
        """Export a collection to a file.

        Args:
            team_id: Team ID
            collection_id: Collection ID
            export_path: Path to export to

        Returns:
            True if exported, False on error
        """
        content = self.get_collection(team_id, collection_id)
        if content is None:
            return False

        try:
            with open(export_path, 'w') as f:
                json.dump(content, f, indent=2)
            return True
        except Exception:
            return False

    def import_collection(self, team_id: str, import_path: str,
                         shared_by: str, name: Optional[str] = None) -> Optional[str]:
        """Import a collection from a file.

        Args:
            team_id: Team ID
            import_path: Path to import from
            shared_by: User ID importing the collection
            name: Optional collection name

        Returns:
            Collection ID or None on error
        """
        try:
            with open(import_path) as f:
                content = json.load(f)

            # Generate collection ID
            import uuid
            collection_id = str(uuid.uuid4())

            # Update metadata
            if name:
                content['name'] = name
            content['imported_at'] = datetime.now().isoformat()
            content['imported_by'] = shared_by

            # Save collection
            collection_file = self.base_dir / team_id / f"{collection_id}.json"
            collection_file.parent.mkdir(parents=True, exist_ok=True)
            with open(collection_file, 'w') as f:
                json.dump(content, f, indent=2)

            return collection_id
        except Exception:
            return None
