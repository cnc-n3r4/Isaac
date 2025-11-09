"""
Cache Manager - Manage local cache for offline access
"""

import json
import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import hashlib


class CacheManager:
    """
    Manages local cache of data for offline access
    """

    def __init__(self, storage_path: Optional[str] = None, max_size_mb: int = 500):
        if storage_path is None:
            storage_path = Path.home() / '.isaac' / 'cache'

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.db_path = self.storage_path / 'cache.db'
        self.max_size_bytes = max_size_mb * 1024 * 1024

        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                category TEXT,
                size INTEGER,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                expires_at TEXT,
                access_count INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON cache(category)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
        ''')

        conn.commit()
        conn.close()

    def set(
        self,
        key: str,
        value: Any,
        category: Optional[str] = None,
        ttl_seconds: Optional[int] = None
    ):
        """
        Set cache entry

        Args:
            key: Cache key
            value: Value to cache
            category: Optional category
            ttl_seconds: Time to live in seconds
        """
        # Serialize value
        serialized = json.dumps(value)
        size = len(serialized.encode('utf-8'))

        # Calculate expiration
        expires_at = None
        if ttl_seconds:
            expires_at = (
                datetime.utcnow() + timedelta(seconds=ttl_seconds)
            ).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()

        cursor.execute('''
            INSERT OR REPLACE INTO cache
            (key, value, category, size, created_at, last_accessed, expires_at, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE(
                (SELECT access_count FROM cache WHERE key = ?), 0
            ))
        ''', (key, serialized, category, size, now, now, expires_at, key))

        conn.commit()
        conn.close()

        # Check if we need to evict
        self._evict_if_needed()

    def get(self, key: str) -> Optional[Any]:
        """
        Get cache entry

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT value, expires_at
            FROM cache
            WHERE key = ?
        ''', (key,))

        result = cursor.fetchone()

        if not result:
            conn.close()
            return None

        value, expires_at = result

        # Check expiration
        if expires_at:
            if datetime.utcnow() > datetime.fromisoformat(expires_at):
                # Expired, delete it
                cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
                conn.commit()
                conn.close()
                return None

        # Update access stats
        cursor.execute('''
            UPDATE cache
            SET last_accessed = ?,
                access_count = access_count + 1
            WHERE key = ?
        ''', (datetime.utcnow().isoformat(), key))

        conn.commit()
        conn.close()

        # Deserialize and return
        return json.loads(value)

    def delete(self, key: str) -> bool:
        """Delete cache entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    def clear_category(self, category: str) -> int:
        """Clear all entries in a category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM cache WHERE category = ?', (category,))
        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        return deleted

    def clear_expired(self) -> int:
        """Remove expired entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM cache
            WHERE expires_at IS NOT NULL
            AND expires_at < ?
        ''', (datetime.utcnow().isoformat(),))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted

    def _evict_if_needed(self):
        """Evict entries if cache is too large"""
        total_size = self.get_cache_size()

        if total_size <= self.max_size_bytes:
            return

        # Evict least recently used entries
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate how much to evict
        to_evict = total_size - self.max_size_bytes

        cursor.execute('''
            SELECT key, size
            FROM cache
            ORDER BY last_accessed ASC
        ''')

        evicted_size = 0
        keys_to_delete = []

        for key, size in cursor.fetchall():
            keys_to_delete.append(key)
            evicted_size += size

            if evicted_size >= to_evict:
                break

        # Delete selected entries
        for key in keys_to_delete:
            cursor.execute('DELETE FROM cache WHERE key = ?', (key,))

        conn.commit()
        conn.close()

    def get_cache_size(self) -> int:
        """Get total cache size in bytes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT SUM(size) FROM cache')
        result = cursor.fetchone()

        conn.close()

        return result[0] or 0

    def get_entry_count(self) -> int:
        """Get number of cached entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM cache')
        count = cursor.fetchone()[0]

        conn.close()

        return count

    def list_keys(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[str]:
        """
        List cache keys

        Args:
            category: Optional category filter
            limit: Maximum number of keys

        Returns:
            List of keys
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if category:
            cursor.execute('''
                SELECT key
                FROM cache
                WHERE category = ?
                ORDER BY last_accessed DESC
                LIMIT ?
            ''', (category, limit))
        else:
            cursor.execute('''
                SELECT key
                FROM cache
                ORDER BY last_accessed DESC
                LIMIT ?
            ''', (limit,))

        results = cursor.fetchall()
        conn.close()

        return [row[0] for row in results]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get category stats
        cursor.execute('''
            SELECT category, COUNT(*), SUM(size)
            FROM cache
            GROUP BY category
        ''')

        category_stats = {}
        for cat, count, size in cursor.fetchall():
            category_stats[cat or 'uncategorized'] = {
                'count': count,
                'size': size or 0
            }

        conn.close()

        return {
            'total_entries': self.get_entry_count(),
            'total_size': self.get_cache_size(),
            'max_size': self.max_size_bytes,
            'usage_percent': (self.get_cache_size() / self.max_size_bytes * 100),
            'categories': category_stats
        }

    def clear_all(self):
        """Clear entire cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM cache')

        conn.commit()
        conn.close()
