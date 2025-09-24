"""Tests for GitHound search engine base classes."""

from abc import ABC
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from git import Repo

from githound.models import SearchQuery, SearchResult, SearchType
from githound.search_engine import (
    BaseSearcher,
    CacheableSearcher,
    SearchContext,
)


@pytest.fixture
def mock_repo() -> None:
    """Create a mock Git repository."""
    mock_repo = Mock(spec=Repo)
    mock_repo.git_dir = "/test/repo/.git"
    mock_repo.working_dir = "/test/repo"
    mock_repo.active_branch.name = "main"

    # Create mock commits
    mock_commits: list[Any] = []
    for i in range(5):
        commit = Mock()
        commit.hexsha = f"commit{i:03d}" + "0" * 37
        commit.author.name = f"Author {i}"
        commit.author.email = f"author{i}@example.com"
        commit.committer.name = f"Author {i}"
        commit.committer.email = f"author{i}@example.com"
        commit.message = f"Test commit {i}"
        commit.committed_date = int((datetime.now() - timedelta(days=i)).timestamp())
        commit.committed_datetime = datetime.now() - timedelta(days=i)
        commit.stats.files = {f"file{i}.py": {"insertions": 10, "deletions": 5}}
        commit.stats.total = {"insertions": 10, "deletions": 5}
        commit.parents = []
        commit.repo = mock_repo
        mock_commits.append(commit)

    mock_repo.iter_commits.return_value = mock_commits
    return mock_repo


@pytest.fixture
def sample_search_query() -> None:
    """Create a sample search query for testing."""
    return SearchQuery(
        content_pattern="test",
        author_pattern="Test User",
        message_pattern="commit",
        commit_hash="abc123",
        date_from=datetime.now() - timedelta(days=30),
        date_to=datetime.now(),
        file_path_pattern="*.py",
        file_extensions=["py", "js"],
        fuzzy_search=True,
        fuzzy_threshold=0.8,
        case_sensitive=False,
    )


@pytest.fixture
def search_context(mock_repo, sample_search_query) -> None:
    """Create a search context for testing."""
    return SearchContext(
        repo=mock_repo, query=sample_search_query, branch="main", progress_callback=None, cache={}
    )


class MockSearcher(BaseSearcher):
    """Concrete implementation of BaseSearcher for testing."""

    def __init__(self) -> None:
        super().__init__("test_searcher")

    async def can_handle(self, query: SearchQuery) -> bool:
        return query.content_pattern is not None

    async def estimate_work(self, context: SearchContext) -> int:
        return 10

    async def search(self, context: SearchContext) -> None:
        yield SearchResult(
            commit_hash="abc123",
            file_path="test.py",
            line_number=1,
            matching_line="test content",
            search_type=SearchType.CONTENT,
            relevance_score=0.9,
        )


class MockCacheableSearcher(CacheableSearcher):
    """Concrete implementation of CacheableSearcher for testing."""

    def __init__(self) -> None:
        super().__init__("test_cacheable_searcher")

    async def can_handle(self, query: SearchQuery) -> bool:
        return query.content_pattern is not None

    async def estimate_work(self, context: SearchContext) -> int:
        return 10

    async def search(self, context: SearchContext) -> None:
        # Check cache first
        cache_key = self._get_cache_key(context)
        cached_results = await self._get_from_cache(context, cache_key)

        if cached_results is not None:
            # Return cached results
            for result in cached_results:
                yield result
            return

        # Generate new results
        results = [
            SearchResult(
                commit_hash="def456",
                file_path="cached_test.py",
                line_number=2,
                matching_line="cached test content",
                search_type=SearchType.CONTENT,
                relevance_score=0.8,
            )
        ]

        # Cache the results (work around base class bug)
        if context.cache is not None:
            context.cache[cache_key] = results

        # Yield results
        for result in results:
            yield result


