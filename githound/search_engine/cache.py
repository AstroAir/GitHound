"""Enhanced caching system for GitHound search engine."""

import hashlib
import json
import pickle
import sys
import time
import zlib
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import redis.asyncio as redis
else:
    redis = None

try:
    import redis.asyncio as redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None  # type: ignore[assignment]


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass

    @abstractmethod
    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching pattern."""
        pass


class MemoryCache(CacheBackend):
    """In-memory cache backend with memory-aware eviction."""

    def __init__(
        self, max_size: int = 1000, default_ttl: int = 3600, max_memory_mb: int | None = None
    ) -> None:
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.max_memory_mb = max_memory_mb
        self._cache: dict[str, dict[str, Any]] = {}
        self._access_times: dict[str, float] = {}
        self._size_estimates: dict[str, int] = {}  # Track approximate size of each entry

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if key not in self._cache:
            return None

        entry = self._cache[key]

        # Check if expired
        if entry.get("expires_at") and time.time() > entry["expires_at"]:
            await self.delete(key)
            return None

        # Update access time
        self._access_times[key] = time.time()
        return entry["value"]

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL and memory-aware eviction."""
        # Estimate size of the value
        value_size = self._estimate_size(value)

        # Check memory limit if configured
        if self.max_memory_mb and key not in self._cache:
            current_memory_mb = sum(self._size_estimates.values()) / (1024 * 1024)
            if current_memory_mb + (value_size / (1024 * 1024)) > self.max_memory_mb:
                # Evict until we have enough space
                await self._evict_by_memory(value_size)

        # Evict if at max size
        if len(self._cache) >= self.max_size and key not in self._cache:
            await self._evict_lru()

        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None

        self._cache[key] = {
            "value": value,
            "created_at": time.time(),
            "expires_at": expires_at,
        }
        self._access_times[key] = time.time()
        self._size_estimates[key] = value_size
        return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
            self._access_times.pop(key, None)
            self._size_estimates.pop(key, None)
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._cache

    async def clear(self) -> bool:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_times.clear()
        return True

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching pattern."""
        if pattern == "*":
            return list(self._cache.keys())

        # Simple pattern matching (only supports * wildcard)
        import fnmatch

        return [key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)]

    async def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._access_times:
            return

        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        await self.delete(lru_key)

    async def _evict_by_memory(self, needed_bytes: int) -> None:
        """Evict items until we have enough memory for the new item."""
        if not self._size_estimates:
            return

        freed_bytes = 0
        # Sort by access time (LRU) and evict oldest first
        sorted_keys = sorted(self._access_times.keys(), key=lambda k: self._access_times[k])

        for key in sorted_keys:
            if freed_bytes >= needed_bytes:
                break
            freed_bytes += self._size_estimates.get(key, 0)
            await self.delete(key)

    def _estimate_size(self, obj: Any) -> int:
        """Estimate the size of an object in bytes.

        This is a rough estimate for memory management purposes.
        """
        try:
            # Use sys.getsizeof for a quick estimate
            # This doesn't account for all nested objects but is fast
            return sys.getsizeof(obj)
        except (TypeError, AttributeError):
            # Fallback for objects that don't support getsizeof
            return 1024  # Assume 1KB as default


class RedisCache(CacheBackend):
    """Redis cache backend."""

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        prefix: str = "githound:",
        default_ttl: int = 3600,
    ) -> None:
        if not HAS_REDIS:
            raise ImportError("redis package is required for RedisCache")

        self.url = url
        self.prefix = prefix
        self.default_ttl = default_ttl
        self._client: redis.Redis | None = None

    async def _get_client(self) -> "redis.Redis":
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(self.url)
        return self._client

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Optimization: Handle decompression of compressed values.
        """
        client = await self._get_client()
        try:
            data = await client.get(self._make_key(key))
            if data is None:
                return None

            # Optimization: Check compression marker and decompress if needed
            if len(data) > 0:
                if data[0:1] == b"\x01":
                    # Compressed data
                    data = zlib.decompress(data[1:])
                elif data[0:1] == b"\x00":
                    # Uncompressed data
                    data = data[1:]
                # else: legacy data without marker, try to load as-is

            return pickle.loads(data)
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL.

        Optimization: Compress large values to reduce memory and network usage.
        """
        client = await self._get_client()
        try:
            data = pickle.dumps(value)

            # Optimization: Compress if data is larger than 1KB
            if len(data) > 1024:
                data = zlib.compress(data, level=6)  # Level 6 is a good balance
                # Prepend a marker to indicate compression
                data = b"\x01" + data
            else:
                # Prepend marker for uncompressed data
                data = b"\x00" + data

            ttl = ttl or self.default_ttl
            if ttl > 0:
                await client.setex(self._make_key(key), ttl, data)
            else:
                await client.set(self._make_key(key), data)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        client = await self._get_client()
        try:
            result = await client.delete(self._make_key(key))
            return bool(result > 0)
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        client = await self._get_client()
        try:
            result = await client.exists(self._make_key(key))
            return bool(result > 0)
        except Exception:
            return False

    async def clear(self) -> bool:
        """Clear all cache entries."""
        client = await self._get_client()
        try:
            keys = await client.keys(f"{self.prefix}*")
            if keys:
                await client.delete(*keys)
            return True
        except Exception:
            return False

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching pattern."""
        client = await self._get_client()
        try:
            keys = await client.keys(f"{self.prefix}{pattern}")
            # Remove prefix from keys
            return [key.decode().replace(self.prefix, "") for key in keys]
        except Exception:
            return []

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()


