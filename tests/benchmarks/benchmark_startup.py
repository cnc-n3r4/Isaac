#!/usr/bin/env python3
"""
Phase 3: Startup Performance Benchmark
Demonstrates 60-80% improvement with parallel plugin loading
"""

import time
from pathlib import Path

from isaac.core.boot_loader import BootLoader


def benchmark_startup():
    """Benchmark sequential vs parallel plugin loading"""
    print("=" * 80)
    print("PHASE 3: STARTUP PERFORMANCE BENCHMARK")
    print("=" * 80)
    print()

    commands_dir = Path(__file__).parent.parent.parent / "isaac" / "commands"

    if not commands_dir.exists():
        print(f"Commands directory not found: {commands_dir}")
        return

    # Count plugins
    plugin_count = sum(1 for item in commands_dir.iterdir() if item.is_dir() and not item.name.startswith('_'))
    print(f"Testing with {plugin_count} plugins")
    print()

    # 1. Sequential loading
    print("1. Sequential Loading (Original)")
    print("-" * 40)
    loader_seq = BootLoader(commands_dir=commands_dir, quiet=True, parallel_loading=False)

    start = time.time()
    loader_seq.load_all()
    sequential_time = time.time() - start

    summary_seq = loader_seq.get_plugin_summary()

    print(f"   Plugins loaded: {summary_seq['ok']}/{summary_seq['total']}")
    print(f"   Discovery time: {loader_seq.discovery_time:.3f}s")
    print(f"   Validation time: {loader_seq.validation_time:.3f}s")
    print(f"   Total time: {sequential_time:.3f}s")
    print()

    # 2. Parallel loading (2 workers)
    print("2. Parallel Loading (2 workers)")
    print("-" * 40)
    loader_par2 = BootLoader(commands_dir=commands_dir, quiet=True, parallel_loading=True, max_workers=2)

    start = time.time()
    loader_par2.load_all()
    parallel2_time = time.time() - start

    summary_par2 = loader_par2.get_plugin_summary()

    print(f"   Plugins loaded: {summary_par2['ok']}/{summary_par2['total']}")
    print(f"   Discovery time: {loader_par2.discovery_time:.3f}s")
    print(f"   Validation time: {loader_par2.validation_time:.3f}s")
    print(f"   Total time: {parallel2_time:.3f}s")
    print(f"   Speedup: {sequential_time/parallel2_time:.2f}x")
    print()

    # 3. Parallel loading (4 workers - optimal)
    print("3. Parallel Loading (4 workers - optimal)")
    print("-" * 40)
    loader_par4 = BootLoader(commands_dir=commands_dir, quiet=True, parallel_loading=True, max_workers=4)

    start = time.time()
    loader_par4.load_all()
    parallel4_time = time.time() - start

    summary_par4 = loader_par4.get_plugin_summary()

    print(f"   Plugins loaded: {summary_par4['ok']}/{summary_par4['total']}")
    print(f"   Discovery time: {loader_par4.discovery_time:.3f}s")
    print(f"   Validation time: {loader_par4.validation_time:.3f}s")
    print(f"   Total time: {parallel4_time:.3f}s")
    print(f"   Speedup: {sequential_time/parallel4_time:.2f}x")
    print()

    # 4. Parallel loading (8 workers)
    print("4. Parallel Loading (8 workers)")
    print("-" * 40)
    loader_par8 = BootLoader(commands_dir=commands_dir, quiet=True, parallel_loading=True, max_workers=8)

    start = time.time()
    loader_par8.load_all()
    parallel8_time = time.time() - start

    summary_par8 = loader_par8.get_plugin_summary()

    print(f"   Plugins loaded: {summary_par8['ok']}/{summary_par8['total']}")
    print(f"   Discovery time: {loader_par8.discovery_time:.3f}s")
    print(f"   Validation time: {loader_par8.validation_time:.3f}s")
    print(f"   Total time: {parallel8_time:.3f}s")
    print(f"   Speedup: {sequential_time/parallel8_time:.2f}x")
    print()

    # Summary comparison
    print("=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)
    print()

    results = [
        ("Sequential", sequential_time, 1.0),
        ("Parallel (2 workers)", parallel2_time, sequential_time/parallel2_time),
        ("Parallel (4 workers)", parallel4_time, sequential_time/parallel4_time),
        ("Parallel (8 workers)", parallel8_time, sequential_time/parallel8_time),
    ]

    print(f"{'Configuration':<25} {'Time':>10} {'Speedup':>10} {'Improvement':>12}")
    print("-" * 60)

    for config, exec_time, speedup in results:
        improvement = ((sequential_time - exec_time) / sequential_time) * 100
        print(f"{config:<25} {exec_time:>9.3f}s {speedup:>9.2f}x {improvement:>11.0f}%")

    print()

    # Best configuration
    best_time = min(parallel2_time, parallel4_time, parallel8_time)
    best_speedup = sequential_time / best_time
    best_improvement = ((sequential_time - best_time) / sequential_time) * 100

    if best_time == parallel4_time:
        best_config = "4 workers"
    elif best_time == parallel2_time:
        best_config = "2 workers"
    else:
        best_config = "8 workers"

    print(f"Best Configuration: {best_config}")
    print(f"  Time saved: {sequential_time - best_time:.3f}s")
    print(f"  Improvement: {best_improvement:.0f}%")
    print(f"  Speedup: {best_speedup:.2f}x")

    if best_improvement >= 60:
        print(f"  ✅ Target achieved (60-80% improvement)")
    elif best_improvement >= 40:
        print(f"  ⚠️  Good but below target ({best_improvement:.0f}% vs 60% target)")
    else:
        print(f"  ❌ Below expectations ({best_improvement:.0f}%)")

    print()

    # Recommendations
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()

    if plugin_count < 10:
        print("  • Plugin count is low (<10), sequential loading may be sufficient")
    elif plugin_count < 30:
        print("  • Recommended: 4 workers (optimal for most systems)")
    else:
        print("  • Recommended: 4-8 workers (large plugin count)")

    print("  • Parallel loading provides diminishing returns beyond 8 workers")
    print("  • I/O-bound operations (YAML parsing) benefit from parallelism")
    print("  • CPU-bound validation may see less improvement")

    print()
    print("=" * 80)


def benchmark_real_startup():
    """Benchmark actual boot sequence with visual output"""
    print("\n\n" + "=" * 80)
    print("REAL STARTUP BENCHMARK (with visual output)")
    print("=" * 80)
    print()

    print("Sequential boot:")
    print("-" * 80)
    start = time.time()
    loader_seq = BootLoader(quiet=False, parallel_loading=False)
    loader_seq.load_all()
    seq_time = time.time() - start

    print(f"\nSequential startup time: {seq_time:.3f}s")

    print("\n\nParallel boot (4 workers):")
    print("-" * 80)
    start = time.time()
    loader_par = BootLoader(quiet=False, parallel_loading=True, max_workers=4)
    loader_par.load_all()
    par_time = time.time() - start

    print(f"\nParallel startup time: {par_time:.3f}s")

    improvement = ((seq_time - par_time) / seq_time) * 100
    print(f"\n⚡ Improvement: {improvement:.0f}% faster ({seq_time/par_time:.2f}x speedup)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import sys

    print("\n🚀 Starting Phase 3 Startup Benchmarks...\n")

    # Run quiet benchmark
    benchmark_startup()

    # Ask if user wants to see visual startup
    if "--with-visual" in sys.argv:
        benchmark_real_startup()

    print("\n✅ Benchmark complete!\n")
    print("Run with --with-visual to see boot sequence output")
