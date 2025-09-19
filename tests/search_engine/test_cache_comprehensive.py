"""Comprehensive tests for GitHound search engine cache module."""

import pytest
import asyncio
import json
import pickle
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Any, Dict, List, Optional

from githound.search_engine.cache import (
    CacheBackend,
    MemoryCache,
    RedisCache,
    SearchCache,
    CacheConfig,
    CacheStats
)
from githound.models import SearchQuery, SearchResult, SearchType


@pytest.fixture
def cache_config() -> CacheConfig:
    """Create cache configuration for testing."""
    return CacheConfig(
        backend="memory",
        default_ttl=3600,
        max_size=1000,
        cleanup_interval=300
    )


@pytest.fixture
def sample_cache_data() -> Dict[str, Any]:
    """Create sample data for caching."""
    return {
        "search_results": [
            {
                "commit_hash": "abc123",
                "file_path": "test.py",
                "line_number": 10,
                "content": "def test_function():"
            }
        ],
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "query_hash": "query123",
            "result_count": 1
        }
    }


class TestMemoryCache:
    """Test MemoryCache implementation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.cache = MemoryCache(max_size=100, default_ttl=3600)

    @pytest.mark.asyncio
    async def test_memory_cache_initialization(self) -> None:
        """Test memory cache initialization."""
        cache = MemoryCache(max_size=50, default_ttl=1800)
        
        assert cache.max_size == 50
        assert cache.default_ttl == 1800
        assert len(cache._data) == 0
        assert len(cache._expiry) == 0

    @pytest.mark.asyncio
    async def test_set_and_get_basic(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test basic set and get operations."""
        key = "test_key"
        
        # Set data
        result = await self.cache.set(key, sample_cache_data)
        assert result is True
        
        # Get data
        retrieved = await self.cache.get(key)
        assert retrieved == sample_cache_data

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self) -> None:
        """Test getting non-existent key."""
        result = await self.cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test setting data with custom TTL."""
        key = "ttl_test"
        custom_ttl = 1  # 1 second
        
        await self.cache.set(key, sample_cache_data, ttl=custom_ttl)
        
        # Should exist immediately
        assert await self.cache.exists(key) is True
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        assert await self.cache.get(key) is None
        assert await self.cache.exists(key) is False

    @pytest.mark.asyncio
    async def test_delete_key(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test deleting a key."""
        key = "delete_test"
        
        await self.cache.set(key, sample_cache_data)
        assert await self.cache.exists(key) is True
        
        result = await self.cache.delete(key)
        assert result is True
        assert await self.cache.exists(key) is False

    @pytest.mark.asyncio
    async def test_clear_cache(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test clearing all cache data."""
        # Add multiple items
        for i in range(5):
            await self.cache.set(f"key_{i}", sample_cache_data)
        
        assert len(self.cache._data) == 5
        
        result = await self.cache.clear()
        assert result is True
        assert len(self.cache._data) == 0
        assert len(self.cache._expiry) == 0

    @pytest.mark.asyncio
    async def test_keys_pattern_matching(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test getting keys with pattern matching."""
        # Add test data
        test_keys = ["user:123", "user:456", "session:789", "cache:abc"]
        for key in test_keys:
            await self.cache.set(key, sample_cache_data)
        
        # Test pattern matching
        user_keys = await self.cache.keys("user:*")
        assert len(user_keys) == 2
        assert "user:123" in user_keys
        assert "user:456" in user_keys
        
        all_keys = await self.cache.keys("*")
        assert len(all_keys) == 4

    @pytest.mark.asyncio
    async def test_cache_size_limit(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test cache size limit enforcement."""
        small_cache = MemoryCache(max_size=3)
        
        # Add items up to limit
        for i in range(5):
            await small_cache.set(f"key_{i}", sample_cache_data)
        
        # Should only keep the most recent items
        assert len(small_cache._data) <= 3
        
        # Newest items should still exist
        assert await small_cache.exists("key_4") is True
        assert await small_cache.exists("key_3") is True

    @pytest.mark.asyncio
    async def test_cleanup_expired_items(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test cleanup of expired items."""
        # Add item with short TTL
        await self.cache.set("short_lived", sample_cache_data, ttl=1)
        await self.cache.set("long_lived", sample_cache_data, ttl=3600)
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Trigger cleanup
        await self.cache._cleanup_expired()
        
        assert await self.cache.exists("short_lived") is False
        assert await self.cache.exists("long_lived") is True

    @pytest.mark.asyncio
    async def test_cache_statistics(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test cache statistics collection."""
        # Perform various operations
        await self.cache.set("key1", sample_cache_data)
        await self.cache.get("key1")  # Hit
        await self.cache.get("nonexistent")  # Miss
        
        stats = await self.cache.get_stats()
        
        assert stats["total_keys"] >= 1
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert "hit_rate" in stats


@pytest.mark.skipif(
    not hasattr(pytest, "redis_available") or not pytest.redis_available,
    reason="Redis not available for testing"
)
class TestRedisCache:
    """Test RedisCache implementation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.cache = RedisCache(
            url="redis://localhost:6379/15",  # Test database
            prefix="test:",
            default_ttl=3600
        )

    @pytest.mark.asyncio
    async def test_redis_cache_initialization(self) -> None:
        """Test Redis cache initialization."""
        cache = RedisCache(
            url="redis://localhost:6379/14",
            prefix="custom:",
            default_ttl=1800
        )
        
        assert cache.url == "redis://localhost:6379/14"
        assert cache.prefix == "custom:"
        assert cache.default_ttl == 1800

    @pytest.mark.asyncio
    async def test_redis_set_and_get(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test Redis set and get operations."""
        key = "redis_test"
        
        # Set data
        result = await self.cache.set(key, sample_cache_data)
        assert result is True
        
        # Get data
        retrieved = await self.cache.get(key)
        assert retrieved == sample_cache_data

    @pytest.mark.asyncio
    async def test_redis_key_prefix(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test Redis key prefixing."""
        key = "prefix_test"
        
        await self.cache.set(key, sample_cache_data)
        
        # Check that the key is stored with prefix
        client = await self.cache._get_client()
        prefixed_key = self.cache._make_key(key)
        assert await client.exists(prefixed_key) == 1

    @pytest.mark.asyncio
    async def test_redis_ttl_expiration(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test Redis TTL and expiration."""
        key = "ttl_test"
        
        await self.cache.set(key, sample_cache_data, ttl=1)
        
        # Should exist immediately
        assert await self.cache.exists(key) is True
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        assert await self.cache.exists(key) is False

    @pytest.mark.asyncio
    async def test_redis_delete_and_clear(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test Redis delete and clear operations."""
        # Add test data
        keys = ["del_test_1", "del_test_2", "del_test_3"]
        for key in keys:
            await self.cache.set(key, sample_cache_data)
        
        # Delete single key
        result = await self.cache.delete("del_test_1")
        assert result is True
        assert await self.cache.exists("del_test_1") is False
        
        # Clear all keys with prefix
        result = await self.cache.clear()
        assert result is True
        
        for key in keys[1:]:  # Check remaining keys
            assert await self.cache.exists(key) is False


class TestSearchCache:
    """Test SearchCache high-level interface."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.cache = SearchCache(backend="memory")

    @pytest.mark.asyncio
    async def test_search_cache_initialization(self, cache_config: CacheConfig) -> None:
        """Test search cache initialization."""
        cache = SearchCache(config=cache_config)
        
        assert cache.config == cache_config
        assert isinstance(cache._backend, MemoryCache)

    @pytest.mark.asyncio
    async def test_cache_search_results(self) -> None:
        """Test caching search results."""
        query = SearchQuery(content_pattern="test")
        results = [
            SearchResult(
                commit_hash="abc123",
                file_path="test.py",
                line_number=10,
                matching_line="def test():",
                search_type=SearchType.CONTENT,
                relevance_score=0.9
            )
        ]
        
        # Cache results
        cache_key = await self.cache.cache_search_results(
            query=query,
            results=results,
            repo_path="/test/repo",
            branch="main"
        )
        
        assert cache_key is not None
        
        # Retrieve results
        cached_results = await self.cache.get_cached_results(cache_key)
        assert cached_results is not None
        assert len(cached_results) == len(results)

    @pytest.mark.asyncio
    async def test_generate_cache_key(self) -> None:
        """Test cache key generation."""
        query1 = SearchQuery(content_pattern="test")
        query2 = SearchQuery(content_pattern="test")
        query3 = SearchQuery(content_pattern="different")
        
        key1 = await self.cache._generate_cache_key(query1, "/repo", "main")
        key2 = await self.cache._generate_cache_key(query2, "/repo", "main")
        key3 = await self.cache._generate_cache_key(query3, "/repo", "main")
        
        # Same queries should generate same keys
        assert key1 == key2
        
        # Different queries should generate different keys
        assert key1 != key3

    @pytest.mark.asyncio
    async def test_cache_invalidation(self) -> None:
        """Test cache invalidation."""
        query = SearchQuery(content_pattern="test")
        results = []
        
        cache_key = await self.cache.cache_search_results(
            query=query,
            results=results,
            repo_path="/test/repo"
        )
        
        # Verify cached
        assert await self.cache.get_cached_results(cache_key) is not None
        
        # Invalidate
        await self.cache.invalidate_cache(repo_path="/test/repo")
        
        # Should be gone
        assert await self.cache.get_cached_results(cache_key) is None

    @pytest.mark.asyncio
    async def test_cache_statistics(self) -> None:
        """Test cache statistics."""
        # Perform some cache operations
        query = SearchQuery(content_pattern="test")
        await self.cache.cache_search_results(query, [], "/repo")
        
        stats = await self.cache.get_statistics()
        
        assert "total_keys" in stats
        assert "cache_size" in stats
        assert "hit_rate" in stats


@pytest.mark.integration
class TestCacheIntegration:
    """Integration tests for cache components."""

    @pytest.mark.asyncio
    async def test_cache_backend_switching(self, cache_config: CacheConfig) -> None:
        """Test switching between cache backends."""
        # Test memory backend
        memory_config = cache_config.copy()
        memory_config.backend = "memory"
        memory_cache = SearchCache(config=memory_config)
        
        query = SearchQuery(content_pattern="test")
        key = await memory_cache.cache_search_results(query, [], "/repo")
        assert await memory_cache.get_cached_results(key) is not None

    @pytest.mark.asyncio
    async def test_cache_performance_under_load(self) -> None:
        """Test cache performance under load."""
        cache = SearchCache(backend="memory")
        
        # Simulate concurrent cache operations
        async def cache_operation(i: int) -> None:
            query = SearchQuery(content_pattern=f"test_{i}")
            await cache.cache_search_results(query, [], f"/repo_{i}")
        
        # Run concurrent operations
        tasks = [cache_operation(i) for i in range(100)]
        await asyncio.gather(*tasks)
        
        stats = await cache.get_statistics()
        assert stats["total_keys"] >= 100

    @pytest.mark.asyncio
    async def test_cache_serialization_formats(self, sample_cache_data: Dict[str, Any]) -> None:
        """Test different serialization formats."""
        cache = MemoryCache()
        
        # Test JSON serializable data
        json_data = {"key": "value", "number": 42}
        await cache.set("json_test", json_data)
        retrieved = await cache.get("json_test")
        assert retrieved == json_data
        
        # Test complex objects
        complex_data = {
            "datetime": datetime.now(),
            "list": [1, 2, 3],
            "nested": {"inner": "value"}
        }
        await cache.set("complex_test", complex_data)
        retrieved = await cache.get("complex_test")
        assert retrieved == complex_data
