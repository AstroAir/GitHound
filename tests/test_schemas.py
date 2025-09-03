"""Tests for GitHound schemas."""

from datetime import datetime
from pathlib import Path

from githound.schemas import (
    OutputFormat,
    SortOrder,  # Added missing import
    ExportOptions,
    PaginationInfo,
    SortCriteria,
    DataFilter,
    AuthorSchema,
    BranchSchema,
    TagSchema,
    FileChangeSchema,
    CommitSchema,
    BlameLineSchema,
    FileBlameSchema,
    DiffLineSchema,
    FileDiffSchema,
    CommitDiffSchema,
    RepositorySchema,
    SearchResultSchema,
    SearchResultsCollectionSchema,
)


class TestOutputFormat:
    """Test OutputFormat enum."""

    def test_output_format_values(self):
        """Test that OutputFormat has expected values."""
        assert OutputFormat.TEXT == "text"
        assert OutputFormat.JSON == "json"
        assert OutputFormat.CSV == "csv"
        assert OutputFormat.YAML == "yaml"
        assert OutputFormat.XML == "xml"
        assert OutputFormat.TEXT == "text"  # Fixed: HTML doesn't exist, use TEXT instead


class TestExportOptions:
    """Test ExportOptions schema."""

    def test_export_options_creation(self):
        """Test creating ExportOptions."""
        options = ExportOptions(
            format=OutputFormat.JSON,
            include_metadata=True,
            pretty_print=True
        )
        
        assert options.format == OutputFormat.JSON
        assert options.include_metadata is True
        assert options.pretty_print is True

    def test_export_options_defaults(self):
        """Test ExportOptions default values."""
        options = ExportOptions(format=OutputFormat.JSON)
        
        assert options.format == OutputFormat.JSON
        assert options.include_metadata is True  # Fixed: defaults to True, not False
        assert options.pretty_print is True  # Fixed: defaults to True, not False
        assert options.fields is None  # Fixed: defaults to None, not []
        assert options.exclude_fields is None  # Fixed: defaults to None, not []
        assert options.filters == []
        assert options.sort_by == []


class TestPaginationInfo:
    """Test PaginationInfo schema."""

    def test_pagination_info_creation(self):
        """Test creating PaginationInfo."""
        pagination = PaginationInfo(
            page=2,
            page_size=50,
            total_items=200,
            total_pages=4,
            has_next=True,  # Added required field
            has_previous=True  # Added required field
        )
        
        assert pagination.page == 2
        assert pagination.page_size == 50
        assert pagination.total_items == 200
        assert pagination.total_pages == 4

    def test_pagination_info_defaults(self):
        """Test PaginationInfo default values."""
        pagination = PaginationInfo(
            total_items=100,  # Required field
            total_pages=10,   # Required field
            has_next=True,    # Required field
            has_previous=False  # Required field
        )

        assert pagination.page == 1  # Default value
        assert pagination.page_size == 100  # Default value
        assert pagination.total_items == 100  # Value we provided
        assert pagination.total_pages == 10   # Value we provided


class TestSortCriteria:
    """Test SortCriteria schema."""

    def test_sort_criteria_creation(self):
        """Test creating SortCriteria."""
        sort = SortCriteria(
            field="date",
            order=SortOrder.DESC  # Fixed: ascending -> order
        )

        assert sort.field == "date"
        assert sort.order == SortOrder.DESC  # Fixed: ascending -> order

    def test_sort_criteria_defaults(self):
        """Test SortCriteria default values."""
        sort = SortCriteria(field="date")
        
        assert sort.field == "date"
        assert sort.order == SortOrder.ASC  # Fixed: ascending -> order, defaults to ASC


class TestDataFilter:
    """Test DataFilter schema."""

    def test_data_filter_creation(self):
        """Test creating DataFilter."""
        filter_obj = DataFilter(
            field="author",
            operator="contains",
            value="john"
        )
        
        assert filter_obj.field == "author"
        assert filter_obj.operator == "contains"
        assert filter_obj.value == "john"


class TestAuthorSchema:
    """Test AuthorSchema."""

    def test_author_schema_creation(self):
        """Test creating AuthorSchema."""
        author = AuthorSchema(
            name="John Doe",
            email="john@example.com",
            commits_count=50,
            lines_authored=1000
        )
        
        assert author.name == "John Doe"
        assert author.email == "john@example.com"
        assert author.commits_count == 50
        assert author.lines_authored == 1000

    def test_author_schema_minimal(self):
        """Test creating AuthorSchema with minimal data."""
        author = AuthorSchema(
            name="John Doe",
            email="john@example.com"
        )
        
        assert author.name == "John Doe"
        assert author.email == "john@example.com"
        assert author.commits_count is None
        assert author.lines_authored is None


