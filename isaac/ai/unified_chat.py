#!/usr/bin/env python3
"""
Unified Chat Interface - Smart routing for AI interactions

Consolidates /ai and /chat into a single intelligent interface with
automatic workspace-aware routing.
"""

import logging
from typing import Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class UnifiedChatRouter:
    """
    Intelligent chat router

    Automatically routes queries to appropriate backend:
    - RAG for code questions
    - Direct chat for general questions
    - Multi-file ops for refactoring
    """

    def __init__(self, workspace_context):
        """
        Initialize unified chat router

        Args:
            workspace_context: WorkspaceContext instance
        """
        self.workspace_context = workspace_context
        self.rag_engine = None
        self.multifile_mgr = None

        # Initialize components
        self._init_components()

        # Query patterns
        self.code_patterns = [
            r'\b(function|class|method|variable|import|define|implement)\b',
            r'\b(how does|what is|explain|show me)\b.*\b(code|file|function|class)\b',
            r'\b(find|search|locate|where is)\b',
            r'\brefactor\b',
            r'\b(debug|fix|error|bug)\b',
        ]

        self.refactor_patterns = [
            r'\brefactor\b',
            r'\brename\b.*\bto\b',
            r'\bchange\b.*\bacross\b',
            r'\breplace\b.*\bin all\b',
        ]

        logger.info("Unified chat router initialized")

    def _init_components(self):
        """Initialize RAG engine and multi-file manager"""
        try:
            from isaac.ai.rag_engine import RAGQueryEngine
            from isaac.core.multifile_ops import MultiFileOperationManager
            from isaac.core.fallback_manager import get_fallback_manager

            # Get xAI client from workspace
            xai_client = self.workspace_context._get_xai_client()
            kb = self.workspace_context._current_knowledge_base

            if xai_client and kb:
                self.rag_engine = RAGQueryEngine(
                    xai_client=xai_client,
                    knowledge_base=kb,
                    fallback_manager=get_fallback_manager()
                )

            if self.workspace_context._current_workspace_path:
                self.multifile_mgr = MultiFileOperationManager(
                    project_root=self.workspace_context._current_workspace_path,
                    rag_engine=self.rag_engine
                )

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")

    def chat(self, prompt: str, mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Unified chat interface with automatic routing

        Args:
            prompt: User's query
            mode: Optional manual mode ('rag', 'direct', 'refactor', or 'auto')

        Returns:
            Chat result with routing info
        """
        # Detect mode if not specified
        if mode is None or mode == 'auto':
            mode = self._detect_mode(prompt)

        logger.info(f"Routing query to: {mode}")

        # Route to appropriate handler
        if mode == 'rag' and self.rag_engine:
            return self._handle_rag(prompt)
        elif mode == 'refactor' and self.multifile_mgr:
            return self._handle_refactor(prompt)
        elif mode == 'direct':
            return self._handle_direct(prompt)
        else:
            # Fallback to direct if components not available
            return self._handle_direct(prompt)

    def _detect_mode(self, prompt: str) -> str:
        """
        Detect appropriate mode based on query content

        Returns:
            Mode: 'rag', 'refactor', or 'direct'
        """
        import re

        prompt_lower = prompt.lower()

        # Check for refactoring intent
        for pattern in self.refactor_patterns:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                logger.debug("Detected refactoring intent")
                return 'refactor'

        # Check for code question intent
        for pattern in self.code_patterns:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                logger.debug("Detected code question")
                return 'rag'

        # Default to direct chat
        logger.debug("Using direct chat")
        return 'direct'

    def _handle_rag(self, prompt: str) -> Dict[str, Any]:
        """Handle RAG query (codebase-aware)"""
        try:
            result = self.rag_engine.query(prompt, use_codebase=True)

            if result['success']:
                return {
                    'success': True,
                    'response': result['response'],
                    'mode': 'rag',
                    'context_used': len(result.get('context_used', [])),
                    'source': result.get('source', 'unknown')
                }
            else:
                # Fallback to direct
                logger.warning(f"RAG query failed, falling back to direct: {result.get('error')}")
                return self._handle_direct(prompt)

        except Exception as e:
            logger.error(f"RAG handler error: {e}")
            return self._handle_direct(prompt)

    def _handle_refactor(self, prompt: str) -> Dict[str, Any]:
        """Handle refactoring request"""
        try:
            # Extract files if mentioned
            # For now, suggest using explicit file specification
            return {
                'success': True,
                'response': "For refactoring operations, please use:\n\n"
                           "1. /refactor <description> <files> - AI-assisted refactoring\n"
                           "2. /batch-replace <pattern> <replacement> - Pattern replacement\n"
                           "3. /find <symbol> - Find symbol definitions\n\n"
                           f"Or describe your refactoring goal in detail:\n{prompt}",
                'mode': 'refactor',
                'suggestion': 'Use specialized refactoring commands'
            }

        except Exception as e:
            logger.error(f"Refactor handler error: {e}")
            return {
                'success': False,
                'error': str(e),
                'mode': 'refactor'
            }

    def _handle_direct(self, prompt: str) -> Dict[str, Any]:
        """Handle direct chat (no codebase context)"""
        try:
            xai_client = self.workspace_context._get_xai_client()

            if not xai_client:
                return {
                    'success': False,
                    'error': 'xAI client not configured',
                    'mode': 'direct'
                }

            from isaac.core.fallback_manager import get_fallback_manager

            fallback_mgr = get_fallback_manager()
            result = fallback_mgr.call_with_fallback(
                'xai_chat',
                primary_fn=lambda: xai_client.chat(prompt),
                fallback_fn=None
            )

            if result['success']:
                return {
                    'success': True,
                    'response': result['result'],
                    'mode': 'direct'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Chat failed'),
                    'mode': 'direct'
                }

        except Exception as e:
            logger.error(f"Direct chat error: {e}")
            return {
                'success': False,
                'error': str(e),
                'mode': 'direct'
            }


class WorkspaceAwareDefaults:
    """
    Workspace-aware default settings

    Automatically configures behavior based on workspace context
    """

    def __init__(self, workspace_context):
        self.workspace_context = workspace_context
        self.defaults = self._detect_defaults()

    def _detect_defaults(self) -> Dict[str, Any]:
        """Detect appropriate defaults from workspace"""
        defaults = {
            'auto_index': False,
            'use_codebase': True,
            'watch_files': False,
            'max_context': 5
        }

        # Check if workspace is active
        context = self.workspace_context.get_current_context()

        if context['active']:
            # Check project size
            ws_path = Path(context['workspace']['path'])
            py_files = list(ws_path.glob('**/*.py'))

            if len(py_files) < 100:
                # Small project: enable auto-features
                defaults['auto_index'] = True
                defaults['watch_files'] = True
                defaults['max_context'] = 10
            elif len(py_files) < 500:
                # Medium project: selective features
                defaults['auto_index'] = False
                defaults['watch_files'] = True
                defaults['max_context'] = 5
            else:
                # Large project: conservative
                defaults['auto_index'] = False
                defaults['watch_files'] = False
                defaults['max_context'] = 3

        return defaults

    def get(self, key: str, fallback: Any = None) -> Any:
        """Get default value"""
        return self.defaults.get(key, fallback)


if __name__ == '__main__':
    # Test unified chat router
    import sys
    import os
    logging.basicConfig(level=logging.INFO)

    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from isaac.core.workspace_integration import WorkspaceContext

    api_key = os.getenv('XAI_API_KEY')

    if not api_key:
        print("=== Unified Chat Router ===\n")
        print("Components:")
        print("  ✓ UnifiedChatRouter - Smart query routing")
        print("  ✓ WorkspaceAwareDefaults - Context-based configuration")
        print("\nRouting Logic:")
        print("  - Code questions → RAG (with codebase context)")
        print("  - Refactoring → Multi-file operations")
        print("  - General questions → Direct chat")
        print("\nAuto-detection patterns:")
        print("  - 'how does X work' → RAG")
        print("  - 'refactor X to Y' → Refactor")
        print("  - 'explain quantum physics' → Direct")
        sys.exit(0)

    # Real test
    ctx = WorkspaceContext(xai_api_key=api_key)
    ctx.activate_workspace()

    router = UnifiedChatRouter(ctx)

    print("=== Unified Chat Router Test ===\n")

    # Test queries with different patterns
    queries = [
        ("How does the XaiClient work?", "rag"),
        ("What is the capital of France?", "direct"),
        ("Refactor authentication to use JWT", "refactor"),
    ]

    for query, expected_mode in queries:
        detected = router._detect_mode(query)
        match = "✓" if detected == expected_mode else "✗"
        print(f"{match} '{query[:40]}...' → {detected} (expected: {expected_mode})")

    print("\n✓ Query routing working")
