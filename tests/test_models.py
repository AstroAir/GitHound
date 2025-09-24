"""Tests for GitHound core models."""

from datetime import datetime
from pathlib import Path

from githound.models import (
    BlameLineInfo,
    BranchInfo,
    CommitInfo,
    FileBlameInfo,
    FileChangeInfo,
    OutputFormat,
    RemoteInfo,
    RepositoryInfo,
    SearchConfig,
    SearchMetrics,
    SearchQuery,
    SearchResult,
    SearchType,
    TagInfo,
)


class TestSearchType:
    """Test SearchType enum."""

    def test_search_type_values(self) -> None:
        """Test that SearchType has expected values."""
        assert SearchType.CONTENT == "content"
        assert SearchType.COMMIT_HASH == "commit_hash"
        assert SearchType.AUTHOR == "author"
        assert SearchType.MESSAGE == "message"
        assert SearchType.DATE_RANGE == "date_range"
        assert SearchType.FILE_PATH == "file_path"
        assert SearchType.FILE_TYPE == "file_type"
        assert SearchType.COMBINED == "combined"


class TestOutputFormat:
    """Test OutputFormat enum."""

    def test_output_format_values(self) -> None:
        """Test that OutputFormat has expected values."""
        assert OutputFormat.TEXT == "text"
        assert OutputFormat.JSON == "json"
        assert OutputFormat.CSV == "csv"


class TestSearchQuery:
    """Test SearchQuery model."""

    def test_search_query_creation(self) -> None:
        """Test creating a SearchQuery with basic parameters."""
        query = SearchQuery(
            content_pattern="test", author_pattern="john", case_sensitive=True, fuzzy_search=False
        )

        assert query.content_pattern == "test"
        assert query.author_pattern == "john"
        assert query.case_sensitive is True
        assert query.fuzzy_search is False

    def test_search_query_defaults(self) -> None:
        """Test SearchQuery default values."""
        query = SearchQuery()

        assert query.content_pattern is None
        assert query.commit_hash is None
        assert query.author_pattern is None
        assert query.message_pattern is None
        assert query.case_sensitive is False
        assert query.fuzzy_search is False
        assert query.fuzzy_threshold == 0.8
        assert query.include_globs is None  # Fixed: defaults to None, not []
        assert query.exclude_globs is None  # Fixed: defaults to None, not []

    def test_search_query_date_range(self) -> None:
        """Test SearchQuery with date range."""
        date_from = datetime(2023, 1, 1)
        date_to = datetime(2023, 12, 31)

        query = SearchQuery(date_from=date_from, date_to=date_to)

        assert query.date_from == date_from
        assert query.date_to == date_to


class TestSearchResult:
    """Test SearchResult model."""

    def test_search_result_creation(self) -> None:
        """Test creating a SearchResult."""
        result = SearchResult(
            commit_hash="abc123",
            file_path="test.py",
            line_number=10,
            matching_line="def test() -> None:",  # Fixed: line_content -> matching_line
            search_type=SearchType.CONTENT,  # Fixed: match_type -> search_type
            relevance_score=0.95,
        )

        assert result.commit_hash == "abc123"
        # Fixed: file_path is a Path object
        assert str(result.file_path) == "test.py"
        assert result.line_number == 10
        # Fixed: line_content -> matching_line
        assert result.matching_line == "def test() -> None:"
        # Fixed: match_type -> search_type
        assert result.search_type == SearchType.CONTENT
        assert result.relevance_score == 0.95

    def test_search_result_with_commit_info(self) -> None:
        """Test SearchResult with commit information."""
        commit_info = CommitInfo(
            hash="abc123",
            short_hash="abc123",
            author_name="John Doe",
            author_email="john@example.com",
            committer_name="John Doe",  # Added required field
            committer_email="john@example.com",  # Added required field
            message="Test commit",
            date=datetime.now(),
            files_changed=1,  # Added required field
        )

        result = SearchResult(
            commit_hash="abc123",
            file_path="test.py",
            line_number=10,
            matching_line="def test() -> None:",  # Fixed: line_content -> matching_line
            search_type=SearchType.CONTENT,  # Fixed: match_type -> search_type
            commit_info=commit_info,
        )

        assert result.commit_info == commit_info
        assert result.commit_info.author_name == "John Doe"