class TestBranchSchema:
    """Test BranchSchema."""

    def test_branch_schema_creation(self):
        """Test creating BranchSchema."""
        branch = BranchSchema(
            name="main",
            commit_hash="abc123",  # Required field
            is_remote=False
        )

        assert branch.name == "main"
        assert branch.commit_hash == "abc123"
        assert branch.is_remote is False


class TestTagSchema:
    """Test TagSchema."""

    def test_tag_schema_creation(self):
        """Test creating TagSchema."""
        tag = TagSchema(
            name="v1.0.0",
            commit_hash="abc123",
            message="Release version 1.0.0"
        )
        
        assert tag.name == "v1.0.0"
        assert tag.commit_hash == "abc123"
        assert tag.message == "Release version 1.0.0"


class TestFileChangeSchema:
    """Test FileChangeSchema."""

    def test_file_change_schema_creation(self):
        """Test creating FileChangeSchema."""
        change = FileChangeSchema(
            file_path="src/main.py",
            change_type="modified",
            lines_added=10,
            lines_deleted=5,
            is_binary=False
        )
        
        assert change.file_path == "src/main.py"
        assert change.change_type == "modified"
        assert change.lines_added == 10
        assert change.lines_deleted == 5
        assert change.is_binary is False


class TestCommitSchema:
    """Test CommitSchema."""

    def test_commit_schema_creation(self):
        """Test creating CommitSchema."""
        author = AuthorSchema(name="John Doe", email="john@example.com")
        committer = AuthorSchema(name="John Doe", email="john@example.com")
        commit_date = datetime.now()
        
        commit = CommitSchema(
            hash="abc123def456",
            short_hash="abc123d",
            author=author,
            committer=committer,
            message="Fix bug in search",
            date=commit_date
        )
        
        assert commit.hash == "abc123def456"
        assert commit.short_hash == "abc123d"
        assert commit.author == author
        assert commit.committer == committer
        assert commit.message == "Fix bug in search"
        assert commit.date == commit_date


class TestBlameLineSchema:
    """Test BlameLineSchema."""

    def test_blame_line_schema_creation(self):
        """Test creating BlameLineSchema."""
        blame_date = datetime.now()
        author = AuthorSchema(name="John Doe", email="john@example.com")  # Create AuthorSchema
        blame_line = BlameLineSchema(
            line_number=10,
            content="def test():",
            commit_hash="abc123",
            author=author,  # Fixed: use AuthorSchema instead of separate fields
            commit_date=blame_date,  # Fixed: date -> commit_date
            commit_message="Test commit"  # Added required field
        )
        
        assert blame_line.line_number == 10
        assert blame_line.content == "def test():"
        assert blame_line.commit_hash == "abc123"
        assert blame_line.author.name == "John Doe"  # Fixed: access through author object
        assert blame_line.author.email == "john@example.com"  # Fixed: access through author object
        assert blame_line.commit_date == blame_date  # Fixed: date -> commit_date


class TestFileBlameSchema:
    """Test FileBlameSchema."""

    def test_file_blame_schema_creation(self):
        """Test creating FileBlameSchema."""
        author = AuthorSchema(name="John Doe", email="john@example.com")  # Create AuthorSchema
        blame_line = BlameLineSchema(
            line_number=1,
            content="# Test file",
            commit_hash="abc123",
            author=author,  # Fixed: use AuthorSchema instead of separate fields
            commit_date=datetime.now(),  # Fixed: date -> commit_date
            commit_message="Test commit"  # Added required field
        )
        
        file_blame = FileBlameSchema(
            file_path="test.py",
            total_lines=100,
            lines=[blame_line],  # Fixed: blame_lines -> lines
            contributors=[author]  # Added required field
        )
        
        assert file_blame.file_path == "test.py"
        assert file_blame.total_lines == 100
        assert len(file_blame.lines) == 1  # Fixed: blame_lines -> lines


class TestDiffLineSchema:
    """Test DiffLineSchema."""

    def test_diff_line_schema_creation(self):
        """Test creating DiffLineSchema."""
        diff_line = DiffLineSchema(
            line_number_new=10,  # Fixed: line_number -> line_number_new
            content="def test():",
            change_type="added"
        )

        assert diff_line.line_number_new == 10  # Fixed: line_number -> line_number_new
        assert diff_line.content == "def test():"
        assert diff_line.change_type == "added"


class TestFileDiffSchema:
    """Test FileDiffSchema."""

    def test_file_diff_schema_creation(self):
        """Test creating FileDiffSchema."""
        diff_line = DiffLineSchema(
            line_number=1,
            content="# Test file",
            change_type="added"
        )
        
        file_diff = FileDiffSchema(
            file_path="test.py",
            change_type="added",
            lines_added=10,
            lines_deleted=0,
            diff_lines=[diff_line]
        )
        
        assert file_diff.file_path == "test.py"
        assert file_diff.change_type == "added"
        assert file_diff.lines_added == 10
        assert file_diff.lines_deleted == 0
        assert len(file_diff.diff_lines) == 1


