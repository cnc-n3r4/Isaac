#!/usr/bin/env python3
"""
RAG Query Engine - Retrieval-Augmented Generation for codebase-aware AI

Combines semantic search from xAI Collections with AI chat for context-aware responses.
"""

import logging
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class RAGQueryEngine:
    """
    Retrieval-Augmented Generation engine

    Combines semantic search over project knowledge base with AI chat
    to provide codebase-aware responses.
    """

    def __init__(self, xai_client, knowledge_base=None, fallback_manager=None):
        """
        Initialize RAG query engine

        Args:
            xai_client: XaiClient for chat
            knowledge_base: ProjectKnowledgeBase for semantic search
            fallback_manager: Optional FallbackManager for graceful degradation
        """
        self.xai_client = xai_client
        self.knowledge_base = knowledge_base
        self.fallback_manager = fallback_manager

        # Configuration
        self.max_context_chunks = 5  # Max search results to include
        self.context_char_limit = 4000  # Max characters of context
        self.relevance_threshold = 0.5  # Minimum relevance score

        logger.info("RAG query engine initialized")

    def query(self, user_prompt: str,
             use_codebase: bool = True,
             top_k: int = 5,
             include_file_paths: bool = True) -> Dict[str, Any]:
        """
        Query with retrieval-augmented generation

        Args:
            user_prompt: User's question
            use_codebase: Search codebase for context (default: True)
            top_k: Number of search results to retrieve
            include_file_paths: Include file paths in context

        Returns:
            {
                'success': bool,
                'response': str,
                'context_used': List[Dict],  # Search results used
                'tokens_saved': int,  # Tokens saved by not including irrelevant context
                'source': str  # 'rag' or 'direct'
            }
        """
        # Determine if we should use RAG
        should_use_rag = use_codebase and self.knowledge_base is not None

        if not should_use_rag:
            # Direct chat without RAG
            return self._direct_query(user_prompt)

        # Perform semantic search
        search_results = self._search_codebase(user_prompt, top_k)

        if not search_results or len(search_results) == 0:
            logger.info("No relevant context found, using direct query")
            return self._direct_query(user_prompt)

        # Build context from search results
        context = self._build_context(search_results, include_file_paths)

        # Generate response with context
        return self._rag_query(user_prompt, context, search_results)

    def _search_codebase(self, query: str, top_k: int) -> List[Dict]:
        """Search codebase for relevant context"""
        try:
            result = self.knowledge_base.search(query, top_k=top_k)

            if result.get('success'):
                results = result.get('results', [])

                # Filter by relevance threshold
                filtered = [
                    r for r in results
                    if r.get('score', 0) >= self.relevance_threshold
                ]

                logger.info(f"Found {len(filtered)}/{len(results)} relevant results")
                return filtered
            else:
                logger.warning(f"Search failed: {result.get('error')}")
                return []

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def _build_context(self, search_results: List[Dict], include_file_paths: bool) -> str:
        """Build context string from search results"""
        context_parts = []
        total_chars = 0

        for i, result in enumerate(search_results):
            if total_chars >= self.context_char_limit:
                break

            content = result.get('content', '')
            metadata = result.get('metadata', {})
            result.get('score', 0)

            # Build context block
            block_parts = []

            if include_file_paths and metadata.get('file'):
                file_path = metadata['file']
                start_line = metadata.get('start_line', '?')
                end_line = metadata.get('end_line', '?')

                block_parts.append(f"[{file_path}:{start_line}-{end_line}]")

            block_parts.append(content)

            block = '\n'.join(block_parts)

            # Check if adding this block exceeds limit
            if total_chars + len(block) > self.context_char_limit:
                # Truncate block to fit
                remaining = self.context_char_limit - total_chars
                if remaining > 100:  # Only include if meaningful amount remains
                    block = block[:remaining] + "..."
                    context_parts.append(block)
                break

            context_parts.append(block)
            total_chars += len(block)

        context = "\n\n---\n\n".join(context_parts)

        logger.debug(f"Built context: {total_chars} chars from {len(context_parts)} chunks")

        return context

    def _rag_query(self, user_prompt: str, context: str, search_results: List[Dict]) -> Dict[str, Any]:
        """Query with RAG (context injection)"""
        # Build system prompt with context
        system_prompt = f"""You are an AI assistant helping with code questions.
You have access to relevant code from the project:

{context}

Use the above code context to answer the user's question accurately.
If the context doesn't contain relevant information, say so.
Include file paths and line numbers when referencing specific code."""

        # Call AI with context
        try:
            if self.fallback_manager:
                # Use fallback manager for resilience
                result = self.fallback_manager.call_with_fallback(
                    'xai_chat',
                    primary_fn=lambda: self.xai_client.chat(user_prompt, system_prompt),
                    fallback_fn=None,
                    queue_on_failure=False
                )

                if not result['success']:
                    return {
                        'success': False,
                        'error': result.get('error', 'AI service unavailable'),
                        'context_used': search_results,
                        'source': 'rag_failed'
                    }

                response = result['result']
            else:
                # Direct call
                response = self.xai_client.chat(user_prompt, system_prompt)

            return {
                'success': True,
                'response': response,
                'context_used': search_results,
                'tokens_saved': 0,  # TODO: Calculate based on filtered results
                'source': 'rag'
            }

        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'context_used': search_results,
                'source': 'rag_failed'
            }

    def _direct_query(self, user_prompt: str) -> Dict[str, Any]:
        """Direct query without RAG"""
        try:
            if self.fallback_manager:
                result = self.fallback_manager.call_with_fallback(
                    'xai_chat',
                    primary_fn=lambda: self.xai_client.chat(user_prompt),
                    fallback_fn=None,
                    queue_on_failure=False
                )

                if not result['success']:
                    return {
                        'success': False,
                        'error': result.get('error', 'AI service unavailable'),
                        'source': 'direct_failed'
                    }

                response = result['result']
            else:
                response = self.xai_client.chat(user_prompt)

            return {
                'success': True,
                'response': response,
                'context_used': [],
                'tokens_saved': 0,
                'source': 'direct'
            }

        except Exception as e:
            logger.error(f"Direct query failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'direct_failed'
            }

    def configure(self, **kwargs):
        """
        Configure RAG engine parameters

        Args:
            max_context_chunks: Max search results to include
            context_char_limit: Max characters of context
            relevance_threshold: Minimum relevance score
        """
        if 'max_context_chunks' in kwargs:
            self.max_context_chunks = kwargs['max_context_chunks']

        if 'context_char_limit' in kwargs:
            self.context_char_limit = kwargs['context_char_limit']

        if 'relevance_threshold' in kwargs:
            self.relevance_threshold = kwargs['relevance_threshold']

        logger.info(f"RAG engine configured: max_chunks={self.max_context_chunks}, "
                   f"char_limit={self.context_char_limit}, threshold={self.relevance_threshold}")