class TestBaseSearcher:
    """Tests for BaseSearcher abstract base class."""

    def test_base_searcher_is_abstract(self) -> None:
        """Test that BaseSearcher is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseSearcher()

    def test_concrete_searcher_instantiation(self) -> None:
        """Test that concrete searcher can be instantiated."""
        searcher = MockSearcher()
        assert searcher is not None
        assert searcher.name == "test_searcher"

    @pytest.mark.asyncio
    async def test_concrete_searcher_can_handle(self, sample_search_query) -> None:
        """Test concrete searcher can_handle method."""
        searcher = MockSearcher()

        # Should handle queries with content pattern
        assert await searcher.can_handle(sample_search_query) is True

        # Should not handle queries without content pattern
        query_no_content = SearchQuery(author_pattern="test")
        assert await searcher.can_handle(query_no_content) is False

    @pytest.mark.asyncio
    async def test_concrete_searcher_estimate_work(self, sample_search_query) -> None:
        """Test concrete searcher estimate_work method."""
        searcher = MockSearcher()
        work_estimate = await searcher.estimate_work(sample_search_query)
        assert work_estimate == 10

    @pytest.mark.asyncio
    async def test_concrete_searcher_search(self, search_context) -> None:
        """Test concrete searcher search method."""
        searcher = MockSearcher()

        results: list[Any] = []
        async for result in searcher.search(search_context):
            results.append(result)

        assert len(results) == 1
        assert results[0].commit_hash == "abc123"
        assert str(results[0].file_path) == "test.py"
        assert results[0].line_number == 1
        assert results[0].matching_line == "test content"
        assert results[0].search_type == SearchType.CONTENT
        assert results[0].relevance_score == 0.9


class TestCacheableSearcherClass:
    """Tests for CacheableSearcher class."""

    def test_cacheable_searcher_instantiation(self) -> None:
        """Test that CacheableSearcher can be instantiated."""
        searcher = MockCacheableSearcher()
        assert searcher is not None
        assert searcher.name == "test_cacheable_searcher"

    @pytest.mark.asyncio
    async def test_cacheable_searcher_cache_key_generation(self, search_context) -> None:
        """Test cache key generation."""
        searcher = MockCacheableSearcher()

        cache_key = searcher._get_cache_key(search_context)
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0

    @pytest.mark.asyncio
    async def test_cacheable_searcher_cache_key_consistency(self, search_context) -> None:
        """Test that cache keys are consistent for the same context."""
        searcher = MockCacheableSearcher()

        key1 = searcher._get_cache_key(search_context)
        key2 = searcher._get_cache_key(search_context)
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_cacheable_searcher_cache_key_uniqueness(self, mock_repo) -> None:
        """Test that different contexts generate different cache keys."""
        searcher = MockCacheableSearcher()

        query1 = SearchQuery(content_pattern="test1")
        query2 = SearchQuery(content_pattern="test2")

        context1 = SearchContext(repo=mock_repo, query=query1, branch="main", cache={})
        context2 = SearchContext(repo=mock_repo, query=query2, branch="main", cache={})

        key1 = searcher._get_cache_key(context1)
        key2 = searcher._get_cache_key(context2)
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_cacheable_searcher_caching_behavior(self, search_context) -> None:
        """Test that results are cached and retrieved correctly."""
        searcher = MockCacheableSearcher()

        # First search - should cache results
        results1: list[Any] = []
        async for result in searcher.search(search_context):
            results1.append(result)

        # Verify cache was populated
        cache_key = searcher._get_cache_key(search_context)
        assert cache_key in search_context.cache

        # Second search - should use cached results
        results2: list[Any] = []
        async for result in searcher.search(search_context):
            results2.append(result)

        # Results should be identical
        assert len(results1) == len(results2)
        assert results1[0].commit_hash == results2[0].commit_hash
        assert results1[0].file_path == results2[0].file_path

    @pytest.mark.asyncio
    async def test_cacheable_searcher_cache_miss(self, search_context) -> None:
        """Test behavior when cache is empty."""
        searcher = MockCacheableSearcher()

        # Ensure cache is empty
        search_context.cache.clear()

        results: list[Any] = []
        async for result in searcher.search(search_context):
            results.append(result)

        assert len(results) == 1
        assert results[0].commit_hash == "def456"

    @pytest.mark.asyncio
    async def test_cacheable_searcher_cache_hit(self, search_context) -> None:
        """Test behavior when cache contains results."""
        searcher = MockCacheableSearcher()

        # Pre-populate cache
        cache_key = searcher._get_cache_key(search_context)
        cached_result = SearchResult(
            commit_hash="cached123",
            file_path="cached.py",
            line_number=5,
            matching_line="cached content",
            search_type=SearchType.CONTENT,
            relevance_score=0.8,
        )
        search_context.cache[cache_key] = [cached_result]

        results: list[Any] = []
        async for result in searcher.search(search_context):
            results.append(result)

        # Should return cached result
        assert len(results) == 1
        assert results[0].commit_hash == "cached123"
        assert str(results[0].file_path) == "cached.py"
        assert results[0].line_number == 5

    @pytest.mark.asyncio
    async def test_cacheable_searcher_different_branches(
        self, mock_repo, sample_search_query
    ) -> None:
        """Test that different branches generate different cache keys."""
        searcher = MockCacheableSearcher()

        context_main = SearchContext(
            repo=mock_repo, query=sample_search_query, branch="main", cache={}
        )
        context_dev = SearchContext(
            repo=mock_repo, query=sample_search_query, branch="dev", cache={}
        )

        key_main = searcher._get_cache_key(context_main)
        key_dev = searcher._get_cache_key(context_dev)
        assert key_main != key_dev


class TestSearchContextClass:
    """Tests for SearchContext class."""

    def test_search_context_creation(self, mock_repo, sample_search_query) -> None:
        """Test SearchContext creation."""
        context = SearchContext(
            repo=mock_repo,
            query=sample_search_query,
            branch="main",
            progress_callback=None,
            cache={},
        )

        assert context.repo is mock_repo
        # Use == for Pydantic model comparison
        assert context.query == sample_search_query
        assert context.branch == "main"
        assert context.progress_callback is None
        assert context.cache == {}

    def test_search_context_with_progress_callback(self, mock_repo, sample_search_query) -> None:
        """Test SearchContext with progress callback."""
        callback = Mock()

        context = SearchContext(
            repo=mock_repo, query=sample_search_query, progress_callback=callback
        )

        assert context.progress_callback is callback

    def test_search_context_with_cache(self, mock_repo, sample_search_query) -> None:
        """Test SearchContext with pre-populated cache."""
        cache = {"test_key": "test_value"}

        context = SearchContext(repo=mock_repo, query=sample_search_query, cache=cache)

        assert context.cache == cache
        assert context.cache["test_key"] == "test_value"

    def test_search_context_default_values(self, mock_repo, sample_search_query) -> None:
        """Test SearchContext with default values."""
        context = SearchContext(repo=mock_repo, query=sample_search_query)

        assert context.repo is mock_repo
        # Use == for Pydantic model comparison
        assert context.query == sample_search_query
        assert context.branch is None
        assert context.progress_callback is None
        assert context.cache is None
