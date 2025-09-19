"""Enhanced caching system for GitHound search engine."""

import asyncio
import hashlib
import json
import pickle
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    import redis.asyncio as redis

try:
    import redis.asyncio as redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
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
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern."""
        pass


class MemoryCache(CacheBackend):
    """In-memory cache backend."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600) -> None:
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
    
    async def get(self, key: str) -> Optional[Any]:
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
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
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
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
            self._access_times.pop(key, None)
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
    
    async def keys(self, pattern: str = "*") -> List[str]:
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


class RedisCache(CacheBackend):
    """Redis cache backend."""
    
    def __init__(
        self, 
        url: str = "redis://localhost:6379", 
        prefix: str = "githound:",
        default_ttl: int = 3600
    ) -> None:
        if not HAS_REDIS:
            raise ImportError("redis package is required for RedisCache")
        
        self.url = url
        self.prefix = prefix
        self.default_ttl = default_ttl
        self._client: Optional["redis.Redis"] = None

    async def _get_client(self) -> "redis.Redis":
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(self.url)
        return self._client
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        client = await self._get_client()
        try:
            data = await client.get(self._make_key(key))
            if data is None:
                return None
            return pickle.loads(data)
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        client = await self._get_client()
        try:
            data = pickle.dumps(value)
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
    
    async def keys(self, pattern: str = "*") -> List[str]:
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
        backend: Optional[CacheBackend] = None,
        default_ttl: int = 3600,
        enable_compression: bool = True
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
        """Create a cache key from arguments."""
        # Create a deterministic hash of the arguments
        key_data = json.dumps(args, sort_keys=True, default=str)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    async def get(self, *args: Any) -> Optional[Any]:
        """Get value from cache."""
        key = self._make_cache_key(*args)
        value = await self.backend.get(key)
        
        if value is not None:
            self._stats["hits"] += 1
            return value
        else:
            self._stats["misses"] += 1
            return None
    
    async def set(self, value: Any, *args: Any, ttl: Optional[int] = None) -> bool:
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0
        
        return {
            **self._stats,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }
    
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