class CodebaseAwareChat:
    """
    High-level interface for codebase-aware chat

    Automatically uses RAG when appropriate and falls back to direct chat otherwise.
    """

    def __init__(self, workspace_context):
        """
        Initialize codebase-aware chat

        Args:
            workspace_context: WorkspaceContext instance
        """
        self.workspace_context = workspace_context

        # Get components from workspace context
        self.xai_client = workspace_context._get_xai_client()
        self.knowledge_base = workspace_context._current_knowledge_base

        # Create RAG engine
        from isaac.core.fallback_manager import get_fallback_manager
        self.rag_engine = RAGQueryEngine(
            xai_client=self.xai_client,
            knowledge_base=self.knowledge_base,
            fallback_manager=get_fallback_manager()
        )

    def chat(self, prompt: str, use_codebase: bool = True) -> str:
        """
        Chat with codebase awareness

        Args:
            prompt: User's question
            use_codebase: Use codebase context (default: True)

        Returns:
            AI response
        """
        result = self.rag_engine.query(prompt, use_codebase=use_codebase)

        if result['success']:
            response = result['response']

            # Add context info if RAG was used
            if result['source'] == 'rag' and result.get('context_used'):
                context_count = len(result['context_used'])
                response += f"\n\n_[Used {context_count} code snippets for context]_"

            return response
        else:
            raise Exception(result.get('error', 'Query failed'))

    def query_with_details(self, prompt: str, use_codebase: bool = True) -> Dict[str, Any]:
        """
        Query with full result details

        Args:
            prompt: User's question
            use_codebase: Use codebase context

        Returns:
            Full query result with metadata
        """
        return self.rag_engine.query(prompt, use_codebase=use_codebase)


if __name__ == '__main__':
    # Test RAG engine
    import sys
    import os
    logging.basicConfig(level=logging.INFO)

    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from isaac.core.workspace_integration import WorkspaceContext

    api_key = os.getenv('XAI_API_KEY')

    if not api_key:
        print("Warning: XAI_API_KEY not set, using mock mode")
        print("\nRAG Engine Components:")
        print("  ✓ RAGQueryEngine - Context injection with semantic search")
        print("  ✓ CodebaseAwareChat - High-level chat interface")
        print("\nUsage:")
        print("  ctx = WorkspaceContext(xai_api_key='...')")
        print("  chat = CodebaseAwareChat(ctx)")
        print("  response = chat.chat('How does authentication work?')")
        sys.exit(0)

    # Real test with API
    ctx = WorkspaceContext(xai_api_key=api_key)
    ctx.activate_workspace()

    chat = CodebaseAwareChat(ctx)

    print("=== Codebase-Aware Chat Test ===\n")

    # Test query
    query = "What is the XaiClient used for?"
    print(f"Query: {query}\n")

    result = chat.query_with_details(query)

    if result['success']:
        print(f"Response: {result['response']}\n")
        print(f"Source: {result['source']}")
        print(f"Context used: {len(result.get('context_used', []))} chunks")
    else:
        print(f"Error: {result.get('error')}")
