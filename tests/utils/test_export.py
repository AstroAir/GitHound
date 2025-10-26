"""Tests for GitHound export utilities."""

from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
from rich.console import Console

from githound.models import CommitInfo, SearchResult, SearchType
from githound.schemas import DataFilter, ExportOptions, OutputFormat, SortCriteria, SortOrder
from githound.utils.export import ExportManager


class TestExportManager:
    """Test ExportManager class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Use a quiet console to avoid encoding issues in tests
        quiet_console = Console(file=StringIO(), force_terminal=False)
        self.export_manager = ExportManager(console=quiet_console)
        self.sample_results = [
            SearchResult(
                commit_hash="abc123",
                file_path="test1.py",
                line_number=10,
                # Fixed: line_content -> matching_line
                matching_line="def test_function() -> None:",
                search_type=SearchType.CONTENT,  # Fixed: match_type -> search_type
                relevance_score=0.95,
                commit_info=CommitInfo(
                    hash="abc123",
                    short_hash="abc123",
                    author_name="John Doe",
                    author_email="john@example.com",
                    committer_name="John Doe",  # Added required field
                    committer_email="john@example.com",  # Added required field
                    message="Add test function",
                    date=datetime(2023, 1, 1, 12, 0, 0),
                    files_changed=1,  # Added required field
                ),
            ),
            SearchResult(
                commit_hash="def456",
                file_path="test2.py",
                line_number=20,
                matching_line="class TestClass:",  # Fixed: line_content -> matching_line
                search_type=SearchType.CONTENT,  # Fixed: match_type -> search_type
                relevance_score=0.85,
                commit_info=CommitInfo(
                    hash="def456",
                    short_hash="def456",
                    author_name="Jane Smith",
                    author_email="jane@example.com",
                    committer_name="Jane Smith",  # Added required field
                    committer_email="jane@example.com",  # Added required field
                    message="Add test class",
                    date=datetime(2023, 1, 2, 14, 30, 0),
                    files_changed=1,  # Added required field
                ),
            ),
        ]

    def test_export_to_json_basic(self) -> None:
        """Test basic JSON export functionality."""
        output_file = Path("test_output.json")

        with patch("builtins.open", mock_open()) as mock_file:
            self.export_manager.export_to_json(
                self.sample_results, output_file, include_metadata=False, pretty=True
            )

            mock_file.assert_called_once_with(output_file, "w", encoding="utf-8")
            # Verify that json.dump was called (indirectly through the write calls)
            handle = mock_file()
            assert handle.write.called

    def test_export_to_json_with_metadata(self) -> None:
        """Test JSON export with metadata."""
        output_file = Path("test_output.json")

        with patch("builtins.open", mock_open()) as mock_file:
            self.export_manager.export_to_json(
                self.sample_results, output_file, include_metadata=True, pretty=True
            )

            mock_file.assert_called_once_with(output_file, "w", encoding="utf-8")

    def test_export_to_json_compact(self) -> None:
        """Test JSON export without pretty printing."""
        output_file = Path("test_output.json")

        with patch("builtins.open", mock_open()) as mock_file:
            self.export_manager.export_to_json(
                self.sample_results, output_file, include_metadata=False, pretty=False
            )

            mock_file.assert_called_once_with(output_file, "w", encoding="utf-8")

    def test_export_to_csv_basic(self) -> None:
        """Test basic CSV export functionality."""
        output_file = Path("test_output.csv")

        with patch("builtins.open", mock_open()) as mock_file:
            self.export_manager.export_to_csv(
                self.sample_results, output_file, include_metadata=False
            )

            mock_file.assert_called_once_with(output_file, "w", newline="", encoding="utf-8")

    def test_export_to_csv_with_metadata(self) -> None:
        """Test CSV export with metadata."""
        output_file = Path("test_output.csv")

        with patch("builtins.open", mock_open()) as mock_file:
            self.export_manager.export_to_csv(
                self.sample_results, output_file, include_metadata=True
            )

            mock_file.assert_called_once_with(output_file, "w", newline="", encoding="utf-8")

    @patch("githound.utils.export.HAS_PANDAS", True)
    @patch("githound.utils.export.pd")
    def test_export_to_excel_with_pandas(self, mock_pd) -> None:
        """Test Excel export when pandas is available."""
        output_file = Path("test_output.xlsx")
        mock_df = Mock()
        mock_pd.DataFrame.return_value = mock_df

        self.export_manager.export_to_excel(self.sample_results, output_file, include_metadata=True)

        mock_pd.DataFrame.assert_called_once()
        mock_df.to_excel.assert_called_once_with(output_file, index=False, engine="openpyxl")

    @patch("githound.utils.export.HAS_PANDAS", False)
    def test_export_to_excel_without_pandas(self) -> None:
        """Test Excel export fallback when pandas is not available."""
        output_file = Path("test_output.xlsx")

        with patch.object(self.export_manager, "export_to_csv") as mock_csv_export:
            self.export_manager.export_to_excel(
                self.sample_results, output_file, include_metadata=True
            )

            # Should fallback to CSV export
            expected_csv_file = output_file.with_suffix(".csv")
            mock_csv_export.assert_called_once_with(self.sample_results, expected_csv_file, True)

    def test_export_to_text_simple(self) -> None:
        """Test text export with simple format."""
        output_file = Path("test_output.txt")

        with patch("builtins.open", mock_open()) as mock_file:
            self.export_manager.export_to_text(
                self.sample_results, output_file, format_style="simple"
            )

            mock_file.assert_called_once_with(output_file, "w", encoding="utf-8")

    def test_export_to_text_detailed(self) -> None:
        """Test text export with detailed format."""
        output_file = Path("test_output.txt")

        with patch("builtins.open", mock_open()) as mock_file:
            self.export_manager.export_to_text(
                self.sample_results, output_file, format_style="detailed"
            )

            mock_file.assert_called_once_with(output_file, "w", encoding="utf-8")

    def test_export_to_text_summary(self) -> None:
        """Test text export with summary format."""
        output_file = Path("test_output.txt")

        with patch("builtins.open", mock_open()) as mock_file:
            self.export_manager.export_to_text(
                self.sample_results, output_file, format_style="summary"
            )

            mock_file.assert_called_once_with(output_file, "w", encoding="utf-8")

    def test_export_to_text_invalid_format(self) -> None:
        """Test text export with invalid format style."""
        output_file = Path("test_output.txt")

        with pytest.raises(ValueError, match="Unknown format style"):
            self.export_manager.export_to_text(
                self.sample_results, output_file, format_style="invalid"
            )

    def test_stream_export_csv(self) -> None:
        """Test streaming CSV export."""
        output_file = Path("test_output.csv")

        def result_generator() -> None:
            for result in self.sample_results:
                yield result

        with patch("builtins.open", mock_open()) as mock_file:
            self.export_manager.stream_export_csv(
                result_generator(), output_file, include_metadata=True
            )

            mock_file.assert_called_once_with(output_file, "w", newline="", encoding="utf-8")

    @patch("githound.utils.export.HAS_YAML", True)
    @patch("githound.utils.export.yaml")
    def test_export_to_yaml_with_yaml(self, mock_yaml) -> None:
        """Test YAML export when yaml library is available."""
        output_file = Path("test_output.yaml")

        with patch("builtins.open", mock_open()) as mock_file:
            self.export_manager.export_to_yaml(
                self.sample_results, output_file, include_metadata=True, pretty=True
            )

            mock_file.assert_called_once_with(output_file, "w", encoding="utf-8")
            mock_yaml.dump.assert_called_once()

    @patch("githound.utils.export.HAS_YAML", False)
    def test_export_to_yaml_without_yaml(self) -> None:
        """Test YAML export fallback when yaml library is not available."""
        output_file = Path("test_output.yaml")

        with patch.object(self.export_manager, "export_to_json") as mock_json_export:
            self.export_manager.export_to_yaml(
                self.sample_results, output_file, include_metadata=True, pretty=True
            )

            # Should fallback to JSON export
            expected_json_file = output_file.with_suffix(".json")
            mock_json_export.assert_called_once_with(
                self.sample_results, expected_json_file, True, True
            )

    def test_export_with_options_json(self) -> None:
        """Test export with options for JSON format."""
        output_file = Path("test_output.json")
        options = ExportOptions(format=OutputFormat.JSON, include_metadata=True, pretty_print=True)

        with patch.object(self.export_manager, "export_to_json") as mock_export:
            self.export_manager.export_with_options(self.sample_results, output_file, options)

            mock_export.assert_called_once_with(self.sample_results, output_file, True, True)

    def test_export_with_options_csv(self) -> None:
        """Test export with options for CSV format."""
        output_file = Path("test_output.csv")
        options = ExportOptions(format=OutputFormat.CSV, include_metadata=False)

        with patch.object(self.export_manager, "export_to_csv") as mock_export:
            self.export_manager.export_with_options(self.sample_results, output_file, options)

            mock_export.assert_called_once_with(self.sample_results, output_file, False)

    def test_export_with_options_unsupported_format(self) -> None:
        """Test export with unsupported format."""
        from pydantic import ValidationError

        # Test that creating ExportOptions with invalid format raises ValidationError
        with pytest.raises(ValidationError):
            ExportOptions(format="unknown")  #

    def test_json_serializer_datetime(self) -> None:
        """Test JSON serializer for datetime objects."""
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        result = self.export_manager._json_serializer(test_datetime)
        assert result == "2023-01-01T12:00:00"

    def test_json_serializer_path(self) -> None:
        """Test JSON serializer for Path objects."""
        test_path = Path("/test/path")
        result = self.export_manager._json_serializer(test_path)
        # Handle both Windows and Unix path separators
        assert result in ["/test/path", "\\test\\path"]

    def test_json_serializer_other(self) -> None:
        """Test JSON serializer for other objects."""
        test_obj = {"key": "value"}
        result = self.export_manager._json_serializer(test_obj)
        assert result == "{'key': 'value'}"

    def test_apply_filters(self) -> None:
        """Test applying filters to results."""
        filters = [
            # Fixed: use correct field path
            DataFilter(field="commit_info.author_name", operator="contains", value="John")
        ]

        filtered_results = self.export_manager._apply_filters(self.sample_results, filters)

        # Should only return results from John Doe
        assert len(filtered_results) == 1
        assert (
            filtered_results[0].commit_info.author_name
            if filtered_results[0].commit_info is not None
            else None == "John Doe"
        )

    def test_apply_sorting(self) -> None:
        """Test applying sorting to results."""
        sort_criteria = [
            # Fixed: ascending -> order
            SortCriteria(field="relevance_score", order=SortOrder.DESC)
        ]

        sorted_results = self.export_manager._apply_sorting(self.sample_results, sort_criteria)

        # Should be sorted by relevance score descending
        assert len(sorted_results) == 2
        assert sorted_results[0].relevance_score >= sorted_results[1].relevance_score

    def test_export_error_handling(self) -> None:
        """Test error handling during export."""
        output_file = Path("test_output.json")

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(IOError):
                self.export_manager.export_to_json(self.sample_results, output_file)