class TestCommitDiffSchema:
    """Test CommitDiffSchema."""

    def test_commit_diff_schema_creation(self):
        """Test creating CommitDiffSchema."""
        file_diff = FileDiffSchema(
            file_path="test.py",
            change_type="modified",
            lines_added=5,
            lines_deleted=2,
            diff_lines=[]
        )
        
        commit_diff = CommitDiffSchema(
            from_commit="abc123",
            to_commit="def456",
            files_changed=1,  # Fixed: should be int, not list
            total_additions=5,  # Fixed: total_lines_added -> total_additions
            total_deletions=2,  # Fixed: total_lines_deleted -> total_deletions
            file_diffs=[file_diff]  # Added required field
        )
        
        assert commit_diff.from_commit == "abc123"
        assert commit_diff.to_commit == "def456"
        assert commit_diff.files_changed == 1  # Fixed: files_changed is int, not list
        assert commit_diff.total_additions == 5  # Fixed: total_lines_added -> total_additions
        assert commit_diff.total_deletions == 2  # Fixed: total_lines_deleted -> total_deletions


class TestRepositorySchema:
    """Test RepositorySchema."""

    def test_repository_schema_creation(self):
        """Test creating RepositorySchema."""
        branch = BranchSchema(name="main", is_active=True, commit_hash="abc123")
        tag = TagSchema(name="v1.0.0", commit_hash="abc123")
        author = AuthorSchema(name="John Doe", email="john@example.com")
        
        repo = RepositorySchema(
            path="/path/to/repo",
            name="test-repo",
            is_bare=False,
            head_commit="abc123",
            active_branch="main",
            branches=[branch],
            tags=[tag],
            remotes=[{"origin": "https://github.com/user/repo.git"}],
            total_commits=100,
            contributors=[author]
        )
        
        assert repo.path == "/path/to/repo"
        assert repo.name == "test-repo"
        assert repo.is_bare is False
        assert repo.head_commit == "abc123"
        assert repo.active_branch == "main"
        assert len(repo.branches) == 1
        assert len(repo.tags) == 1
        assert len(repo.contributors) == 1


class TestSearchResultSchema:
    """Test SearchResultSchema."""

    def test_search_result_schema_creation(self):
        """Test creating SearchResultSchema."""
        commit = CommitSchema(
            hash="abc123",
            short_hash="abc123",
            author=AuthorSchema(name="John Doe", email="john@example.com"),
            committer=AuthorSchema(name="John Doe", email="john@example.com"),
            message="Test commit",
            date=datetime.now()
        )
        
        result = SearchResultSchema(
            commit=commit,  # Fixed: commit_info -> commit, and it's required
            file_path="test.py",
            line_number=10,
            matching_line="def test():",  # Fixed: line_content -> matching_line
            search_type="content",  # Fixed: match_type -> search_type, and it's required
            relevance_score=0.95
        )
        
        assert result.commit.hash == "abc123"  # Fixed: access through commit object
        assert result.file_path == "test.py"
        assert result.line_number == 10
        assert result.matching_line == "def test():"  # Fixed: line_content -> matching_line
        assert result.search_type == "content"  # Fixed: match_type -> search_type
        assert result.relevance_score == 0.95
        assert result.commit == commit  # Fixed: commit_info -> commit


class TestSearchResultsCollectionSchema:
    """Test SearchResultsCollectionSchema."""

    def test_search_results_collection_schema_creation(self):
        """Test creating SearchResultsCollectionSchema."""
        commit = CommitSchema(
            hash="abc123",
            short_hash="abc123",
            author=AuthorSchema(name="John Doe", email="john@example.com"),
            committer=AuthorSchema(name="John Doe", email="john@example.com"),
            message="Test commit",
            date=datetime.now()
        )

        result = SearchResultSchema(
            commit=commit,  # Fixed: provide required commit field
            file_path="test.py",
            line_number=10,
            matching_line="def test():",  # Fixed: line_content -> matching_line
            search_type="content",  # Fixed: match_type -> search_type, and it's required
            relevance_score=0.95
        )
        
        pagination = PaginationInfo(
            page=1,
            page_size=100,
            total_items=1,
            total_pages=1,
            has_next=False,  # Added required field
            has_previous=False  # Added required field
        )
        
        collection = SearchResultsCollectionSchema(
            query="test query",  # Added required field
            results=[result],
            total_results=1,  # Fixed: total_count -> total_results
            pagination=pagination,
            search_time_ms=150.0  # Fixed: search_duration_ms -> search_time_ms
        )
        
        assert len(collection.results) == 1
        assert collection.total_results == 1  # Fixed: total_count -> total_results
        assert collection.pagination == pagination
        assert collection.search_time_ms == 150.0  # Fixed: search_duration_ms -> search_time_ms
