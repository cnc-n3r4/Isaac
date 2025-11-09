"""
Cache Management Command
Provides tools to view, clear, and manage Isaac's caching systems
"""

from typing import Any, Dict, List

from isaac.commands.base import BaseCommand, CommandManifest, CommandResponse, FlagParser


class CacheCommand(BaseCommand):
    """
    Manage Isaac's caching systems (alias cache and query cache)

    Supports operations:
    - status: View cache statistics and hit rates
    - clear: Clear all caches or specific cache types
    - warmup: Pre-load caches with common data
    """

    def execute(self, args: List[str], flags: Dict[str, Any]) -> CommandResponse:
        """
        Execute cache management command

        Args:
            args: Command arguments [action, cache_type]
            flags: Command flags

        Returns:
            CommandResponse with cache operation results
        """
        parser = FlagParser(args)
        action = parser.get_positional(0, "status")
        cache_type = parser.get_positional(1, "all")  # all, alias, query

        # Validate action
        valid_actions = ["status", "clear", "warmup", "stats"]
        if action not in valid_actions:
            return CommandResponse(
                False,
                error=f"Invalid action '{action}'. Valid actions: {', '.join(valid_actions)}"
            )

        # Route to appropriate handler
        if action == "status" or action == "stats":
            return self._show_status(cache_type)
        elif action == "clear":
            return self._clear_caches(cache_type)
        elif action == "warmup":
            return self._warmup_caches(cache_type)

    def get_manifest(self) -> CommandManifest:
        """Get command metadata"""
        return CommandManifest(
            name="cache",
            description="Manage Isaac's caching systems for performance optimization",
            usage="/cache <action> [cache_type]",
            examples=[
                "/cache status          # Show all cache statistics",
                "/cache status alias    # Show alias cache stats only",
                "/cache status query    # Show query cache stats only",
                "/cache clear           # Clear all caches",
                "/cache clear alias     # Clear alias cache only",
                "/cache clear query     # Clear query cache only",
                "/cache warmup          # Pre-load all caches",
            ],
            tier=1,  # Safe operation
            aliases=["caches"],
            category="system"
        )

    def _show_status(self, cache_type: str) -> CommandResponse:
        """
        Show cache statistics

        Args:
            cache_type: Type of cache to show (all, alias, query)

        Returns:
            CommandResponse with cache statistics
        """
        stats = {}

        try:
            # Alias cache stats
            if cache_type in ["all", "alias"]:
                from isaac.crossplatform.alias_cache import AliasCache
                alias_cache = AliasCache()
                stats["alias_cache"] = alias_cache.get_cache_stats()

            # Query cache stats
            if cache_type in ["all", "query"]:
                from isaac.ai.query_cache import QueryCache
                query_cache = QueryCache()
                stats["query_cache"] = query_cache.get_stats()

            # Format output
            output = self._format_cache_stats(stats)

            return CommandResponse(
                True,
                data=output,
                metadata={"stats": stats}
            )

        except Exception as e:
            return CommandResponse(
                False,
                error=f"Failed to get cache statistics: {str(e)}"
            )

    def _clear_caches(self, cache_type: str) -> CommandResponse:
        """
        Clear cache(s)

        Args:
            cache_type: Type of cache to clear (all, alias, query)

        Returns:
            CommandResponse with clear results
        """
        cleared = []
        errors = []

        try:
            # Clear alias cache
            if cache_type in ["all", "alias"]:
                from isaac.crossplatform.alias_cache import AliasCache
                alias_cache = AliasCache()
                alias_cache.invalidate()
                cleared.append("alias_cache")

            # Clear query cache
            if cache_type in ["all", "query"]:
                from isaac.ai.query_cache import QueryCache
                query_cache = QueryCache()
                query_cache.clear()
                cleared.append("query_cache")

            if not cleared:
                return CommandResponse(
                    False,
                    error=f"Unknown cache type: {cache_type}"
                )

            output = f"✓ Cleared caches: {', '.join(cleared)}"

            return CommandResponse(
                True,
                data=output,
                metadata={"cleared": cleared}
            )

        except Exception as e:
            return CommandResponse(
                False,
                error=f"Failed to clear caches: {str(e)}"
            )

    def _warmup_caches(self, cache_type: str) -> CommandResponse:
        """
        Pre-load cache(s)

        Args:
            cache_type: Type of cache to warmup (all, alias, query)

        Returns:
            CommandResponse with warmup results
        """
        warmed = []
        errors = []

        try:
            # Warmup alias cache
            if cache_type in ["all", "alias"]:
                from isaac.crossplatform.alias_cache import AliasCache
                alias_cache = AliasCache()
                success = alias_cache.warmup()
                if success:
                    warmed.append("alias_cache")
                else:
                    errors.append("alias_cache: warmup failed")

            # Query cache doesn't need warmup (auto-loads from disk)
            if cache_type in ["all", "query"]:
                warmed.append("query_cache (auto-loads from disk)")

            if not warmed and not errors:
                return CommandResponse(
                    False,
                    error=f"Unknown cache type: {cache_type}"
                )

            output = []
            if warmed:
                output.append(f"✓ Warmed caches: {', '.join(warmed)}")
            if errors:
                output.append(f"⚠ Errors: {', '.join(errors)}")

            return CommandResponse(
                True,
                data="\n".join(output),
                metadata={"warmed": warmed, "errors": errors}
            )

        except Exception as e:
            return CommandResponse(
                False,
                error=f"Failed to warmup caches: {str(e)}"
            )

    def _format_cache_stats(self, stats: Dict[str, Any]) -> str:
        """
        Format cache statistics for display

        Args:
            stats: Dictionary of cache statistics

        Returns:
            Formatted string output
        """
        lines = []
        lines.append("=" * 60)
        lines.append("ISAAC CACHE STATISTICS")
        lines.append("=" * 60)

        # Alias cache stats
        if "alias_cache" in stats:
            alias_stats = stats["alias_cache"]
            lines.append("\n📝 ALIAS CACHE")
            lines.append("-" * 60)
            lines.append(f"Status:          {'Loaded' if alias_stats['cache_loaded'] else 'Not loaded'}")
            lines.append(f"Aliases:         {alias_stats['cache_size']}")
            lines.append(f"TTL:             {alias_stats['ttl']}s")
            if alias_stats['cache_loaded']:
                lines.append(f"Time since load: {alias_stats['time_since_load']:.1f}s")
                lines.append(f"TTL remaining:   {alias_stats['ttl_remaining']:.1f}s")
            lines.append(f"Cache file:      {alias_stats['cache_file']}")

        # Query cache stats
        if "query_cache" in stats:
            query_stats = stats["query_cache"]
            lines.append("\n💾 QUERY CACHE")
            lines.append("-" * 60)
            lines.append(f"Memory entries:  {query_stats['memory_entries']} / {query_stats['max_memory_entries']}")
            lines.append(f"Total queries:   {query_stats['total_queries']}")
            lines.append(f"Memory hits:     {query_stats['memory_hits']}")
            lines.append(f"Disk hits:       {query_stats['disk_hits']}")
            lines.append(f"Misses:          {query_stats['misses']}")
            lines.append(f"Hit rate:        {query_stats['hit_rate']:.2f}%")
            lines.append(f"  - Memory:      {query_stats['memory_hit_rate']:.2f}%")
            lines.append(f"  - Disk:        {query_stats['disk_hit_rate']:.2f}%")
            lines.append(f"Cost saved:      ${query_stats['cost_saved']:.4f}")
            lines.append(f"Disk cache size: {query_stats['disk_cache_size_mb']:.2f} MB")
            lines.append(f"Cache dir:       {query_stats['cache_dir']}")

        lines.append("\n" + "=" * 60)

        # Performance summary
        if "query_cache" in stats:
            query_stats = stats["query_cache"]
            if query_stats['total_queries'] > 0:
                lines.append("\n💰 COST SAVINGS SUMMARY")
                lines.append("-" * 60)
                lines.append(f"Total saved:     ${query_stats['cost_saved']:.4f}")
                lines.append(f"Avg per hit:     ${query_stats['cost_saved'] / max(1, query_stats['memory_hits'] + query_stats['disk_hits']):.4f}")

        return "\n".join(lines)