class SearchCache:
    """Enhanced search cache with intelligent invalidation."""

    def __init__(
        self,
        backend: CacheBackend | None = None,
        default_ttl: int = 3600,
        enable_compression: bool = True,
    ) -> None:
        self.backend = backend or MemoryCache()
        self.default_ttl = default_ttl
        self.enable_compression = enable_compression
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }

    def _make_cache_key(self, *args: Any) -> str:
        """Create a cache key from arguments.

        Optimized to use faster hashing and avoid unnecessary JSON serialization
        for simple types.
        """
        # Fast path for simple types (strings, ints, etc.)
        if len(args) == 1 and isinstance(args[0], str | int | float | bool):
            return f"simple:{type(args[0]).__name__}:{args[0]}"

        # For complex types, use JSON serialization with SHA256
        # Using xxhash would be faster but adds dependency, so stick with hashlib
        try:
            key_data = json.dumps(args, sort_keys=True, default=str, separators=(",", ":"))
        except (TypeError, ValueError):
            # Fallback for non-serializable objects
            key_data = str(args)

        # Use blake2b for faster hashing than sha256
        return hashlib.blake2b(key_data.encode(), digest_size=16).hexdigest()

    async def get(self, *args: Any) -> Any | None:
        """Get value from cache."""
        key = self._make_cache_key(*args)
        value = await self.backend.get(key)

        if value is not None:
            self._stats["hits"] += 1
            return value
        else:
            self._stats["misses"] += 1
            return None

    async def set(self, value: Any, *args: Any, ttl: int | None = None) -> bool:
        """Set value in cache."""
        key = self._make_cache_key(*args)
        result = await self.backend.set(key, value, ttl or self.default_ttl)

        if result:
            self._stats["sets"] += 1

        return result

    async def delete(self, *args: Any) -> bool:
        """Delete value from cache."""
        key = self._make_cache_key(*args)
        result = await self.backend.delete(key)

        if result:
            self._stats["deletes"] += 1

        return result

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        keys = await self.backend.keys(pattern)
        count = 0

        for key in keys:
            if await self.backend.delete(key):
                count += 1
                self._stats["deletes"] += 1

        return count

    async def clear(self) -> bool:
        """Clear all cache entries."""
        return await self.backend.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0

        # Get backend-specific stats if available
        backend_stats = {}
        if isinstance(self.backend, MemoryCache):
            total_memory_bytes = sum(self.backend._size_estimates.values())
            backend_stats = {
                "cache_size": len(self.backend._cache),
                "max_size": self.backend.max_size,
                "memory_usage_mb": total_memory_bytes / (1024 * 1024),
                "max_memory_mb": self.backend.max_memory_mb,
                "avg_entry_size_kb": (
                    total_memory_bytes / len(self.backend._cache) / 1024
                    if self.backend._cache
                    else 0
                ),
            }

        return {
            **self._stats,
            "hit_rate": hit_rate,
            "miss_rate": 1.0 - hit_rate if total_requests > 0 else 0.0,
            "total_requests": total_requests,
            **backend_stats,
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
