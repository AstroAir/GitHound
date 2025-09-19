"""Tests for GitHound web models."""

import pytest
from datetime import datetime
from pathlib import Path

from githound.web.models import (
    SearchRequest,
    SearchResultResponse,
    SearchResponse,
    SearchStatusResponse,
    ExportRequest,
    HealthResponse,
)
from githound.models import (
    SearchQuery,
    SearchResult,
    SearchMetrics,
    SearchType,
    OutputFormat,
    CommitInfo,
)


class TestSearchRequest:
    """Test SearchRequest model."""

    def test_search_request_creation(self) -> None:
        """Test creating a SearchRequest."""
        request = SearchRequest(
            repo_path="/test/repo",
            branch="main",
            content_pattern="test",
            author_pattern="john",
            case_sensitive=True,
            fuzzy_search=False,
            max_results=50
        )

        assert request.repo_path == "/test/repo"
        assert request.branch == "main"
        assert request.content_pattern == "test"
        assert request.author_pattern == "john"
        assert request.case_sensitive is True
        assert request.fuzzy_search is False
        assert request.max_results == 50

    def test_search_request_defaults(self) -> None:
        """Test SearchRequest default values."""
        request = SearchRequest(repo_path="/test/repo")

        assert request.repo_path == "/test/repo"
        assert request.branch is None
        assert request.content_pattern is None
        assert request.commit_hash is None
        assert request.author_pattern is None
        assert request.message_pattern is None
        assert request.case_sensitive is False
        assert request.fuzzy_search is False
        assert request.fuzzy_threshold == 0.8
        assert request.max_results is None  # Fixed: default is None, not 1000
        assert request.include_globs is None  # Fixed: default is None, not []
        assert request.exclude_globs is None  # Fixed: default is None, not []

    def test_search_request_date_range(self) -> None:
        """Test SearchRequest with date range."""
        date_from = datetime(2023, 1, 1)
        date_to = datetime(2023, 12, 31)

        request = SearchRequest(
            repo_path="/test/repo",
            date_from=date_from,
            date_to=date_to
        )

        assert request.date_from == date_from
        assert request.date_to == date_to

    def test_search_request_to_search_query(self) -> None:
        """Test converting SearchRequest to SearchQuery."""
        request = SearchRequest(
            repo_path="/test/repo",
            content_pattern="test",
            author_pattern="john",
            case_sensitive=True,
            fuzzy_search=True,
            fuzzy_threshold=0.9,
            include_globs=["*.py"],
            exclude_globs=["*.pyc"],
            max_file_size=1000000
        )

        query = request.to_search_query()

        assert isinstance(query, SearchQuery)
        assert query.content_pattern == "test"
        assert query.author_pattern == "john"
        assert query.case_sensitive is True
        assert query.fuzzy_search is True
        assert query.fuzzy_threshold == 0.9
        assert query.include_globs == ["*.py"]
        assert query.exclude_globs == ["*.pyc"]
        assert query.max_file_size == 1000000

    def test_search_request_file_extensions(self) -> None:
        """Test SearchRequest with file extensions."""
        request = SearchRequest(
            repo_path="/test/repo",
            file_extensions=["py", "js", "ts"]
        )

        assert request.file_extensions == ["py", "js", "ts"]


class TestSearchResultResponse:
    """Test SearchResultResponse model."""

    def test_search_result_response_creation(self) -> None:
        """Test creating a SearchResultResponse."""
        response = SearchResultResponse(
            commit_hash="abc123",
            file_path="test.py",
            line_number=10,
            matching_line="def test() -> None:",  # Fixed: line_content -> matching_line
            search_type="content",  # Fixed: match_type -> search_type
            relevance_score=0.95
        )

        assert response.commit_hash == "abc123"
        assert response.file_path == "test.py"
        assert response.line_number == 10
        # Fixed: line_content -> matching_line
        assert response.matching_line == "def test() -> None:"
        assert response.search_type == "content"  # Fixed: match_type -> search_type
        assert response.relevance_score == 0.95

    def test_search_result_response_from_search_result(self) -> None:
        """Test creating SearchResultResponse from SearchResult."""
        commit_info = CommitInfo(
            hash="abc123",
            short_hash="abc123",
            author_name="John Doe",
            author_email="john@example.com",
            committer_name="John Doe",  # Added required field
            committer_email="john@example.com",  # Added required field
            message="Add test function",
            date=datetime(2023, 1, 1, 12, 0, 0),
            files_changed=1  # Added required field
        )

        search_result = SearchResult(
            commit_hash="abc123",
            file_path="test.py",
            line_number=10,
            matching_line="def test() -> None:",  # Fixed: line_content -> matching_line
            search_type=SearchType.CONTENT,  # Fixed: match_type -> search_type
            relevance_score=0.95,
            commit_info=commit_info
        )

        response = SearchResultResponse.from_search_result(
            search_result, include_metadata=True)

        assert response.commit_hash == "abc123"
        assert response.file_path == "test.py"
        assert response.line_number == 10
        # Fixed: line_content -> matching_line
        assert response.matching_line == "def test() -> None:"
        assert response.search_type == "content"  # Fixed: match_type -> search_type
        assert response.relevance_score == 0.95
        # Fixed: commit_author -> author_name
        assert response.author_name == "John Doe"
        assert response.commit_message == "Add test function"
        assert response.commit_date == datetime(2023, 1, 1, 12, 0, 0)

    def test_search_result_response_without_metadata(self) -> None:
        """Test creating SearchResultResponse without metadata."""
        search_result = SearchResult(
            commit_hash="abc123",
            file_path="test.py",
            line_number=10,
            matching_line="def test() -> None:",  # Fixed: line_content -> matching_line
            search_type=SearchType.CONTENT,  # Fixed: match_type -> search_type
            relevance_score=0.95
        )

        response = SearchResultResponse.from_search_result(
            search_result, include_metadata=False)

        assert response.commit_hash == "abc123"
        assert response.file_path == "test.py"
        assert response.author_name is None  # Fixed: commit_author -> author_name
        assert response.commit_message is None
        assert response.commit_date is None