class TestSearchMetrics:
    """Test SearchMetrics model."""

    def test_search_metrics_creation(self) -> None:
        """Test creating SearchMetrics."""
        metrics = SearchMetrics(
            total_commits_searched=100,
            total_files_searched=500,
            total_results_found=25,  # Fixed: matches_found -> total_results_found
            search_duration_ms=1500.0,
        )

        assert metrics.total_commits_searched == 100
        assert metrics.total_files_searched == 500
        # Fixed: matches_found -> total_results_found
        assert metrics.total_results_found == 25
        assert metrics.search_duration_ms == 1500.0

    def test_search_metrics_defaults(self) -> None:
        """Test SearchMetrics default values."""
        metrics = SearchMetrics()

        assert metrics.total_commits_searched == 0
        assert metrics.total_files_searched == 0
        # Fixed: matches_found -> total_results_found
        assert metrics.total_results_found == 0
        assert metrics.search_duration_ms == 0.0


class TestSearchConfig:
    """Test SearchConfig model."""

    def test_search_config_creation(self) -> None:
        """Test creating SearchConfig."""
        config = SearchConfig(case_sensitive=True, max_results=100, timeout_seconds=30)

        assert config.case_sensitive is True  # [attr-defined]
        assert config.max_results == 100  # [attr-defined]
        assert config.timeout_seconds == 30  # [attr-defined]

    def test_search_config_defaults(self) -> None:
        """Test SearchConfig default values."""
        config = SearchConfig()

        assert config.case_sensitive is False  # [attr-defined]
        # Fixed: defaults to None, not 1000  # [attr-defined]
        assert config.max_results is None
        # Fixed: defaults to None, not 60  # [attr-defined]
        assert config.timeout_seconds is None


class TestFileChangeInfo:
    """Test FileChangeInfo model."""

    def test_file_change_info_creation(self) -> None:
        """Test creating FileChangeInfo."""
        change = FileChangeInfo(
            file_path="test.py", change_type="modified", lines_added=10, lines_deleted=5
        )

        assert change.file_path == "test.py"
        assert change.change_type == "modified"
        assert change.lines_added == 10
        assert change.lines_deleted == 5


class TestCommitInfo:
    """Test CommitInfo model."""

    def test_commit_info_creation(self) -> None:
        """Test creating CommitInfo."""
        commit_date = datetime.now()
        commit = CommitInfo(
            hash="abc123def456",
            short_hash="abc123d",
            author_name="John Doe",
            author_email="john@example.com",
            committer_name="John Doe",  # Added required field
            committer_email="john@example.com",  # Added required field
            message="Fix bug in search",
            date=commit_date,
            files_changed=3,  # Added required field
        )

        assert commit.hash == "abc123def456"
        assert commit.short_hash == "abc123d"
        assert commit.author_name == "John Doe"
        assert commit.author_email == "john@example.com"
        assert commit.message == "Fix bug in search"
        assert commit.date == commit_date


class TestRepositoryInfo:
    """Test RepositoryInfo model."""

    def test_repository_info_creation(self) -> None:
        """Test creating RepositoryInfo."""
        repo = RepositoryInfo(
            path="/path/to/repo",
            name="test-repo",
            is_bare=False,
            head_commit="abc123",
            active_branch="main",
            total_commits=100,
        )

        assert repo.path == "/path/to/repo"
        assert repo.name == "test-repo"
        assert repo.is_bare is False
        assert repo.head_commit == "abc123"
        assert repo.active_branch == "main"
        assert repo.total_commits == 100


class TestBlameLineInfo:
    """Test BlameLineInfo model."""

    def test_blame_line_info_creation(self) -> None:
        """Test creating BlameLineInfo."""
        blame_date = datetime.now()
        blame_line = BlameLineInfo(
            line_number=10,
            content="def test() -> None:",
            commit_hash="abc123",
            author_name="John Doe",
            author_email="john@example.com",
            commit_date=blame_date,  # Fixed: date -> commit_date
            commit_message="Test commit",  # Added required field
        )

        assert blame_line.line_number == 10
        assert blame_line.content == "def test() -> None:"
        assert blame_line.commit_hash == "abc123"
        assert blame_line.author_name == "John Doe"
        assert blame_line.author_email == "john@example.com"
        assert blame_line.commit_date == blame_date  # Fixed: date -> commit_date


class TestFileBlameInfo:
    """Test FileBlameInfo model."""

    def test_file_blame_info_creation(self) -> None:
        """Test creating FileBlameInfo."""
        blame_line = BlameLineInfo(
            line_number=1,
            content="# Test file",
            commit_hash="abc123",
            author_name="John Doe",
            author_email="john@example.com",
            commit_date=datetime.now(),  # Fixed: date -> commit_date
            commit_message="Test commit",  # Added required field
        )

        file_blame = FileBlameInfo(
            file_path="test.py",
            total_lines=100,
            blame_lines=[blame_line],
            contributors=["John Doe"],
        )

        assert file_blame.file_path == "test.py"
        assert file_blame.total_lines == 100
        assert len(file_blame.blame_lines) == 1
        assert file_blame.contributors == ["John Doe"]
