"""
Async AI Router - High-performance asynchronous AI operations
Provides non-blocking AI operations with connection pooling and smart caching
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
import aiohttp
import logging

logger = logging.getLogger(__name__)


class AsyncAIRouter:
    """
    Asynchronous AI router for high-performance operations
    
    Features:
    - Non-blocking AI requests
    - Connection pooling
    - Parallel provider queries
    - Smart response selection
    - Intelligent caching
    """
    
    def __init__(self, sync_router):
        """Initialize with existing sync router for configuration"""
        self.sync_router = sync_router
        self.session = None  # aiohttp session, created lazily
        self._response_cache = {}
        self._active_requests = {}  # Track ongoing requests to avoid duplicates
  
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if self.session is None:
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection limit
                limit_per_host=30,  # Per-host limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30, connect=10)
            )
     
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
        self.session = None
    
    async def chat_async(
        self, 
        message: str, 
        context: Optional[List[Dict[str, str]]] = None,
        prefer_speed: bool = False,
        prefer_quality: bool = False
    ):
        """
  Async chat with intelligent provider selection
        
        Args:
            message: User message
   context: Conversation context
            prefer_speed: Prioritize response speed
          prefer_quality: Prioritize response quality
    
        Returns:
     AIResponse from best available provider
        """
        await self._ensure_session()
        
        # Check cache first
        cache_key = self._get_cache_key(message, context)
        if cache_key in self._response_cache:
            cached = self._response_cache[cache_key]
            if time.time() - cached['timestamp'] < 300:  # 5 minute cache
                logger.debug(f"Cache hit for message: {message[:50]}...")
                return cached['response']
        
        # Check for duplicate requests
        if cache_key in self._active_requests:
            logger.debug(f"Waiting for ongoing request: {message[:50]}...")
            return await self._active_requests[cache_key]
        
        # Create request future
        request_future = asyncio.create_task(
            self._execute_parallel_requests(message, context, prefer_speed, prefer_quality)
        )
        self._active_requests[cache_key] = request_future
        
        try:
            response = await request_future
 
            # Cache successful response
            self._response_cache[cache_key] = {
                'response': response,
                'timestamp': time.time()
            }
            
            return response
        finally:
            # Clean up active request tracking
            self._active_requests.pop(cache_key, None)
 
    async def _execute_parallel_requests(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]],
        prefer_speed: bool,
        prefer_quality: bool
    ):
        """Execute requests to multiple providers in parallel"""
        
        # Determine provider strategy
        if prefer_speed:
            providers = ['grok']  # Fastest
        elif prefer_quality:
            providers = ['claude', 'grok', 'openai']  # Best quality first
        else:
            providers = ['grok', 'claude', 'openai']  # Balanced
   
        # Create tasks for available providers
        tasks = []
        for provider in providers:
            if self._is_provider_available(provider):
                task = asyncio.create_task(
                    self._query_provider_async(provider, message, context)
                )
                tasks.append((provider, task))
        
        if not tasks:
             # Mock response for testing
            return type('AIResponse', (), {
                'success': False,
                'content': "No AI providers available",
                'provider': "none"
            })()
   
        # Wait for first successful response
        for provider, task in tasks:
            try:
                response = await asyncio.wait_for(task, timeout=30)
                if getattr(response, 'success', False):
                    # Cancel remaining tasks
                    for _, other_task in tasks:
                        if other_task != task and not other_task.done():
                            other_task.cancel()
                    return response
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(f"Provider {provider} failed: {e}")
                continue
    
        # If all providers failed, return the last error
        return type('AIResponse', (), {
            'success': False,
            'content': "All AI providers failed",
            'provider': "none"
        })()
        
    async def _query_provider_async(
        self,
        provider: str,
        message: str,
        context: Optional[List[Dict[str, str]]]
    ):
 """Query specific provider asynchronously"""
        try:
     # Get provider client
            client = getattr(self.sync_router, '_get_client', lambda x: None)(provider)
            if not client:
       raise Exception(f"Provider {provider} not available")
            
            # Execute request
    # Note: This is a simplified implementation
            # In practice, each provider would have async implementation
  response = getattr(client, 'chat', lambda x, y: None)(message, context)
  
        return response
        except Exception as e:
      return type('AIResponse', (), {
 'success': False,
    'content': f"Provider {provider} error: {str(e)}",
       'provider': provider
            })()
    
    def _is_provider_available(self, provider: str) -> bool:
     """Check if provider is available"""
        available_method = getattr(self.sync_router, '_is_provider_available', None)
   if available_method:
  return available_method(provider)
        return provider == 'grok'  # Mock availability
        
    def _get_cache_key(self, message: str, context: Optional[List[Dict[str, str]]]) -> str:
        """Generate cache key for request"""
        context_str = str(context) if context else ""
      return f"{hash(message + context_str)}"
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get async router performance statistics"""
        return {
  'cache_size': len(self._response_cache),
            'active_requests': len(self._active_requests),
   'session_active': self.session is not None
      }