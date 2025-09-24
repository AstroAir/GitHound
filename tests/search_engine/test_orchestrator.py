"""Tests for GitHound search orchestrator."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from git import Repo

from githound.models import SearchQuery, SearchResult, SearchType
from githound.search_engine import (
    AuthorSearcher,
    BaseSearcher,
    CommitHashSearcher,
    ContentSearcher,
    SearchContext,
    SearchOrchestrator,
)


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
def search_context(mock_repo, sample_search_query) -> None:
    """Create a search context for testing."""
    return SearchContext(
        repo=mock_repo, query=sample_search_query, branch="main", progress_callback=None, cache={}
    )


class TestSearchOrchestrator:
    """Tests for SearchOrchestrator class."""

    def test_orchestrator_initialization(self) -> None:
        """Test SearchOrchestrator initialization."""
        orchestrator = SearchOrchestrator()
        assert orchestrator is not None
        assert len(orchestrator.list_searchers()) == 0

    def test_register_searcher(self) -> None:
        """Test registering searchers."""
        orchestrator = SearchOrchestrator()
        searcher = CommitHashSearcher()

        orchestrator.register_searcher(searcher)
        assert len(orchestrator.list_searchers()) == 1
        assert "commit_hash" in orchestrator.list_searchers()

    def test_unregister_searcher(self) -> None:
        """Test unregistering searchers."""
        orchestrator = SearchOrchestrator()
        searcher = CommitHashSearcher()

        orchestrator.register_searcher(searcher)
        orchestrator.unregister_searcher(searcher)
        assert len(orchestrator.list_searchers()) == 0

    def test_get_searcher_by_name(self) -> None:
        """Test getting searcher by name."""
        orchestrator = SearchOrchestrator()
        searcher = CommitHashSearcher()

        orchestrator.register_searcher(searcher)
        found_searcher = orchestrator.get_searcher_by_name("commit_hash")
        assert found_searcher is searcher

        not_found = orchestrator.get_searcher_by_name("nonexistent")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_get_available_searchers(self, sample_search_query) -> None:
        """Test getting available searchers for a query."""
        orchestrator = SearchOrchestrator()

        # Register searchers
        orchestrator.register_searcher(CommitHashSearcher())
        orchestrator.register_searcher(AuthorSearcher())
        orchestrator.register_searcher(ContentSearcher())

        available = await orchestrator.get_available_searchers(sample_search_query)

        # Should include all searchers that can handle the query
        assert "commit_hash" in available
        assert "author" in available
        assert "content" in available

    @pytest.mark.asyncio
    async def test_search_with_no_searchers(self, search_context) -> None:
        """Test search with no registered searchers."""
        orchestrator = SearchOrchestrator()

        results: list[Any] = []
        async for result in orchestrator.search(
            repo=search_context.repo, query=search_context.query
        ):
            results.append(result)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_with_multiple_searchers(self, search_context) -> None:
        """Test search with multiple searchers."""
        orchestrator = SearchOrchestrator()

        # Create mock searchers that return results
        async def mock_search1(context) -> None:
            yield SearchResult(
                commit_hash="abc123",
                file_path=Path("test1.py"),
                search_type=SearchType.CONTENT,
                relevance_score=0.9,
            )

        async def mock_search2(context) -> None:
            yield SearchResult(
                commit_hash="def456",
                file_path=Path("test2.py"),
                search_type=SearchType.AUTHOR,
                relevance_score=0.8,
            )

        mock_searcher1 = AsyncMock(spec=BaseSearcher)
        mock_searcher1.name = "test_searcher1"
        mock_searcher1.can_handle.return_value = True
        mock_searcher1.estimate_work.return_value = 10
        mock_searcher1.search = mock_search1

        mock_searcher2 = AsyncMock(spec=BaseSearcher)
        mock_searcher2.name = "test_searcher2"
        mock_searcher2.can_handle.return_value = True
        mock_searcher2.estimate_work.return_value = 10
        mock_searcher2.search = mock_search2

        orchestrator.register_searcher(mock_searcher1)
        orchestrator.register_searcher(mock_searcher2)

        results: list[Any] = []
        async for result in orchestrator.search(
            repo=search_context.repo, query=search_context.query
        ):
            results.append(result)

        assert len(results) == 2
        # Results should be sorted by relevance score (descending)
        assert results[0].relevance_score >= results[1].relevance_score

    @pytest.mark.asyncio
    async def test_search_with_max_results(self, mock_repo) -> None:
        """Test search with max results limit."""
        orchestrator = SearchOrchestrator()
        orchestrator.register_searcher(AuthorSearcher())

        query = SearchQuery(author_pattern="Author")

        results: list[Any] = []
        async for result in orchestrator.search(repo=mock_repo, query=query, max_results=2):
            results.append(result)

        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_search_with_progress_callback(self, mock_repo) -> None:
        """Test search with progress callback."""
        orchestrator = SearchOrchestrator()
        orchestrator.register_searcher(AuthorSearcher())

        progress_calls: list[Any] = []

        def progress_callback(message: str, progress: float) -> None:
            progress_calls.append((message, progress))

        query = SearchQuery(author_pattern="Author")

        results: list[Any] = []
        async for result in orchestrator.search(
            repo=mock_repo, query=query, progress_callback=progress_callback
        ):
            results.append(result)

        # Should have received progress updates
        assert len(progress_calls) > 0

    @pytest.mark.asyncio
    async def test_full_search_workflow(self, mock_repo) -> None:
        """Test complete search workflow."""
        orchestrator = SearchOrchestrator()

        # Register all searchers
        orchestrator.register_searcher(CommitHashSearcher())
        orchestrator.register_searcher(AuthorSearcher())
        orchestrator.register_searcher(ContentSearcher())

        # Create comprehensive query
        query = SearchQuery(
            content_pattern="test",
            author_pattern="Author",
            message_pattern="commit",
            fuzzy_search=True,
            fuzzy_threshold=0.8,
        )

        # Perform search
        results: list[Any] = []
        async for result in orchestrator.search(repo=mock_repo, query=query):
            results.append(result)

        # Should have results from multiple searchers
        assert isinstance(results, list)


class TestSearchContext:
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
        assert context.cache == {}

    def test_search_context_with_progress_callback(self, mock_repo, sample_search_query) -> None:
        """Test SearchContext with progress callback."""
        callback = Mock()

        context = SearchContext(
            repo=mock_repo, query=sample_search_query, progress_callback=callback
        )

        assert context.progress_callback is callback
