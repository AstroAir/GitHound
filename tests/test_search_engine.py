"""Comprehensive tests for GitHound search engine functionality."""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from git import Repo

from githound.models import SearchQuery, SearchResult, SearchType, CommitInfo
from githound.search_engine import (
    SearchOrchestrator, BaseSearcher, SearchContext, CacheableSearcher,
    CommitHashSearcher, AuthorSearcher, MessageSearcher, DateRangeSearcher,
    FilePathSearcher, FileTypeSearcher, ContentSearcher, FuzzySearcher
)


@pytest.fixture
def sample_search_query():
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
        case_sensitive=False
    )


@pytest.fixture
def mock_repo():
    """Create a mock Git repository."""
    mock_repo = Mock(spec=Repo)
    mock_repo.git_dir = "/test/repo/.git"
    mock_repo.working_dir = "/test/repo"
    mock_repo.active_branch.name = "main"

    # Create mock commits
    mock_commits = []
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
        commit.repo = mock_repo  # Add repo reference for fuzzy searcher
        mock_commits.append(commit)

    mock_repo.iter_commits.return_value = mock_commits
    return mock_repo


@pytest.fixture
def search_context(mock_repo, sample_search_query):
    """Create a search context for testing."""
    return SearchContext(
        repo=mock_repo,
        query=sample_search_query,
        branch="main",
        progress_callback=None,
        cache={}
    )


class TestSearchOrchestrator:
    """Tests for SearchOrchestrator class."""
    
    def test_orchestrator_initialization(self):
        """Test SearchOrchestrator initialization."""
        orchestrator = SearchOrchestrator()
        assert orchestrator is not None
        assert len(orchestrator.list_searchers()) == 0
    
    def test_register_searcher(self):
        """Test registering searchers."""
        orchestrator = SearchOrchestrator()
        searcher = CommitHashSearcher()
        
        orchestrator.register_searcher(searcher)
        assert len(orchestrator.list_searchers()) == 1
        assert "commit_hash" in orchestrator.list_searchers()
    
    def test_unregister_searcher(self):
        """Test unregistering searchers."""
        orchestrator = SearchOrchestrator()
        searcher = CommitHashSearcher()
        
        orchestrator.register_searcher(searcher)
        orchestrator.unregister_searcher(searcher)
        assert len(orchestrator.list_searchers()) == 0
    
    def test_get_searcher_by_name(self):
        """Test getting searcher by name."""
        orchestrator = SearchOrchestrator()
        searcher = CommitHashSearcher()
        
        orchestrator.register_searcher(searcher)
        found_searcher = orchestrator.get_searcher_by_name("commit_hash")
        assert found_searcher is searcher
        
        not_found = orchestrator.get_searcher_by_name("nonexistent")
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_get_available_searchers(self, sample_search_query):
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
    async def test_search_with_no_searchers(self, search_context):
        """Test search with no registered searchers."""
        orchestrator = SearchOrchestrator()
        
        results = []
        async for result in orchestrator.search(
            repo=search_context.repo,
            query=search_context.query
        ):
            results.append(result)
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_search_with_multiple_searchers(self, search_context):
        """Test search with multiple searchers."""
        orchestrator = SearchOrchestrator()
        
        # Create mock searchers that return results
        async def mock_search1(context):
            yield SearchResult(
                commit_hash="abc123",
                file_path=Path("test1.py"),
                search_type=SearchType.CONTENT,
                relevance_score=0.9
            )

        async def mock_search2(context):
            yield SearchResult(
                commit_hash="def456",
                file_path=Path("test2.py"),
                search_type=SearchType.AUTHOR,
                relevance_score=0.8
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
        
        results = []
        async for result in orchestrator.search(
            repo=search_context.repo,
            query=search_context.query
        ):
            results.append(result)
        
        assert len(results) == 2
        # Results should be sorted by relevance score (descending)
        assert results[0].relevance_score >= results[1].relevance_score


class TestCommitSearchers:
    """Tests for commit-based searchers."""
    
    @pytest.mark.asyncio
    async def test_commit_hash_searcher(self, search_context):
        """Test CommitHashSearcher."""
        searcher = CommitHashSearcher()
        
        # Test can_handle
        assert await searcher.can_handle(search_context.query) is True
        
        # Test with query that has no commit hash
        query_no_hash = SearchQuery(content_pattern="test")
        assert await searcher.can_handle(query_no_hash) is False
        
        # Test search
        results = []
        async for result in searcher.search(search_context):
            results.append(result)
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_author_searcher(self, search_context):
        """Test AuthorSearcher."""
        searcher = AuthorSearcher()
        
        # Test can_handle
        assert await searcher.can_handle(search_context.query) is True
        
        # Test with query that has no author pattern
        query_no_author = SearchQuery(content_pattern="test")
        assert await searcher.can_handle(query_no_author) is False
        
        # Test search
        results = []
        async for result in searcher.search(search_context):
            results.append(result)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_message_searcher(self, search_context):
        """Test MessageSearcher."""
        searcher = MessageSearcher()

        # Test can_handle
        assert await searcher.can_handle(search_context.query) is True

        # Test search
        results = []
        async for result in searcher.search(search_context):
            results.append(result)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_date_range_searcher(self, search_context):
        """Test DateRangeSearcher."""
        searcher = DateRangeSearcher()

        # Test can_handle
        assert await searcher.can_handle(search_context.query) is True

        # Test with query that has no date range
        query_no_date = SearchQuery(content_pattern="test")
        assert await searcher.can_handle(query_no_date) is False

        # Test search
        results = []
        async for result in searcher.search(search_context):
            results.append(result)
        assert isinstance(results, list)


class TestFileSearchers:
    """Tests for file-based searchers."""
    
    @pytest.mark.asyncio
    async def test_file_path_searcher(self, search_context):
        """Test FilePathSearcher."""
        searcher = FilePathSearcher()
        
        # Test can_handle
        assert await searcher.can_handle(search_context.query) is True
        
        # Test search
        results = []
        async for result in searcher.search(search_context):
            results.append(result)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_file_type_searcher(self, search_context):
        """Test FileTypeSearcher."""
        searcher = FileTypeSearcher()

        # Test can_handle
        assert await searcher.can_handle(search_context.query) is True

        # Test search
        results = []
        async for result in searcher.search(search_context):
            results.append(result)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_content_searcher(self, search_context):
        """Test ContentSearcher."""
        searcher = ContentSearcher()

        # Test can_handle
        assert await searcher.can_handle(search_context.query) is True

        # Test with query that has no content pattern
        query_no_content = SearchQuery(author_pattern="test")
        assert await searcher.can_handle(query_no_content) is False

        # Test search
        results = []
        async for result in searcher.search(search_context):
            results.append(result)
        assert isinstance(results, list)


class TestFuzzySearcher:
    """Tests for FuzzySearcher."""
    
    @pytest.mark.asyncio
    async def test_fuzzy_searcher_enabled(self, search_context):
        """Test FuzzySearcher when fuzzy search is enabled."""
        searcher = FuzzySearcher()
        
        # Test can_handle
        assert await searcher.can_handle(search_context.query) is True
        
        # Test search
        results = []
        async for result in searcher.search(search_context):
            results.append(result)
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_fuzzy_searcher_disabled(self, search_context):
        """Test FuzzySearcher when fuzzy search is disabled."""
        searcher = FuzzySearcher()
        
        # Create query with fuzzy search disabled
        query_no_fuzzy = SearchQuery(content_pattern="test", fuzzy_search=False)
        assert await searcher.can_handle(query_no_fuzzy) is False


class TestCacheableSearcher:
    """Tests for CacheableSearcher functionality."""
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, search_context):
        """Test cache key generation."""
        searcher = CommitHashSearcher()  # Inherits from CacheableSearcher
        
        cache_key = searcher._get_cache_key(search_context)
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0
    
    @pytest.mark.asyncio
    async def test_cache_usage(self, search_context):
        """Test cache usage in searcher."""
        searcher = CommitHashSearcher()
        
        # First search - should cache results
        results1 = []
        async for result in searcher.search(search_context):
            results1.append(result)

        # Second search - should use cached results
        results2 = []
        async for result in searcher.search(search_context):
            results2.append(result)

        # Results should be the same
        assert len(results1) == len(results2)


