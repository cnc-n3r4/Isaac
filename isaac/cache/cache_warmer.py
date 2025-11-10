"""
Phase 3: Cache Warmer
Intelligently pre-populate cache with common queries on startup
"""

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .multilevel_cache import MultiLevelCache


class CacheWarmer:
    """
    Pre-populate cache with common queries based on usage patterns

    Features:
    - Track query frequency and recency
    - Identify hot queries for pre-warming
    - Learn from usage patterns
    - Configurable warmup strategies
    """

    def __init__(
        self,
        cache: MultiLevelCache,
        usage_log_file: str = ".isaac_cache/usage_log.json"
    ):
        """
        Initialize cache warmer

        Args:
            cache: MultiLevelCache instance to warm
            usage_log_file: Path to usage log file
        """
        self.cache = cache
        self.usage_log_file = Path(usage_log_file)
        self.usage_log_file.parent.mkdir(parents=True, exist_ok=True)

        # In-memory usage tracking
        self.usage: Dict[str, Dict[str, Any]] = {}
        self._load_usage_log()

    def _load_usage_log(self) -> None:
        """Load usage log from disk"""
        if self.usage_log_file.exists():
            try:
                with open(self.usage_log_file, 'r') as f:
                    self.usage = json.load(f)
            except Exception:
                # Corrupted log, start fresh
                self.usage = {}

    def _save_usage_log(self) -> None:
        """Save usage log to disk"""
        try:
            with open(self.usage_log_file, 'w') as f:
                json.dump(self.usage, f, indent=2)
        except Exception:
            pass  # Failed to save, continue anyway

    def track_query(self, query_key: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Track a query for learning

        Args:
            query_key: Cache key that was queried
            metadata: Optional metadata (query type, cost, etc.)
        """
        import time

        if query_key not in self.usage:
            self.usage[query_key] = {
                'count': 0,
                'first_seen': time.time(),
                'last_seen': time.time(),
                'metadata': metadata or {}
            }

        self.usage[query_key]['count'] += 1
        self.usage[query_key]['last_seen'] = time.time()

        # Update metadata
        if metadata:
            self.usage[query_key]['metadata'].update(metadata)

        # Periodically save (every 10 queries)
        if sum(item['count'] for item in self.usage.values()) % 10 == 0:
            self._save_usage_log()

    def get_hot_queries(
        self,
        top_n: int = 20,
        min_count: int = 2,
        recency_weight: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Get hottest queries based on frequency and recency

        Args:
            top_n: Number of top queries to return
            min_count: Minimum query count to consider
            recency_weight: Weight for recency (0-1, 0=only frequency)

        Returns:
            List of (query_key, score) tuples
        """
        import time

        current_time = time.time()
        scored_queries = []

        for query_key, data in self.usage.items():
            count = data['count']

            if count < min_count:
                continue

            # Calculate recency score (exponential decay)
            time_since_last = current_time - data['last_seen']
            days_since_last = time_since_last / 86400  # Convert to days

            # Exponential decay: score decreases by 50% every 7 days
            recency_score = 0.5 ** (days_since_last / 7)

            # Combined score: weighted average of frequency and recency
            frequency_score = count
            combined_score = (
                (1 - recency_weight) * frequency_score +
                recency_weight * (recency_score * count)
            )

            scored_queries.append((query_key, combined_score))

        # Sort by score descending
        scored_queries.sort(key=lambda x: x[1], reverse=True)

        return scored_queries[:top_n]

    def warmup_cache(
        self,
        value_generator: Callable[[str], Any],
        top_n: int = 20,
        verbose: bool = False
    ) -> int:
        """
        Pre-populate cache with hot queries

        Args:
            value_generator: Function to generate value for a query key
            top_n: Number of queries to pre-warm
            verbose: If True, print warming progress

        Returns:
            Number of items warmed
        """
        hot_queries = self.get_hot_queries(top_n=top_n)

        warmed_count = 0
        for query_key, score in hot_queries:
            # Check if already cached
            if self.cache.get(query_key) is not None:
                if verbose:
                    print(f"  ✓ {query_key[:50]}... (already cached)")
                continue

            # Generate and cache value
            try:
                value = value_generator(query_key)
                if value is not None:
                    self.cache.set(query_key, value)
                    warmed_count += 1
                    if verbose:
                        print(f"  + {query_key[:50]}... (score: {score:.1f})")
            except Exception as e:
                if verbose:
                    print(f"  ✗ {query_key[:50]}... (error: {e})")

        return warmed_count

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Analyze usage patterns

        Returns:
            Dict with pattern analysis
        """
        import time

        if not self.usage:
            return {
                'total_queries': 0,
                'unique_queries': 0,
                'most_common': [],
                'recent_queries': [],
            }

        # Calculate statistics
        total_queries = sum(item['count'] for item in self.usage.values())
        unique_queries = len(self.usage)

        # Most common queries
        most_common = sorted(
            self.usage.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:10]

        # Recent queries (last 24 hours)
        current_time = time.time()
        day_ago = current_time - 86400
        recent = [
            (key, data)
            for key, data in self.usage.items()
            if data['last_seen'] > day_ago
        ]
        recent.sort(key=lambda x: x[1]['last_seen'], reverse=True)

        # Query types (if metadata available)
        query_types = defaultdict(int)
        for data in self.usage.values():
            qtype = data['metadata'].get('type', 'unknown')
            query_types[qtype] += data['count']

        return {
            'total_queries': total_queries,
            'unique_queries': unique_queries,
            'queries_per_unique': total_queries / unique_queries if unique_queries > 0 else 0,
            'most_common': [
                {'key': key[:50] + '...', 'count': data['count']}
                for key, data in most_common
            ],
            'recent_queries_24h': len(recent),
            'query_types': dict(query_types),
        }

    def recommend_cache_size(self) -> Dict[str, int]:
        """
        Recommend optimal cache sizes based on usage patterns

        Returns:
            Dict with recommended L1, L2, L3 sizes
        """
        unique_queries = len(self.usage)

        if unique_queries < 50:
            return {'l1': 50, 'l2': 200, 'l3': 500}
        elif unique_queries < 200:
            return {'l1': 100, 'l2': 500, 'l3': 1000}
        elif unique_queries < 1000:
            return {'l1': 200, 'l2': 1000, 'l3': 5000}
        else:
            return {'l1': 500, 'l2': 2000, 'l3': 10000}

    def cleanup_old_entries(self, days_old: int = 30) -> int:
        """
        Remove entries not accessed in N days

        Args:
            days_old: Remove entries older than this many days

        Returns:
            Number of entries removed
        """
        import time

        current_time = time.time()
        cutoff_time = current_time - (days_old * 86400)

        keys_to_remove = [
            key for key, data in self.usage.items()
            if data['last_seen'] < cutoff_time
        ]

        for key in keys_to_remove:
            del self.usage[key]

        if keys_to_remove:
            self._save_usage_log()

        return len(keys_to_remove)

    def get_statistics(self) -> str:
        """
        Get human-readable statistics

        Returns:
            Formatted string with usage statistics
        """
        analysis = self.analyze_patterns()

        stats = f"""Cache Warmer Statistics:
  Total Queries: {analysis['total_queries']}
  Unique Queries: {analysis['unique_queries']}
  Avg Queries per Key: {analysis['queries_per_unique']:.1f}
  Recent (24h): {analysis['recent_queries_24h']}

Most Common Queries:
"""
        for item in analysis['most_common'][:5]:
            stats += f"  {item['count']:>4}x  {item['key']}\n"

        if analysis['query_types']:
            stats += "\nQuery Types:\n"
            for qtype, count in sorted(analysis['query_types'].items(), key=lambda x: x[1], reverse=True):
                stats += f"  {qtype}: {count}\n"

        recommendations = self.recommend_cache_size()
        stats += f"\nRecommended Cache Sizes:\n"
        stats += f"  L1 (hot):  {recommendations['l1']} items\n"
        stats += f"  L2 (warm): {recommendations['l2']} items\n"
        stats += f"  L3 (disk): {recommendations['l3']} items\n"

        return stats
