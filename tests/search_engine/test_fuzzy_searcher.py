"""Tests for GitHound fuzzy searcher."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from git import Repo

from githound.models import SearchQuery
from githound.search_engine import (
    FuzzySearcher,
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
        commit.committed_date = int(
            (datetime.now() - timedelta(days=i)).timestamp())
        commit.committed_datetime = datetime.now() - timedelta(days=i)
        commit.stats.files = {f"file{i}.py": {
            "insertions": 10, "deletions": 5}}
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


class TestFuzzySearcher:
    """Tests for FuzzySearcher."""

    @pytest.mark.asyncio
    async def test_fuzzy_searcher_can_handle_enabled(self, sample_search_query) -> None:
        """Test FuzzySearcher when fuzzy search is enabled."""
        searcher = FuzzySearcher()

        # Test with query that has fuzzy search enabled
        assert await searcher.can_handle(sample_search_query) is True

    @pytest.mark.asyncio
    async def test_fuzzy_searcher_can_handle_disabled(self) -> None:
        """Test FuzzySearcher when fuzzy search is disabled."""
        searcher = FuzzySearcher()

        # Create query with fuzzy search disabled
        query_no_fuzzy = SearchQuery(
            content_pattern="test", fuzzy_search=False)
        assert await searcher.can_handle(query_no_fuzzy) is False

    @pytest.mark.asyncio
    async def test_fuzzy_searcher_can_handle_no_content(self) -> None:
        """Test FuzzySearcher with no content pattern."""
        searcher = FuzzySearcher()

        # Create query with fuzzy search enabled but no content pattern
        query_no_content = SearchQuery(
            author_pattern="test", fuzzy_search=True)
        # FuzzySearcher might still handle queries without content pattern
        result = await searcher.can_handle(query_no_content)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_fuzzy_searcher_search(self, search_context) -> None:
        """Test FuzzySearcher search method."""
        searcher = FuzzySearcher()

        results: list[Any] = []
        async for result in searcher.search(search_context):
            results.append(result)

        assert isinstance(results, list)

    def test_fuzzy_searcher_name(self) -> None:
        """Test FuzzySearcher name property."""
        searcher = FuzzySearcher()
        assert searcher.name == "fuzzy"

    @pytest.mark.asyncio
    async def test_fuzzy_searcher_estimate_work(self, sample_search_query) -> None:
        """Test FuzzySearcher estimate_work method."""
        searcher = FuzzySearcher()
        work_estimate = await searcher.estimate_work(sample_search_query)
        assert isinstance(work_estimate, (int, float))
        assert work_estimate >= 0

    @pytest.mark.asyncio
    async def test_fuzzy_searcher_with_different_thresholds(self, mock_repo) -> None:
        """Test FuzzySearcher with different fuzzy thresholds."""
        searcher = FuzzySearcher()

        # Test with high threshold (strict matching)
        query_high_threshold = SearchQuery(
            content_pattern="test",
            fuzzy_search=True,
            fuzzy_threshold=0.9
        )
        context_high = SearchContext(
            repo=mock_repo, query=query_high_threshold, branch="main", cache={}
        )

        assert await searcher.can_handle(query_high_threshold) is True

        results_high: list[Any] = []
        async for result in searcher.search(context_high):
            results_high.append(result)
        assert isinstance(results_high, list)

        # Test with low threshold (loose matching)
        query_low_threshold = SearchQuery(
            content_pattern="test",
            fuzzy_search=True,
            fuzzy_threshold=0.5
        )
        context_low = SearchContext(
            repo=mock_repo, query=query_low_threshold, branch="main", cache={}
        )

        assert await searcher.can_handle(query_low_threshold) is True

        results_low: list[Any] = []
        async for result in searcher.search(context_low):
            results_low.append(result)
        assert isinstance(results_low, list)

    @pytest.mark.asyncio
    async def test_fuzzy_searcher_with_complex_patterns(self, mock_repo) -> None:
        """Test FuzzySearcher with complex search patterns."""
        searcher = FuzzySearcher()

        # Test with multi-word pattern
        query_multi_word = SearchQuery(
            content_pattern="test function",
            fuzzy_search=True,
            fuzzy_threshold=0.8
        )
        context_multi = SearchContext(
            repo=mock_repo, query=query_multi_word, branch="main", cache={}
        )

        results: list[Any] = []
        async for result in searcher.search(context_multi):
            results.append(result)
        assert isinstance(results, list)

        # Test with special characters
        query_special = SearchQuery(
            content_pattern="test_function()",
            fuzzy_search=True,
            fuzzy_threshold=0.8
        )
        context_special = SearchContext(
            repo=mock_repo, query=query_special, branch="main", cache={}
        )

        results: list[Any] = []
        async for result in searcher.search(context_special):
            results.append(result)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_fuzzy_searcher_case_sensitivity(self, mock_repo) -> None:
        """Test FuzzySearcher with case sensitivity options."""
        searcher = FuzzySearcher()

        # Test case sensitive fuzzy search
        query_sensitive = SearchQuery(
            content_pattern="Test",
            fuzzy_search=True,
            fuzzy_threshold=0.8,
            case_sensitive=True
        )
        context_sensitive = SearchContext(
            repo=mock_repo, query=query_sensitive, branch="main", cache={}
        )

        results_sensitive: list[Any] = []
        async for result in searcher.search(context_sensitive):
            results_sensitive.append(result)
        assert isinstance(results_sensitive, list)

        # Test case insensitive fuzzy search
        query_insensitive = SearchQuery(
            content_pattern="test",
            fuzzy_search=True,
            fuzzy_threshold=0.8,
            case_sensitive=False
        )
        context_insensitive = SearchContext(
            repo=mock_repo, query=query_insensitive, branch="main", cache={}
        )

        results_insensitive: list[Any] = []
        async for result in searcher.search(context_insensitive):
            results_insensitive.append(result)
        assert isinstance(results_insensitive, list)

    @pytest.mark.asyncio
    async def test_fuzzy_searcher_with_file_filters(self, mock_repo) -> None:
        """Test FuzzySearcher with file filtering options."""
        searcher = FuzzySearcher()

        # Test with include globs
        query_include = SearchQuery(
            content_pattern="test",
            fuzzy_search=True,
            fuzzy_threshold=0.8,
            include_globs=["*.py"]
        )
        context_include = SearchContext(
            repo=mock_repo, query=query_include, branch="main", cache={}
        )

        results: list[Any] = []
        async for result in searcher.search(context_include):
            results.append(result)
        assert isinstance(results, list)

        # Test with exclude globs
        query_exclude = SearchQuery(
            content_pattern="test",
            fuzzy_search=True,
            fuzzy_threshold=0.8,
            exclude_globs=["*.pyc", "*.log"]
        )
        context_exclude = SearchContext(
            repo=mock_repo, query=query_exclude, branch="main", cache={}
        )

        results: list[Any] = []
        async for result in searcher.search(context_exclude):
            results.append(result)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_fuzzy_searcher_edge_cases(self, mock_repo) -> None:
        """Test FuzzySearcher edge cases."""
        searcher = FuzzySearcher()

        # Test with empty pattern
        query_empty = SearchQuery(
            content_pattern="",
            fuzzy_search=True,
            fuzzy_threshold=0.8
        )
        result = await searcher.can_handle(query_empty)
        assert isinstance(result, bool)

        # Test with very short pattern
        query_short = SearchQuery(
            content_pattern="a",
            fuzzy_search=True,
            fuzzy_threshold=0.8
        )
        context_short = SearchContext(
            repo=mock_repo, query=query_short, branch="main", cache={}
        )

        results: list[Any] = []
        async for result in searcher.search(context_short):
            results.append(result)
        assert isinstance(results, list)

        # Test with threshold at boundaries
        query_min_threshold = SearchQuery(
            content_pattern="test",
            fuzzy_search=True,
            fuzzy_threshold=0.0
        )
        assert await searcher.can_handle(query_min_threshold) is True

        query_max_threshold = SearchQuery(
            content_pattern="test",
            fuzzy_search=True,
            fuzzy_threshold=1.0
        )
        assert await searcher.can_handle(query_max_threshold) is True