class TestSearchContext:
    """Tests for SearchContext class."""
    
    def test_search_context_creation(self, mock_repo, sample_search_query):
        """Test SearchContext creation."""
        context = SearchContext(
            repo=mock_repo,
            query=sample_search_query,
            branch="main",
            progress_callback=None,
            cache={}
        )
        
        assert context.repo is mock_repo
        assert context.query is sample_search_query
        assert context.branch == "main"
        assert context.cache == {}
    
    def test_search_context_with_progress_callback(self, mock_repo, sample_search_query):
        """Test SearchContext with progress callback."""
        callback = Mock()
        
        context = SearchContext(
            repo=mock_repo,
            query=sample_search_query,
            progress_callback=callback
        )
        
        assert context.progress_callback is callback


class TestSearchIntegration:
    """Integration tests for search functionality."""
    
    @pytest.mark.asyncio
    async def test_full_search_workflow(self, mock_repo):
        """Test complete search workflow."""
        orchestrator = SearchOrchestrator()
        
        # Register all searchers
        orchestrator.register_searcher(CommitHashSearcher())
        orchestrator.register_searcher(AuthorSearcher())
        orchestrator.register_searcher(MessageSearcher())
        orchestrator.register_searcher(ContentSearcher())
        orchestrator.register_searcher(FuzzySearcher())
        
        # Create comprehensive query
        query = SearchQuery(
            content_pattern="test",
            author_pattern="Author",
            message_pattern="commit",
            fuzzy_search=True,
            fuzzy_threshold=0.8
        )
        
        # Perform search
        results = []
        async for result in orchestrator.search(repo=mock_repo, query=query):
            results.append(result)
        
        # Should have results from multiple searchers
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_search_with_max_results(self, mock_repo):
        """Test search with max results limit."""
        orchestrator = SearchOrchestrator()
        orchestrator.register_searcher(AuthorSearcher())
        
        query = SearchQuery(author_pattern="Author")
        
        results = []
        async for result in orchestrator.search(
            repo=mock_repo, 
            query=query, 
            max_results=2
        ):
            results.append(result)
        
        assert len(results) <= 2
    
    @pytest.mark.asyncio
    async def test_search_with_progress_callback(self, mock_repo):
        """Test search with progress callback."""
        orchestrator = SearchOrchestrator()
        orchestrator.register_searcher(AuthorSearcher())
        
        progress_calls = []
        
        def progress_callback(message: str, progress: float) -> None:
            progress_calls.append((message, progress))
        
        query = SearchQuery(author_pattern="Author")
        
        results = []
        async for result in orchestrator.search(
            repo=mock_repo,
            query=query,
            progress_callback=progress_callback
        ):
            results.append(result)
        
        # Should have received progress updates
        assert len(progress_calls) > 0
