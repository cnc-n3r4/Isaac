"""
Comprehensive Error Handling and Recovery System
Provides robust error handling, logging, and recovery mechanisms
"""

import functools
import logging
import sys
import traceback
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class IsaacError(Exception):
    """Base exception for Isaac-specific errors"""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN", context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = time.time()


class CommandError(IsaacError):
    """Error executing a command"""
    pass


class ValidationError(IsaacError):
    """Error in command validation"""
    pass


class AIProviderError(IsaacError):
    """Error with AI provider"""
    pass


class PerformanceError(IsaacError):
    """Performance-related error (timeout, memory, etc.)"""
    pass


class ErrorRecoveryManager:
    """
    Manages error recovery strategies and fallback mechanisms
    """
    
    def __init__(self):
        self.error_log = []
        self.recovery_strategies = {}
        self.error_patterns = {}
        self.max_log_size = 1000
     
        # Setup recovery strategies
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Setup default error recovery strategies"""
        
        # AI Provider fallback
        self.recovery_strategies['AI_PROVIDER_ERROR'] = [
          'try_fallback_provider',
            'use_cached_response',
            'return_error_message'
        ]
        
   # Command execution fallback
      self.recovery_strategies['COMMAND_EXECUTION_ERROR'] = [
            'retry_with_validation',
       'try_alternative_command',
            'return_safe_error'
        ]
        
        # Performance issues
        self.recovery_strategies['PERFORMANCE_ERROR'] = [
  'optimize_memory',
     'clear_caches',
   'reduce_complexity'
     ]
    
     # Validation errors
   self.recovery_strategies['VALIDATION_ERROR'] = [
'auto_correct_command',
 'request_user_confirmation',
         'block_execution'
  ]
    
    def handle_error(
  self,
     error: Exception,
context: Optional[Dict[str, Any]] = None,
        recovery_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Handle error with appropriate recovery strategy
        
        Args:
            error: The exception that occurred
     context: Additional context about the error
 recovery_enabled: Whether to attempt recovery
            
        Returns:
            Dictionary with error info and recovery results
  """
    error_info = self._analyze_error(error, context)
        
        # Log the error
        self._log_error(error_info)
        
        # Attempt recovery if enabled
     recovery_result = None
        if recovery_enabled:
            recovery_result = self._attempt_recovery(error_info)
     
    return {
            'error': error_info,
      'recovery': recovery_result,
    'timestamp': time.time()
        }
    
    def _analyze_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
 """Analyze error and categorize it"""
        
        error_type = type(error).__name__
        error_message = str(error)
    error_traceback = traceback.format_exc()
     
        # Determine error category
        if isinstance(error, AIProviderError):
            category = 'AI_PROVIDER_ERROR'
        elif isinstance(error, CommandError):
      category = 'COMMAND_EXECUTION_ERROR'
   elif isinstance(error, ValidationError):
            category = 'VALIDATION_ERROR'
      elif isinstance(error, PerformanceError):
   category = 'PERFORMANCE_ERROR'
        elif isinstance(error, (TimeoutError, asyncio.TimeoutError)) if 'asyncio' in sys.modules else isinstance(error, TimeoutError):
       category = 'PERFORMANCE_ERROR'
  elif isinstance(error, (MemoryError, OverflowError)):
            category = 'PERFORMANCE_ERROR'
        else:
            category = 'UNKNOWN_ERROR'

        # Extract additional info
        severity = self._determine_severity(error, category)
    
     return {
  'type': error_type,
            'message': error_message,
'category': category,
    'severity': severity,
            'traceback': error_traceback,
      'context': context or {},
            'timestamp': time.time()
  }
    
    def _determine_severity(self, error: Exception, category: str) -> str:
    """Determine error severity"""
   
      # Critical errors that should stop execution
        if isinstance(error, (SystemExit, KeyboardInterrupt, MemoryError)):
            return 'CRITICAL'
        
        # High severity - major functionality broken
        elif category in ['AI_PROVIDER_ERROR', 'PERFORMANCE_ERROR']:
    return 'HIGH'
        
        # Medium severity - some functionality impacted
        elif category in ['VALIDATION_ERROR', 'COMMAND_EXECUTION_ERROR']:
            return 'MEDIUM'
        
        # Low severity - minor issues
        else:
     return 'LOW'
    
    def _log_error(self, error_info: Dict[str, Any]):
        """Log error information"""
        
        # Add to internal log
        self.error_log.append(error_info)
        
      # Trim log if too large
        if len(self.error_log) > self.max_log_size:
            self.error_log = self.error_log[-self.max_log_size//2:]
        
   # Log to system logger
   severity = error_info['severity']
        message = f"[{error_info['category']}] {error_info['message']}"
        
    if severity == 'CRITICAL':
            logger.critical(message)
 elif severity == 'HIGH':
            logger.error(message)
        elif severity == 'MEDIUM':
            logger.warning(message)
        else:
   logger.info(message)
    
    def _attempt_recovery(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from error"""
        
        category = error_info['category']
        strategies = self.recovery_strategies.get(category, ['return_error_message'])
        
      recovery_results = []
        
        for strategy in strategies:
        try:
         result = self._execute_recovery_strategy(strategy, error_info)
    recovery_results.append({
 'strategy': strategy,
                 'success': result.get('success', False),
        'result': result
      })
        
    # If recovery successful, stop trying other strategies
     if result.get('success', False):
        break
     
          except Exception as recovery_error:
                recovery_results.append({
         'strategy': strategy,
          'success': False,
          'error': str(recovery_error)
      })
  
        return {
 'attempted_strategies': strategies,
            'results': recovery_results,
       'final_success': any(r.get('success', False) for r in recovery_results)
      }
  
    def _execute_recovery_strategy(self, strategy: str, error_info: Dict[str, Any]) -> Dict[str, Any]:
  """Execute specific recovery strategy"""
        
        if strategy == 'try_fallback_provider':
    return self._try_fallback_provider(error_info)
   elif strategy == 'use_cached_response':
    return self._use_cached_response(error_info)
        elif strategy == 'retry_with_validation':
         return self._retry_with_validation(error_info)
  elif strategy == 'optimize_memory':
        return self._optimize_memory(error_info)
        elif strategy == 'auto_correct_command':
         return self._auto_correct_command(error_info)
   else:
  return {'success': False, 'message': f'Unknown strategy: {strategy}'}
 
    def _try_fallback_provider(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Try fallback AI provider"""
        # This would integrate with AIRouter for fallback
        return {'success': False, 'message': 'Fallback provider not available'}
    
    def _use_cached_response(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
"""Try to use cached response"""
        # This would integrate with cache system
        return {'success': False, 'message': 'No cached response available'}
    
    def _retry_with_validation(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
 """Retry command with additional validation"""
        return {'success': False, 'message': 'Retry not implemented'}
    
    def _optimize_memory(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
      """Optimize memory usage"""
        try:
         from isaac.core.performance_manager import optimize_memory
result = optimize_memory()
          return {'success': True, 'result': result}
        except Exception as e:
 return {'success': False, 'error': str(e)}
    
    def _auto_correct_command(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Try to auto-correct command"""
    return {'success': False, 'message': 'Auto-correction not implemented'}
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
  if not self.error_log:
return {'total_errors': 0}
 
        # Count by category
        categories = {}
   severities = {}
  
        for error in self.error_log:
            category = error.get('category', 'UNKNOWN')
   severity = error.get('severity', 'UNKNOWN')
    
            categories[category] = categories.get(category, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
        
      return {
   'total_errors': len(self.error_log),
       'by_category': categories,
            'by_severity': severities,
            'last_error': self.error_log[-1] if self.error_log else None
        }


def error_handler(
    recovery_enabled: bool = True,
    reraise: bool = False,
    default_return: Any = None
):
    """
    Decorator for comprehensive error handling
    
    Args:
        recovery_enabled: Whether to attempt error recovery
        reraise: Whether to reraise the exception after handling
        default_return: Default value to return if error occurs
  """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
    return func(*args, **kwargs)
       except Exception as e:
         # Use global error manager
       error_manager = get_error_manager()
                
        # Handle the error
     result = error_manager.handle_error(
    e,
     context={'function': func.__name__, 'args': str(args)[:100]},
   recovery_enabled=recovery_enabled
 )
     
        # Decide what to do next
 if reraise:
            raise
      elif result.get('recovery', {}).get('final_success', False):
           # Recovery successful, return recovery result
                 return result['recovery']['results'][-1].get('result', default_return)
 else:
        # Return default or error info
            return default_return if default_return is not None else result
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[Dict[str, Any]] = None,
 default_return: Any = None,
    timeout: Optional[float] = None
) -> Tuple[bool, Any]:
    """
    Safely execute a function with comprehensive error handling
    
    Args:
        func: Function to execute
      args: Function arguments
      kwargs: Function keyword arguments
        default_return: Default return value if error occurs
        timeout: Optional timeout in seconds
    
    Returns:
        Tuple of (success: bool, result: Any)
"""
    if kwargs is None:
     kwargs = {}
    
    try:
        if timeout:
     import signal
     
   def timeout_handler(signum, frame):
raise TimeoutError(f"Function {func.__name__} timed out after {timeout}s")
            
  old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout))
      
        try:
   result = func(*args, **kwargs)
    return True, result
        finally:
  if timeout:
   signal.alarm(0)
         signal.signal(signal.SIGALRM, old_handler)
    
    except Exception as e:
      logger.error(f"Safe execution failed for {func.__name__}: {e}")
   return False, default_return


# Global error manager instance
_global_error_manager = None


def get_error_manager() -> ErrorRecoveryManager:
    """Get global error manager instance"""
  global _global_error_manager
    if _global_error_manager is None:
   _global_error_manager = ErrorRecoveryManager()
    return _global_error_manager    return _global_error_manager