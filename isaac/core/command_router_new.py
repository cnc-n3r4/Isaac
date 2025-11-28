"""
Optimized CommandRouter - High-performance routing with smart strategies
"""

from typing import Any, Dict, Optional
from isaac.adapters.base_adapter import CommandResult
from isaac.core.tier_validator import TierValidator
import time
import re


class CommandRouter:
    """
    High-performance command router with optimized routing strategies.
    
    Features:
    - Fast prefix matching with compiled patterns
    - Lazy loading of heavy components
    - Performance metrics tracking
    - Intelligent caching
    """
    
    def __init__(self, session_mgr: Any, shell: Any) -> None:
        """Initialize router with session manager and shell adapter."""
        self.session = session_mgr
        self.shell = shell
self.validator = TierValidator(self.session.preferences)
        self.dispatcher = None
      
      # Performance optimizations
self._compile_patterns()
        self._route_cache = {}
        self._stats = {
            'total_routes': 0,
      'cache_hits': 0,
    'routing_time_ms': 0.0
        }
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for faster matching."""
        self._meta_pattern = re.compile(r'^/')
        self._ai_pattern = re.compile(r'^isaac\s+')
 self._whitespace_pattern = re.compile(r'^\s*$')

    def route(self, input_text: str) -> CommandResult:
        """
        Fast command routing with caching and performance tracking.
        
        Args:
     input_text: The command text to route
        
        Returns:
            CommandResult with execution result
        """
        start_time = time.perf_counter()
        
        try:
            # Check cache first
 if input_text in self._route_cache:
        self._stats['cache_hits'] += 1
        return self._route_cache[input_text]
        
   # Route the command
   result = self._route_internal(input_text)
         
        # Cache the result for simple commands
        if len(self._route_cache) < 100:  # Prevent memory bloat
        self._route_cache[input_text] = result
         
return result
        
        finally:
            # Track performance
        elapsed = (time.perf_counter() - start_time) * 1000
            self._stats['total_routes'] += 1
         self._stats['routing_time_ms'] += elapsed
    
    def _route_internal(self, input_text: str) -> CommandResult:
        """Internal routing logic with optimized pattern matching."""
        
        # Skip empty/whitespace input
        if self._whitespace_pattern.match(input_text):
            return CommandResult(False, "Empty command", 1)
        
        # Fast pattern matching
        if self._meta_pattern.match(input_text):
            return self._handle_meta_command(input_text)
        
 if self._ai_pattern.match(input_text):
        return self._handle_ai_query(input_text)
        
        # Default to shell command
    return self._handle_shell_command(input_text)

    def _handle_meta_command(self, input_text: str) -> CommandResult:
        """Handle meta commands like /help, /status."""
        # TODO: Connect to actual dispatcher when available
    return CommandResult(
            success=True,
    output=f"Meta command: {input_text}",
  exit_code=0
    )
    
    def _handle_ai_query(self, input_text: str) -> CommandResult:
        """Handle AI queries with 'isaac' prefix."""
    # TODO: Connect to AI router when available
 return CommandResult(
  success=True,
       output=f"AI query: {input_text}",
        exit_code=0
        )
    
    def _handle_shell_command(self, input_text: str) -> CommandResult:
        """Handle regular shell commands with tier validation."""
    if not self.shell:
            return CommandResult(False, "No shell adapter available", 1)
        
        # Apply tier validation
        if self.validator:
            validation_result = self.validator.validate(input_text)
            if not validation_result.allowed:
        return CommandResult(
              False, 
        f"Command blocked by tier {validation_result.tier}: {validation_result.reason}",
                 1
         )
 
        return self.shell.execute(input_text)

    def route_command(self, input_text: str) -> CommandResult:
        """Legacy method name - redirects to route() for compatibility."""
    return self.route(input_text)
    
    def get_performance_stats(self) -> Dict[str, Any]:
   """Get routing performance statistics."""
        total_routes = self._stats['total_routes']
        if total_routes == 0:
            return {
        'total_routes': 0,
            'cache_hit_rate': 0.0,
          'avg_routing_time_ms': 0.0
            }
        
return {
   'total_routes': total_routes,
         'cache_hit_rate': self._stats['cache_hits'] / total_routes,
    'avg_routing_time_ms': self._stats['routing_time_ms'] / total_routes,
'cache_size': len(self._route_cache)
  }
    
    def clear_cache(self) -> None:
     """Clear the routing cache."""
        self._route_cache.clear()
    
    def set_dispatcher(self, dispatcher: Any) -> None:
        """Set the command dispatcher for meta commands."""
      self.dispatcher = dispatcher