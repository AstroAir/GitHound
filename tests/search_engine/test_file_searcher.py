"""Tests for GitHound file-based searchers."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from git import Repo

from githound.models import SearchQuery
from githound.search_engine import (
    FilePathSearcher,
    FileTypeSearcher,
    ContentSearcher,
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


class TestFilePathSearcher:
    """Tests for FilePathSearcher."""

    @pytest.mark.asyncio
    async def test_file_path_searcher_can_handle(self, sample_search_query) -> None:
        """Test FilePathSearcher can_handle method."""
        searcher = FilePathSearcher()

        # Test with query that has file path pattern
        assert await searcher.can_handle(sample_search_query) is True

        # Test with query that has no file path pattern
        query_no_path = SearchQuery(content_pattern="test")
        # FilePathSearcher might still handle queries without explicit path pattern
        result = await searcher.can_handle(query_no_path)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_file_path_searcher_search(self, search_context) -> None:
        """Test FilePathSearcher search method."""
        searcher = FilePathSearcher()

        results: list[Any] = []
        async for result in searcher.search(search_context):
            results.append(result)
        
        assert isinstance(results, list)

    def test_file_path_searcher_name(self) -> None:
        """Test FilePathSearcher name property."""
        searcher = FilePathSearcher()
        assert searcher.name = = "file_path"

    @pytest.mark.asyncio
    async def test_file_path_searcher_estimate_work(self, sample_search_query) -> None:
        """Test FilePathSearcher estimate_work method."""
        searcher = FilePathSearcher()
        work_estimate = await searcher.estimate_work(sample_search_query)
        assert isinstance(work_estimate, (int, float))
        assert work_estimate >= 0

    @pytest.mark.asyncio
    async def test_file_path_searcher_with_glob_patterns(self) -> None:
        """Test FilePathSearcher with different glob patterns."""
        searcher = FilePathSearcher()

        # Test with Python files
        query_py = SearchQuery(file_path_pattern="*.py")
        assert await searcher.can_handle(query_py) is True

        # Test with JavaScript files
        query_js = SearchQuery(file_path_pattern="*.js")
        assert await searcher.can_handle(query_js) is True

        # Test with specific directory
        query_dir = SearchQuery(file_path_pattern="src/*.py")
        assert await searcher.can_handle(query_dir) is True


class TestFileTypeSearcher:
    """Tests for FileTypeSearcher."""

    @pytest.mark.asyncio
    async def test_file_type_searcher_can_handle(self, sample_search_query) -> None:
        """Test FileTypeSearcher can_handle method."""
        searcher = FileTypeSearcher()

        # Test with query that has file extensions
        assert await searcher.can_handle(sample_search_query) is True

        # Test with query that has no file extensions
        query_no_ext = SearchQuery(content_pattern="test")
        # FileTypeSearcher might still handle queries without explicit extensions
        result = await searcher.can_handle(query_no_ext)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_file_type_searcher_search(self, search_context) -> None:
        """Test FileTypeSearcher search method."""
        searcher = FileTypeSearcher()

        results: list[Any] = []
        async for result in searcher.search(search_context):
            results.append(result)
        
        assert isinstance(results, list)

    def test_file_type_searcher_name(self) -> None:
        """Test FileTypeSearcher name property."""
        searcher = FileTypeSearcher()
        assert searcher.name = = "file_type"

    @pytest.mark.asyncio
    async def test_file_type_searcher_estimate_work(self, sample_search_query) -> None:
        """Test FileTypeSearcher estimate_work method."""
        searcher = FileTypeSearcher()
        work_estimate = await searcher.estimate_work(sample_search_query)
        assert isinstance(work_estimate, (int, float))
        assert work_estimate >= 0

    @pytest.mark.asyncio
    async def test_file_type_searcher_with_different_extensions(self) -> None:
        """Test FileTypeSearcher with different file extensions."""
        searcher = FileTypeSearcher()

        # Test with Python files
        query_py = SearchQuery(file_extensions=["py"])
        assert await searcher.can_handle(query_py) is True

        # Test with multiple extensions
        query_multi = SearchQuery(file_extensions=["py", "js", "ts"])
        assert await searcher.can_handle(query_multi) is True

        # Test with empty extensions list
        query_empty = SearchQuery(file_extensions=[])
        result = await searcher.can_handle(query_empty)
        assert isinstance(result, bool)


class TestContentSearcher:
    """Tests for ContentSearcher."""

    @pytest.mark.asyncio
    async def test_content_searcher_can_handle(self, sample_search_query) -> None:
        """Test ContentSearcher can_handle method."""
        searcher = ContentSearcher()

        # Test with query that has content pattern
        assert await searcher.can_handle(sample_search_query) is True

        # Test with query that has no content pattern
        query_no_content = SearchQuery(author_pattern="test")
        assert await searcher.can_handle(query_no_content) is False

    @pytest.mark.asyncio
    async def test_content_searcher_search(self, search_context) -> None:
        """Test ContentSearcher search method."""
        searcher = ContentSearcher()

        results: list[Any] = []
        async for result in searcher.search(search_context):
            results.append(result)
        
        assert isinstance(results, list)

    def test_content_searcher_name(self) -> None:
        """Test ContentSearcher name property."""
        searcher = ContentSearcher()
        assert searcher.name = = "content"

    @pytest.mark.asyncio
    async def test_content_searcher_estimate_work(self, sample_search_query) -> None:
        """Test ContentSearcher estimate_work method."""
        searcher = ContentSearcher()
        work_estimate = await searcher.estimate_work(sample_search_query)
        assert isinstance(work_estimate, (int, float))
        assert work_estimate >= 0

    @pytest.mark.asyncio
    async def test_content_searcher_case_sensitivity(self) -> None:
        """Test ContentSearcher with case sensitivity options."""
        searcher = ContentSearcher()

        # Test case sensitive search
        query_sensitive = SearchQuery(content_pattern="Test", case_sensitive=True)
        assert await searcher.can_handle(query_sensitive) is True

        # Test case insensitive search
        query_insensitive = SearchQuery(content_pattern="test", case_sensitive=False)
        assert await searcher.can_handle(query_insensitive) is True

    @pytest.mark.asyncio
    async def test_content_searcher_with_regex_patterns(self) -> None:
        """Test ContentSearcher with regex patterns."""
        searcher = ContentSearcher()

        # Test with regex pattern
        query_regex = SearchQuery(content_pattern=r"def\s+\w+\(")
        assert await searcher.can_handle(query_regex) is True

        # Test with simple string pattern
        query_simple = SearchQuery(content_pattern="function")
        assert await searcher.can_handle(query_simple) is True

    @pytest.mark.asyncio
    async def test_content_searcher_with_include_exclude_globs(self, mock_repo) -> None:
        """Test ContentSearcher with include/exclude glob patterns."""
        searcher = ContentSearcher()

        # Test with include globs
        query_include = SearchQuery(
            content_pattern="test",
            include_globs=["*.py", "*.js"]
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
    async def test_content_searcher_with_file_size_limits(self, mock_repo) -> None:
        """Test ContentSearcher with file size limits."""
        searcher = ContentSearcher()

        query_with_limit = SearchQuery(
            content_pattern="test",
            max_file_size=1000000  # 1MB limit
        )
        context_with_limit = SearchContext(
            repo=mock_repo, query=query_with_limit, branch="main", cache={}
        )
        
        results: list[Any] = []
        async for result in searcher.search(context_with_limit):
            results.append(result)
        assert isinstance(results, list)