class TestSearchResponse:
    """Test SearchResponse model."""

    def test_search_response_creation(self) -> None:
        """Test creating a SearchResponse."""
        result_response = SearchResultResponse(
            commit_hash="abc123",
            file_path="test.py",
            line_number=10,
            matching_line="def test() -> None:",  # Fixed: line_content -> matching_line
            search_type="content",  # Fixed: match_type -> search_type
            relevance_score=0.95
        )

        response = SearchResponse(
            results=[result_response],
            total_count=1,
            search_id="search_123",
            status="completed",
            commits_searched=10,
            files_searched=50,
            search_duration_ms=1500.0
        )

        assert len(response.results) == 1
        assert response.total_count == 1
        assert response.search_id == "search_123"
        assert response.status == "completed"
        assert response.commits_searched == 10
        assert response.files_searched == 50
        assert response.search_duration_ms == 1500.0
        assert response.error_message is None

    def test_search_response_from_results(self) -> None:
        """Test creating SearchResponse from search results."""
        search_result = SearchResult(
            commit_hash="abc123",
            file_path="test.py",
            line_number=10,
            matching_line="def test() -> None:",  # Fixed: line_content -> matching_line
            search_type=SearchType.CONTENT,  # Fixed: match_type -> search_type
            relevance_score=0.95
        )

        metrics = SearchMetrics(
            total_commits_searched=10,
            total_files_searched=50,
            matches_found=1,
            search_duration_ms=1500.0
        )

        response = SearchResponse.from_results(
            results=[search_result],
            search_id="search_123",
            metrics=metrics,
            include_metadata=False,
            status="completed"
        )

        assert len(response.results) == 1
        assert response.total_count == 1
        assert response.search_id == "search_123"
        assert response.status == "completed"
        assert response.commits_searched == 10
        assert response.files_searched == 50
        assert response.search_duration_ms == 1500.0

    def test_search_response_with_error(self) -> None:
        """Test SearchResponse with error."""
        response = SearchResponse(
            results=[],
            total_count=0,
            search_id="search_123",
            status="error",
            error_message="Repository not found"
        )

        assert len(response.results) == 0
        assert response.total_count == 0
        assert response.status == "error"
        assert response.error_message == "Repository not found"


class TestSearchStatusResponse:
    """Test SearchStatusResponse model."""

    def test_search_status_response_creation(self) -> None:
        """Test creating a SearchStatusResponse."""
        response = SearchStatusResponse(
            search_id="search_123",
            status="running",
            progress=0.5,
            message="Searching commits...",
            results_count=25,
            started_at=datetime.now()  # Required field
        )

        assert response.search_id == "search_123"
        assert response.status == "running"
        assert response.progress == 0.5
        assert response.message == "Searching commits..."
        assert response.results_count == 25
        # Remove assertions for fields that don't exist in the model
        # assert response.estimated_total == 100  # Field doesn't exist
        # assert response.error_message is None   # Field doesn't exist

    def test_search_status_response_with_error(self) -> None:
        """Test SearchStatusResponse with error."""
        response = SearchStatusResponse(
            search_id="search_123",
            status="error",
            progress=0.0,
            message="Invalid repository path",  # Use message field for error
            results_count=0,
            started_at=datetime.now()  # Required field
        )

        assert response.search_id == "search_123"
        assert response.status == "error"
        # Fixed: error_message -> message
        assert response.message == "Invalid repository path"


class TestExportRequest:
    """Test ExportRequest model."""

    def test_export_request_creation(self) -> None:
        """Test creating an ExportRequest."""
        request = ExportRequest(
            search_id="search_123",
            format=OutputFormat.JSON,
            include_metadata=True,
            filename="results.json"
        )

        assert request.search_id == "search_123"
        assert request.format == OutputFormat.JSON
        assert request.include_metadata is True
        assert request.filename == "results.json"

    def test_export_request_defaults(self) -> None:
        """Test ExportRequest default values."""
        request = ExportRequest(
            search_id="search_123",
            format=OutputFormat.CSV
        )

        assert request.search_id == "search_123"
        assert request.format == OutputFormat.CSV
        assert request.include_metadata is False
        assert request.filename is None


class TestHealthResponse:
    """Test HealthResponse model."""

    def test_health_response_creation(self) -> None:
        """Test creating a HealthResponse."""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            uptime_seconds=3600.0,
            active_searches=5
        )

        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.uptime_seconds == 3600.0
        assert response.active_searches == 5

    def test_health_response_unhealthy(self) -> None:
        """Test HealthResponse for unhealthy status."""
        response = HealthResponse(
            status="unhealthy",
            version="1.0.0",
            uptime_seconds=100.0,
            active_searches=0
        )

        assert response.status == "unhealthy"
        assert response.version == "1.0.0"
        assert response.uptime_seconds == 100.0
        assert response.active_searches == 0
