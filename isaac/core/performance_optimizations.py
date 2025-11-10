"""
Phase 3: Performance Optimizations
Collection of optimization utilities and patterns
"""

import sys
from collections import defaultdict
from typing import Any, Dict, Generator, List


# ===== Data Structure Optimizations =====

# Example: Using sets for O(1) lookup instead of lists O(n)
TIER_4_COMMANDS_SET = {
    'sudo', 'rm -rf', 'format', 'dd', 'mkfs',
    'fdisk', 'parted', 'shutdown', 'reboot', 'init'
}

# Example: Using defaultdict to avoid key checks
def count_items_optimized(items: List[str]) -> Dict[str, int]:
    """
    Optimized item counting using defaultdict
    Avoids if/else for key existence checks
    """
    counts = defaultdict(int)
    for item in items:
        counts[item] += 1
    return dict(counts)


# ===== Generator Patterns for Memory Efficiency =====

def process_large_file(filepath: str, chunk_size: int = 1024) -> Generator[str, None, None]:
    """
    Generator pattern for processing large files
    Memory efficient - processes one chunk at a time
    """
    with open(filepath, 'r') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def get_all_files_generator(directory: str) -> Generator[str, None, None]:
    """
    Generator for file traversal
    Instead of loading all files into memory at once
    """
    import os
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            yield os.path.join(root, filename)


# ===== Object Pooling =====

class ObjectPool:
    """
    Simple object pool for reducing allocations
    Useful for frequently created/destroyed objects
    """

    def __init__(self, factory, max_size: int = 100):
        """
        Initialize object pool

        Args:
            factory: Callable that creates new objects
            max_size: Maximum pool size
        """
        self.factory = factory
        self.max_size = max_size
        self.pool: List[Any] = []

    def acquire(self) -> Any:
        """Get object from pool or create new one"""
        if self.pool:
            return self.pool.pop()
        return self.factory()

    def release(self, obj: Any) -> None:
        """Return object to pool"""
        if len(self.pool) < self.max_size:
            self.pool.append(obj)


# ===== Memory-Efficient Data Classes =====

class OptimizedResult:
    """
    Example of using __slots__ to reduce memory footprint
    Saves ~40% memory compared to regular class with __dict__
    """
    __slots__ = ['success', 'data', 'error', 'timestamp']

    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error
        import time
        self.timestamp = time.time()

    def __repr__(self):
        return f"OptimizedResult(success={self.success}, data={self.data}, error={self.error})"


# ===== String Optimization =====

class StringIntern:
    """
    String interning for memory efficiency when many duplicate strings
    Useful for repeated command names, keys, etc.
    """

    def __init__(self):
        self.pool: Dict[str, str] = {}

    def intern(self, s: str) -> str:
        """
        Intern a string - returns cached instance if exists

        Args:
            s: String to intern

        Returns:
            Interned string (same object for same value)
        """
        if s not in self.pool:
            self.pool[s] = s
        return self.pool[s]

    def size(self) -> int:
        """Get pool size"""
        return len(self.pool)


# ===== Lazy Evaluation =====

class LazyProperty:
    """
    Decorator for lazy property evaluation
    Computes value once on first access, caches result
    """

    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return self

        # Compute and cache
        value = self.func(instance)
        setattr(instance, self.name, value)
        return value


# ===== Profiling Utilities =====

def profile_memory_usage(func):
    """
    Decorator to profile memory usage of a function

    Example:
        @profile_memory_usage
        def my_function():
            # ... code ...
    """
    def wrapper(*args, **kwargs):
        import tracemalloc

        tracemalloc.start()
        result = func(*args, **kwargs)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\n{func.__name__} Memory Usage:")
        print(f"  Current: {current / 1024 / 1024:.2f} MB")
        print(f"  Peak: {peak / 1024 / 1024:.2f} MB")

        return result

    return wrapper


def measure_object_size(obj: Any) -> int:
    """
    Measure approximate size of an object in bytes

    Args:
        obj: Object to measure

    Returns:
        Size in bytes
    """
    return sys.getsizeof(obj)


def compare_implementations(impl1, impl2, iterations: int = 1000):
    """
    Compare performance of two implementations

    Args:
        impl1: First implementation (callable)
        impl2: Second implementation (callable)
        iterations: Number of iterations to run

    Returns:
        Dict with performance comparison
    """
    import time

    # Warm up
    impl1()
    impl2()

    # Measure impl1
    start = time.perf_counter()
    for _ in range(iterations):
        impl1()
    time1 = time.perf_counter() - start

    # Measure impl2
    start = time.perf_counter()
    for _ in range(iterations):
        impl2()
    time2 = time.perf_counter() - start

    speedup = time1 / time2 if time2 > 0 else float('inf')

    return {
        'impl1_time': time1,
        'impl2_time': time2,
        'speedup': speedup,
        'faster': 'impl2' if speedup > 1 else 'impl1',
        'improvement_pct': abs((time1 - time2) / time1 * 100) if time1 > 0 else 0
    }


# ===== Best Practices Examples =====

def example_list_vs_set():
    """Example: List vs Set lookup performance"""
    import time

    items = list(range(10000))
    item_set = set(items)

    # List lookup (O(n))
    start = time.perf_counter()
    for _ in range(1000):
        9999 in items
    list_time = time.perf_counter() - start

    # Set lookup (O(1))
    start = time.perf_counter()
    for _ in range(1000):
        9999 in item_set
    set_time = time.perf_counter() - start

    print(f"\nList vs Set Lookup (1000 iterations):")
    print(f"  List: {list_time:.6f}s")
    print(f"  Set:  {set_time:.6f}s")
    print(f"  Speedup: {list_time / set_time:.1f}x")


def example_string_concatenation():
    """Example: String concatenation vs join"""
    import time

    items = ['item'] * 1000

    # Bad: Repeated concatenation (O(n²))
    start = time.perf_counter()
    result = ""
    for item in items:
        result += item + ","
    concat_time = time.perf_counter() - start

    # Good: Join (O(n))
    start = time.perf_counter()
    result = ",".join(items)
    join_time = time.perf_counter() - start

    print(f"\nString Concatenation (1000 items):")
    print(f"  Concatenation: {concat_time:.6f}s")
    print(f"  Join: {join_time:.6f}s")
    print(f"  Speedup: {concat_time / join_time:.1f}x")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 3: PERFORMANCE OPTIMIZATION EXAMPLES")
    print("=" * 60)

    example_list_vs_set()
    example_string_concatenation()

    # Demonstrate memory savings with __slots__
    class RegularClass:
        def __init__(self):
            self.a = 1
            self.b = 2
            self.c = 3

    class SlottedClass:
        __slots__ = ['a', 'b', 'c']

        def __init__(self):
            self.a = 1
            self.b = 2
            self.c = 3

    regular = RegularClass()
    slotted = SlottedClass()

    print(f"\n__slots__ Memory Savings:")
    print(f"  Regular class: {sys.getsizeof(regular)} bytes")
    print(f"  Slotted class: {sys.getsizeof(slotted)} bytes")
    savings = (sys.getsizeof(regular) - sys.getsizeof(slotted)) / sys.getsizeof(regular) * 100
    print(f"  Savings: {savings:.1f}%")

    print("\n" + "=" * 60)
