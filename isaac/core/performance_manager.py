"""
Performance Manager - Comprehensive optimization system
Handles lazy loading, memory management, and performance monitoring
"""

import functools
import gc
import importlib
import os
import psutil
import sys
import time
import weakref
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set
import logging

logger = logging.getLogger(__name__)


class LazyImportManager:
    """
    Manages lazy imports to reduce startup time
    Only imports modules when first accessed
    """
    
    def __init__(self):
        self._imported_modules: Dict[str, Any] = {}
        self._import_times: Dict[str, float] = {}
        
    def lazy_import(self, module_name: str, alias: Optional[str] = None) -> Any:
        """
        Lazily import a module
      
        Args:
            module_name: Full module name to import
            alias: Optional alias for the module
            
        Returns:
            Proxy object that imports on first access
        """
        key = alias or module_name

        if key not in self._imported_modules:
            
            class LazyModule:
                def __init__(self, name: str):
                    self._name = name
                    self._module = None
                
                def _ensure_imported(self):
                    if self._module is None:
                        start_time = time.time()
                        self._module = importlib.import_module(self._name)
                        import_time = time.time() - start_time
                        self._import_times[self._name] = import_time
                        logger.debug(f"Lazy imported {self._name} in {import_time:.3f}s")
                    return self._module
                
                def __getattr__(self, name):
                    return getattr(self._ensure_imported(), name)
                
                def __call__(self, *args, **kwargs):
                    return self._ensure_imported()(*args, **kwargs)
            
            self._imported_modules[key] = LazyModule(module_name)
        
        return self._imported_modules[key]
    
    def get_import_stats(self) -> Dict[str, float]:
        """Get statistics on import times"""
        return self._import_times.copy()


class MemoryOptimizer:
    """
    Optimizes memory usage through various techniques
    """
    
    def __init__(self, max_memory_mb: int = 100):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._object_pools: Dict[str, list] = {}
        self._weak_refs: Set[weakref.ref] = set()
 
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent()
        }
        
    def optimize_memory(self) -> Dict[str, Any]:
        """Run memory optimization"""
        before = self.get_memory_usage()
        
        # Clean up weak references
        dead_refs = [ref for ref in self._weak_refs if ref() is None]
        for ref in dead_refs:
            self._weak_refs.remove(ref)
        
        # Force garbage collection
        collected = gc.collect()
        
        # Clear module caches if memory is high
        if before['rss_mb'] > self.max_memory_bytes / 1024 / 1024:
            self._clear_caches()
            
        after = self.get_memory_usage()
      
        return {
            'before_mb': before['rss_mb'],
            'after_mb': after['rss_mb'],
            'saved_mb': before['rss_mb'] - after['rss_mb'],
            'objects_collected': collected
        }
        
    def _clear_caches(self):
        """Clear various internal caches"""
        # Clear import caches
        if hasattr(importlib, '_bootstrap'):
            importlib._bootstrap._ModuleLockManager._LOCKS.clear()
            
        # Clear function caches
        for obj in gc.get_objects():
            if hasattr(obj, 'cache_clear') and callable(obj.cache_clear):
                try:
                    obj.cache_clear()
                except:
                    pass 
 
    def register_for_cleanup(self, obj: Any):
        """Register object for automatic cleanup"""
        self._weak_refs.add(weakref.ref(obj))


class PerformanceMonitor:
    """
    Monitors system performance and provides optimization recommendations
    """
    
    def __init__(self):
        self.metrics = {}
        self.thresholds = {
            'startup_time_ms': 2000,  # 2 seconds
            'command_latency_ms': 100,  # 100ms
            'memory_usage_mb': 50,  # 50MB
            'cpu_percent': 10  # 10% CPU when idle
        }
        
    def record_metric(self, name: str, value: float, unit: str = 'ms'):
        """Record a performance metric"""
        self.metrics[name] = {
            'value': value,
            'unit': unit,
            'timestamp': time.time()
        }
        
        # Check if metric exceeds threshold
        if name in self.thresholds:
            if value > self.thresholds[name]:
                logger.warning(f"Performance threshold exceeded: {name}={value}{unit} (threshold: {self.thresholds[name]}{unit})")
        
    def get_recommendations(self) -> list:
        """Get performance optimization recommendations"""
        recommendations = []
        
        if 'startup_time_ms' in self.metrics:
            startup_time = self.metrics['startup_time_ms']['value']
            if startup_time > 3000:
                recommendations.append("Consider enabling lazy loading for commands")
            if startup_time > 5000:
                recommendations.append("Consider parallel plugin loading")
        
        if 'memory_usage_mb' in self.metrics:
            memory_usage = self.metrics['memory_usage_mb']['value']
            if memory_usage > 100:
                recommendations.append("Enable memory optimization and garbage collection")
            if memory_usage > 200:
                recommendations.append("Consider C++ core for memory-intensive operations")
        
        return recommendations


def performance_timer(func: Callable) -> Callable:
    """Decorator to measure function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            logger.debug(f"{func.__name__} executed in {execution_time:.2f}ms")
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"{func.__name__} failed after {execution_time:.2f}ms: {e}")
            raise
    return wrapper


def memory_profile(func: Callable) -> Callable:
    """Decorator to profile memory usage of a function"""
    @functools.wraps(func)  
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        memory_before = process.memory_info().rss
        
        result = func(*args, **kwargs)
        
        memory_after = process.memory_info().rss
        memory_diff = (memory_after - memory_before) / 1024 / 1024  # MB
        
        if memory_diff > 1:  # Only log if significant memory increase
            logger.debug(f"{func.__name__} used {memory_diff:.2f}MB memory")
        
        return result
    return wrapper


# Global instances
lazy_import_manager = LazyImportManager()
memory_optimizer = MemoryOptimizer()
performance_monitor = PerformanceMonitor()


# Convenience functions
def lazy_import(module_name: str, alias: Optional[str] = None):
    """Convenience function for lazy imports"""
    return lazy_import_manager.lazy_import(module_name, alias)


def optimize_memory():
    """Convenience function for memory optimization"""
    return memory_optimizer.optimize_memory()


def get_performance_stats():
    """Get comprehensive performance statistics"""
    return {
        'memory_usage': memory_optimizer.get_memory_usage(),
        'import_stats': lazy_import_manager.get_import_stats(),
        'metrics': performance_monitor.metrics,
        'recommendations': performance_monitor.get_recommendations()
    }