"""Tests for structured data output functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from githound.models import (
    BlameLineInfo,
    BranchInfo,
    CommitInfo,
    FileBlameInfo,
    SearchResult,
    SearchType,
    TagInfo,
)
from githound.schemas import (
    AuthorSchema,
    CommitSchema,
    DataFilter,
    ExportOptions,
    FilterOperator,
    OutputFormat,
    SortCriteria,
    SortOrder,
)
from githound.utils.export import ExportManager


@pytest.fixture
def sample_commit_info():
    """Create sample commit info for testing."""
    return CommitInfo(
        hash="abc123def456",
        short_hash="abc123d",
        author_name="Test Author",
        author_email="test@example.com",
        committer_name="Test Committer",
        committer_email="committer@example.com",
        message="Test commit message",
        date=datetime(2023, 1, 1, 12, 0, 0),
        files_changed=2,
        insertions=10,
        deletions=5,
        parents=["parent123"],
    )


@pytest.fixture
def sample_search_results(sample_commit_info):
    """Create sample search results for testing."""
    return [
        SearchResult(
            commit_hash="abc123def456",
            file_path=Path("test1.py"),
            line_number=10,
            matching_line="def test_function():",
            commit_info=sample_commit_info,
            search_type=SearchType.CONTENT,
            relevance_score=0.9,
            search_time_ms=15.5,
        ),
        SearchResult(
            commit_hash="def456ghi789",
            file_path=Path("test2.py"),
            line_number=25,
            matching_line="class TestClass:",
            commit_info=CommitInfo(
                hash="def456ghi789",
                short_hash="def456g",
                author_name="Another Author",
                author_email="another@example.com",
                committer_name="Another Committer",
                committer_email="another_committer@example.com",
                message="Another test commit",
                date=datetime(2023, 1, 2, 14, 30, 0),
                files_changed=1,
                insertions=5,
                deletions=2,
                parents=["parent456"],
            ),
            search_type=SearchType.CONTENT,
            relevance_score=0.8,
            search_time_ms=12.3,
        ),
    ]


class TestSchemas:
    """Tests for data schemas."""

    def test_author_schema_creation(self):
        """Test AuthorSchema creation and validation."""
        author = AuthorSchema(
            name="Test Author",
            email="test@example.com",
            commits_count=10,
            lines_authored=500,
            first_commit_date=datetime(2023, 1, 1),
            last_commit_date=datetime(2023, 12, 31),
            files_touched=25,
        )

        assert author.name == "Test Author"
        assert author.email == "test@example.com"
        assert author.commits_count == 10
        assert author.lines_authored == 500
        assert author.files_touched == 25

    def test_commit_schema_creation(self, sample_commit_info):
        """Test CommitSchema creation."""
        author = AuthorSchema(
            name=sample_commit_info.author_name, email=sample_commit_info.author_email
        )
        committer = AuthorSchema(
            name=sample_commit_info.committer_name, email=sample_commit_info.committer_email
        )

        commit = CommitSchema(
            hash=sample_commit_info.hash,
            short_hash=sample_commit_info.short_hash,
            author=author,
            committer=committer,
            message=sample_commit_info.message,
            date=sample_commit_info.date,
            parent_hashes=sample_commit_info.parents,
            stats={
                "files_changed": sample_commit_info.files_changed,
                "insertions": sample_commit_info.insertions,
                "deletions": sample_commit_info.deletions,
            },
        )

        assert commit.hash == sample_commit_info.hash
        assert commit.author.name == sample_commit_info.author_name
        assert commit.stats["files_changed"] == sample_commit_info.files_changed

    def test_export_options_validation(self):
        """Test ExportOptions validation."""
        options = ExportOptions(
            format=OutputFormat.JSON,
            include_metadata=True,
            pretty_print=True,
            filters=[
                DataFilter(field="commit_hash", operator=FilterOperator.CONTAINS, value="abc123")
            ],
            sort_by=[SortCriteria(field="relevance_score", order=SortOrder.DESC)],
        )

        assert options.format == OutputFormat.JSON
        assert options.include_metadata is True
        assert len(options.filters) == 1
        assert len(options.sort_by) == 1
        assert options.filters[0].operator == FilterOperator.CONTAINS


class TestEnhancedModels:
    """Tests for enhanced data models."""

    def test_branch_info_creation(self):
        """Test BranchInfo model creation."""
        branch = BranchInfo(
            name="main",
            commit_hash="abc123def456",
            is_remote=False,
            ahead_count=5,
            behind_count=0,
            last_commit_date=datetime(2023, 1, 1),
            last_commit_author="Test Author <test@example.com>",
        )

        assert branch.name == "main"
        assert branch.commit_hash == "abc123def456"
        assert branch.is_remote is False
        assert branch.ahead_count == 5

    def test_tag_info_creation(self):
        """Test TagInfo model creation."""
        tag = TagInfo(
            name="v1.0.0",
            commit_hash="abc123def456",
            message="Release version 1.0.0",
            tagger="Tagger <tagger@example.com>",
            tag_date=datetime(2023, 1, 1),
            is_annotated=True,
        )

        assert tag.name == "v1.0.0"
        assert tag.commit_hash == "abc123def456"
        assert tag.is_annotated is True

    def test_blame_line_info_creation(self):
        """Test BlameLineInfo model creation."""
        blame_line = BlameLineInfo(
            line_number=1,
            content="def test_function():",
            commit_hash="abc123def456",
            author_name="Test Author",
            author_email="test@example.com",
            commit_date=datetime(2023, 1, 1),
            commit_message="Add test function",
        )

        assert blame_line.line_number == 1
        assert blame_line.content == "def test_function():"
        assert blame_line.commit_hash == "abc123def456"

    def test_file_blame_info_creation(self):
        """Test FileBlameInfo model creation."""
        blame_lines = [
            BlameLineInfo(
                line_number=1,
                content="def test_function():",
                commit_hash="abc123def456",
                author_name="Test Author",
                author_email="test@example.com",
                commit_date=datetime(2023, 1, 1),
                commit_message="Add test function",
            )
        ]

        file_blame = FileBlameInfo(
            file_path="test.py",
            total_lines=1,
            blame_lines=blame_lines,
            contributors=["Test Author <test@example.com>"],
            oldest_line_date=datetime(2023, 1, 1),
            newest_line_date=datetime(2023, 1, 1),
            file_age_days=365,
        )

        assert file_blame.file_path == "test.py"
        assert file_blame.total_lines == 1
        assert len(file_blame.blame_lines) == 1
        assert len(file_blame.contributors) == 1


class TestExportManager:
    """Tests for enhanced export functionality."""

    def test_yaml_export(self, sample_search_results):
        """Test YAML export functionality."""
        export_manager = ExportManager()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            output_file = Path(f.name)

        try:
            export_manager.export_to_yaml(sample_search_results, output_file)

            # Verify file was created and contains valid YAML
            assert output_file.exists()

            with open(output_file, encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)

            assert isinstance(yaml_data, dict)
            assert "results" in yaml_data
            assert len(yaml_data["results"]) == 2

        finally:
            if output_file.exists():
                output_file.unlink()

    def test_export_with_options_json(self, sample_search_results):
        """Test export with options - JSON format."""
        export_manager = ExportManager()

        options = ExportOptions(
            format=OutputFormat.JSON,
            include_metadata=True,
            pretty_print=True,
            filters=[
                DataFilter(
                    field="relevance_score", operator=FilterOperator.GREATER_THAN, value=0.85
                )
            ],
            sort_by=[SortCriteria(field="relevance_score", order=SortOrder.DESC)],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = Path(f.name)

        try:
            export_manager.export_with_options(sample_search_results, output_file, options)

            # Verify file was created and contains filtered results
            assert output_file.exists()

            with open(output_file, encoding="utf-8") as f:
                json_data = json.load(f)

            assert isinstance(json_data, dict)
            assert "results" in json_data
            # Should only have 1 result with relevance_score > 0.85
            assert len(json_data["results"]) == 1
            assert json_data["results"][0]["relevance_score"] == 0.9

        finally:
            if output_file.exists():
                output_file.unlink()

    def test_filter_evaluation(self, sample_search_results):
        """Test filter evaluation logic."""
        export_manager = ExportManager()

        # Test CONTAINS filter
        contains_filter = DataFilter(
            field="matching_line", operator=FilterOperator.CONTAINS, value="function"
        )

        filtered_results = export_manager._apply_filters(sample_search_results, [contains_filter])
        assert len(filtered_results) == 1
        assert (
            filtered_results[0].matching_line is not None
            and "function" in filtered_results[0].matching_line
        )

        # Test GREATER_THAN filter
        gt_filter = DataFilter(
            field="relevance_score", operator=FilterOperator.GREATER_THAN, value=0.85
        )

        filtered_results = export_manager._apply_filters(sample_search_results, [gt_filter])
        assert len(filtered_results) == 1
        assert filtered_results[0].relevance_score > 0.85

    def test_sorting_functionality(self, sample_search_results):
        """Test sorting functionality."""
        export_manager = ExportManager()

        # Test descending sort by relevance_score
        sort_criteria = [SortCriteria(field="relevance_score", order=SortOrder.DESC)]

        sorted_results = export_manager._apply_sorting(sample_search_results, sort_criteria)
        assert len(sorted_results) == 2
        assert sorted_results[0].relevance_score >= sorted_results[1].relevance_score

        # Test ascending sort by line_number
        sort_criteria = [SortCriteria(field="line_number", order=SortOrder.ASC)]

        sorted_results = export_manager._apply_sorting(sample_search_results, sort_criteria)
        assert len(sorted_results) == 2
        assert (sorted_results[0].line_number or 0) <= (sorted_results[1].line_number or 0)

    def test_field_value_extraction(self, sample_search_results):
        """Test field value extraction with dot notation."""
        export_manager = ExportManager()

        result = sample_search_results[0]

        # Test simple field
        assert export_manager._get_field_value(result, "commit_hash") == "abc123def456"

        # Test nested field
        assert export_manager._get_field_value(result, "commit_info.author_name") == "Test Author"

        # Test non-existent field
        assert export_manager._get_field_value(result, "non_existent_field") is None


class TestDataValidation:
    """Tests for data validation and serialization."""

    def test_datetime_serialization(self, sample_commit_info):
        """Test datetime serialization in models."""
        # Test that datetime fields are properly handled
        # Use dict() for Pydantic v1 compatibility instead of model_dump()
        commit_dict = sample_commit_info.dict()

        assert isinstance(commit_dict["date"], datetime)

        # Test JSON serialization
        # Use json() for Pydantic v1 compatibility instead of model_dump_json()
        json_str = sample_commit_info.json()
        assert isinstance(json_str, str)

        # Parse back and verify
        parsed_data = json.loads(json_str)
        assert "date" in parsed_data

    def test_model_validation_errors(self):
        """Test model validation with invalid data."""
        with pytest.raises(ValueError):
            # Missing required fields should raise validation error
            CommitInfo(
                hash="abc123",
                short_hash="abc",
                author_name="Test Author",
                author_email="test@example.com",
                committer_name="Test Committer",
                committer_email="test@example.com",
                message="Test commit",
                date="invalid_date",  # This should cause validation error
                files_changed=1,
            )

    def test_enum_validation(self):
        """Test enum validation in models."""
        # Test valid enum value
        options = ExportOptions(format=OutputFormat.JSON)
        assert options.format == OutputFormat.JSON

        # Test invalid enum value should be caught by Pydantic
        with pytest.raises(ValueError):
            ExportOptions(format="invalid_format")
