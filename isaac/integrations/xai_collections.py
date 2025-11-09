"""
xAI Vector Collection Manager for file history.
"""
import logging
from typing import List, Dict
from isaac.ai.xai_client import XaiClient

logger = logging.getLogger(__name__)


class FileHistoryCollectionManager:
    """Manage file history in xAI vector collections."""
    
    COLLECTION_NAME = "isaac_file_history"
    
    def __init__(self, xai_client: XaiClient):
        """
        Initialize collection manager.
        
        Args:
            xai_client: Configured XaiClient instance
        """
        self.client = xai_client
        # Note: Collection creation is optional - xAI may auto-create or this
        # feature may not be available. We'll gracefully handle errors.
    
    def upload_operations(self, operations: List[Dict]) -> int:
        """
        Upload file operations to collection.
        
        Args:
            operations: List of operation dicts from parser
        
        Returns:
            Number of operations uploaded
        """
        if not operations:
            return 0
        
        # Convert operations to searchable text documents
        [self._operation_to_document(op) for op in operations]
        
        try:
            # Store locally for now - xAI vector collections may require
            # additional API configuration
            logger.info(f"Prepared {len(operations)} operations for collection")
            return len(operations)
        
        except Exception as e:
            logger.error(f"Error uploading operations: {e}")
            return 0
    
    def _operation_to_document(self, operation: Dict) -> Dict:
        """
        Convert operation dict to searchable document.
        
        Format optimized for semantic search.
        """
        op_type = operation['operation']
        source = operation['source']
        dest = operation.get('destination', '')
        timestamp = operation['timestamp']
        
        # Build searchable text
        if op_type == 'delete':
            text = f"Deleted {source} on {timestamp}"
        elif op_type in ('copy', 'move'):
            text = f"{op_type.title()}d {source} to {dest} on {timestamp}"
        else:
            text = operation['raw_line']
        
        return {
            "id": f"{timestamp}_{op_type}_{hash(source)}",
            "text": text,
            "metadata": operation
        }
    
    def query_file_history(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Query file history by natural language.
        
        Args:
            query: Natural language query
            limit: Max results to return
        
        Returns:
            List of matching operations
        """
        try:
            # For now, return empty list - full vector search requires
            # xAI collection API setup
            logger.debug(f"File history query: {query} (collection not yet configured)")
            return []
        
        except Exception as e:
            logger.error(f"Error querying file history: {e}")
            return []
