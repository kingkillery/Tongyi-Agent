"""
Caching Module for Performance Optimization
--------------------------------------------
Provides in-memory and optional file-based caching for API calls and other expensive operations.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import threading
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Default cache configuration
DEFAULT_TTL = 600  # 10 minutes in seconds
DEFAULT_CACHE_DIR = Path.home() / ".tongyi_cache"


@dataclass
class CacheEntry:
    """A cache entry with value and expiration."""
    value: Any
    expires_at: float
    hit_count: int = 0


@dataclass
class CacheStats:
    """Cache statistics for monitoring."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_entries: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class Cache:
    """
    Simple in-memory cache with optional file-based persistence.

    Features:
    - Time-based expiration (TTL)
    - Thread-safe operations
    - Optional file persistence
    - Statistics tracking
    """

    def __init__(
        self,
        ttl: int = DEFAULT_TTL,
        max_size: int = 1000,
        persistent: bool = False,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize cache.

        Args:
            ttl: Time-to-live in seconds (default: 600)
            max_size: Maximum number of entries (default: 1000)
            persistent: Enable file-based persistence (default: False)
            cache_dir: Directory for cache files (default: ~/.tongyi_cache)
        """
        self.ttl = ttl
        self.max_size = max_size
        self.persistent = persistent
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = CacheStats()
        self._dirty = False  # Track if cache needs saving

        if self.persistent:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        """
        Create a cache key from function arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            SHA256 hash of serialized arguments
        """
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats.misses += 1
                return None

            # Check expiration
            if time.time() > entry.expires_at:
                # Remove expired entry
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                self._stats.total_entries = len(self._cache)
                self._dirty = True
                return None

            # Cache hit
            entry.hit_count += 1
            self._stats.hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Override default TTL (optional)
        """
        with self._lock:
            # Evict if at max size
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_oldest()

            # Create cache entry
            entry_ttl = ttl or self.ttl
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=time.time() + entry_ttl,
                hit_count=0
            )
            self._stats.total_entries = len(self._cache)
            self._dirty = True

            if self.persistent:
                self._save_to_disk_async()

    def _evict_oldest(self) -> None:
        """Remove the oldest entry to make room."""
        if not self._cache:
            return
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].expires_at)
        del self._cache[oldest_key]
        self._stats.evictions += 1

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()
            self._dirty = True
            if self.persistent:
                self._save_to_disk()

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Optional pattern to match keys (glob-style)

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                self._stats.total_entries = 0
                self._dirty = True
                return count

            import fnmatch
            keys_to_remove = [k for k in self._cache if fnmatch.fnmatch(k, pattern)]
            for key in keys_to_remove:
                del self._cache[key]
            self._stats.total_entries = len(self._cache)
            self._dirty = True
            return len(keys_to_remove)

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                total_entries=len(self._cache)
            )

    def _save_to_disk(self) -> None:
        """Save cache to disk if persistent."""
        if not self.persistent:
            return

        try:
            # Save only non-expired entries
            now = time.time()
            cache_data = {
                key: {
                    "value": entry.value,
                    "expires_at": entry.expires_at,
                    "hit_count": entry.hit_count
                }
                for key, entry in self._cache.items()
                if entry.expires_at > now
            }

            cache_file = self.cache_dir / "cache.json"
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, default=str)

            self._dirty = False
        except (IOError, json.JSONEncodeError) as e:
            # Silently fail on save errors
            pass

    def _save_to_disk_async(self) -> None:
        """Save cache asynchronously in background thread."""
        if not self.persistent or not self._dirty:
            return

        def save():
            self._save_to_disk()

        thread = threading.Thread(target=save, daemon=True)
        thread.start()

    def _load_from_disk(self) -> None:
        """Load cache from disk if persistent."""
        if not self.persistent:
            return

        try:
            cache_file = self.cache_dir / "cache.json"
            if not cache_file.exists():
                return

            with open(cache_file, 'r') as f:
                cache_data = json.load(f)

            now = time.time()
            for key, data in cache_data.items():
                if data["expires_at"] > now:
                    self._cache[key] = CacheEntry(
                        value=data["value"],
                        expires_at=data["expires_at"],
                        hit_count=data.get("hit_count", 0)
                    )

            self._stats.total_entries = len(self._cache)
        except (IOError, json.JSONDecodeError):
            # Start fresh on load errors
            self._cache.clear()

    def __len__(self) -> int:
        """Return number of cache entries."""
        with self._lock:
            return len(self._cache)


# Global cache instances
_api_cache: Optional[Cache] = None
_file_cache: Optional[Cache] = None
_cache_lock = threading.Lock()


def get_api_cache() -> Cache:
    """Get or create global API cache instance."""
    global _api_cache
    with _cache_lock:
        if _api_cache is None:
            _api_cache = Cache(
                ttl=600,  # 10 minutes for API responses
                max_size=500,
                persistent=False  # In-memory only for API
            )
        return _api_cache


def get_file_cache() -> Cache:
    """Get or create global file cache instance."""
    global _file_cache
    with _cache_lock:
        if _file_cache is None:
            _file_cache = Cache(
                ttl=1800,  # 30 minutes for file contents
                max_size=200,
                persistent=True,  # Persist file cache
                cache_dir=DEFAULT_CACHE_DIR
            )
        return _file_cache


def clear_all_caches() -> None:
    """Clear all global cache instances."""
    with _cache_lock:
        if _api_cache:
            _api_cache.clear()
        if _file_cache:
            _file_cache.clear()


def get_all_stats() -> Dict[str, Any]:
    """Get statistics for all caches."""
    with _cache_lock:
        stats = {}
        if _api_cache:
            stats["api"] = asdict(_api_cache.get_stats())
            stats["api"]["hit_rate"] = _api_cache.get_stats().hit_rate
        if _file_cache:
            stats["file"] = asdict(_file_cache.get_stats())
            stats["file"]["hit_rate"] = _file_cache.get_stats().hit_rate
        return stats


if __name__ == "__main__":
    # Simple test
    cache = Cache(ttl=10)

    # Test basic operations
    key1 = cache._make_key("test", "arg1", arg2="value")
    cache.set(key1, "test_value")
    assert cache.get(key1) == "test_value"
    print("Basic cache operations: OK")

    # Test expiration
    time.sleep(11)
    assert cache.get(key1) is None
    print("Cache expiration: OK")

    # Test stats
    cache2 = Cache(ttl=60)
    key2 = cache2._make_key("stats_test")
    cache2.set(key2, "value")
    cache2.get(key2)  # Hit
    cache2.get("nonexistent")  # Miss
    stats = cache2.get_stats()
    assert stats.hits == 1
    assert stats.misses == 1
    assert stats.hit_rate == 0.5
    print("Cache statistics: OK")

    print("\nAll cache tests passed!")
