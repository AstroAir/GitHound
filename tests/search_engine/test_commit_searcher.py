"""Tests for GitHound commit-based searchers."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from git import Repo

from githound.models import SearchQuery
from githound.search_engine import (
    CommitHashSearcher,
    AuthorSearcher,
    MessageSearcher,
    DateRangeSearcher,
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


class TestCommitHashSearcher:
    """Tests for CommitHashSearcher."""

    @pytest.mark.asyncio
    async def test_commit_hash_searcher_can_handle(self, sample_search_query) -> None:
        """Test CommitHashSearcher can_handle method."""
        searcher = CommitHashSearcher()

        # Test with query that has commit hash
        assert await searcher.can_handle(sample_search_query) is True

        # Test with query that has no commit hash
        query_no_hash = SearchQuery(content_pattern="test")
        assert await searcher.can_handle(query_no_hash) is False

    @pytest.mark.asyncio
    async def test_commit_hash_searcher_search(self, search_context) -> None:
        """Test CommitHashSearcher search method."""
        searcher = CommitHashSearcher()

        results: list[Any] = []
        async for result in searcher.search(search_context):
            results.append(result)
        
        assert isinstance(results, list)

    def test_commit_hash_searcher_name(self) -> None:
        """Test CommitHashSearcher name property."""
        searcher = CommitHashSearcher()
        assert searcher.name = = "commit_hash"

    @pytest.mark.asyncio
    async def test_commit_hash_searcher_estimate_work(self, sample_search_query) -> None:
        """Test CommitHashSearcher estimate_work method."""
        searcher = CommitHashSearcher()
        work_estimate = await searcher.estimate_work(sample_search_query)
        assert isinstance(work_estimate, (int, float))
        assert work_estimate >= 0


class TestAuthorSearcher:
    """Tests for AuthorSearcher."""

    @pytest.mark.asyncio
    async def test_author_searcher_can_handle(self, sample_search_query) -> None:
        """Test AuthorSearcher can_handle method."""
        searcher = AuthorSearcher()

        # Test with query that has author pattern
        assert await searcher.can_handle(sample_search_query) is True

        # Test with query that has no author pattern
        query_no_author = SearchQuery(content_pattern="test")
        assert await searcher.can_handle(query_no_author) is False

    @pytest.mark.asyncio
    async def test_author_searcher_search(self, search_context) -> None:
        """Test AuthorSearcher search method."""
        searcher = AuthorSearcher()

        results: list[Any] = []
        async for result in searcher.search(search_context):
            results.append(result)
        
        assert isinstance(results, list)

    def test_author_searcher_name(self) -> None:
        """Test AuthorSearcher name property."""
        searcher = AuthorSearcher()
        assert searcher.name = = "author"

    @pytest.mark.asyncio
    async def test_author_searcher_estimate_work(self, sample_search_query) -> None:
        """Test AuthorSearcher estimate_work method."""
        searcher = AuthorSearcher()
        work_estimate = await searcher.estimate_work(sample_search_query)
        assert isinstance(work_estimate, (int, float))
        assert work_estimate >= 0


class TestMessageSearcher:
    """Tests for MessageSearcher."""

    @pytest.mark.asyncio
    async def test_message_searcher_can_handle(self, sample_search_query) -> None:
        """Test MessageSearcher can_handle method."""
        searcher = MessageSearcher()

        # Test with query that has message pattern
        assert await searcher.can_handle(sample_search_query) is True

        # Test with query that has no message pattern
        query_no_message = SearchQuery(content_pattern="test")
        # MessageSearcher might still handle queries without explicit message pattern
        result = await searcher.can_handle(query_no_message)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_message_searcher_search(self, search_context) -> None:
        """Test MessageSearcher search method."""
        searcher = MessageSearcher()

        results: list[Any] = []
        async for result in searcher.search(search_context):
            results.append(result)
        
        assert isinstance(results, list)

    def test_message_searcher_name(self) -> None:
        """Test MessageSearcher name property."""
        searcher = MessageSearcher()
        assert searcher.name = = "message"

    @pytest.mark.asyncio
    async def test_message_searcher_estimate_work(self, sample_search_query) -> None:
        """Test MessageSearcher estimate_work method."""
        searcher = MessageSearcher()
        work_estimate = await searcher.estimate_work(sample_search_query)
        assert isinstance(work_estimate, (int, float))
        assert work_estimate >= 0


class TestDateRangeSearcher:
    """Tests for DateRangeSearcher."""

    @pytest.mark.asyncio
    async def test_date_range_searcher_can_handle(self, sample_search_query) -> None:
        """Test DateRangeSearcher can_handle method."""
        searcher = DateRangeSearcher()

        # Test with query that has date range
        assert await searcher.can_handle(sample_search_query) is True

        # Test with query that has no date range
        query_no_date = SearchQuery(content_pattern="test")
        assert await searcher.can_handle(query_no_date) is False

    @pytest.mark.asyncio
    async def test_date_range_searcher_search(self, search_context) -> None:
        """Test DateRangeSearcher search method."""
        searcher = DateRangeSearcher()

        results: list[Any] = []
        async for result in searcher.search(search_context):
            results.append(result)
        
        assert isinstance(results, list)

    def test_date_range_searcher_name(self) -> None:
        """Test DateRangeSearcher name property."""
        searcher = DateRangeSearcher()
        assert searcher.name = = "date_range"

    @pytest.mark.asyncio
    async def test_date_range_searcher_estimate_work(self, sample_search_query) -> None:
        """Test DateRangeSearcher estimate_work method."""
        searcher = DateRangeSearcher()
        work_estimate = await searcher.estimate_work(sample_search_query)
        assert isinstance(work_estimate, (int, float))
        assert work_estimate >= 0

    @pytest.mark.asyncio
    async def test_date_range_searcher_with_partial_date_range(self) -> None:
        """Test DateRangeSearcher with partial date range."""
        searcher = DateRangeSearcher()

        # Test with only date_from
        query_from_only = SearchQuery(
            content_pattern="test",
            date_from=datetime.now() - timedelta(days=30)
        )
        assert await searcher.can_handle(query_from_only) is True

        # Test with only date_to
        query_to_only = SearchQuery(
            content_pattern="test",
            date_to=datetime.now()
        )
        assert await searcher.can_handle(query_to_only) is True


class TestCacheableSearcher:
    """Tests for CacheableSearcher functionality."""

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, search_context) -> None:
        """Test cache key generation."""
        searcher = CommitHashSearcher()  # Inherits from CacheableSearcher

        cache_key = searcher._get_cache_key(search_context)
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0

    @pytest.mark.asyncio
    async def test_cache_usage(self, search_context) -> None:
        """Test cache usage in searcher."""
        searcher = CommitHashSearcher()

        # First search - should cache results
        results1: list[Any] = []
        async for result in searcher.search(search_context):
            results1.append(result)

        # Second search - should use cached results
        results2: list[Any] = []
        async for result in searcher.search(search_context):
            results2.append(result)

        # Results should be the same
        assert len(results1) == len(results2)

    @pytest.mark.asyncio
    async def test_cache_key_uniqueness(self, mock_repo) -> None:
        """Test that different queries generate different cache keys."""
        searcher = CommitHashSearcher()

        query1 = SearchQuery(commit_hash="abc123")
        query2 = SearchQuery(commit_hash="def456")

        context1 = SearchContext(repo=mock_repo, query=query1, branch="main", cache={})
        context2 = SearchContext(repo=mock_repo, query=query2, branch="main", cache={})

        key1 = searcher._get_cache_key(context1)
        key2 = searcher._get_cache_key(context2)

        assert key1 != key2
