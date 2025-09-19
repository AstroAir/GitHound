"""Basic tests for GitHound search engine cache module."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from githound.search_engine.cache import (
    CacheBackend,
    MemoryCache,
    RedisCache,
    SearchCache
)


class TestCacheBackend:
    """Test CacheBackend abstract class."""

    def test_cache_backend_is_abstract(self) -> None:
        """Test that CacheBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CacheBackend()


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

    @pytest.mark.asyncio
    async def test_set_and_get_basic(self) -> None:
        """Test basic set and get operations."""
        key = "test_key"
        value = {"data": "test_value", "number": 42}
        
        # Set data
        result = await self.cache.set(key, value)
        assert result is True
        
        # Get data
        retrieved = await self.cache.get(key)
        assert retrieved == value

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self) -> None:
        """Test getting non-existent key."""
        result = await self.cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists_key(self) -> None:
        """Test checking if key exists."""
        key = "exists_test"
        value = "test_data"
        
        # Key should not exist initially
        assert await self.cache.exists(key) is False
        
        # Set key
        await self.cache.set(key, value)
        
        # Key should exist now
        assert await self.cache.exists(key) is True

    @pytest.mark.asyncio
    async def test_delete_key(self) -> None:
        """Test deleting a key."""
        key = "delete_test"
        value = "test_data"
        
        await self.cache.set(key, value)
        assert await self.cache.exists(key) is True
        
        result = await self.cache.delete(key)
        assert result is True
        assert await self.cache.exists(key) is False

    @pytest.mark.asyncio
    async def test_clear_cache(self) -> None:
        """Test clearing all cache data."""
        # Add multiple items
        for i in range(5):
            await self.cache.set(f"key_{i}", f"value_{i}")
        
        assert len(self.cache._data) == 5
        
        result = await self.cache.clear()
        assert result is True
        assert len(self.cache._data) == 0

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self) -> None:
        """Test setting data with custom TTL."""
        key = "ttl_test"
        value = "test_data"
        custom_ttl = 1  # 1 second
        
        await self.cache.set(key, value, ttl=custom_ttl)
        
        # Should exist immediately
        assert await self.cache.exists(key) is True
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired (trigger cleanup)
        await self.cache._cleanup_expired()
        assert await self.cache.exists(key) is False

    @pytest.mark.asyncio
    async def test_cache_size_limit(self) -> None:
        """Test cache size limit enforcement."""
        small_cache = MemoryCache(max_size=3)
        
        # Add items up to and beyond limit
        for i in range(5):
            await small_cache.set(f"key_{i}", f"value_{i}")
        
        # Should only keep the most recent items
        assert len(small_cache._data) <= 3


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
    async def test_redis_set_and_get(self) -> None:
        """Test Redis set and get operations."""
        key = "redis_test"
        value = {"test": "data", "number": 123}
        
        # Set data
        result = await self.cache.set(key, value)
        assert result is True
        
        # Get data
        retrieved = await self.cache.get(key)
        assert retrieved == value

    @pytest.mark.asyncio
    async def test_redis_key_prefix(self) -> None:
        """Test Redis key prefixing."""
        key = "prefix_test"
        value = "test_data"
        
        await self.cache.set(key, value)
        
        # Check that the key is stored with prefix
        client = await self.cache._get_client()
        prefixed_key = self.cache._make_key(key)
        assert await client.exists(prefixed_key) == 1

    @pytest.mark.asyncio
    async def test_redis_delete_and_clear(self) -> None:
        """Test Redis delete and clear operations."""
        # Add test data
        keys = ["del_test_1", "del_test_2", "del_test_3"]
        for key in keys:
            await self.cache.set(key, "test_data")
        
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
    async def test_search_cache_initialization(self) -> None:
        """Test search cache initialization."""
        cache = SearchCache(backend="memory", default_ttl=1800)
        
        assert cache.backend == "memory"
        assert cache.default_ttl == 1800
        assert isinstance(cache._backend, MemoryCache)

    @pytest.mark.asyncio
    async def test_cache_search_results(self) -> None:
        """Test caching search results."""
        from githound.models import SearchQuery, SearchResult, SearchType
        
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
        from githound.models import SearchQuery
        
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
        from githound.models import SearchQuery
        
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
        from githound.models import SearchQuery
        
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
    async def test_cache_backend_switching(self) -> None:
        """Test switching between cache backends."""
        # Test memory backend
        memory_cache = SearchCache(backend="memory")
        
        from githound.models import SearchQuery
        query = SearchQuery(content_pattern="test")
        key = await memory_cache.cache_search_results(query, [], "/repo")
        assert await memory_cache.get_cached_results(key) is not None

    @pytest.mark.asyncio
    async def test_cache_performance_under_load(self) -> None:
        """Test cache performance under load."""
        cache = SearchCache(backend="memory")
        
        from githound.models import SearchQuery
        
        # Simulate concurrent cache operations
        async def cache_operation(i: int) -> None:
            query = SearchQuery(content_pattern=f"test_{i}")
            await cache.cache_search_results(query, [], f"/repo_{i}")
        
        # Run concurrent operations
        tasks = [cache_operation(i) for i in range(50)]
        await asyncio.gather(*tasks)
        
        stats = await cache.get_statistics()
        assert stats["total_keys"] >= 50
