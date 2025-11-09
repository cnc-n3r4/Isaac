#!/usr/bin/env python3
"""
Workspace Integration - Unified interface for workspace, session, and knowledge base management

Provides a single entry point for managing workspace-scoped AI contexts.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class WorkspaceContext:
    """
    Unified workspace context with automatic session and knowledge base binding

    Features:
    - Auto-detect workspace from current directory
    - Automatic AI session creation/binding
    - Automatic knowledge base initialization
    - Workspace switching with context preservation
    """

    def __init__(self, xai_api_key: Optional[str] = None, task_manager=None, message_queue=None):
        """
        Initialize workspace context manager

        Args:
            xai_api_key: xAI API key for AI client
            task_manager: Optional TaskManager for background operations
            message_queue: Optional MessageQueue for notifications
        """
        # Import managers (lazy to avoid circular imports)
        from isaac.core.workspace_sessions import get_workspace_manager
        from isaac.ai.session_manager import get_session_manager

        self.workspace_manager = get_workspace_manager()
        self.session_manager = get_session_manager()
        self.task_manager = task_manager
        self.message_queue = message_queue

        # XAI clients (lazy initialized)
        self.xai_api_key = xai_api_key
        self._xai_client = None
        self._collections_client = None

        # Current context
        self._current_workspace_path: Optional[Path] = None
        self._current_session_id: Optional[str] = None
        self._current_knowledge_base = None

        logger.info("Workspace context initialized")

    def _get_xai_client(self):
        """Lazy load xAI client"""
        if self._xai_client is None and self.xai_api_key:
            from isaac.ai.xai_client import XaiClient
            self._xai_client = XaiClient(
                api_key=self.xai_api_key,
                session_id=self._current_session_id
            )
        return self._xai_client

    def _get_collections_client(self):
        """Lazy load collections client"""
        if self._collections_client is None and self.xai_api_key:
            from isaac.ai.xai_collections_client import XaiCollectionsClient
            self._collections_client = XaiCollectionsClient(
                api_key=self.xai_api_key
            )
        return self._collections_client

    def activate_workspace(self, path: Optional[Path] = None, auto_index: bool = False) -> Dict[str, Any]:
        """
        Activate workspace with automatic session and knowledge base setup

        Args:
            path: Workspace path (default: auto-detect from cwd)
            auto_index: Automatically start indexing (default: False)

        Returns:
            Workspace activation result with metadata
        """
        # Detect workspace
        if path is None:
            workspace_path = self.workspace_manager.detect_workspace()
            if not workspace_path:
                return {
                    'success': False,
                    'error': 'No workspace detected. Are you in a project directory?'
                }
        else:
            workspace_path = Path(path).resolve()

        # Switch to workspace
        success, message = self.workspace_manager.switch_workspace(workspace_path)
        if not success:
            return {'success': False, 'error': message}

        # Get workspace name for session
        workspace_name = self.workspace_manager.get_workspace_name(workspace_path)

        # Get or create AI session for this workspace
        session_id = self.session_manager.get_or_create_session(workspace_name)

        # Bind session to workspace
        self.workspace_manager.bind_session(workspace_path, session_id)

        # Update current context
        self._current_workspace_path = workspace_path
        self._current_session_id = session_id

        # Update xAI client with new session
        if self._xai_client:
            self._xai_client.set_session_id(session_id)

        # Initialize knowledge base if collections client available
        collection_id = None
        if self._collections_client or self.xai_api_key:
            from isaac.ai.collections_core import get_knowledge_base

            kb = get_knowledge_base(
                project_root=workspace_path,
                xai_client=self._get_collections_client(),
                task_manager=self.task_manager
            )
            self._current_knowledge_base = kb

            # Get or create collection
            if not kb.collection_id:
                collection_name = f"isaac_{workspace_name}"
                try:
                    result = self._get_collections_client().create_collection(
                        name=collection_name,
                        chunk_configuration={'max_chunk_size': 2000}
                    )
                    kb.collection_id = result['id']
                    collection_id = result['id']

                    # Bind to workspace
                    self.workspace_manager.bind_collection(workspace_path, collection_id)

                    # Auto-index if requested
                    if auto_index:
                        task_id = kb.index_project_async()
                        logger.info(f"Started background indexing: {task_id}")

                except Exception as e:
                    logger.error(f"Failed to create collection: {e}")
            else:
                collection_id = kb.collection_id

        # Get session info
        session_info = self.session_manager.get_session_info(workspace_name)

        return {
            'success': True,
            'workspace': {
                'name': workspace_name,
                'path': str(workspace_path)
            },
            'session': {
                'id': session_id,
                'age': session_info.get('age') if session_info else None,
                'remaining': session_info.get('remaining') if session_info else None
            },
            'collection': {
                'id': collection_id
            } if collection_id else None,
            'message': f"Activated workspace '{workspace_name}'"
        }

    def get_current_context(self) -> Dict[str, Any]:
        """
        Get current workspace context

        Returns:
            Context metadata including workspace, session, and knowledge base info
        """
        if not self._current_workspace_path:
            return {
                'active': False,
                'message': 'No active workspace'
            }

        workspace_info = self.workspace_manager.get_workspace_info(self._current_workspace_path)
        if not workspace_info:
            return {
                'active': False,
                'message': 'Workspace not registered'
            }

        workspace_name = workspace_info['name']
        session_info = self.session_manager.get_session_info(workspace_name)

        kb_stats = None
        if self._current_knowledge_base:
            kb_stats = self._current_knowledge_base.get_stats()

        return {
            'active': True,
            'workspace': {
                'name': workspace_name,
                'path': str(self._current_workspace_path),
                'created_at': workspace_info.get('created_at'),
                'last_accessed': workspace_info.get('last_accessed')
            },
            'session': {
                'id': self._current_session_id,
                'age': session_info.get('age') if session_info else None,
                'remaining': session_info.get('remaining') if session_info else None,
                'rotations': session_info.get('rotation_count') if session_info else 0
            },
            'knowledge_base': kb_stats
        }

    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Chat with AI using current workspace context

        Args:
            prompt: User query
            system_prompt: Optional system context

        Returns:
            AI response

        Raises:
            Exception: If no xAI client configured or chat fails
        """
        client = self._get_xai_client()
        if not client:
            raise Exception("No xAI API key configured")

        return client.chat(prompt, system_prompt)

    def search_project(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Search current project knowledge base

        Args:
            query: Natural language search query
            top_k: Number of results

        Returns:
            Search results
        """
        if not self._current_knowledge_base:
            return {
                'success': False,
                'error': 'No knowledge base active. Activate a workspace first.'
            }

        return self._current_knowledge_base.search(query, top_k)

    def index_project(self, async_mode: bool = True) -> Optional[str]:
        """
        Index current project

        Args:
            async_mode: Run in background (default: True)

        Returns:
            Task ID if async, None if sync
        """
        if not self._current_knowledge_base:
            raise Exception("No knowledge base active. Activate a workspace first.")

        if async_mode:
            return self._current_knowledge_base.index_project_async()
        else:
            self._current_knowledge_base.index_project_sync()
            return None

    def switch_workspace(self, path: Path) -> Dict[str, Any]:
        """
        Switch to different workspace

        Args:
            path: Target workspace path

        Returns:
            Activation result
        """
        return self.activate_workspace(path)

    def list_workspaces(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered workspaces

        Returns:
            Dict mapping workspace paths to metadata
        """
        return self.workspace_manager.list_workspaces()


# Global instance (lazy loaded)
_workspace_context: Optional[WorkspaceContext] = None


def get_workspace_context(xai_api_key: Optional[str] = None,
                          task_manager=None,
                          message_queue=None) -> WorkspaceContext:
    """
    Get or create global workspace context instance

    Args:
        xai_api_key: xAI API key (only used on first call)
        task_manager: TaskManager instance (only used on first call)
        message_queue: MessageQueue instance (only used on first call)

    Returns:
        WorkspaceContext instance
    """
    global _workspace_context

    if _workspace_context is None:
        _workspace_context = WorkspaceContext(
            xai_api_key=xai_api_key,
            task_manager=task_manager,
            message_queue=message_queue
        )

    return _workspace_context


if __name__ == '__main__':
    # Test workspace integration
    import sys
    import os
    from pathlib import Path

    # Add project root to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    logging.basicConfig(level=logging.INFO)

    # Get API key from environment
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        print("Warning: XAI_API_KEY not set, some features will be unavailable")

    ctx = WorkspaceContext(xai_api_key=api_key)

    print("=== Workspace Integration Test ===\n")

    # Activate current workspace
    result = ctx.activate_workspace()
    print(f"Activation result:")
    print(f"  Success: {result['success']}")
    if result['success']:
        print(f"  Workspace: {result['workspace']['name']}")
        print(f"  Session ID: {result['session']['id']}")
        print(f"  Message: {result['message']}")

    # Get current context
    print("\nCurrent context:")
    context = ctx.get_current_context()
    if context['active']:
        print(f"  Workspace: {context['workspace']['name']}")
        print(f"  Path: {context['workspace']['path']}")
        print(f"  Session age: {context['session']['age']}")
        print(f"  Session remaining: {context['session']['remaining']}")

    # List workspaces
    print(f"\nAll workspaces: {len(ctx.list_workspaces())}")
    for ws_path, ws_data in ctx.list_workspaces().items():
        print(f"  {ws_data['name']}: {ws_path}")

    print("\n✓ Workspace integration test complete")
